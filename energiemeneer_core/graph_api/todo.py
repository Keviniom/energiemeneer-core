"""Microsoft To Do via Microsoft Graph — taken aanmaken én lezen.

Bron: ``aanmeldformulier_tool/ms_graph.py`` (``maak_todo_taak``). Generiek
gehouden: de aanroeper levert de lijstnaam en taaknaam aan — geen vaste
lijstnamen ingebakken.

De "naam al bezet → _1/_2"-logica zit ook hier in de core, om per ongeluk
dubbele taken voor hetzelfde dossier te voorkomen.

De lees-functies (:func:`lees_lijsten`, :func:`lees_taken`) zijn **alleen-lezen**
en maken — anders dan :func:`maak_taak` — **geen** lijst aan als die ontbreekt
(een onbekende lijst geeft simpelweg een lege lijst taken terug).

Zie BOUWPLAN.md, Module 6 (onderdeel 4).
"""

from __future__ import annotations

import logging
from typing import Any

from energiemeneer_core.graph_api import _client

_log = logging.getLogger(__name__)


def maak_taak(lijst_naam: str, taak_naam: str, deadline: str | None = None) -> dict[str, Any]:
    """Maak een taak aan in Microsoft To Do.

    Args:
        lijst_naam: naam van de To Do-lijst (wordt aangemaakt als hij nog
            niet bestaat).
        taak_naam: titel van de taak. Bestaat die al in de lijst, dan krijgt
            de taak een ``_1``/``_2``-achtervoegsel.
        deadline: optionele vervaldatum als ``"DD-MM-YYYY"``.

    Returns:
        Dict met ``id``, ``lijst``, ``taak`` (de uiteindelijke naam) en
        ``deadline``.

    Raises:
        ValueError: lege lijst-/taaknaam of een onleesbare datum.
        RuntimeError: Graph geeft een fout.
    """
    if not lijst_naam or not lijst_naam.strip():
        raise ValueError("lijst_naam is verplicht")
    if not taak_naam or not taak_naam.strip():
        raise ValueError("taak_naam is verplicht")

    lijst_id = _vind_of_maak_lijst(lijst_naam.strip())
    unieke_naam = _unieke_taaknaam(lijst_id, taak_naam.strip())

    payload: dict[str, Any] = {"title": unieke_naam}
    if deadline:
        payload["dueDateTime"] = {
            "dateTime": _deadline_naar_iso(deadline),
            "timeZone": "Europe/Amsterdam",
        }

    resp = _client.post(f"/me/todo/lists/{lijst_id}/tasks", json=payload)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Taak aanmaken mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )
    _log.info("To Do-taak aangemaakt in '%s': %s", lijst_naam, unieke_naam)
    return {
        "id": resp.json().get("id"),
        "lijst": lijst_naam,
        "taak": unieke_naam,
        "deadline": deadline,
    }


# ── Lezen (alleen-lezen) ─────────────────────────────────────────────────────
def lees_lijsten() -> list[dict[str, Any]]:
    """Geef alle To Do-lijsten terug als ``[{id, naam}]`` (alleen-lezen).

    Raises:
        RuntimeError: Graph geeft een fout.
    """
    resp = _client.get("/me/todo/lists")
    if resp.status_code != 200:
        raise RuntimeError(
            f"To Do-lijsten ophalen mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )
    return [{"id": l.get("id", ""), "naam": l.get("displayName", "")}
            for l in resp.json().get("value", [])]


def _vind_lijst_id(naam: str) -> str | None:
    """Zoek het id van een lijst op naam (hoofdletter-ongevoelig). Geen aanmaak;
    returnt ``None`` als de lijst niet bestaat."""
    if not naam or not naam.strip():
        return None
    for lijst in lees_lijsten():
        if lijst["naam"].lower() == naam.strip().lower():
            return lijst["id"]
    return None


def lees_taken(lijst_naam: str, alleen_open: bool = True, max: int = 100) -> list[dict[str, Any]]:
    """Lees de taken uit een To Do-lijst op naam (alleen-lezen).

    Args:
        lijst_naam: naam van de lijst (bijv. "Energielabels"). Bestaat de lijst
            niet, dan is het resultaat een lege lijst — er wordt **niets**
            aangemaakt.
        alleen_open: alleen niet-afgeronde taken (status ≠ ``completed``).
        max: maximaal aantal taken (Graph ``$top``).

    Returns:
        Lijst van dicts: ``titel``, ``status``, ``deadline`` (ISO of ""),
        ``notitie`` (body-tekst), ``aangemaakt`` en ``id``.

    Raises:
        RuntimeError: Graph geeft een fout (bij het ophalen van de lijsten/taken).
    """
    lijst_id = _vind_lijst_id(lijst_naam)
    if not lijst_id:
        return []

    resp = _client.get(
        f"/me/todo/lists/{lijst_id}/tasks",
        params={"$top": int(max),
                "$select": "id,title,status,dueDateTime,body,createdDateTime,importance"},
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"To Do-taken ophalen mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )

    taken = []
    for t in resp.json().get("value", []):
        status = t.get("status", "")
        if alleen_open and status == "completed":
            continue
        body = (t.get("body") or {}).get("content", "") or ""
        taken.append({
            "id": t.get("id", ""),
            "titel": t.get("title", "") or "",
            "status": status,
            "belangrijk": t.get("importance") == "high",
            "deadline": (t.get("dueDateTime") or {}).get("dateTime", "") or "",
            "notitie": body.strip(),
            "aangemaakt": t.get("createdDateTime", "") or "",
        })
    return taken


# ── Hulpjes ──────────────────────────────────────────────────────────────────


def _vind_of_maak_lijst(naam: str) -> str:
    """Geef het id van de lijst met deze naam; maak hem aan als hij ontbreekt."""
    resp = _client.get("/me/todo/lists")
    if resp.status_code != 200:
        raise RuntimeError(
            f"To Do-lijsten ophalen mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )
    for lijst in resp.json().get("value", []):
        if lijst.get("displayName", "").lower() == naam.lower():
            return lijst["id"]

    # Niet gevonden → aanmaken.
    resp = _client.post("/me/todo/lists", json={"displayName": naam})
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"To Do-lijst aanmaken mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )
    return resp.json()["id"]


def _unieke_taaknaam(lijst_id: str, taak_naam: str) -> str:
    """Voeg _1/_2 toe als de taaknaam al in de lijst voorkomt."""
    resp = _client.get(f"/me/todo/lists/{lijst_id}/tasks")
    if resp.status_code != 200:
        raise RuntimeError(
            f"To Do-taken ophalen mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )
    bestaande = {t.get("title", "").lower() for t in resp.json().get("value", [])}

    naam, teller = taak_naam, 1
    while naam.lower() in bestaande:
        naam = f"{taak_naam}_{teller}"
        teller += 1
    return naam


def _deadline_naar_iso(deadline: str) -> str:
    """Zet ``"DD-MM-YYYY"`` om naar het Graph-formaat ``YYYY-MM-DDT00:00:00``."""
    delen = deadline.strip().split("-")
    if len(delen) != 3:
        raise ValueError(f"Ongeldige deadline (verwacht DD-MM-YYYY): {deadline}")
    dag, maand, jaar = delen
    if not (dag.isdigit() and maand.isdigit() and jaar.isdigit()):
        raise ValueError(f"Ongeldige deadline (verwacht DD-MM-YYYY): {deadline}")
    return f"{jaar}-{maand.zfill(2)}-{dag.zfill(2)}T00:00:00.0000000"

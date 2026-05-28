"""Microsoft To Do via Microsoft Graph — een taak aanmaken.

Bron: ``aanmeldformulier_tool/ms_graph.py`` (``maak_todo_taak``). Generiek
gehouden: de aanroeper levert de lijstnaam en taaknaam aan — geen vaste
lijstnamen ingebakken.

De "naam al bezet → _1/_2"-logica zit ook hier in de core, om per ongeluk
dubbele taken voor hetzelfde dossier te voorkomen.

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

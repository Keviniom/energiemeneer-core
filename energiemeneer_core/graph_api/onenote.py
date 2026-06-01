"""OneNote via Microsoft Graph — een sjabloonpagina kopiëren en hernoemen.

Bron: ``DeEnergieMeneer_IntakeTool/backend/ms_graph.py`` (``maak_onenote_pagina``,
identiek in drie tools). Generiek gehouden: de namen van het notitieboek, de
sectie en de sjabloonpagina waren in de oude code ingebakken ("De Energiemeneer",
"Opnames", "Adres"). Die zijn hier losgemaakt tot parameters — geen vaste namen
in de core.

Dit is het gevoeligste onderdeel van Module 6, om twee redenen:

1. **Kopiëren is asynchroon.** ``copyToSection`` geeft niet meteen de nieuwe
   pagina terug, maar een *operatie*. De oude code deed blind ``sleep(4)`` en
   pakte daarna "de meest recent gewijzigde pagina met dezelfde titel" — gokwerk.
   Hier wachten we netjes op de statuslink van de operatie tot Microsoft
   "completed" meldt, en krijgen we het juiste pagina-id terug.

2. **De terugval mocht niet stil zijn.** Als de sjabloon ontbreekt, maakte de
   oude code zwijgend een lege pagina — waardoor een typefout in de sjabloontitel
   maandenlang ongemerkt lege pagina's opleverde. Hier is dat omgedraaid:
   standaard een duidelijke fout, en alléén een lege pagina als de aanroeper daar
   expliciet om vraagt (``maak_lege_bij_ontbreken=True``).

Zie BOUWPLAN.md, Module 6 (onderdeel 5).
"""

from __future__ import annotations

import html
import logging
import time
from typing import Any

from energiemeneer_core.graph_api import _client

_log = logging.getLogger(__name__)

# Het kopiëren is een asynchrone operatie; we pollen de statuslink.
_POLL_INTERVAL = 2  # seconden tussen twee statuschecks
_MAX_POGINGEN = 15  # samen ~30 s; ruim genoeg voor een pagina-kopie


def kopieer_sjabloonpagina(
    notitieboek_naam: str,
    sectie_naam: str,
    sjabloon_titel: str,
    nieuwe_titel: str,
    *,
    maak_lege_bij_ontbreken: bool = False,
) -> dict[str, Any]:
    """Kopieer een sjabloonpagina binnen een sectie en hernoem de kopie.

    De pagina wordt gekopieerd via ``copyToSection`` (zo blijven inkt en
    tekeningen behouden) en daarna hernoemd naar ``nieuwe_titel``. Bestaat die
    titel al in de sectie, dan krijgt de pagina een ``_1``/``_2``-achtervoegsel.

    Args:
        notitieboek_naam: naam van het notitieboek (exact, hoofdletter-ongevoelig).
        sectie_naam: naam van de sectie binnen dat notitieboek.
        sjabloon_titel: titel van de sjabloonpagina die gekopieerd wordt.
        nieuwe_titel: gewenste titel voor de nieuwe pagina.
        maak_lege_bij_ontbreken: als de sjabloon niet bestaat, maak dan een
            lege pagina aan i.p.v. een fout te geven. Standaard ``False`` —
            een ontbrekende sjabloon is dan een duidelijke fout, zodat een
            typefout of hernoemde sjabloon niet ongemerkt lege pagina's oplevert.

    Returns:
        Dict met ``id`` (de nieuwe pagina), ``titel`` (de uiteindelijke titel,
        kan ``_1``/``_2`` bevatten) en ``methode`` (``"kopie"`` of ``"leeg"``).

    Raises:
        ValueError: een verplichte naam ontbreekt.
        RuntimeError: notitieboek/sectie/sjabloon niet gevonden, of Graph geeft
            een fout. Ook als de sjabloon ontbreekt en
            ``maak_lege_bij_ontbreken`` ``False`` is.
    """
    for veld, waarde in (
        ("notitieboek_naam", notitieboek_naam),
        ("sectie_naam", sectie_naam),
        ("sjabloon_titel", sjabloon_titel),
        ("nieuwe_titel", nieuwe_titel),
    ):
        if not waarde or not waarde.strip():
            raise ValueError(f"{veld} is verplicht")

    notebook_id = _vind_notitieboek(notitieboek_naam.strip())
    sectie_id = _vind_sectie(notebook_id, notitieboek_naam.strip(), sectie_naam.strip())

    paginas = _haal_paginas(sectie_id)
    bestaande_titels = {p.get("title", "").strip().lower() for p in paginas}
    unieke_titel = _unieke_titel(nieuwe_titel.strip(), bestaande_titels)

    sjabloon_id = _vind_sjabloon(paginas, sjabloon_titel.strip())

    if sjabloon_id is None:
        if maak_lege_bij_ontbreken:
            pagina_id = _maak_lege_pagina(sectie_id, unieke_titel)
            _log.info(
                "OneNote-sjabloon '%s' niet gevonden — lege pagina '%s' aangemaakt "
                "zoals gevraagd",
                sjabloon_titel,
                unieke_titel,
            )
            return {"id": pagina_id, "titel": unieke_titel, "methode": "leeg"}
        raise RuntimeError(
            f"Sjabloonpagina '{sjabloon_titel}' niet gevonden in sectie "
            f"'{sectie_naam}' — controleer de titel. Geef "
            f"maak_lege_bij_ontbreken=True mee om bewust een lege pagina te maken."
        )

    nieuwe_id = _kopieer_en_wacht(sjabloon_id, sectie_id)
    _hernoem(nieuwe_id, unieke_titel)
    _log.info("OneNote-pagina gekopieerd uit sjabloon '%s': %s", sjabloon_titel, unieke_titel)
    return {"id": nieuwe_id, "titel": unieke_titel, "methode": "kopie"}


# ── Zoeken ───────────────────────────────────────────────────────────────────


def _vind_notitieboek(naam: str) -> str:
    resp = _client.get("/me/onenote/notebooks")
    if resp.status_code != 200:
        raise RuntimeError(
            f"Notitieboeken ophalen mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )
    for nb in resp.json().get("value", []):
        if nb.get("displayName", "").strip().lower() == naam.lower():
            return nb["id"]
    raise RuntimeError(f"Notitieboek '{naam}' niet gevonden")


def _vind_sectie(notebook_id: str, notitieboek_naam: str, naam: str) -> str:
    resp = _client.get(f"/me/onenote/notebooks/{notebook_id}/sections")
    if resp.status_code != 200:
        raise RuntimeError(
            f"Secties ophalen mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )
    for sec in resp.json().get("value", []):
        if sec.get("displayName", "").strip().lower() == naam.lower():
            return sec["id"]
    raise RuntimeError(
        f"Sectie '{naam}' niet gevonden in notitieboek '{notitieboek_naam}'"
    )


def _haal_paginas(sectie_id: str) -> list[dict[str, Any]]:
    resp = _client.get(
        f"/me/onenote/sections/{sectie_id}/pages", params={"$top": "100"}
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Pagina's ophalen mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )
    return resp.json().get("value", [])


def _vind_sjabloon(paginas: list[dict[str, Any]], titel: str) -> str | None:
    doel = titel.lower()
    for p in paginas:
        if p.get("title", "").strip().lower() == doel:
            return p["id"]
    return None


def _unieke_titel(titel: str, bestaande: set[str]) -> str:
    """Voeg _1/_2 toe als de titel al in de sectie voorkomt."""
    naam, teller = titel, 1
    while naam.lower() in bestaande:
        naam = f"{titel}_{teller}"
        teller += 1
    return naam


# ── Kopiëren (asynchroon) + hernoemen ───────────────────────────────────────────


def _kopieer_en_wacht(sjabloon_id: str, sectie_id: str) -> str:
    """Start copyToSection en wacht op de operatie tot de kopie klaar is."""
    resp = _client.post(
        f"/me/onenote/pages/{sjabloon_id}/copyToSection", json={"id": sectie_id}
    )
    if resp.status_code not in (200, 201, 202):
        raise RuntimeError(
            f"OneNote-kopie starten mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )

    operatie_id = _operatie_id(resp)
    return _wacht_op_operatie(operatie_id)


def _operatie_id(resp: Any) -> str:
    """Haal het id van de kopieer-operatie uit de body of de Operation-Location."""
    try:
        body = resp.json()
    except ValueError:
        body = {}
    if isinstance(body, dict) and body.get("id"):
        return body["id"]
    locatie = resp.headers.get("Operation-Location", "") if resp.headers else ""
    if locatie:
        return locatie.rstrip("/").rsplit("/", 1)[-1].split("?")[0]
    raise RuntimeError("OneNote-kopie gaf geen operatie-id terug")


def _wacht_op_operatie(operatie_id: str) -> str:
    """Pol de operatie-status tot 'completed' en geef het nieuwe pagina-id terug."""
    for poging in range(_MAX_POGINGEN):
        resp = _client.get(f"/me/onenote/operations/{operatie_id}")
        if resp.status_code != 200:
            raise RuntimeError(
                f"OneNote-operatie opvragen mislukt (HTTP {resp.status_code}): "
                f"{resp.text[:300]}"
            )
        body = resp.json()
        status = body.get("status")
        if status == "completed":
            return _pagina_id_uit_operatie(body)
        if status == "failed":
            fout = body.get("error") or {}
            raise RuntimeError(
                f"OneNote-kopie mislukt: {fout.get('message', body)}"
            )
        # Nog 'running' of 'notStarted' → even wachten en opnieuw kijken.
        if poging < _MAX_POGINGEN - 1:
            time.sleep(_POLL_INTERVAL)
    raise RuntimeError(
        "OneNote-kopie duurde te lang (geen 'completed'-status binnen "
        f"{_MAX_POGINGEN} pogingen)"
    )


def _pagina_id_uit_operatie(body: dict[str, Any]) -> str:
    """Lees het pagina-id uit een voltooide operatie (resourceId of -Location)."""
    if body.get("resourceId"):
        return body["resourceId"]
    locatie = body.get("resourceLocation", "")
    if "/pages/" in locatie:
        return locatie.rsplit("/pages/", 1)[-1].split("?")[0]
    raise RuntimeError("OneNote-kopie klaar, maar geen pagina-id ontvangen")


def _hernoem(pagina_id: str, nieuwe_titel: str) -> None:
    """Hernoem een pagina door de titel te vervangen via een content-PATCH."""
    commando = [{"target": "title", "action": "replace", "content": nieuwe_titel}]
    resp = _client.patch(f"/me/onenote/pages/{pagina_id}/content", json=commando)
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"OneNote-pagina hernoemen mislukt (HTTP {resp.status_code}): "
            f"{resp.text[:300]}"
        )


# ── Lege pagina (alleen op expliciet verzoek) ───────────────────────────────────


def _maak_lege_pagina(sectie_id: str, titel: str) -> str:
    """Maak een lege pagina met alleen de titel. Titel wordt XML-veilig gemaakt."""
    veilige_titel = html.escape(titel)
    pagina_html = (
        "<!DOCTYPE html><html><head>"
        f"<title>{veilige_titel}</title>"
        "</head><body></body></html>"
    )
    resp = _client.verzoek(
        "POST",
        f"/me/onenote/sections/{sectie_id}/pages",
        data=pagina_html.encode("utf-8"),
        headers_extra={"Content-Type": "application/xhtml+xml"},
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Lege OneNote-pagina aanmaken mislukt (HTTP {resp.status_code}): "
            f"{resp.text[:300]}"
        )
    return resp.json().get("id")

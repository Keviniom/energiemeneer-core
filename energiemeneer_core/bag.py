"""Adres- en pandgegevens via BAG en PDOK Locatieserver.

Bronnen:
  * architectuur (retry, key-injection) — ``VvE - adressenlijst/vve_adressen.py``
  * use-case (postcode + huisnummer → adres/VBO/pand) — ``admin-portal/server.py``
  * PDOK Locatieserver-helper — ``DeEnergieMeneer_IntakeTool/backend/data_api.py``

Zie BOUWPLAN.md, Module 2.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any

import requests

_log = logging.getLogger(__name__)

_BAG_BASE = "https://api.bag.kadaster.nl/lvbag/individuelebevragingen/v2"
_PDOK_BASE = "https://api.pdok.nl/bzk/locatieserver/search/v3_1"
_USER_AGENT = "energiemeneer-core (https://de-energiemeneer.nl)"
_ENV_KEY_BAG = "OVERHEID_API_KEY"


def normaliseer_postcode(postcode: str | None) -> str:
    """Maak een postcode kanoniek: hoofdletters, geen spaties."""
    return re.sub(r"\s+", "", postcode or "").upper()


def zoek_adres(
    postcode: str,
    huisnummer: int | str,
    huisletter: str | None = None,
    toevoeging: str | None = None,
) -> dict[str, Any] | None:
    """Zoek een adres in BAG op postcode + huisnummer.

    Bundelt drie BAG-calls (``/adressen``, ``/adresseerbareobjecten/<vbo>``,
    ``/panden/<id>``) tot één dict met de belangrijkste velden voor het
    energielabel-traject.

    Returns:
        Dict met ``straatnaam``, ``huisnummer``, ``huisletter``, ``toevoeging``,
        ``postcode``, ``woonplaats``, ``vbo_id``, ``pand_ids``, ``bouwjaar``,
        ``oppervlakte`` — of ``None`` als BAG geen adres kent.

    Raises:
        ValueError: postcode of huisnummer ontbreekt.
        RuntimeError: API-key ontbreekt of BAG geeft een fout.
    """
    pc = normaliseer_postcode(postcode)
    if not pc:
        raise ValueError("Postcode is verplicht")
    if huisnummer is None or str(huisnummer).strip() == "":
        raise ValueError("Huisnummer is verplicht")

    params: dict[str, str] = {
        "postcode": pc,
        "huisnummer": str(huisnummer),
        "exacteMatch": "true",
    }
    if huisletter:
        params["huisletter"] = huisletter
    if toevoeging:
        params["huisnummertoevoeging"] = toevoeging

    data = _bag_get("/adressen", params)
    adressen = (data.get("_embedded") or {}).get("adressen") or []
    if not adressen:
        return None
    adres = adressen[0]

    vbo_id = adres.get("adresseerbaarObjectIdentificatie")
    pand_ids = adres.get("pandIdentificaties") or []

    oppervlakte = _vbo_oppervlakte(vbo_id) if vbo_id else None
    bouwjaar = _pand_bouwjaar(pand_ids[0]) if pand_ids else None

    return {
        "straatnaam": adres.get("openbareRuimteNaam"),
        "huisnummer": adres.get("huisnummer"),
        "huisletter": adres.get("huisletter"),
        "toevoeging": adres.get("huisnummertoevoeging"),
        "postcode": adres.get("postcode"),
        "woonplaats": adres.get("woonplaatsNaam"),
        "vbo_id": vbo_id,
        "pand_ids": pand_ids,
        "bouwjaar": bouwjaar,
        "oppervlakte": oppervlakte,
    }


def vrij_zoeken(zoektekst: str, max: int = 5) -> list[dict[str, Any]]:
    """Adres-suggesties via PDOK Locatieserver (gratis, geen API-key).

    Bedoeld voor autosuggest in formulieren. Returnt een lijst dicts met
    ``weergavenaam``, ``straatnaam``, ``huisnummer``, ``huis_nlt``,
    ``postcode``, ``woonplaats``, ``vbo_id``, ``nummeraanduiding_id``,
    ``pand_id``. Lege lijst bij lege zoekterm of geen match.

    Raises:
        RuntimeError: PDOK geeft een fout of is onbereikbaar.
    """
    q = (zoektekst or "").strip()
    if not q:
        return []
    params = {
        "q": q,
        "fq": "type:adres",
        "fl": ",".join([
            "weergavenaam", "straatnaam", "huisnummer", "huis_nlt",
            "postcode", "woonplaatsnaam",
            "adresseerbaarobject_id", "nummeraanduiding_id", "pandid",
        ]),
        "rows": str(max),
    }
    data = _pdok_get("/free", params)
    docs = (data.get("response") or {}).get("docs") or []
    return [
        {
            "weergavenaam": doc.get("weergavenaam"),
            "straatnaam": doc.get("straatnaam"),
            "huisnummer": doc.get("huisnummer"),
            "huis_nlt": doc.get("huis_nlt"),
            "postcode": doc.get("postcode"),
            "woonplaats": doc.get("woonplaatsnaam"),
            "vbo_id": doc.get("adresseerbaarobject_id"),
            "nummeraanduiding_id": doc.get("nummeraanduiding_id"),
            "pand_id": doc.get("pandid"),
        }
        for doc in docs
    ]


def _bag_get(path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    """Generieke BAG-call met retry op 429 en netwerkfouten.

    Returnt het JSON-resultaat. Bij 404 een lege dict (caller bepaalt
    of dat 'geen resultaat' betekent). Alle andere fouten → RuntimeError.
    """
    headers = {
        "X-Api-Key": _api_key_bag(),
        "Accept": "application/hal+json",
        "Accept-Crs": "epsg:28992",
    }
    url = _BAG_BASE + path

    for poging in range(3):
        try:
            r = requests.get(url, headers=headers, params=params or {}, timeout=15)
        except requests.RequestException as e:
            if poging < 2:
                time.sleep(2)
                continue
            raise RuntimeError(f"BAG niet bereikbaar ({path}): {e}") from e

        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return {}
        if r.status_code == 401:
            raise RuntimeError("BAG 401: API-key ongeldig of verlopen")
        if r.status_code == 403:
            raise RuntimeError("BAG 403: geen rechten voor deze endpoint")
        if r.status_code == 429:
            wacht = int(r.headers.get("Retry-After", "5"))
            _log.warning("BAG 429 op %s, wacht %ss", path, wacht)
            time.sleep(wacht)
            continue
        try:
            detail = r.json()
        except ValueError:
            detail = r.text[:300]
        raise RuntimeError(f"BAG {r.status_code} op {path}: {detail}")

    raise RuntimeError(f"BAG: te vaak 429 op {path}")


def _pdok_get(path: str, params: dict[str, str]) -> dict[str, Any]:
    """PDOK Locatieserver-call. Geen API-key vereist."""
    url = _PDOK_BASE + path
    headers = {"User-Agent": _USER_AGENT}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
    except requests.RequestException as e:
        raise RuntimeError(f"PDOK niet bereikbaar ({path}): {e}") from e
    if r.status_code != 200:
        raise RuntimeError(f"PDOK {r.status_code} op {path}: {r.text[:200]}")
    return r.json()


def _vbo_oppervlakte(vbo_id: str) -> int | None:
    """Oppervlakte uit BAG ``/adresseerbareobjecten/<vbo>`` (None bij fout)."""
    try:
        data = _bag_get(f"/adresseerbareobjecten/{vbo_id}")
    except RuntimeError as e:
        _log.warning("Kon VBO %s niet ophalen: %s", vbo_id, e)
        return None
    vbo = data.get("verblijfsobject") or {}
    if isinstance(vbo, dict) and isinstance(vbo.get("verblijfsobject"), dict):
        vbo = vbo["verblijfsobject"]
    opp = vbo.get("oppervlakte")
    return int(opp) if opp is not None else None


def _pand_bouwjaar(pand_id: str) -> int | None:
    """Bouwjaar uit BAG ``/panden/<id>`` (None bij fout)."""
    try:
        data = _bag_get(f"/panden/{pand_id}")
    except RuntimeError as e:
        _log.warning("Kon pand %s niet ophalen: %s", pand_id, e)
        return None
    pand = data.get("pand") or {}
    if isinstance(pand, dict) and isinstance(pand.get("pand"), dict):
        pand = pand["pand"]
    bj = pand.get("oorspronkelijkBouwjaar")
    return int(bj) if bj is not None else None


def _api_key_bag() -> str:
    key = os.environ.get(_ENV_KEY_BAG, "").strip()
    if not key:
        raise RuntimeError(
            f"BAG API-key ontbreekt: zet env-var {_ENV_KEY_BAG} "
            f"(zie pyproject of secrets-store)."
        )
    return key

"""Toegang tot de VABI-objectenbibliotheek-templates die met de core meekomen.

De templates (per woningtype + bouwjaar-categorie) reizen mee als package-data
onder ``energiemeneer_core/objectbibliotheken/<woningtype>/Objectenbibliotheek
<categorie>.xml``. Zo kan een consumer (zoals de admin-portal op Railway) ze
lezen zonder lokale VABI-installatie.

Let op: dit levert alléén het (blanco) sjabloon-pad — er wordt hier NIETS
gerekend en de ``nta8800.exe`` zit bewust niet in het pakket.
"""

from __future__ import annotations

import importlib.resources as _resources
from pathlib import Path

_SUBMAP = "objectbibliotheken"

# Bouwjaar-categorie (zoals bag.bepaal_bouwjaar_klasse / voorbereiden teruggeeft)
# → templatebestandsnaam (zonder extensie).
_TEMPLATE_PER_KLASSE = {
    "voor 1965":     "Objectenbibliotheek voor 1965",
    "1965-1974":     "Objectenbibliotheek 1965-1974",
    "1975-1982":     "Objectenbibliotheek 1975-1982",
    "1983-1987":     "Objectenbibliotheek 1983-1987",
    "1988-1991":     "Objectenbibliotheek 1988-1991",
    "1992-2013":     "Objectenbibliotheek 1992-2013",
    "2021 en later": "Objectenbibliotheek 2021 en later",
}

_FALLBACK = "Objectenbibliotheek 1992-2013"


def root() -> Path:
    """Pad naar de map met de objectenbibliotheek-templates binnen het pakket."""
    return Path(_resources.files("energiemeneer_core")) / _SUBMAP


def beschikbare_woningtypes() -> list[str]:
    """De woningtype-mappen die als template aanwezig zijn."""
    r = root()
    if not r.is_dir():
        return []
    return sorted(p.name for p in r.iterdir() if p.is_dir())


def vind_template(woningtype_map: str, bouwjaar_klasse: str) -> Path | None:
    """Geef het pad naar het juiste objectenbibliotheek-sjabloon, of None.

    Args:
        woningtype_map: mapnaam per woningtype (bijv. 'Tussenwoning',
            'Twee onder een kap woning') — zoals ``bepaal_woningtype_info``
            in ``template_map`` teruggeeft.
        bouwjaar_klasse: bijv. '1975-1982' of '2021 en later'.

    Valt terug op het 1992-2013-sjabloon als de exacte categorie ontbreekt
    (zoals de oude tool deed voor recente bouwjaren).
    """
    naam = _TEMPLATE_PER_KLASSE.get(bouwjaar_klasse)
    basis = root() / woningtype_map
    if naam:
        pad = basis / f"{naam}.xml"
        if pad.exists():
            return pad
    fallback = basis / f"{_FALLBACK}.xml"
    return fallback if fallback.exists() else None

"""Prijsmatrix voor energielabels.

Bron: Meesterbrein v4.0 §9.1 (Prijsmatrix energielabels). Alle bedragen
incl. BTW, in hele euro's. Pure functie, geen externe calls.

Zie BOUWPLAN.md, Module 4.
"""

from __future__ import annotations

import logging
from typing import Any

_log = logging.getLogger(__name__)

# (boven_m2, categorie_key, label, prijs_bestaand, prijs_nieuwbouw)
_MATRIX = (
    (100, "tot_100",  "Tot 100 m²",  280, 425),
    (150, "100_150",  "100–150 m²", 315, 460),
    (200, "150_200",  "150–200 m²", 355, 500),
)
SPOEDTOESLAG_EUR = 30

# Publieke drempelwaarden — één bron, ook voor consumers (admin-portal e.d.).
# Bouwjaar vanaf dit jaar telt als nieuwbouw (Meesterbrein §9.1: "Nieuwbouw ≥2021").
NIEUWBOUW_JAAR_VANAF = 2021
# Oppervlakte (in m²) waarboven een opname maatwerk wordt i.p.v. een vaste prijs.
MAATWERK_BOVEN_M2 = 200


def is_nieuwbouw(bouwjaar: int | None) -> bool:
    """Bepaal of een bouwjaar als nieuwbouw telt.

    Pure functie. ``None`` of een bouwjaar vóór :data:`NIEUWBOUW_JAAR_VANAF`
    geeft ``False``; vanaf dat jaar ``True``.

    Args:
        bouwjaar: het bouwjaar van de woning, of ``None`` als onbekend.

    Returns:
        ``True`` als ``bouwjaar >= NIEUWBOUW_JAAR_VANAF``, anders ``False``.
    """
    if bouwjaar is None:
        return False
    return bouwjaar >= NIEUWBOUW_JAAR_VANAF


def krijg_matrix() -> dict[str, Any]:
    """Geef de prijsmatrix als JSON-vriendelijke data terug.

    Bedoeld als bron voor consumers (bijv. de admin-portal) zodat die geen
    eigen kopie van tarieven, grenzen of toeslagen meer hoeven te kennen.
    De waarden komen uit :data:`_MATRIX` en de publieke constanten — niets
    wordt los gedupliceerd. ``_MATRIX`` zelf blijft privé.

    Returns:
        Dict met ``tarieven`` (lijst van rijen met ``max_m2``, ``categorie``,
        ``label``, ``bestaand``, ``nieuwbouw``), ``maatwerk_boven_m2`` en
        ``spoedtoeslag_eur``.
    """
    return {
        "tarieven": [
            {
                "max_m2": boven,
                "categorie": key,
                "label": label,
                "bestaand": bestaand,
                "nieuwbouw": nb,
            }
            for boven, key, label, bestaand, nb in _MATRIX
        ],
        "maatwerk_boven_m2": MAATWERK_BOVEN_M2,
        "spoedtoeslag_eur": SPOEDTOESLAG_EUR,
    }


def bereken_prijs(
    oppervlakte_m2: float | int | None,
    nieuwbouw: bool = False,
    spoed: bool = False,
) -> dict[str, Any]:
    """Bepaal prijscategorie en bedrag voor een energielabel-opname.

    Bron: Meesterbrein §9.1. Alle bedragen incl. BTW.

    Args:
        oppervlakte_m2: gebruiksoppervlakte in m². ``None``, ``<= 0``
            of ``> 200`` → maatwerk.
        nieuwbouw: ``True`` voor bouwjaar ≥ 2021.
        spoed: ``True`` als spoedtoeslag van toepassing is.

    Returns:
        Dict met ``categorie``, ``categorie_label``, ``bedrag``,
        ``spoedtoeslag``, ``totaal``, ``nieuwbouw``, ``maatwerk``.
        ``bedrag`` en ``totaal`` zijn ``None`` bij maatwerk.
    """
    spoedtoeslag = SPOEDTOESLAG_EUR if spoed else 0

    if oppervlakte_m2 is None or oppervlakte_m2 <= 0 or oppervlakte_m2 > MAATWERK_BOVEN_M2:
        return {
            "categorie": "maatwerk",
            "categorie_label": f">{MAATWERK_BOVEN_M2} m² of onbekend",
            "bedrag": None,
            "spoedtoeslag": spoedtoeslag,
            "totaal": None,
            "nieuwbouw": nieuwbouw,
            "maatwerk": True,
        }

    for boven, key, label, bestaand, nb in _MATRIX:
        if oppervlakte_m2 <= boven:
            bedrag = nb if nieuwbouw else bestaand
            return {
                "categorie": key,
                "categorie_label": label,
                "bedrag": bedrag,
                "spoedtoeslag": spoedtoeslag,
                "totaal": bedrag + spoedtoeslag,
                "nieuwbouw": nieuwbouw,
                "maatwerk": False,
            }

    raise RuntimeError(f"Onverwachte oppervlakte: {oppervlakte_m2}")

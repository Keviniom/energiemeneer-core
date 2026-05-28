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

    if oppervlakte_m2 is None or oppervlakte_m2 <= 0 or oppervlakte_m2 > 200:
        return {
            "categorie": "maatwerk",
            "categorie_label": ">200 m² of onbekend",
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

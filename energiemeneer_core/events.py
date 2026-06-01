"""Centrale logging — het append-only events-logboek (fundament dashboard).

Eén plek waar elke module naartoe schrijft *wat* hij deed: wie/wat/wanneer/
resultaat (zie Meesterbrein H4.2). Het dashboard (H6) leest hier straks uit.

Bovenop :mod:`energiemeneer_core.storage`: zelfde datamap en dezelfde
``ENERGIEMENEER_DATA_DIR``-fallback. Events liggen als **JSON Lines** (één event
per regel) in ``events.jsonl`` — er komt steeds bij, er wordt nooit iets
overschreven. Bij een crash mid-write verlies je hooguit de laatste regel; alle
eerdere blijven heel.

De opslag zit achter :func:`_pad_events` plus de twee publieke functies. Gaan we
later naar een echte database (beslispunt B1: SQLite/PostgreSQL), dan verandert
alleen de binnenkant — de aanroepende modules merken er niets van.

Zie BOUWPLAN.md, Module 8.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from energiemeneer_core import storage

_log = logging.getLogger(__name__)

_BESTAND = "events.jsonl"
_schrijf_lock = threading.Lock()

# Vaste, afgesproken waarden — strikt, zodat het dashboard betrouwbaar kan
# filteren en kleuren. Vrije tekst is bewust niet toegestaan.
RESULTATEN = ("gelukt", "mislukt", "in_uitvoering")
NIVEAUS = ("info", "waarschuwing", "kritiek")


def schrijf_event(
    module: str,
    actie: str,
    resultaat: str,
    *,
    niveau: str = "info",
    vbo_id: str | None = None,
    bericht: str = "",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Leg één gebeurtenis vast in het centrale logboek.

    Args:
        module: welke module/onderdeel het event schrijft (bijv. ``"bag"``).
        actie: wat er gebeurde (bijv. ``"zoek_adres"``).
        resultaat: uitkomst — één van :data:`RESULTATEN`
            (``"gelukt"`` / ``"mislukt"`` / ``"in_uitvoering"``).
        niveau: urgentie — één van :data:`NIVEAUS`
            (``"info"`` / ``"waarschuwing"`` / ``"kritiek"``). Standaard ``"info"``.
        vbo_id: optionele koppeling naar het dossier (de sleutel uit H4.2).
        bericht: vrije, leesbare toelichting.
        details: vrij dict voor module-specifieke extra informatie.

    Returns:
        Het opgeslagen event als dict (inclusief automatisch ``id`` en ``tijd``).

    Raises:
        ValueError: ``module``/``actie`` ontbreekt, of ``resultaat``/``niveau``
            heeft een niet-toegestane waarde.
        RuntimeError: het logboek kon niet worden geschreven.
    """
    if not module or not module.strip():
        raise ValueError("module is verplicht")
    if not actie or not actie.strip():
        raise ValueError("actie is verplicht")
    if resultaat not in RESULTATEN:
        raise ValueError(
            f"resultaat '{resultaat}' is ongeldig — kies uit {RESULTATEN}"
        )
    if niveau not in NIVEAUS:
        raise ValueError(f"niveau '{niveau}' is ongeldig — kies uit {NIVEAUS}")

    event = {
        "id": uuid.uuid4().hex,
        "tijd": _nu(),
        "module": module.strip(),
        "actie": actie.strip(),
        "resultaat": resultaat,
        "niveau": niveau,
        "vbo_id": vbo_id,
        "bericht": bericht,
        "details": details or {},
    }

    regel = json.dumps(event, ensure_ascii=False)
    pad = _pad_events()
    with _schrijf_lock:
        try:
            with open(pad, "a", encoding="utf-8") as f:
                f.write(regel + "\n")
        except OSError as e:
            raise RuntimeError(f"Event schrijven mislukt: {e}") from e

    _log.info("Event: %s/%s → %s (%s)", event["module"], event["actie"],
              resultaat, niveau)
    return event


def lees_events(
    *,
    module: str | None = None,
    vbo_id: str | None = None,
    resultaat: str | None = None,
    niveau: str | None = None,
    sinds: str | None = None,
    limiet: int | None = None,
) -> list[dict[str, Any]]:
    """Lees events terug, nieuwste eerst, met optionele filters.

    Args:
        module: alleen events van deze module.
        vbo_id: alleen events van dit dossier.
        resultaat: alleen events met deze uitkomst (zie :data:`RESULTATEN`).
        niveau: alleen events van dit niveau (zie :data:`NIVEAUS`).
        sinds: alleen events met ``tijd >= sinds`` (UTC-ISO, bijv.
            ``"2026-06-01T00:00:00Z"``).
        limiet: geef hoogstens dit aantal events terug (na sorteren).

    Returns:
        Lijst events (dicts), nieuwste eerst. Lege lijst als er niets is.
    """
    events: list[dict[str, Any]] = []
    for ev in _alle_events():
        if module is not None and ev.get("module") != module:
            continue
        if vbo_id is not None and ev.get("vbo_id") != vbo_id:
            continue
        if resultaat is not None and ev.get("resultaat") != resultaat:
            continue
        if niveau is not None and ev.get("niveau") != niveau:
            continue
        if sinds is not None and ev.get("tijd", "") < sinds:
            continue
        events.append(ev)

    # Nieuwste eerst: events staan chronologisch in het bestand.
    events.reverse()
    if limiet is not None:
        events = events[:limiet]
    return events


# ── Interne opslag ───────────────────────────────────────────────────────────


def _pad_events() -> str:
    """De enige plek die weet wáár en hóe events liggen (zie module-docstring)."""
    return storage.pad_voor(_BESTAND)


def _alle_events() -> list[dict[str, Any]]:
    """Lees alle events uit het JSONL-bestand; sla corrupte regels netjes over."""
    pad = _pad_events()
    events: list[dict[str, Any]] = []
    try:
        with open(pad, "r", encoding="utf-8") as f:
            for regelnr, regel in enumerate(f, start=1):
                regel = regel.strip()
                if not regel:
                    continue
                try:
                    events.append(json.loads(regel))
                except json.JSONDecodeError:
                    _log.warning("Corrupte event-regel %d overgeslagen", regelnr)
    except FileNotFoundError:
        return []
    except OSError as e:
        _log.error("Kon events niet lezen: %s", e)
        return []
    return events


def _nu() -> str:
    """Huidige tijd als UTC-ISO die op ``Z`` eindigt (apart voor testbaarheid)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

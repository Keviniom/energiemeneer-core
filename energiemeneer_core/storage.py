"""Datamap-detectie en atomic JSON-opslag.

Bron: admin-portal/storage.py (de schoonste van de bestaande versies).
Zie BOUWPLAN.md, Module 1 voor het volledige verhaal.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from typing import Any

from energiemeneer_core import environment

_log = logging.getLogger(__name__)

_VOLUME_PADEN = ("/app/data", "/data/volume", "/data", "/app/volume")
_ENV_FALLBACK = "ENERGIEMENEER_DATA_DIR"

_data_dir_cache: str | None = None
_dir_cache_lock = threading.Lock()
_file_locks: dict[str, threading.Lock] = {}
_file_locks_lock = threading.Lock()


def vind_data_dir() -> str:
    """Geef het pad naar de datamap.

    Volgorde:
      0. De env-override uit :func:`energiemeneer_core.environment.storage_root_override`
         (``STORAGE_ROOT`` / non-prod ``STORAGE_ROOT_TEST``) — de policy-laag wint.
      1. Eerste bestaande pad uit ``/app/data``, ``/data/volume``, ``/data``,
         ``/app/volume`` (Railway-volume-conventie).
      2. Env-var ``ENERGIEMENEER_DATA_DIR``.
      3. ``os.getcwd()``.

    Resultaat wordt na de eerste aanroep gecached.
    """
    global _data_dir_cache
    if _data_dir_cache is not None:
        return _data_dir_cache
    with _dir_cache_lock:
        if _data_dir_cache is not None:
            return _data_dir_cache
        override = environment.storage_root_override()
        if override:
            _data_dir_cache = override
            return _data_dir_cache
        for pad in _VOLUME_PADEN:
            if os.path.isdir(pad):
                _data_dir_cache = pad
                return _data_dir_cache
        env_pad = os.environ.get(_ENV_FALLBACK)
        if env_pad:
            _data_dir_cache = env_pad
            return _data_dir_cache
        _data_dir_cache = os.getcwd()
        return _data_dir_cache


def pad_voor(bestandsnaam: str) -> str:
    """Volledig pad voor ``bestandsnaam`` binnen de datamap."""
    return os.path.join(vind_data_dir(), bestandsnaam)


def laad_json(bestandsnaam: str, default: Any = None) -> Any:
    """Lees JSON uit de datamap.

    Geeft ``default`` terug als het bestand niet bestaat of de inhoud
    geen geldige JSON is.
    """
    pad = pad_voor(bestandsnaam)
    if not os.path.exists(pad):
        return default
    try:
        with open(pad, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        _log.warning("Kon %s niet lezen: %s", bestandsnaam, e)
        return default


def bewaar_json(bestandsnaam: str, data: Any) -> bool:
    """Schrijf ``data`` atomic als JSON naar de datamap.

    Schrijft eerst naar ``<naam>.tmp`` en doet daarna ``os.replace`` —
    zo blijft het oude bestand bij een crash mid-write intact. UTF-8,
    ``ensure_ascii=False``, ``indent=2``. Per bestand een eigen lock.
    """
    pad = pad_voor(bestandsnaam)
    lock = _lock_voor(pad)
    with lock:
        tmp = pad + ".tmp"
        try:
            os.makedirs(os.path.dirname(pad) or ".", exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, pad)
            return True
        except OSError as e:
            _log.error("Kon %s niet schrijven: %s", bestandsnaam, e)
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            return False


def _lock_voor(pad: str) -> threading.Lock:
    with _file_locks_lock:
        lock = _file_locks.get(pad)
        if lock is None:
            lock = threading.Lock()
            _file_locks[pad] = lock
        return lock

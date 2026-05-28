import json
import os

import pytest

from energiemeneer_core import storage


@pytest.fixture(autouse=True)
def _isoleer_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_VOLUME_PADEN", ())
    monkeypatch.setattr(storage, "_data_dir_cache", None)
    storage._file_locks.clear()
    monkeypatch.setenv(storage._ENV_FALLBACK, str(tmp_path))
    yield


def test_roundtrip_schrijven_en_lezen():
    payload = {"a": 1, "naam": "Café", "lijst": [1, 2, 3]}
    assert storage.bewaar_json("test.json", payload) is True
    assert storage.laad_json("test.json") == payload


def test_default_bij_ontbrekend_bestand():
    assert storage.laad_json("bestaat-niet.json") is None
    assert storage.laad_json("bestaat-niet.json", default={}) == {}
    assert storage.laad_json("bestaat-niet.json", default=[]) == []


def test_default_bij_corrupte_json(tmp_path):
    (tmp_path / "stuk.json").write_text("{niet valide", encoding="utf-8")
    assert storage.laad_json("stuk.json", default={}) == {}


def test_atomic_write_laat_geen_tmp_achter(tmp_path):
    storage.bewaar_json("x.json", {"k": "v"})
    rommel = list(tmp_path.glob("*.tmp"))
    assert rommel == []


def test_utf8_wordt_niet_geescaped(tmp_path):
    storage.bewaar_json("nl.json", {"plaats": "'s-Gravenhage", "char": "é"})
    raw = (tmp_path / "nl.json").read_text(encoding="utf-8")
    assert "'s-Gravenhage" in raw
    assert "é" in raw
    assert "\\u" not in raw


def test_env_var_wordt_gebruikt_als_geen_volume(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "_data_dir_cache", None)
    monkeypatch.setenv(storage._ENV_FALLBACK, str(tmp_path / "elders"))
    os.makedirs(tmp_path / "elders", exist_ok=True)
    assert storage.vind_data_dir() == str(tmp_path / "elders")


def test_cwd_fallback_zonder_env_var(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "_data_dir_cache", None)
    monkeypatch.delenv(storage._ENV_FALLBACK, raising=False)
    monkeypatch.chdir(tmp_path)
    assert storage.vind_data_dir() == str(tmp_path)


def test_volume_pad_wint_van_env_var(monkeypatch, tmp_path):
    volume = tmp_path / "volume"
    volume.mkdir()
    monkeypatch.setattr(storage, "_VOLUME_PADEN", (str(volume),))
    monkeypatch.setattr(storage, "_data_dir_cache", None)
    monkeypatch.setenv(storage._ENV_FALLBACK, str(tmp_path / "elders"))
    assert storage.vind_data_dir() == str(volume)


def test_pad_voor_bouwt_correct_pad(tmp_path):
    assert storage.pad_voor("a.json") == os.path.join(str(tmp_path), "a.json")

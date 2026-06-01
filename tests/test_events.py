import json

import pytest

from energiemeneer_core import events, storage


@pytest.fixture(autouse=True)
def _isoleer_datamap(tmp_path, monkeypatch):
    # Zelfde isolatie-aanpak als test_storage: datamap naar een wegwerp-tmp_path.
    monkeypatch.setattr(storage, "_VOLUME_PADEN", ())
    monkeypatch.setattr(storage, "_data_dir_cache", None)
    storage._file_locks.clear()
    monkeypatch.setenv(storage._ENV_FALLBACK, str(tmp_path))
    yield


# ── Schrijven + teruglezen ──────────────────────────────────────────────────────


def test_schrijf_en_lees_roundtrip():
    ev = events.schrijf_event("bag", "zoek_adres", "gelukt",
                              vbo_id="0518010000812345", bericht="Adres gevonden")
    assert ev["module"] == "bag"
    assert ev["actie"] == "zoek_adres"
    assert ev["resultaat"] == "gelukt"
    assert ev["niveau"] == "info"  # standaard
    assert ev["vbo_id"] == "0518010000812345"
    assert ev["id"] and ev["tijd"]  # automatisch ingevuld

    terug = events.lees_events()
    assert len(terug) == 1
    assert terug[0]["id"] == ev["id"]


def test_meerdere_events_nieuwste_eerst(monkeypatch):
    tijden = iter(["2026-06-01T10:00:00Z", "2026-06-01T11:00:00Z",
                   "2026-06-01T12:00:00Z"])
    monkeypatch.setattr(events, "_nu", lambda: next(tijden))
    events.schrijf_event("a", "stap1", "gelukt")
    events.schrijf_event("b", "stap2", "gelukt")
    events.schrijf_event("c", "stap3", "gelukt")

    terug = events.lees_events()
    assert [e["module"] for e in terug] == ["c", "b", "a"]  # nieuwste eerst


def test_append_verliest_geen_oude_events():
    events.schrijf_event("a", "x", "gelukt")
    events.schrijf_event("b", "y", "mislukt")
    # Tweede schrijf-actie mag de eerste niet overschrijven.
    assert len(events.lees_events()) == 2


# ── Filters ──────────────────────────────────────────────────────────────────


def test_filter_op_module():
    events.schrijf_event("bag", "x", "gelukt")
    events.schrijf_event("prijs", "y", "gelukt")
    terug = events.lees_events(module="prijs")
    assert len(terug) == 1
    assert terug[0]["module"] == "prijs"


def test_filter_op_vbo_id():
    events.schrijf_event("a", "x", "gelukt", vbo_id="VBO1")
    events.schrijf_event("a", "y", "gelukt", vbo_id="VBO2")
    terug = events.lees_events(vbo_id="VBO2")
    assert [e["actie"] for e in terug] == ["y"]


def test_filter_op_resultaat_en_niveau():
    events.schrijf_event("a", "x", "gelukt")
    events.schrijf_event("a", "y", "mislukt", niveau="kritiek")
    assert len(events.lees_events(resultaat="mislukt")) == 1
    assert len(events.lees_events(niveau="kritiek")) == 1
    assert len(events.lees_events(niveau="info")) == 1


def test_filter_sinds(monkeypatch):
    tijden = iter(["2026-06-01T09:00:00Z", "2026-06-01T15:00:00Z"])
    monkeypatch.setattr(events, "_nu", lambda: next(tijden))
    events.schrijf_event("a", "ochtend", "gelukt")
    events.schrijf_event("a", "middag", "gelukt")
    terug = events.lees_events(sinds="2026-06-01T12:00:00Z")
    assert [e["actie"] for e in terug] == ["middag"]


def test_limiet():
    for i in range(5):
        events.schrijf_event("a", f"stap{i}", "gelukt")
    assert len(events.lees_events(limiet=2)) == 2


# ── Strikte waarden ────────────────────────────────────────────────────────────


def test_resultaat_moet_geldig_zijn():
    with pytest.raises(ValueError, match="resultaat"):
        events.schrijf_event("a", "x", "ok")  # geen toegestane waarde


def test_niveau_moet_geldig_zijn():
    with pytest.raises(ValueError, match="niveau"):
        events.schrijf_event("a", "x", "gelukt", niveau="urgent")


def test_alle_toegestane_resultaten_en_niveaus():
    for r in events.RESULTATEN:
        events.schrijf_event("a", "x", r)
    for n in events.NIVEAUS:
        events.schrijf_event("a", "x", "gelukt", niveau=n)
    # 3 resultaten + 3 niveaus = 6 events.
    assert len(events.lees_events()) == 6


def test_module_en_actie_verplicht():
    with pytest.raises(ValueError, match="module"):
        events.schrijf_event("", "x", "gelukt")
    with pytest.raises(ValueError, match="actie"):
        events.schrijf_event("a", "  ", "gelukt")


# ── Robuustheid ────────────────────────────────────────────────────────────────


def test_ontbrekend_bestand_geeft_lege_lijst():
    assert events.lees_events() == []


def test_corrupte_regel_wordt_overgeslagen(tmp_path):
    events.schrijf_event("a", "goed", "gelukt")
    # Plak een kapotte regel tussendoor.
    with open(tmp_path / "events.jsonl", "a", encoding="utf-8") as f:
        f.write("{dit is geen json\n")
    events.schrijf_event("b", "ook_goed", "gelukt")

    terug = events.lees_events()
    assert len(terug) == 2  # de corrupte regel telt niet mee
    assert {e["actie"] for e in terug} == {"goed", "ook_goed"}


def test_utf8_blijft_intact(tmp_path):
    events.schrijf_event("a", "x", "gelukt", bericht="Café 's-Gravenhage é")
    raw = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
    assert "Café 's-Gravenhage é" in raw
    assert "\\u" not in raw
    assert events.lees_events()[0]["bericht"] == "Café 's-Gravenhage é"


def test_details_vrij_dict():
    ev = events.schrijf_event("a", "x", "gelukt",
                              details={"oppervlakte": 120, "extra": ["lijst"]})
    assert events.lees_events()[0]["details"] == {"oppervlakte": 120, "extra": ["lijst"]}
    assert ev["details"]["oppervlakte"] == 120

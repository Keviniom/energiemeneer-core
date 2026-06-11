from unittest.mock import MagicMock

import pytest
import requests

from energiemeneer_core import bag


@pytest.fixture(autouse=True)
def _zet_api_key(monkeypatch):
    monkeypatch.setenv(bag._ENV_KEY_BAG, "test-key")
    yield


def _resp(status: int = 200, json_data=None, headers=None, text: str = ""):
    r = MagicMock(spec=requests.Response)
    r.status_code = status
    r.json.return_value = json_data if json_data is not None else {}
    r.headers = headers or {}
    r.text = text
    return r


def _seq_responses(monkeypatch, responses):
    calls: list[dict] = []
    iterator = iter(responses)

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append({"url": url, "headers": headers, "params": params})
        return next(iterator)

    monkeypatch.setattr(requests, "get", fake_get)
    return calls


def test_normaliseer_postcode_varianten():
    assert bag.normaliseer_postcode("1234 ab") == "1234AB"
    assert bag.normaliseer_postcode("  9876ZZ ") == "9876ZZ"
    assert bag.normaliseer_postcode("") == ""
    assert bag.normaliseer_postcode(None) == ""


def test_zoek_adres_volledige_flow(monkeypatch):
    adres_resp = _resp(json_data={
        "_embedded": {
            "adressen": [{
                "openbareRuimteNaam": "Graskopstraat",
                "huisnummer": 8,
                "huisletter": None,
                "huisnummertoevoeging": None,
                "postcode": "2548BV",
                "woonplaatsNaam": "'s-Gravenhage",
                "adresseerbaarObjectIdentificatie": "0518010000123456",
                "pandIdentificaties": ["0518100000987654"],
            }]
        }
    })
    vbo_resp = _resp(json_data={
        "verblijfsobject": {"verblijfsobject": {"oppervlakte": 95}}
    })
    pand_resp = _resp(json_data={
        "pand": {"pand": {"oorspronkelijkBouwjaar": 1968}}
    })
    calls = _seq_responses(monkeypatch, [adres_resp, vbo_resp, pand_resp])

    result = bag.zoek_adres("2548 bv", 8)

    assert result == {
        "straatnaam": "Graskopstraat",
        "huisnummer": 8,
        "huisletter": None,
        "toevoeging": None,
        "postcode": "2548BV",
        "woonplaats": "'s-Gravenhage",
        "vbo_id": "0518010000123456",
        "pand_ids": ["0518100000987654"],
        "bouwjaar": 1968,
        "oppervlakte": 95,
    }
    # Eerste call gaat naar /adressen met genormaliseerde postcode
    assert calls[0]["url"].endswith("/adressen")
    assert calls[0]["params"]["postcode"] == "2548BV"
    assert calls[0]["params"]["huisnummer"] == "8"
    assert calls[0]["headers"]["X-Api-Key"] == "test-key"


def test_zoek_adres_zonder_pand_en_vbo(monkeypatch):
    """Adres bestaat, maar BAG levert geen VBO/pand → bouwjaar en oppervlakte zijn None."""
    adres_resp = _resp(json_data={
        "_embedded": {
            "adressen": [{
                "openbareRuimteNaam": "Onbekend",
                "huisnummer": 1,
                "postcode": "1234AB",
                "woonplaatsNaam": "Nergens",
                "adresseerbaarObjectIdentificatie": None,
                "pandIdentificaties": [],
            }]
        }
    })
    _seq_responses(monkeypatch, [adres_resp])
    result = bag.zoek_adres("1234AB", 1)
    assert result["bouwjaar"] is None
    assert result["oppervlakte"] is None
    assert result["vbo_id"] is None
    assert result["pand_ids"] == []


def test_zoek_adres_niet_gevonden_geeft_none(monkeypatch):
    leeg = _resp(json_data={"_embedded": {"adressen": []}})
    _seq_responses(monkeypatch, [leeg])
    assert bag.zoek_adres("9999AA", 1) is None


def test_zoek_adres_eist_postcode_en_huisnummer():
    with pytest.raises(ValueError, match="Postcode"):
        bag.zoek_adres("", 8)
    with pytest.raises(ValueError, match="Huisnummer"):
        bag.zoek_adres("2548BV", "")
    with pytest.raises(ValueError, match="Huisnummer"):
        bag.zoek_adres("2548BV", None)  # type: ignore[arg-type]


def test_ontbrekende_api_key(monkeypatch):
    monkeypatch.delenv(bag._ENV_KEY_BAG, raising=False)
    with pytest.raises(RuntimeError, match=bag._ENV_KEY_BAG):
        bag.zoek_adres("2548BV", 8)


def test_bag_401_geeft_runtime_error(monkeypatch):
    _seq_responses(monkeypatch, [_resp(status=401)])
    with pytest.raises(RuntimeError, match="BAG 401"):
        bag.zoek_adres("2548BV", 8)


def test_bag_404_op_adressen_telt_als_niet_gevonden(monkeypatch):
    _seq_responses(monkeypatch, [_resp(status=404)])
    assert bag.zoek_adres("2548BV", 8) is None


def test_vbo_lookup_faalt_zacht(monkeypatch):
    """Als VBO/pand-lookup faalt, blijft het hoofdresultaat staan met None-velden."""
    adres_resp = _resp(json_data={
        "_embedded": {
            "adressen": [{
                "openbareRuimteNaam": "X",
                "huisnummer": 1,
                "postcode": "1234AB",
                "woonplaatsNaam": "Y",
                "adresseerbaarObjectIdentificatie": "vbo-1",
                "pandIdentificaties": ["pand-1"],
            }]
        }
    })
    vbo_fout = _resp(status=500, text="oeps")
    pand_resp = _resp(json_data={"pand": {"pand": {"oorspronkelijkBouwjaar": 2000}}})
    _seq_responses(monkeypatch, [adres_resp, vbo_fout, pand_resp])
    r = bag.zoek_adres("1234AB", 1)
    assert r["oppervlakte"] is None
    assert r["bouwjaar"] == 2000


def test_vrij_zoeken_levert_suggesties(monkeypatch):
    resp = _resp(json_data={
        "response": {
            "docs": [{
                "weergavenaam": "Graskopstraat 8, 2548BV 's-Gravenhage",
                "straatnaam": "Graskopstraat",
                "huisnummer": 8,
                "huis_nlt": "8",
                "postcode": "2548BV",
                "woonplaatsnaam": "'s-Gravenhage",
                "adresseerbaarobject_id": "0518010000123456",
                "nummeraanduiding_id": "0518200000111222",
                "pandid": "0518100000987654",
            }]
        }
    })
    calls = _seq_responses(monkeypatch, [resp])
    out = bag.vrij_zoeken("Graskopstraat 8", max=3)
    assert len(out) == 1
    s = out[0]
    assert s["weergavenaam"] == "Graskopstraat 8, 2548BV 's-Gravenhage"
    assert s["vbo_id"] == "0518010000123456"
    assert s["pand_id"] == "0518100000987654"
    assert s["nummeraanduiding_id"] == "0518200000111222"
    # PDOK gebruikt geen API-key; wel een User-Agent
    assert "X-Api-Key" not in (calls[0]["headers"] or {})
    assert "User-Agent" in calls[0]["headers"]


def test_vrij_zoeken_lege_invoer():
    assert bag.vrij_zoeken("") == []
    assert bag.vrij_zoeken("   ") == []


def test_vrij_zoeken_pdok_fout(monkeypatch):
    _seq_responses(monkeypatch, [_resp(status=503, text="down")])
    with pytest.raises(RuntimeError, match="PDOK 503"):
        bag.vrij_zoeken("test")

from unittest.mock import MagicMock

import pytest
import requests

from energiemeneer_core import graph_auth
from energiemeneer_core.graph_api import onenote


@pytest.fixture(autouse=True)
def _altijd_geldig_token(monkeypatch):
    monkeypatch.setattr(graph_auth, "haal_graph_token", lambda: "AT-test")
    yield


@pytest.fixture(autouse=True)
def _geen_echte_wachttijd(monkeypatch):
    # De kopie-polling slaapt tussen pogingen; in tests willen we dat niet.
    monkeypatch.setattr(onenote.time, "sleep", lambda *_a: None)
    yield


def _resp(status=200, json_data=None, text="", headers=None):
    r = MagicMock(spec=requests.Response)
    r.status_code = status
    r.json.return_value = json_data if json_data is not None else {}
    r.text = text
    r.headers = headers if headers is not None else {}
    return r


def _vang_request(monkeypatch, responder):
    """responder(method, url, json) -> Response; logt alle calls."""
    calls: list[dict] = []

    def fake_request(method, url, headers=None, params=None, json=None,
                     data=None, timeout=None):
        calls.append({"method": method, "url": url, "json": json,
                      "data": data, "headers": headers, "params": params})
        return responder(method, url, json)

    monkeypatch.setattr(requests, "request", fake_request)
    return calls


# Standaard-Graph-antwoorden voor een geslaagde kopie. Een test kan een eigen
# responder schrijven; deze helper dekt het "alles gaat goed"-pad.
def _gelukkige_responder(extra_paginas=None):
    paginas = [{"id": "P-sjabloon", "title": "Adres"}]
    if extra_paginas:
        paginas = paginas + extra_paginas

    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/onenote/notebooks"):
            return _resp(json_data={"value": [
                {"id": "NB1", "displayName": "De Energiemeneer"},
                {"id": "NB2", "displayName": "Privé"}]})
        if method == "GET" and url.endswith("/notebooks/NB1/sections"):
            return _resp(json_data={"value": [
                {"id": "S1", "displayName": "Opnames"}]})
        if method == "GET" and "/sections/S1/pages" in url:
            return _resp(json_data={"value": paginas})
        if method == "POST" and url.endswith("/pages/P-sjabloon/copyToSection"):
            return _resp(status=202, json_data={"id": "OP1", "status": "running"})
        if method == "GET" and url.endswith("/onenote/operations/OP1"):
            return _resp(json_data={"status": "completed", "resourceId": "P-nieuw"})
        if method == "PATCH" and url.endswith("/pages/P-nieuw/content"):
            return _resp(status=204)
        raise AssertionError(f"onverwachte call {method} {url}")

    return responder


def test_kopieer_sjabloon_gelukkig_pad(monkeypatch):
    calls = _vang_request(monkeypatch, _gelukkige_responder())
    r = onenote.kopieer_sjabloonpagina(
        "De Energiemeneer", "Opnames", "Adres", "Graskopstraat 8, 's-Gravenhage")

    assert r == {"id": "P-nieuw", "titel": "Graskopstraat 8, 's-Gravenhage",
                 "methode": "kopie"}
    # De kopie ging via copyToSection naar de juiste sectie.
    copy = [c for c in calls if c["method"] == "POST"][0]
    assert copy["json"] == {"id": "S1"}
    # De pagina is hernoemd via een title-replace command.
    patch = [c for c in calls if c["method"] == "PATCH"][0]
    assert patch["json"] == [
        {"target": "title", "action": "replace",
         "content": "Graskopstraat 8, 's-Gravenhage"}]


def test_namen_zijn_niet_ingebakken_maar_parameters(monkeypatch):
    # Bewijs dat de aanroeper de namen bepaalt: andere namen → andere lookups.
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/onenote/notebooks"):
            return _resp(json_data={"value": [{"id": "NBx", "displayName": "Klusboek"}]})
        if method == "GET" and url.endswith("/notebooks/NBx/sections"):
            return _resp(json_data={"value": [{"id": "Sx", "displayName": "Tuin"}]})
        if method == "GET" and "/sections/Sx/pages" in url:
            return _resp(json_data={"value": [{"id": "P-tmpl", "title": "Basis"}]})
        if method == "POST" and url.endswith("/pages/P-tmpl/copyToSection"):
            return _resp(status=202, json_data={"id": "OPx", "status": "running"})
        if method == "GET" and url.endswith("/operations/OPx"):
            return _resp(json_data={"status": "completed", "resourceId": "P-x"})
        if method == "PATCH" and url.endswith("/pages/P-x/content"):
            return _resp(status=204)
        raise AssertionError(f"onverwachte call {method} {url}")

    _vang_request(monkeypatch, responder)
    r = onenote.kopieer_sjabloonpagina("Klusboek", "Tuin", "Basis", "Nieuwe klus")
    assert r["methode"] == "kopie"
    assert r["titel"] == "Nieuwe klus"


def test_dubbele_titel_krijgt_suffix(monkeypatch):
    extra = [{"id": "P-a", "title": "Straat 8"}, {"id": "P-b", "title": "Straat 8_1"}]
    _vang_request(monkeypatch, _gelukkige_responder(extra_paginas=extra))
    r = onenote.kopieer_sjabloonpagina("De Energiemeneer", "Opnames", "Adres", "Straat 8")
    assert r["titel"] == "Straat 8_2"  # _1 was ook al bezet


def test_operatie_id_uit_header_als_body_leeg(monkeypatch):
    # Sommige antwoorden geven de operatie alleen via de Operation-Location-header.
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/onenote/notebooks"):
            return _resp(json_data={"value": [{"id": "NB1", "displayName": "De Energiemeneer"}]})
        if method == "GET" and url.endswith("/notebooks/NB1/sections"):
            return _resp(json_data={"value": [{"id": "S1", "displayName": "Opnames"}]})
        if method == "GET" and "/sections/S1/pages" in url:
            return _resp(json_data={"value": [{"id": "P-sjabloon", "title": "Adres"}]})
        if method == "POST" and url.endswith("/copyToSection"):
            return _resp(status=202, headers={
                "Operation-Location":
                "https://graph.microsoft.com/v1.0/me/onenote/operations/OP-h"})
        if method == "GET" and url.endswith("/operations/OP-h"):
            # Geen resourceId, wel resourceLocation → pagina-id uit het pad.
            return _resp(json_data={
                "status": "completed",
                "resourceLocation":
                "https://graph.microsoft.com/v1.0/me/onenote/pages/P-uit-loc"})
        if method == "PATCH" and url.endswith("/pages/P-uit-loc/content"):
            return _resp(status=204)
        raise AssertionError(f"onverwachte call {method} {url}")

    _vang_request(monkeypatch, responder)
    r = onenote.kopieer_sjabloonpagina("De Energiemeneer", "Opnames", "Adres", "Test")
    assert r["id"] == "P-uit-loc"


def test_operatie_wacht_tot_completed(monkeypatch):
    # Eerst 'running', dan 'completed' — de polling moet doorgaan.
    statussen = iter([
        {"status": "running"},
        {"status": "completed", "resourceId": "P-laat"}])

    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/onenote/notebooks"):
            return _resp(json_data={"value": [{"id": "NB1", "displayName": "De Energiemeneer"}]})
        if method == "GET" and url.endswith("/notebooks/NB1/sections"):
            return _resp(json_data={"value": [{"id": "S1", "displayName": "Opnames"}]})
        if method == "GET" and "/sections/S1/pages" in url:
            return _resp(json_data={"value": [{"id": "P-sjabloon", "title": "Adres"}]})
        if method == "POST" and url.endswith("/copyToSection"):
            return _resp(status=202, json_data={"id": "OP1"})
        if method == "GET" and url.endswith("/operations/OP1"):
            return _resp(json_data=next(statussen))
        if method == "PATCH":
            return _resp(status=204)
        raise AssertionError(f"onverwachte call {method} {url}")

    _vang_request(monkeypatch, responder)
    r = onenote.kopieer_sjabloonpagina("De Energiemeneer", "Opnames", "Adres", "Test")
    assert r["id"] == "P-laat"


def test_operatie_failed_geeft_fout(monkeypatch):
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/onenote/notebooks"):
            return _resp(json_data={"value": [{"id": "NB1", "displayName": "De Energiemeneer"}]})
        if method == "GET" and url.endswith("/notebooks/NB1/sections"):
            return _resp(json_data={"value": [{"id": "S1", "displayName": "Opnames"}]})
        if method == "GET" and "/sections/S1/pages" in url:
            return _resp(json_data={"value": [{"id": "P-sjabloon", "title": "Adres"}]})
        if method == "POST" and url.endswith("/copyToSection"):
            return _resp(status=202, json_data={"id": "OP1"})
        if method == "GET" and url.endswith("/operations/OP1"):
            return _resp(json_data={"status": "failed",
                                    "error": {"message": "iets ging mis"}})
        raise AssertionError(f"onverwachte call {method} {url}")

    _vang_request(monkeypatch, responder)
    with pytest.raises(RuntimeError, match="iets ging mis"):
        onenote.kopieer_sjabloonpagina("De Energiemeneer", "Opnames", "Adres", "Test")


def test_sjabloon_ontbreekt_geeft_fout_standaard(monkeypatch):
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/onenote/notebooks"):
            return _resp(json_data={"value": [{"id": "NB1", "displayName": "De Energiemeneer"}]})
        if method == "GET" and url.endswith("/notebooks/NB1/sections"):
            return _resp(json_data={"value": [{"id": "S1", "displayName": "Opnames"}]})
        if method == "GET" and "/sections/S1/pages" in url:
            return _resp(json_data={"value": [{"id": "P1", "title": "Iets anders"}]})
        raise AssertionError(f"onverwachte call {method} {url}")

    calls = _vang_request(monkeypatch, responder)
    with pytest.raises(RuntimeError, match="Sjabloonpagina 'Adres' niet gevonden"):
        onenote.kopieer_sjabloonpagina("De Energiemeneer", "Opnames", "Adres", "Test")
    # Belangrijk: er is NIET stilletjes een pagina aangemaakt.
    assert not [c for c in calls if c["method"] == "POST"]


def test_sjabloon_ontbreekt_maakt_lege_pagina_op_verzoek(monkeypatch):
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/onenote/notebooks"):
            return _resp(json_data={"value": [{"id": "NB1", "displayName": "De Energiemeneer"}]})
        if method == "GET" and url.endswith("/notebooks/NB1/sections"):
            return _resp(json_data={"value": [{"id": "S1", "displayName": "Opnames"}]})
        if method == "GET" and "/sections/S1/pages" in url:
            return _resp(json_data={"value": []})
        if method == "POST" and "/sections/S1/pages" in url:
            return _resp(status=201, json_data={"id": "P-leeg"})
        raise AssertionError(f"onverwachte call {method} {url}")

    calls = _vang_request(monkeypatch, responder)
    r = onenote.kopieer_sjabloonpagina(
        "De Energiemeneer", "Opnames", "Adres", "Straat 8 & co",
        maak_lege_bij_ontbreken=True)
    assert r == {"id": "P-leeg", "titel": "Straat 8 & co", "methode": "leeg"}
    # De lege pagina ging als xhtml met XML-veilige titel naar Graph.
    post = [c for c in calls if c["method"] == "POST"][0]
    assert post["headers"]["Content-Type"] == "application/xhtml+xml"
    assert b"Straat 8 &amp; co" in post["data"]


def test_notitieboek_niet_gevonden(monkeypatch):
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/onenote/notebooks"):
            return _resp(json_data={"value": [{"id": "NB1", "displayName": "Ander boek"}]})
        raise AssertionError(f"onverwachte call {method} {url}")

    _vang_request(monkeypatch, responder)
    with pytest.raises(RuntimeError, match="Notitieboek 'De Energiemeneer' niet gevonden"):
        onenote.kopieer_sjabloonpagina("De Energiemeneer", "Opnames", "Adres", "Test")


def test_sectie_niet_gevonden(monkeypatch):
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/onenote/notebooks"):
            return _resp(json_data={"value": [{"id": "NB1", "displayName": "De Energiemeneer"}]})
        if method == "GET" and url.endswith("/notebooks/NB1/sections"):
            return _resp(json_data={"value": [{"id": "S1", "displayName": "Andere sectie"}]})
        raise AssertionError(f"onverwachte call {method} {url}")

    _vang_request(monkeypatch, responder)
    with pytest.raises(RuntimeError, match="Sectie 'Opnames' niet gevonden"):
        onenote.kopieer_sjabloonpagina("De Energiemeneer", "Opnames", "Adres", "Test")


def test_eist_alle_namen():
    with pytest.raises(ValueError, match="notitieboek_naam"):
        onenote.kopieer_sjabloonpagina("", "Opnames", "Adres", "Test")
    with pytest.raises(ValueError, match="sectie_naam"):
        onenote.kopieer_sjabloonpagina("Boek", "  ", "Adres", "Test")
    with pytest.raises(ValueError, match="sjabloon_titel"):
        onenote.kopieer_sjabloonpagina("Boek", "Opnames", "", "Test")
    with pytest.raises(ValueError, match="nieuwe_titel"):
        onenote.kopieer_sjabloonpagina("Boek", "Opnames", "Adres", "")


def test_notitieboeken_ophalen_fout(monkeypatch):
    _vang_request(monkeypatch, lambda *a: _resp(status=500, text="boom"))
    with pytest.raises(RuntimeError, match="Notitieboeken ophalen mislukt"):
        onenote.kopieer_sjabloonpagina("Boek", "Opnames", "Adres", "Test")

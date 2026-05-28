from unittest.mock import MagicMock

import pytest
import requests

from energiemeneer_core import graph_auth
from energiemeneer_core.graph_api import todo


@pytest.fixture(autouse=True)
def _altijd_geldig_token(monkeypatch):
    monkeypatch.setattr(graph_auth, "haal_graph_token", lambda: "AT-test")
    yield


def _resp(status=200, json_data=None, text=""):
    r = MagicMock(spec=requests.Response)
    r.status_code = status
    r.json.return_value = json_data if json_data is not None else {}
    r.text = text
    return r


def _vang_request(monkeypatch, responder):
    """responder(method, url, json) -> Response; logt alle calls."""
    calls: list[dict] = []

    def fake_request(method, url, headers=None, params=None, json=None,
                     data=None, timeout=None):
        calls.append({"method": method, "url": url, "json": json})
        return responder(method, url, json)

    monkeypatch.setattr(requests, "request", fake_request)
    return calls


def test_maak_taak_in_bestaande_lijst(monkeypatch):
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/todo/lists"):
            return _resp(json_data={"value": [{"id": "L1", "displayName": "Opnames"}]})
        if method == "GET" and url.endswith("/L1/tasks"):
            return _resp(json_data={"value": []})
        if method == "POST" and url.endswith("/L1/tasks"):
            return _resp(status=201, json_data={"id": "T1"})
        raise AssertionError(f"onverwachte call {method} {url}")

    calls = _vang_request(monkeypatch, responder)
    r = todo.maak_taak("Opnames", "Opname Straat 8", deadline="15-06-2026")
    assert r["lijst"] == "Opnames"
    assert r["taak"] == "Opname Straat 8"
    assert r["id"] == "T1"
    post = [c for c in calls if c["method"] == "POST"][0]
    assert post["json"]["title"] == "Opname Straat 8"
    assert post["json"]["dueDateTime"] == {
        "dateTime": "2026-06-15T00:00:00.0000000", "timeZone": "Europe/Amsterdam"}


def test_maak_taak_maakt_lijst_aan_als_die_ontbreekt(monkeypatch):
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/todo/lists"):
            return _resp(json_data={"value": []})  # geen lijsten
        if method == "POST" and url.endswith("/me/todo/lists"):
            return _resp(status=201, json_data={"id": "L-nieuw"})
        if method == "GET" and url.endswith("/L-nieuw/tasks"):
            return _resp(json_data={"value": []})
        if method == "POST" and url.endswith("/L-nieuw/tasks"):
            return _resp(status=201, json_data={"id": "T2"})
        raise AssertionError(f"onverwachte call {method} {url}")

    calls = _vang_request(monkeypatch, responder)
    r = todo.maak_taak("Nieuwe lijst", "Taak")
    assert r["id"] == "T2"
    # Lijst is aangemaakt met de juiste naam.
    lijst_post = [c for c in calls if c["method"] == "POST"
                  and c["url"].endswith("/me/todo/lists")][0]
    assert lijst_post["json"]["displayName"] == "Nieuwe lijst"
    # Taak zonder deadline: geen dueDateTime.
    taak_post = [c for c in calls if c["method"] == "POST"
                 and c["url"].endswith("/L-nieuw/tasks")][0]
    assert "dueDateTime" not in taak_post["json"]


def test_maak_taak_dubbele_naam_krijgt_suffix(monkeypatch):
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/todo/lists"):
            return _resp(json_data={"value": [{"id": "L1", "displayName": "Opnames"}]})
        if method == "GET" and url.endswith("/L1/tasks"):
            return _resp(json_data={"value": [
                {"title": "Opname"}, {"title": "Opname_1"}]})
        if method == "POST" and url.endswith("/L1/tasks"):
            return _resp(status=201, json_data={"id": "T3"})
        raise AssertionError(f"onverwachte call {method} {url}")

    calls = _vang_request(monkeypatch, responder)
    r = todo.maak_taak("Opnames", "Opname")
    assert r["taak"] == "Opname_2"  # _1 was ook al bezet
    post = [c for c in calls if c["method"] == "POST"][0]
    assert post["json"]["title"] == "Opname_2"


def test_maak_taak_eist_namen():
    with pytest.raises(ValueError, match="lijst_naam"):
        todo.maak_taak("", "Taak")
    with pytest.raises(ValueError, match="taak_naam"):
        todo.maak_taak("Lijst", "  ")


def test_maak_taak_ongeldige_deadline(monkeypatch):
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/todo/lists"):
            return _resp(json_data={"value": [{"id": "L1", "displayName": "Opnames"}]})
        if method == "GET" and url.endswith("/L1/tasks"):
            return _resp(json_data={"value": []})
        raise AssertionError(f"onverwachte call {method} {url}")

    _vang_request(monkeypatch, responder)
    with pytest.raises(ValueError, match="Ongeldige deadline"):
        todo.maak_taak("Opnames", "Taak", deadline="2026/06/15")


def test_maak_taak_lijsten_ophalen_fout(monkeypatch):
    _vang_request(monkeypatch, lambda *a: _resp(status=500, text="boom"))
    with pytest.raises(RuntimeError, match="lijsten ophalen mislukt"):
        todo.maak_taak("Opnames", "Taak")


def test_maak_taak_aanmaken_fout(monkeypatch):
    def responder(method, url, json):
        if method == "GET" and url.endswith("/me/todo/lists"):
            return _resp(json_data={"value": [{"id": "L1", "displayName": "Opnames"}]})
        if method == "GET" and url.endswith("/L1/tasks"):
            return _resp(json_data={"value": []})
        return _resp(status=400, text="bad")  # POST task

    _vang_request(monkeypatch, responder)
    with pytest.raises(RuntimeError, match="Taak aanmaken mislukt"):
        todo.maak_taak("Opnames", "Taak")

from unittest.mock import MagicMock

import pytest
import requests

from energiemeneer_core import graph_auth
from energiemeneer_core.graph_api import onedrive


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
    """responder(method, url, json, data) -> Response. Logt alle calls."""
    calls: list[dict] = []

    def fake_request(method, url, headers=None, params=None, json=None,
                     data=None, timeout=None):
        calls.append({"method": method, "url": url, "json": json,
                      "data": data, "headers": headers})
        return responder(method, url, json, data)

    monkeypatch.setattr(requests, "request", fake_request)
    return calls


# ── Map aanmaken ───────────────────────────────────────────────────────────────


def test_maak_map_enkele_nieuwe_map(monkeypatch):
    def responder(method, url, json, data):
        if method == "GET":
            return _resp(status=404)  # bestaat nog niet
        return _resp(status=201, json_data={"id": "F1"})  # POST create

    calls = _vang_request(monkeypatch, responder)
    r = onedrive.maak_map("Energielabels")
    assert r == {"pad": "Energielabels", "mapnaam": "Energielabels"}
    # root-niveau create gaat naar /children
    post = [c for c in calls if c["method"] == "POST"][0]
    assert post["url"].endswith("/me/drive/root/children")
    assert post["json"]["name"] == "Energielabels"


def test_maak_map_slaat_bestaande_tussenmappen_over(monkeypatch):
    # "A/B/C": A en B bestaan al, C is nieuw.
    bestaande = {"A", "A/B"}

    def responder(method, url, json, data):
        if method == "GET":
            pad = url.split("/me/drive/root:/", 1)[1]
            return _resp(status=200) if pad in bestaande else _resp(status=404)
        return _resp(status=201, json_data={"id": "x"})

    calls = _vang_request(monkeypatch, responder)
    r = onedrive.maak_map("A/B/C")
    assert r["pad"] == "A/B/C" and r["mapnaam"] == "C"
    # Alleen C wordt aangemaakt (A en B bestonden al).
    posts = [c for c in calls if c["method"] == "POST"]
    assert len(posts) == 1
    assert posts[0]["json"]["name"] == "C"
    assert posts[0]["url"].endswith("/me/drive/root:/A/B:/children")


def test_maak_map_unieke_naam_bij_botsing(monkeypatch):
    # "Klanten/Straat 8" bestaat al, "Klanten/Straat 8_1" niet.
    bestaande = {"Klanten", "Klanten/Straat 8"}

    def responder(method, url, json, data):
        if method == "GET":
            pad = url.split("/me/drive/root:/", 1)[1]
            return _resp(status=200) if pad in bestaande else _resp(status=404)
        return _resp(status=201, json_data={"id": "x"})

    calls = _vang_request(monkeypatch, responder)
    r = onedrive.maak_map("Klanten/Straat 8")
    assert r["mapnaam"] == "Straat 8_1"
    assert r["pad"] == "Klanten/Straat 8_1"
    post = [c for c in calls if c["method"] == "POST"][0]
    assert post["json"]["name"] == "Straat 8_1"


def test_maak_map_eist_pad():
    with pytest.raises(ValueError, match="pad is verplicht"):
        onedrive.maak_map("   ")


def test_maak_map_fout_bij_controle(monkeypatch):
    _vang_request(monkeypatch, lambda *a: _resp(status=500, text="boom"))
    with pytest.raises(RuntimeError, match="controleren mislukt"):
        onedrive.maak_map("X")


# ── Upload: klein ──────────────────────────────────────────────────────────────


def test_upload_klein_bestand(monkeypatch, tmp_path):
    bestand = tmp_path / "doc.pdf"
    bestand.write_bytes(b"kleine inhoud")

    calls = _vang_request(monkeypatch, lambda *a: _resp(status=201))
    r = onedrive.upload_bestand(str(bestand), "Map/doc.pdf")
    assert r == {"pad": "Map/doc.pdf", "grootte": len(b"kleine inhoud")}
    assert calls[0]["method"] == "PUT"
    assert calls[0]["url"].endswith("/me/drive/root:/Map/doc.pdf:/content")
    assert calls[0]["data"] == b"kleine inhoud"
    assert calls[0]["headers"]["Content-Type"] == "application/octet-stream"


def test_upload_eist_doelpad(tmp_path):
    bestand = tmp_path / "x.txt"
    bestand.write_bytes(b"x")
    with pytest.raises(ValueError, match="onedrive_pad"):
        onedrive.upload_bestand(str(bestand), "")


def test_upload_bestand_niet_gevonden():
    with pytest.raises(RuntimeError, match="niet gevonden"):
        onedrive.upload_bestand("/bestaat/niet.txt", "Map/x.txt")


def test_upload_klein_fout(monkeypatch, tmp_path):
    bestand = tmp_path / "doc.pdf"
    bestand.write_bytes(b"data")
    _vang_request(monkeypatch, lambda *a: _resp(status=403, text="nee"))
    with pytest.raises(RuntimeError, match="Upload mislukt"):
        onedrive.upload_bestand(str(bestand), "Map/doc.pdf")


# ── Upload: groot (upload-sessie in stukjes) ───────────────────────────────────


def test_upload_groot_bestand_in_stukjes(monkeypatch, tmp_path):
    # Verlaag grenzen zodat een klein testbestand de 'grote' weg neemt.
    monkeypatch.setattr(onedrive, "_SIMPEL_MAX", 4)
    monkeypatch.setattr(onedrive, "_CHUNK", 4)

    bestand = tmp_path / "groot.bin"
    bestand.write_bytes(b"0123456789")  # 10 bytes -> 3 brokken van 4/4/2

    # createUploadSession loopt via requests.request (POST).
    def responder(method, url, json, data):
        return _resp(status=200, json_data={"uploadUrl": "https://upload.example/sessie"})

    req_calls = _vang_request(monkeypatch, responder)

    # De brokken gaan via requests.put naar de uploadUrl.
    put_calls: list[dict] = []

    def fake_put(url, data=None, headers=None, timeout=None):
        bereik = headers["Content-Range"]
        put_calls.append({"url": url, "len": len(data), "range": bereik})
        # Laatste brok ("bytes 8-9/10"): 201 klaar; tussenbrokken: 202.
        eind, totaal = bereik.split(" ")[1].split("/")
        laatste = int(eind.split("-")[1]) == int(totaal) - 1
        return _resp(status=201 if laatste else 202)

    monkeypatch.setattr(requests, "put", fake_put)

    r = onedrive.upload_bestand(str(bestand), "Map/groot.bin")
    assert r["grootte"] == 10
    # createUploadSession is aangevraagd.
    assert any("createUploadSession" in c["url"] for c in req_calls)
    # 3 brokken: 0-3, 4-7, 8-9.
    assert [c["range"] for c in put_calls] == [
        "bytes 0-3/10", "bytes 4-7/10", "bytes 8-9/10",
    ]
    assert [c["len"] for c in put_calls] == [4, 4, 2]


def test_upload_groot_sessie_fout(monkeypatch, tmp_path):
    monkeypatch.setattr(onedrive, "_SIMPEL_MAX", 1)
    bestand = tmp_path / "groot.bin"
    bestand.write_bytes(b"abcd")
    _vang_request(monkeypatch, lambda *a: _resp(status=500, text="nee"))
    with pytest.raises(RuntimeError, match="Upload-sessie aanvragen mislukt"):
        onedrive.upload_bestand(str(bestand), "Map/groot.bin")

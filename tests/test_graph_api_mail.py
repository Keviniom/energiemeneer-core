from unittest.mock import MagicMock

import pytest
import requests

from energiemeneer_core import graph_auth
from energiemeneer_core.graph_api import mail


@pytest.fixture(autouse=True)
def _altijd_geldig_token(monkeypatch):
    monkeypatch.setattr(graph_auth, "haal_graph_token", lambda: "AT-test")
    yield


def _resp(status=202, json_data=None, text=""):
    r = MagicMock(spec=requests.Response)
    r.status_code = status
    r.json.return_value = json_data if json_data is not None else {}
    r.text = text
    return r


def _vang_request(monkeypatch, response):
    calls: list[dict] = []

    def fake_request(method, url, headers=None, params=None, json=None, timeout=None):
        calls.append({"method": method, "url": url, "json": json})
        return response

    monkeypatch.setattr(requests, "request", fake_request)
    return calls


def test_stuur_mail_enkel_adres(monkeypatch):
    calls = _vang_request(monkeypatch, _resp(status=202))
    ok = mail.stuur_mail("klant@example.nl", "Hoi", "<b>test</b>")
    assert ok is True
    payload = calls[0]["json"]
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"].endswith("/me/sendMail")
    bericht = payload["message"]
    assert bericht["subject"] == "Hoi"
    assert bericht["body"] == {"contentType": "HTML", "content": "<b>test</b>"}
    assert bericht["toRecipients"] == [{"emailAddress": {"address": "klant@example.nl"}}]
    assert payload["saveToSentItems"] is True
    # Geen cc/bcc/replyTo als die niet zijn meegegeven.
    assert "ccRecipients" not in bericht
    assert "bccRecipients" not in bericht
    assert "replyTo" not in bericht


def test_stuur_mail_lijsten_en_cc_bcc_replyto(monkeypatch):
    calls = _vang_request(monkeypatch, _resp(status=202))
    mail.stuur_mail(
        ["a@x.nl", "b@x.nl"], "Onderwerp", "<p>hoi</p>",
        cc="c@x.nl", bcc=["d@x.nl", "e@x.nl"], reply_to="info@de-energiemeneer.nl",
        opslaan_in_verzonden=False,
    )
    bericht = calls[0]["json"]["message"]
    assert [r["emailAddress"]["address"] for r in bericht["toRecipients"]] == ["a@x.nl", "b@x.nl"]
    assert [r["emailAddress"]["address"] for r in bericht["ccRecipients"]] == ["c@x.nl"]
    assert [r["emailAddress"]["address"] for r in bericht["bccRecipients"]] == ["d@x.nl", "e@x.nl"]
    assert bericht["replyTo"] == [{"emailAddress": {"address": "info@de-energiemeneer.nl"}}]
    assert calls[0]["json"]["saveToSentItems"] is False


def test_stuur_mail_negeert_lege_adressen_in_lijst(monkeypatch):
    calls = _vang_request(monkeypatch, _resp(status=202))
    mail.stuur_mail(["  ", "a@x.nl", ""], "x", "y")
    bericht = calls[0]["json"]["message"]
    assert [r["emailAddress"]["address"] for r in bericht["toRecipients"]] == ["a@x.nl"]


def test_stuur_mail_eist_ontvanger(monkeypatch):
    _vang_request(monkeypatch, _resp(status=202))
    with pytest.raises(ValueError, match="ontvanger"):
        mail.stuur_mail("", "Hoi", "<b>x</b>")
    with pytest.raises(ValueError, match="ontvanger"):
        mail.stuur_mail(["  ", ""], "Hoi", "<b>x</b>")


def test_stuur_mail_accepteert_200(monkeypatch):
    _vang_request(monkeypatch, _resp(status=200))
    assert mail.stuur_mail("a@x.nl", "x", "y") is True


def test_stuur_mail_fout(monkeypatch):
    _vang_request(monkeypatch, _resp(status=400, text="bad request"))
    with pytest.raises(RuntimeError, match="Mail versturen mislukt"):
        mail.stuur_mail("a@x.nl", "x", "y")

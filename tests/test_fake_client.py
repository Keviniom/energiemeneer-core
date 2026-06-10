"""De fake Graph-client: dev/test zonder echte Microsoft 365-tenant.

Elke test bewijst tevens dat er géén netwerk aan te pas komt: elke echte
``requests``-aanroep klapt eruit via de autouse-fixture.
"""

import pytest
import requests

from energiemeneer_core import graph_auth
from energiemeneer_core.graph_api import _client, _fake_client, agenda, mail, onenote, todo


@pytest.fixture(autouse=True)
def _fake_modus(monkeypatch):
    monkeypatch.setenv("USE_FAKE_CLIENTS", "1")
    _fake_client.reset_onenote()  # elke test start met een verse OneNote-store

    def _boem(*a, **k):
        raise AssertionError("Echte HTTP-aanroep in fake-modus!")

    for naam in ("request", "get", "post", "put", "patch", "delete"):
        monkeypatch.setattr(requests, naam, _boem)
    yield


# ── Auth-stub ────────────────────────────────────────────────────────────────


def test_haal_graph_token_geeft_fake_token():
    assert graph_auth.haal_graph_token() == graph_auth._FAKE_ACCESS_TOKEN


def test_device_login_slaagt_direct():
    data = graph_auth.start_device_login()
    assert data["user_code"]
    assert graph_auth.voltooi_device_login(data["device_code"]) is True


# ── Writes -> succes-vorm, geen netwerk ──────────────────────────────────────


def test_write_sendmail_geeft_202():
    resp = _client.post("/me/sendMail", json={"message": {}})
    assert resp.status_code == 202


def test_write_event_geeft_id():
    resp = _client.post("/me/events", json={})
    assert resp.status_code == 201
    assert resp.json()["id"]


# ── Reads -> minimale fixtures ───────────────────────────────────────────────


def test_agenda_read_geeft_lege_lijst():
    assert agenda.haal_agenda_op("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z") == []


def test_todo_read_geeft_lege_lijst():
    assert todo.lees_lijsten() == []


def test_mail_read_geeft_een_minimaal_bericht():
    res = mail.zoek_berichten()
    assert len(res) == 1
    assert res[0]["afzender"] == "noreply@fake.local"


# ── Beide remmen samen: mail AAN + fake -> verstuurt naar de fake ────────────


def test_stuur_mail_in_fake_met_mail_aan(monkeypatch):
    monkeypatch.setenv("MAIL_ENABLED", "1")
    assert mail.stuur_mail("a@x.nl", "Hoi", "<b>x</b>") is True


def test_maak_taak_end_to_end_in_fake():
    # Leeg lijst-overzicht -> lijst aanmaken -> taak aanmaken, allemaal fake.
    res = todo.maak_taak("Energielabels", "Dossier 2521DV")
    assert res["taak"] == "Dossier 2521DV"
    assert res["id"]


# ── Stateful OneNote: kopieerflow draait end-to-end ──────────────────────────


def test_onenote_kopieer_end_to_end():
    # Standaard-seed: notitieboek "De Energiemeneer" / sectie "Opnames" / sjabloon "Adres".
    res = onenote.kopieer_sjabloonpagina(
        "De Energiemeneer", "Opnames", "Adres", "Straat 8"
    )
    assert res["methode"] == "kopie"
    assert res["titel"] == "Straat 8"
    assert res["id"]


def test_onenote_tweede_kopie_krijgt_suffix():
    onenote.kopieer_sjabloonpagina("De Energiemeneer", "Opnames", "Adres", "Straat 8")
    tweede = onenote.kopieer_sjabloonpagina(
        "De Energiemeneer", "Opnames", "Adres", "Straat 8"
    )
    assert tweede["titel"] == "Straat 8_1"


def test_onenote_seed_custom(monkeypatch):
    _fake_client.seed_onenote([
        {"displayName": "Testboek", "sections": [
            {"displayName": "Sectie A", "pages": [{"title": "Sjabloon X"}]},
        ]},
    ])
    res = onenote.kopieer_sjabloonpagina("Testboek", "Sectie A", "Sjabloon X", "Nieuw dossier")
    assert res["methode"] == "kopie"
    assert res["titel"] == "Nieuw dossier"


def test_onenote_ontbrekende_sjabloon_geeft_duidelijke_fout():
    with pytest.raises(RuntimeError, match="niet gevonden"):
        onenote.kopieer_sjabloonpagina(
            "De Energiemeneer", "Opnames", "Bestaat niet", "Straat 8"
        )


def test_onenote_lege_pagina_op_verzoek():
    res = onenote.kopieer_sjabloonpagina(
        "De Energiemeneer", "Opnames", "Bestaat niet", "Straat 8",
        maak_lege_bij_ontbreken=True,
    )
    assert res["methode"] == "leeg"
    assert res["titel"] == "Straat 8"

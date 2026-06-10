"""Fake Microsoft Graph-client voor dev/test zonder echte Microsoft 365-tenant.

Wordt ingeschakeld door :mod:`energiemeneer_core.graph_api._client` zodra
:func:`energiemeneer_core.environment.use_fake_clients` waar is. Geeft objecten
terug met dezelfde vorm als ``requests.Response`` (``status_code``, ``json()``,
``text``, ``headers``), zodat de aanroepende modules niets merken.

- **Writes** (sendMail, agenda, OneDrive, OneNote, ToDo) doen niets echt: ze
  loggen een ``[FAKE]``-regel en geven een succes-vormige respons.
- **Reads** geven minimale fixtures die qua structuur matchen met wat de echte
  Graph teruggeeft (lege collecties waar de caller dat verdraagt, één minimaal
  item waar hij er minstens één nodig heeft).

Bewust een *leaf*-module: importeert alleen de standaardbibliotheek, zodat er
geen circulaire imports ontstaan. De auth-stub (token, device-login) zit niet
hier maar in :mod:`energiemeneer_core.graph_auth`.

De volledige, stateful OneNote-kopieerflow komt in een latere stap; hier geven
de OneNote-reads nog lege collecties.
"""

from __future__ import annotations

import logging
from typing import Any

_log = logging.getLogger(__name__)

# Eén minimaal bericht voor de mailbox-scan — qua structuur gelijk aan Graph.
_FAKE_BERICHT = {
    "id": "fake-msg-1",
    "subject": "[FAKE] Voorbeeldbericht",
    "from": {"emailAddress": {"address": "noreply@fake.local"}},
    "receivedDateTime": "2026-01-01T00:00:00Z",
    "hasAttachments": False,
}


class _FakeResponse:
    """Minimale ``requests.Response``-vorm: ``status_code``/``json()``/``text``/``headers``."""

    def __init__(
        self,
        status_code: int,
        json_data: Any = None,
        *,
        text: str = "",
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self._json = {} if json_data is None else json_data
        self.text = text
        self.headers = headers or {}

    def json(self) -> Any:
        return self._json


def verzoek(
    methode: str,
    pad: str,
    *,
    params: Any = None,
    json: Any = None,
    data: Any = None,
    headers_extra: dict[str, str] | None = None,
    timeout: int = 15,
) -> _FakeResponse:
    """Beantwoord een Graph-aanroep met een fake respons (geen netwerk)."""
    return _dispatch((methode or "").upper(), pad)


def _dispatch(m: str, pad: str) -> _FakeResponse:
    # ── Agenda / mail / events (writes) ──────────────────────────────────────
    if m == "POST" and pad == "/me/sendMail":
        _log.info("[FAKE] POST /me/sendMail — niet echt verzonden")
        return _FakeResponse(202)
    if m == "POST" and pad == "/me/events":
        _log.info("[FAKE] POST /me/events — afspraak niet echt aangemaakt")
        return _FakeResponse(201, {"id": "fake-event-1"})
    if m == "PATCH" and pad.startswith("/me/events/"):
        _log.info("[FAKE] PATCH %s — afspraak niet echt gewijzigd", pad)
        return _FakeResponse(200, {"id": pad.rsplit("/", 1)[-1]})
    if m == "DELETE" and pad.startswith("/me/events/"):
        _log.info("[FAKE] DELETE %s — afspraak niet echt geannuleerd", pad)
        return _FakeResponse(204)

    # ── ToDo ─────────────────────────────────────────────────────────────────
    if m == "POST" and pad == "/me/todo/lists":
        _log.info("[FAKE] POST /me/todo/lists — lijst niet echt aangemaakt")
        return _FakeResponse(201, {"id": "fake-list-1"})
    if m == "POST" and pad.endswith("/tasks"):
        _log.info("[FAKE] POST %s — taak niet echt aangemaakt", pad)
        return _FakeResponse(201, {"id": "fake-task-1"})
    if m == "GET" and (pad == "/me/todo/lists" or pad.endswith("/tasks")):
        return _FakeResponse(200, {"value": []})

    # ── OneDrive ─────────────────────────────────────────────────────────────
    if m == "PUT" and pad.endswith(":/content"):
        _log.info("[FAKE] PUT %s — bestand niet echt geüpload", pad)
        return _FakeResponse(
            201, {"id": "fake-file-1", "webUrl": "https://fake.local/bestand"}
        )
    if m == "POST" and pad.endswith(":/createUploadSession"):
        return _FakeResponse(200, {"uploadUrl": "https://fake.local/upload-session"})
    if m == "POST" and pad.endswith("/children"):
        _log.info("[FAKE] POST %s — map niet echt aangemaakt", pad)
        return _FakeResponse(201, {"id": "fake-folder-1"})
    if m == "GET" and pad.startswith("/me/drive/root"):
        # 'bestaat nog niet' -> maak_map gaat netjes door met aanmaken;
        # web_url geeft "" terug bij non-200 (geen fout).
        return _FakeResponse(404, text="[FAKE] pad bestaat niet")

    # ── OneNote (basis; stateful kopieerflow volgt in een latere stap) ───────
    if m == "POST" and pad.endswith("/copyToSection"):
        _log.info("[FAKE] POST %s — OneNote-kopie niet echt gestart", pad)
        return _FakeResponse(
            202,
            {"id": "fake-op-1"},
            headers={"Operation-Location": "/me/onenote/operations/fake-op-1"},
        )
    if m == "GET" and pad.startswith("/me/onenote/operations/"):
        return _FakeResponse(200, {"status": "completed", "resourceId": "fake-page-1"})
    if m == "PATCH" and pad.endswith("/content"):
        _log.info("[FAKE] PATCH %s — OneNote-pagina niet echt gewijzigd", pad)
        return _FakeResponse(204)
    if m == "POST" and pad.endswith("/pages"):
        _log.info("[FAKE] POST %s — OneNote-pagina niet echt aangemaakt", pad)
        return _FakeResponse(201, {"id": "fake-page-1"})
    if m == "GET" and pad.startswith("/me/onenote"):
        return _FakeResponse(200, {"value": []})

    # ── Mail (reads) ─────────────────────────────────────────────────────────
    if m == "GET" and pad.endswith("/attachments"):
        return _FakeResponse(200, {"value": []})
    if m == "GET" and pad == "/me/messages":
        return _FakeResponse(200, {"value": [_FAKE_BERICHT]})

    # ── Agenda (read) ────────────────────────────────────────────────────────
    if m == "GET" and pad.startswith("/me/calendarView"):
        return _FakeResponse(200, {"value": []})

    # Onbekend pad: log en geef een lege, geldige respons (nooit crashen).
    _log.warning("[FAKE] onbekende Graph-aanroep %s %s — lege respons", m, pad)
    return _FakeResponse(200, {"value": []})

"""E-mail versturen via Microsoft Graph (``/me/sendMail``).

Bron: ``admin-portal/admin-portal/ms_graph.py`` (de generieke ``stuur_mail``).
Bewust generiek: de aanroeper levert ontvanger(s), onderwerp en HTML-body.
Geen vaste afzender of opmaak ingebakken — de mail vertrekt vanaf het
ingelogde account. Een eventuele vaste sjabloon komt later in een aparte
``mail_template``-module.

Zie BOUWPLAN.md, Module 6 (onderdeel 2).
"""

from __future__ import annotations

import logging

from energiemeneer_core.graph_api import _client

_log = logging.getLogger(__name__)

# Type voor "één adres of een lijst adressen".
Adressen = "str | list[str] | None"


def stuur_mail(
    naar: "str | list[str]",
    onderwerp: str,
    body_html: str,
    cc: "str | list[str] | None" = None,
    bcc: "str | list[str] | None" = None,
    reply_to: "str | list[str] | None" = None,
    opslaan_in_verzonden: bool = True,
) -> bool:
    """Verstuur een HTML-e-mail vanaf het ingelogde account.

    Args:
        naar: ontvanger(s) — één adres of een lijst.
        onderwerp: onderwerpregel.
        body_html: inhoud als HTML.
        cc, bcc, reply_to: optioneel, één adres of een lijst.
        opslaan_in_verzonden: bewaar de mail in "Verzonden items" (standaard).

    Returns:
        ``True`` als Microsoft de mail heeft geaccepteerd.

    Raises:
        ValueError: geen geldige ontvanger.
        RuntimeError: Graph geeft een fout.
    """
    ontvangers = _als_lijst(naar)
    if not ontvangers:
        raise ValueError("Minstens één ontvanger (naar) is verplicht")

    bericht: dict = {
        "subject": onderwerp or "",
        "body": {"contentType": "HTML", "content": body_html or ""},
        "toRecipients": _adres_objecten(ontvangers),
    }
    cc_lijst = _als_lijst(cc)
    if cc_lijst:
        bericht["ccRecipients"] = _adres_objecten(cc_lijst)
    bcc_lijst = _als_lijst(bcc)
    if bcc_lijst:
        bericht["bccRecipients"] = _adres_objecten(bcc_lijst)
    reply_lijst = _als_lijst(reply_to)
    if reply_lijst:
        bericht["replyTo"] = _adres_objecten(reply_lijst)

    payload = {"message": bericht, "saveToSentItems": opslaan_in_verzonden}
    resp = _client.post("/me/sendMail", json=payload)
    if resp.status_code not in (200, 202):
        raise RuntimeError(
            f"Mail versturen mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )
    _log.info("Mail verstuurd aan %s — %s", ", ".join(ontvangers), onderwerp)
    return True


def _als_lijst(adressen: "str | list[str] | None") -> list[str]:
    """Maak van één adres of een lijst een schone lijst zonder lege waarden."""
    if not adressen:
        return []
    if isinstance(adressen, str):
        adressen = [adressen]
    return [a.strip() for a in adressen if a and a.strip()]


def _adres_objecten(adressen: list[str]) -> list[dict]:
    return [{"emailAddress": {"address": a}} for a in adressen]

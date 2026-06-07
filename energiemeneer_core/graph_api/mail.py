"""E-mail via Microsoft Graph: versturen (``/me/sendMail``) en lezen
(``/me/messages``, alleen-lezen).

Bron: ``admin-portal/admin-portal/ms_graph.py`` (de generieke ``stuur_mail``)
en ``energielabel_upload_tool/backend/outlook_handler.py`` (mails + bijlagen
lezen). Bewust generiek: de aanroeper levert ontvanger(s)/filters, geen vaste
afzender of opmaak ingebakken.

De lees-functies (:func:`zoek_berichten`, :func:`haal_bijlagen`) zijn strikt
**alleen-lezen** — ze verwijderen, verplaatsen of markeren niets. Bedoeld voor
o.a. de upload-module (het EP-Online-afschrift ophalen).

Zie BOUWPLAN.md, Module 6 (onderdeel 2).
"""

from __future__ import annotations

import base64
import binascii
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


# ── Lezen (alleen-lezen) ─────────────────────────────────────────────────────
# Voor het ophalen van inkomende mails + bijlagen (bijv. het EP-Online-afschrift
# voor de upload-module). Strikt alleen-lezen: er wordt NIETS verwijderd,
# verplaatst of als gelezen gemarkeerd.

def zoek_berichten(
    afzender: str | None = None,
    onderwerp_bevat: str | None = None,
    alleen_met_bijlagen: bool = False,
    max: int = 50,
) -> list[dict]:
    """Lees berichten uit de mailbox van het ingelogde account (alleen-lezen).

    Filtert server-side op ``afzender`` (exacte match op het e-mailadres) en
    ``alleen_met_bijlagen``. ``onderwerp_bevat`` wordt client-side gefilterd
    (Graph ``$filter`` ondersteunt geen ``contains`` op ``subject``).

    Args:
        afzender: alleen mails van dit exacte afzender-adres (hoofdletter-
            ongevoelig vergeleken; server-side gefilterd).
        onderwerp_bevat: alleen mails waarvan het onderwerp deze tekst bevat
            (hoofdletter-ongevoelig).
        alleen_met_bijlagen: alleen mails met minstens één bijlage.
        max: maximaal aantal mails om op te halen (Graph ``$top``).

    Returns:
        Lijst van dicts: ``id``, ``onderwerp``, ``afzender`` (e-mailadres),
        ``ontvangen`` (ISO-tijd) en ``heeft_bijlagen`` (bool). Nieuwste eerst.

    Raises:
        RuntimeError: Graph geeft een fout.
    """
    filters = []
    if afzender:
        veilig = afzender.replace("'", "''")
        filters.append(f"from/emailAddress/address eq '{veilig}'")
    if alleen_met_bijlagen:
        filters.append("hasAttachments eq true")

    params: dict = {
        "$top": int(max),
        "$select": "id,subject,from,receivedDateTime,hasAttachments",
    }
    if filters:
        # Bij een $filter op 'from' laat Graph geen $orderby op een ander veld
        # toe; we sorteren daarom zelf (client-side) op ontvangsttijd.
        params["$filter"] = " and ".join(filters)
    else:
        params["$orderby"] = "receivedDateTime desc"

    resp = _client.get("/me/messages", params=params)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Mails lezen mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )

    zoek = (onderwerp_bevat or "").lower()
    berichten = []
    for m in resp.json().get("value", []):
        onderwerp = m.get("subject", "") or ""
        if zoek and zoek not in onderwerp.lower():
            continue
        berichten.append({
            "id": m.get("id", ""),
            "onderwerp": onderwerp,
            "afzender": (m.get("from", {}) or {}).get("emailAddress", {}).get("address", ""),
            "ontvangen": m.get("receivedDateTime", ""),
            "heeft_bijlagen": bool(m.get("hasAttachments")),
        })
    berichten.sort(key=lambda b: b.get("ontvangen", ""), reverse=True)
    return berichten


def haal_bijlagen(bericht_id: str) -> list[dict]:
    """Haal de bestandsbijlagen van één bericht op (alleen-lezen).

    Alleen echte bestand-bijlagen (``fileAttachment``) worden teruggegeven;
    inline-/item-bijlagen zonder inhoud worden overgeslagen.

    Args:
        bericht_id: de Graph-``id`` van het bericht (uit :func:`zoek_berichten`).

    Returns:
        Lijst van dicts: ``naam``, ``content_type``, ``grootte`` (bytes) en
        ``inhoud`` (de gedecodeerde bestand-bytes).

    Raises:
        ValueError: geen ``bericht_id``.
        RuntimeError: Graph geeft een fout.
    """
    if not bericht_id:
        raise ValueError("bericht_id is verplicht")

    resp = _client.get(
        f"/me/messages/{bericht_id}/attachments",
        params={"$select": "id,name,contentType,size,contentBytes"},
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Bijlagen ophalen mislukt (HTTP {resp.status_code}): {resp.text[:300]}"
        )

    bijlagen = []
    for a in resp.json().get("value", []):
        inhoud_b64 = a.get("contentBytes")
        if not inhoud_b64:
            # itemAttachment / referenceAttachment hebben geen contentBytes — overslaan.
            continue
        try:
            inhoud = base64.b64decode(inhoud_b64)
        except (binascii.Error, ValueError):
            continue
        bijlagen.append({
            "naam": a.get("name", "") or "",
            "content_type": a.get("contentType", "") or "",
            "grootte": a.get("size", 0) or len(inhoud),
            "inhoud": inhoud,
        })
    return bijlagen

import pytest

from energiemeneer_core import email_format


def _afspraak():
    return {
        "token": "abc123token",
        "start": "2026-06-01T07:00:00Z",   # 09:00 Amsterdam (zomertijd)
        "end": "2026-06-01T08:30:00Z",     # 10:30 Amsterdam
        "klant": {
            "voornaam": "Jan",
            "achternaam": "Jansen",
            "email": "jan@example.nl",
            "telefoon": "0612345678",
        },
        "adres": {
            "straatnaam": "Graskopstraat",
            "huisnummer": 8,
            "postcode": "2541 AB",
            "woonplaats": "'s-Gravenhage",
            "oppervlakte": 120,
            "bouwjaar": 1998,
        },
        "woningtype": "tussenwoning",
        "prijs": "315",
        "label": "C",
    }


# ── _fmt_periode ──────────────────────────────────────────────────────────────


def test_periode_amsterdam_zomertijd():
    p = email_format._fmt_periode("2026-06-01T07:00:00Z", "2026-06-01T08:30:00Z")
    assert p["dag"] == "maandag"
    assert p["datum"] == "1 juni 2026"
    assert p["tijd"] == "09:00 – 10:30"
    assert p["duur"] == "90 minuten"


def test_periode_wintertijd_offset_plus_1():
    # 2026-01-05 08:00Z = 09:00 Amsterdam (wintertijd, +1)
    p = email_format._fmt_periode("2026-01-05T08:00:00Z", "2026-01-05T09:30:00Z")
    assert p["tijd"] == "09:00 – 10:30"
    assert p["dag"] == "maandag"


# ── bevestigingsmail ──────────────────────────────────────────────────────────


def test_bevestiging_onderwerp_en_body():
    subj, body = email_format.bevestigingsmail(
        _afspraak(), portal_url="https://portal.example.nl", intro_tekst="Bedankt voor je opdracht!")
    assert subj == "Afspraak bevestigd — maandag 1 juni 2026 09:00 – 10:30"
    assert "Hallo Jan, je afspraak staat ingepland" in body
    assert "Bedankt voor je opdracht!" in body
    # detail-tabel
    assert "Graskopstraat 8, 2541 AB 's-Gravenhage" in body
    assert "120 m²" in body and "1998" in body and "€ 315" in body
    assert "Tussenwoning" in body
    # actieknop-link met token
    assert "https://portal.example.nl/a/abc123token" in body


def test_bevestiging_opdrachtbevestiging_blok_ingevoegd():
    _, body = email_format.bevestigingsmail(
        _afspraak(), portal_url="https://p.nl", intro_tekst="x",
        opdrachtbevestiging_html="<div id='ob'>OB-blok</div>")
    assert "<div id='ob'>OB-blok</div>" in body


def test_portal_url_trailing_slash_genormaliseerd():
    _, body = email_format.bevestigingsmail(
        _afspraak(), portal_url="https://p.nl/", intro_tekst="x")
    assert "https://p.nl/a/abc123token" in body
    assert "https://p.nl//a/" not in body


# ── wijziging / annulering ────────────────────────────────────────────────────


def test_wijziging_onderwerp_en_kop():
    subj, body = email_format.wijzigingsmail(
        _afspraak(), portal_url="https://p.nl", intro_tekst="Gewijzigd.")
    assert subj == "Afspraak gewijzigd — maandag 1 juni 2026 09:00 – 10:30"
    assert "je nieuwe afspraak is bevestigd" in body
    assert "Nieuwe tijd" in body


def test_annulering_onderwerp_en_kop():
    subj, body = email_format.annuleringsmail(
        _afspraak(), portal_url="https://p.nl", intro_tekst="Geannuleerd.")
    assert subj == "Afspraak geannuleerd — maandag 1 juni 2026"
    assert "je afspraak is geannuleerd" in body
    assert "line-through" in body  # doorgestreepte tijd


# ── admin_notificatie ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("soort,vlag", [
    ("nieuw", "🟢 Nieuwe afspraak ingepland"),
    ("gewijzigd", "🟡 Afspraak gewijzigd door klant"),
    ("geannuleerd", "🔴 Afspraak geannuleerd door klant"),
])
def test_admin_notificatie_soorten(soort, vlag):
    subj, body = email_format.admin_notificatie(_afspraak(), soort)
    assert vlag in body
    assert subj.startswith(vlag + ": Jan Jansen")
    assert "jan@example.nl" in body and "0612345678" in body
    assert "abc123token" in body


def test_klant_naam_fallback():
    a = _afspraak()
    a["klant"] = {}
    subj, body = email_format.bevestigingsmail(a, portal_url="https://p.nl", intro_tekst="x")
    # zonder naam valt _klant_naam terug op "klant"
    assert "Hallo klant" in body

import pytest

from energiemeneer_core import prijs


def test_tot_100_bestaand():
    r = prijs.bereken_prijs(80)
    assert r["categorie"] == "tot_100"
    assert r["categorie_label"] == "Tot 100 m²"
    assert r["bedrag"] == 280
    assert r["totaal"] == 280
    assert r["nieuwbouw"] is False
    assert r["maatwerk"] is False


def test_tot_100_nieuwbouw():
    r = prijs.bereken_prijs(80, nieuwbouw=True)
    assert r["categorie"] == "tot_100"
    assert r["bedrag"] == 425
    assert r["nieuwbouw"] is True


def test_100_150_bestaand():
    r = prijs.bereken_prijs(125)
    assert r["categorie"] == "100_150"
    assert r["bedrag"] == 315


def test_150_200_nieuwbouw():
    r = prijs.bereken_prijs(175, nieuwbouw=True)
    assert r["categorie"] == "150_200"
    assert r["bedrag"] == 500


def test_grens_100_valt_in_tot_100():
    """100 m² valt in de gunstigste categorie."""
    r = prijs.bereken_prijs(100)
    assert r["categorie"] == "tot_100"
    assert r["bedrag"] == 280


def test_grens_150_valt_in_100_150():
    r = prijs.bereken_prijs(150)
    assert r["categorie"] == "100_150"
    assert r["bedrag"] == 315


def test_grens_200_valt_in_150_200():
    r = prijs.bereken_prijs(200)
    assert r["categorie"] == "150_200"
    assert r["bedrag"] == 355


def test_boven_200_is_maatwerk():
    r = prijs.bereken_prijs(250)
    assert r["categorie"] == "maatwerk"
    assert r["bedrag"] is None
    assert r["totaal"] is None
    assert r["maatwerk"] is True


def test_onbekende_oppervlakte_is_maatwerk():
    r = prijs.bereken_prijs(None)
    assert r["maatwerk"] is True
    assert r["bedrag"] is None
    assert r["totaal"] is None


def test_nul_en_negatief_zijn_maatwerk():
    assert prijs.bereken_prijs(0)["maatwerk"] is True
    assert prijs.bereken_prijs(-10)["maatwerk"] is True


def test_spoedtoeslag_op_normale_prijs():
    r = prijs.bereken_prijs(80, spoed=True)
    assert r["spoedtoeslag"] == 30
    assert r["bedrag"] == 280
    assert r["totaal"] == 310


def test_spoedtoeslag_op_nieuwbouw():
    r = prijs.bereken_prijs(125, nieuwbouw=True, spoed=True)
    assert r["bedrag"] == 460
    assert r["spoedtoeslag"] == 30
    assert r["totaal"] == 490


def test_spoed_zonder_bedrag_bij_maatwerk():
    """Bij maatwerk blijft totaal None, ook al is spoedtoeslag van toepassing."""
    r = prijs.bereken_prijs(250, spoed=True)
    assert r["spoedtoeslag"] == 30
    assert r["bedrag"] is None
    assert r["totaal"] is None


@pytest.mark.parametrize("opp,nieuwbouw,verwacht", [
    (50,  False, 280), (50,  True, 425),
    (100, False, 280), (100, True, 425),
    (101, False, 315), (101, True, 460),
    (125, False, 315), (125, True, 460),
    (150, False, 315), (150, True, 460),
    (151, False, 355), (151, True, 500),
    (175, False, 355), (175, True, 500),
    (200, False, 355), (200, True, 500),
])
def test_meesterbrein_matrix(opp, nieuwbouw, verwacht):
    """Verifieer elke prijsrij uit Meesterbrein §9.1."""
    r = prijs.bereken_prijs(opp, nieuwbouw=nieuwbouw)
    assert r["bedrag"] == verwacht


def test_default_geen_spoed_geen_nieuwbouw():
    r = prijs.bereken_prijs(80)
    assert r["spoedtoeslag"] == 0
    assert r["nieuwbouw"] is False


def test_constante_publiek():
    """Spoedtoeslag is publiek beschikbaar voor consumers (factuur etc.)."""
    assert prijs.SPOEDTOESLAG_EUR == 30

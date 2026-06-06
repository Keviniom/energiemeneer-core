import pytest

from energiemeneer_core import objectbib


def test_root_bestaat_en_bevat_woningtypes():
    assert objectbib.root().is_dir()
    types = objectbib.beschikbare_woningtypes()
    for verwacht in ["Tussenwoning", "Hoekwoning", "Vrijstaande woning",
                     "Twee onder een kap woning", "Appartement"]:
        assert verwacht in types


@pytest.mark.parametrize("woningtype,klasse,fragment", [
    ("Tussenwoning", "voor 1965", "Objectenbibliotheek voor 1965.xml"),
    ("Tussenwoning", "1975-1982", "Objectenbibliotheek 1975-1982.xml"),
    ("Hoekwoning", "2021 en later", "Objectenbibliotheek 2021 en later.xml"),
    ("Appartement", "1992-2013", "Objectenbibliotheek 1992-2013.xml"),
])
def test_vind_template_bestaande(woningtype, klasse, fragment):
    pad = objectbib.vind_template(woningtype, klasse)
    assert pad is not None and pad.exists()
    assert pad.name == fragment
    assert pad.read_text(encoding="utf-8", errors="ignore").strip() != ""


def test_onbekende_klasse_valt_terug_op_1992_2013():
    pad = objectbib.vind_template("Tussenwoning", "iets-onbekends")
    assert pad is not None and pad.name == "Objectenbibliotheek 1992-2013.xml"


def test_vrijstaand_zonder_2021_valt_terug():
    # 'Vrijstaande woning' heeft (nog) geen 2021-en-later-template → fallback.
    pad = objectbib.vind_template("Vrijstaande woning", "2021 en later")
    assert pad is not None and pad.name == "Objectenbibliotheek 1992-2013.xml"


def test_onbekend_woningtype_geeft_none():
    assert objectbib.vind_template("Kasteel", "1975-1982") is None

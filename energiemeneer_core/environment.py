"""
core/environment.py — gedeelde safety-/policy-laag voor De Energiemeneer.

Single source of truth voor welke side-effects (upload, mail, scheduler,
storage-writes) in welke omgeving zijn toegestaan. De gevaarlijke functies
in core raadplegen deze module; de portal gebruikt describe()/banner() voor
de preflight en scheduler_enabled() voor de start-beslissing.

Regels:
- APP_ENV bepaalt de modus; leeg of onbekend -> 'dev' (veiligst).
- Feature-vlaggen zijn tri-state: leeg -> afgeleid van env (prod=aan, anders
  uit), expliciet gezet -> gehonoreerd. Non-prod is dus uit tenzij je bewust
  aanzet; prod is aan tenzij je bewust een kill-switch zet.
- storage_root() is een echte rem (bestemming), geen vlag.
- upload/mail kennen geen 'test'-bestemming (EP-Online / echte mailboxen zijn
  prod of niets): in non-prod uit, tenzij je ze bewust tegen een sandbox test.
- use_fake_clients() bepaalt of de externe clients (Microsoft Graph, BAG,
  EP-Online) door fakes worden vervangen: non-prod -> fake, prod -> echt,
  tenzij USE_FAKE_CLIENTS expliciet gezet is (dev/test bewust tegen een
  echte sandbox draaien).
"""

import os

_SAFE_DEFAULT = "dev"
_KNOWN = {"dev", "test", "prod"}
_TRUE = {"1", "true", "yes", "on"}


def current_env() -> str:
    env = os.environ.get("APP_ENV", "").strip().lower()
    if env in ("prod", "production"):
        return "prod"
    return env if env in _KNOWN else _SAFE_DEFAULT


def is_production() -> bool:
    return current_env() == "prod"


def _flag(name: str) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return is_production()            # leeg -> afgeleid van env
    return raw.strip().lower() in _TRUE   # expliciet -> gehonoreerd


def uploads_enabled() -> bool:
    return _flag("EP_UPLOAD_ENABLED")


def mail_enabled() -> bool:
    return _flag("MAIL_ENABLED")


def scheduler_enabled() -> bool:
    return _flag("SCHEDULER_ENABLED")


def use_fake_clients() -> bool:
    """Of de externe clients (Graph/BAG/EP-Online) door fakes vervangen worden.

    Leeg -> afgeleid van env (non-prod = fake, prod = echt). Expliciet gezet
    via ``USE_FAKE_CLIENTS`` -> gehonoreerd, zodat je dev/test bewust tegen een
    echte (sandbox) tenant kunt draaien (``USE_FAKE_CLIENTS=0``).
    """
    raw = os.environ.get("USE_FAKE_CLIENTS")
    if raw is None or raw.strip() == "":
        return not is_production()
    return raw.strip().lower() in _TRUE


def storage_root_override() -> str | None:
    """De env-gestuurde storage-bestemming, of ``None`` voor autodetectie.

    Precedentie:
      1. expliciete ``STORAGE_ROOT`` (elke omgeving),
      2. non-prod: ``STORAGE_ROOT_TEST`` (alleen als gezet),
      3. anders ``None`` -> ``storage.vind_data_dir()`` valt terug op zijn eigen
         autodetectie (Railway-volume, ``ENERGIEMENEER_DATA_DIR``, cwd).

    Pure env-leesfunctie: importeert ``storage`` NIET, zodat environment
    afhankelijkheidsarm blijft en er geen circulaire import ontstaat.
    """
    expliciet = os.environ.get("STORAGE_ROOT", "").strip()
    if expliciet:
        return expliciet
    if not is_production():
        test = os.environ.get("STORAGE_ROOT_TEST", "").strip()
        if test:
            return test
    return None


def storage_root() -> str:
    """De effectieve storage-root (voor describe()/banner()).

    Geeft de env-override als die er is, anders het pad dat ``storage`` zélf
    bepaalt via zijn autodetectie. De storage-import is bewust lazy zodat
    environment afhankelijkheidsarm blijft en er geen circulaire import op
    moduleniveau ontstaat.
    """
    override = storage_root_override()
    if override:
        return override
    from energiemeneer_core import storage  # lazy: vermijd circulaire import
    return storage.vind_data_dir()


def describe() -> dict:
    return {
        "env": current_env(),
        "clients": "fake" if use_fake_clients() else "echt",
        "storage_root": storage_root(),
        "uploads": uploads_enabled(),
        "mail": mail_enabled(),
        "scheduler": scheduler_enabled(),
    }


def banner() -> str:
    d = describe()
    return (
        "-" * 48 + "\n"
        f"  De Energiemeneer - omgeving: {d['env'].upper()}\n"
        f"  clients      : {'FAKE' if d['clients'] == 'fake' else 'echt'}\n"
        f"  storage_root : {d['storage_root']}\n"
        f"  uploads      : {'AAN' if d['uploads'] else 'uit'}\n"
        f"  mail         : {'AAN' if d['mail'] else 'uit'}\n"
        f"  scheduler    : {'AAN' if d['scheduler'] else 'uit'}\n"
        + "-" * 48
    )


if __name__ == "__main__":
    print(banner())
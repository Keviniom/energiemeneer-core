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


def storage_root() -> str:
    if is_production():
        root = os.environ.get("STORAGE_ROOT")
        if not root:
            raise RuntimeError(
                "STORAGE_ROOT is verplicht in productie en is niet gezet."
            )
        return root
    # non-prod: dwing een aparte test-map af (per omgeving overschrijven)
    return os.environ.get("STORAGE_ROOT_TEST", "./data-test")


def describe() -> dict:
    return {
        "env": current_env(),
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
        f"  storage_root : {d['storage_root']}\n"
        f"  uploads      : {'AAN' if d['uploads'] else 'uit'}\n"
        f"  mail         : {'AAN' if d['mail'] else 'uit'}\n"
        f"  scheduler    : {'AAN' if d['scheduler'] else 'uit'}\n"
        + "-" * 48
    )


if __name__ == "__main__":
    print(banner())
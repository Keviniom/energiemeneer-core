"""Gedeelde test-instellingen.

Standaard draaien alle tests op het **echte** client-pad (met gemockte HTTP),
zodat de bestaande Graph-/BAG-/EP-tests hun payloads blijven controleren. Tests
die juist de fake willen, zetten zelf ``USE_FAKE_CLIENTS=1`` (dat overschrijft
deze default, omdat een module-fixture ná deze conftest-fixture draait).
"""

import pytest


@pytest.fixture(autouse=True)
def _echte_clients_tenzij_anders(monkeypatch):
    monkeypatch.setenv("USE_FAKE_CLIENTS", "0")
    yield

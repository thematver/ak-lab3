import pytest

from machine.simulation import simulation
from machine.translator import parse_code


@pytest.mark.golden_test("*.yaml")
def test_translator_and_machine(golden):
    data, code = parse_code(golden["source"].split("\n"))
    mnemo = list(map(lambda x: str(x), code))
    assert mnemo == golden["mnemo"]
    assert data == golden["data"]
    journal = simulation(data, code, list(golden["input"]), 32, 1e4)
    assert journal.strip() == golden.out["journal"].strip()

import pytest

from designdojo.contract import ContractError, parse_type, snake_to_camel
from designdojo.problems import get_problem

KINDS = {"SpotSize": "enum", "Ticket": "dto", "Clock": "iface"}


def test_primitives_and_named():
    assert parse_type("str", KINDS) == {"kind": "str"}
    assert parse_type("Ticket", KINDS) == {"kind": "dto", "name": "Ticket"}


def test_nested_generics():
    assert parse_type("map[SpotSize, list[Ticket]]", KINDS) == {
        "kind": "map",
        "key": {"kind": "enum", "name": "SpotSize"},
        "value": {"kind": "list", "of": {"kind": "dto", "name": "Ticket"}},
    }


@pytest.mark.parametrize("bad", ["Nope", "list[int, int]", "map[int]", "map[Ticket, int]", "list[int", "int]"])
def test_rejects_bad_types(bad):
    with pytest.raises(ContractError):
        parse_type(bad, KINDS)


def test_snake_to_camel():
    assert snake_to_camel("hourly_rate_cents") == "hourlyRateCents"
    assert snake_to_camel("id") == "id"


def test_parking_lot_contract_loads():
    c = get_problem("parking-lot").contract
    assert c.entrypoint.returns == {"kind": "iface", "name": "ParkingLotApi"}
    assert set(c.errors) == {"LotFull", "AlreadyParked", "InvalidTicket"}
    park = c.interfaces["ParkingLotApi"]["park"]
    assert [p.name for p in park.params] == ["plate", "vehicle_type"]
    assert park.raises == ["LotFull", "AlreadyParked"]


def test_scenario_names_unique_and_defaults_applied():
    p = get_problem("parking-lot")
    for suite in ("sample", "hidden", "concurrency"):
        for sc in p.suite(suite)["scenarios"]:
            assert "config" in sc, sc["name"]

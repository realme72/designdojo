"""Every problem package must lint clean (contract, scenarios, decision points, reference)."""

import pytest

from designdojo.problems import lint_problem, list_problems


@pytest.mark.parametrize("problem", list_problems(), ids=lambda p: p.id)
def test_problem_lints_clean(problem):
    assert lint_problem(problem) == []


def test_type_lint_catches_yaml_surprises():
    from designdojo.contract import parse_type
    from designdojo.problems import _type_issue, get_problem

    c = get_problem("parking-lot").contract
    kinds = {**{k: "enum" for k in c.enums}, **{k: "dto" for k in c.dtos}}
    assert _type_issue(False, parse_type("str", kinds), c, "x")          # YAML `OFF` -> False
    assert _type_issue("BUS", parse_type("VehicleType", kinds), c, "x")  # not an enum value
    assert _type_issue({"small": 1}, parse_type("FloorConfig", kinds), c, "x")  # missing fields
    assert _type_issue("$t.id", parse_type("str", kinds), c, "x") is None      # references skipped

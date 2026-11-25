"""Every problem package must lint clean (contract, scenarios, decision points, reference)."""

import pytest

from joinery.problems import lint_problem, list_problems


@pytest.mark.parametrize("problem", list_problems(), ids=lambda p: p.id)
def test_problem_lints_clean(problem):
    assert lint_problem(problem) == []

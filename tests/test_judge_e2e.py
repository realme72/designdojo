"""End-to-end: real containers, real reference solutions and deliberately broken ones."""

from pathlib import Path

import pytest

from joinery.judge import Workspace, judge
from joinery.problems import SUITES

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "problems" / "parking-lot" / "reference"
NAIVE = ROOT / "tests" / "fixtures" / "parking-lot"
LANGS = ["java", "python"]

pytestmark = pytest.mark.docker


def failures(result: dict) -> dict[str, set[str]]:
    assert result["status"] == "ok", result
    return {s["name"]: {c["name"] for c in s["cases"] if c["status"] != "pass"} for s in result["suites"]}


@pytest.mark.parametrize("lang", LANGS)
def test_reference_passes_everything(lang):
    result = judge(Workspace.open(REF / lang), list(SUITES))
    assert failures(result) == {s: set() for s in SUITES}


@pytest.mark.parametrize("lang", LANGS)
def test_naive_solution_is_caught(lang):
    f = failures(judge(Workspace.open(NAIVE / lang / "naive"), list(SUITES)))
    assert f["sample"] == set()
    assert f["hidden"] == {"partial_hour_rounds_up", "long_stay", "fee_uses_spot_size_not_vehicle"}
    # Every race scenario must catch the unsynchronized solution, in both languages
    # (Java: spin-start on 4 CPUs; Python: chaos scheduling defeats the GIL).
    assert f["concurrency"] == {
        "last_spots_race", "ticket_ids_unique_under_load", "same_plate_race",
        "double_redeem_race", "concurrent_park_then_unpark",
    }


@pytest.mark.parametrize("lang", LANGS)
def test_unimplemented_stub_fails_cleanly(lang, workspace):
    result = judge(workspace(lang, {}), ["sample"])
    cases = result["suites"][0]["cases"]
    assert all(c["kind"] == "unexpected_error" and c["step"] == 0 for c in cases)


def test_java_compile_error_reported(workspace):
    ws = workspace("java", {"solution/Solution.java": "package solution;\npublic final class Solution { int x = ; }\n"})
    result = judge(ws, ["sample"])
    assert result["status"] == "compile_error"
    assert result["diagnostics"][0]["file"] == "solution/Solution.java"
    assert result["diagnostics"][0]["line"] == 2


def test_python_syntax_error_reported(workspace):
    ws = workspace("python", {"solution/__init__.py": "def create(config, clock)\n    pass\n"})
    result = judge(ws, ["sample"])
    assert result["status"] == "compile_error"
    assert result["diagnostics"][0]["file"] == "solution/__init__.py"


def test_python_wrong_return_type_flagged(workspace):
    src = (REF / "python" / "solution" / "lot.py").read_text().replace(
        "        return Receipt(ticket_id, fee)", "        return {'ticket_id': ticket_id, 'fee_cents': fee}")
    files = {f"solution/{p.name}": p.read_text() for p in (REF / "python" / "solution").glob("*.py")}
    files["solution/lot.py"] = src
    result = judge(workspace("python", files), ["sample"])
    case = next(c for c in result["suites"][0]["cases"] if c["name"] == "car_parks_and_pays_one_hour")
    assert case["kind"] == "unexpected_error"
    assert "contract requires contract.Receipt" in case["message"]


def test_python_infinite_loop_times_out_and_skips_rest(workspace):
    ws = workspace("python", {"solution/__init__.py": "def create(config, clock):\n    while True:\n        pass\n"})
    cases = judge(ws, ["sample"])["suites"][0]["cases"]
    assert cases[0]["kind"] == "timeout"
    assert {c["status"] for c in cases[1:]} == {"skipped"}


def test_java_deadlock_times_out(workspace):
    src = """package solution;
import contract.*;
public final class Solution {
    public static ParkingLotApi create(LotConfig config, Clock clock) {
        Object lock = new Object();
        synchronized (lock) { try { lock.wait(); } catch (InterruptedException e) { throw new RuntimeException(e); } }
        return null;
    }
}
"""
    cases = judge(workspace("java", {"solution/Solution.java": src}), ["sample"])["suites"][0]["cases"]
    assert all(c["kind"] == "timeout" for c in cases)

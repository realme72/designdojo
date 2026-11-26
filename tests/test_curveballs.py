"""Curveballs: contract patching, the unlock flow, churn that separates good designs from bad, scoring."""

import json
import shutil
from pathlib import Path

import pytest

from joinery.analyzer.churn import churn
from joinery.curveballs import CurveballLocked, score, unlock_next
from joinery.judge import Workspace, judge
from joinery.problems import get_problem

ROOT = Path(__file__).resolve().parents[1]


def write(root: Path, files: dict[str, str]) -> Path:
    for rel, src in files.items():
        (root / "solution" / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / "solution" / rel).write_text(src)
    return root


TABLE_BEFORE = '''
FITS = {
    "BIKE": ["S", "M"],
    "CAR": ["M"],
}

class Lot:
    def sizes(self, kind):
        return FITS[kind]
'''
IFCHAIN_BEFORE = '''
class Lot:
    def sizes(self, kind):
        if kind == "BIKE":
            return ["S", "M"]
        elif kind == "CAR":
            return ["M"]
        raise ValueError(kind)
'''


def test_table_row_is_extension_but_new_branch_is_modification(tmp_path):
    a = write(tmp_path / "a0", {"lot.py": TABLE_BEFORE})
    a1 = write(tmp_path / "a1", {"lot.py": TABLE_BEFORE.replace('"CAR": ["M"],', '"CAR": ["M"],\n    "MOTO": ["S"],')})
    good = churn(a, a1, "python")
    assert good["extended"] == ["lot (module)"] and good["modified"] == [] and good["extensibility"] == 1.0

    b = write(tmp_path / "b0", {"lot.py": IFCHAIN_BEFORE})
    b1 = write(tmp_path / "b1", {"lot.py": IFCHAIN_BEFORE.replace(
        '            return ["M"]\n', '            return ["M"]\n        elif kind == "MOTO":\n            return ["S"]\n')})
    bad = churn(b, b1, "python")
    assert bad["modified"] == ["Lot.sizes"] and bad["extensibility"] == 0.0


def test_new_strategy_class_plus_wiring_is_free(tmp_path):
    before = {"__init__.py": "from .p import Hourly\n\ndef create(c):\n    return Hourly()\n",
              "p.py": "class Hourly:\n    def fee(self, h):\n        return h * 10\n"}
    after = dict(before)
    after["__init__.py"] = "from .p import Capped, Hourly\n\ndef create(c):\n    return Capped(Hourly())\n"
    after["p.py"] = before["p.py"] + "\nclass Capped:\n    def __init__(self, inner):\n        self.inner = inner\n\n    def fee(self, h):\n        return min(self.inner.fee(h), 100)\n"
    r = churn(write(tmp_path / "x", before), write(tmp_path / "y", after), "python")
    assert r["wiring"] == ["__init__:create"]
    assert r["modified"] == [] and r["extensibility"] == 1.0
    assert "Capped.fee" in r["added"]


def test_editing_existing_lines_is_modification_java(tmp_path):
    before = {"Pricing.java": "package solution;\nclass Pricing {\n  long fee(long h) {\n    return h * 10;\n  }\n}\n"}
    after = {"Pricing.java": before["Pricing.java"].replace("h * 10", "Math.min(h * 10, 100)")}
    r = churn(write(tmp_path / "x", before), write(tmp_path / "y", after), "java")
    assert r["modified"] == ["Pricing.fee(1)"] and r["extensibility"] == 0.0


def test_java_switch_case_is_modification(tmp_path):
    before = {"A.java": "package solution;\nclass A {\n  int f(int k) {\n    switch (k) {\n      case 1: return 1;\n      default: return 0;\n    }\n  }\n}\n"}
    after = {"A.java": before["A.java"].replace("      case 1: return 1;\n", "      case 1: return 1;\n      case 2: return 2;\n")}
    assert churn(write(tmp_path / "x", before), write(tmp_path / "y", after), "java")["modified"] == ["A.f(1)"]


def test_contract_patch_levels():
    p = get_problem("parking-lot")
    assert len(p.curveballs) == 2
    assert "MOTORBIKE" not in p.contract_at(0).enums["VehicleType"]
    assert p.contract_at(1).enums["VehicleType"][-1] == "MOTORBIKE"
    assert "set_daily_cap" not in p.contract_at(1).interfaces["ParkingLotApi"]
    assert "set_daily_cap" in p.contract_at(2).interfaces["ParkingLotApi"]
    assert "InvalidCap" in p.contract_at(2).errors
    assert p.suites_at(2)[-2:] == ["curveball-1", "curveball-2"]


def test_score_reweights_missing_components():
    result = {"status": "ok", "suites": [{"name": "sample", "passed": 3, "total": 3},
                                         {"name": "hidden", "passed": 7, "total": 7},
                                         {"name": "concurrency", "passed": 0, "total": 0}]}
    s = score(result, [], None)
    assert s["total"] == 100
    assert [c["name"] for c in s["components"] if c["weight"]] == ["correctness"]
    with_design = score(result, [], 40)
    assert with_design["total"] == round((35 + 10) / 60 * 100)


@pytest.mark.docker
def test_unlock_flow_snapshots_and_scores(tmp_path):
    from joinery.curveballs import evaluate

    ws_dir = tmp_path / "ws"
    shutil.copytree(ROOT / "tests/fixtures/parking-lot/python/level0", ws_dir)  # solves the base problem only
    ws = Workspace.open(ws_dir)
    assert ws.level == 0

    info = unlock_next(ws)
    assert info["index"] == 1 and "Motorbike" in info["title"]
    ws = Workspace.open(ws_dir)
    assert ws.level == 1
    assert (ws_dir / ".joinery-snapshots/1/solution/allocation.py").exists()
    assert "MOTORBIKE" in (ws_dir / "contract/__init__.py").read_text()
    assert "## Curveball 1" in (ws_dir / "PROBLEM.md").read_text()

    # unchanged code fails the new scenarios
    view = evaluate(ws, judge(ws, ws.suites), design_score=None)
    cb = next(s for s in view["suites"] if s["name"] == "curveball-1")
    assert cb["passed"] < cb["total"]

    # the table-driven design needs one new row: an extension, not a modification
    alloc = ws_dir / "solution/allocation.py"
    alloc.write_text(alloc.read_text().replace(
        "        VehicleType.TRUCK: (SpotSize.LARGE,),\n",
        "        VehicleType.TRUCK: (SpotSize.LARGE,),\n        VehicleType.MOTORBIKE: (SpotSize.SMALL,),\n"))
    view = evaluate(ws, judge(ws, ws.suites), design_score=None)
    assert view.get("status") == "ok", view.get("diagnostics")
    assert all(s["passed"] == s["total"] for s in view["suites"])
    ch = view["churn"][0]
    assert ch["extended"] == ["Compatibility (body)"] and ch["modified"] == [] and ch["extensibility"] == 1.0
    assert view["score"]["total"] == 100

    unlock_next(ws)  # all passing -> curveball 2
    ws = Workspace.open(ws_dir)
    assert ws.level == 2 and "set_daily_cap" in (ws_dir / "contract/__init__.py").read_text()
    with pytest.raises(CurveballLocked, match="no more curveballs"):
        unlock_next(ws)


@pytest.mark.docker
def test_unlock_requires_passing_submit(tmp_path):
    ws_dir = tmp_path / "ws"
    shutil.copytree(ROOT / "tests/fixtures/parking-lot/python/naive", ws_dir)
    with pytest.raises(CurveballLocked, match="pass every scenario first"):
        unlock_next(Workspace.open(ws_dir))

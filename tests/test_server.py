import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(tmp_path, monkeypatch):
    from joinery import server

    monkeypatch.setattr(server, "WORK_DIR", tmp_path)
    return TestClient(server.app), tmp_path


def test_problems_and_workspace_scaffold(client):
    c, root = client
    assert "parking-lot" in [p["id"] for p in c.get("/api/problems").json()]
    ws = c.get("/api/ws/parking-lot/python").json()
    paths = {f["path"]: f["editable"] for f in ws["files"]}
    assert paths["solution/__init__.py"] is True
    assert paths["contract/__init__.py"] is False
    assert (root / "parking-lot-python" / ".joinery.json").exists()


@pytest.mark.parametrize("path", [
    "../../etc/passwd.py", "contract/__init__.py", "solution/x.java", "/abs/solution/x.py",
    "solution/../../x.py", "solution/.hidden.py", "solution",
])
def test_rejects_paths_outside_solution(client, path):
    c, _ = client
    c.get("/api/ws/parking-lot/python")
    r = c.put("/api/ws/parking-lot/python/file", json={"path": path, "content": "x"})
    assert r.status_code == 400


def test_file_lifecycle_and_reset_keeps_backup(client):
    c, root = client
    c.get("/api/ws/parking-lot/java")
    assert c.post("/api/ws/parking-lot/java/file", json={"path": "solution/a/Spot.java", "content": "x"}).status_code == 200
    assert c.post("/api/ws/parking-lot/java/file", json={"path": "solution/a/Spot.java", "content": "x"}).status_code == 409
    assert c.post("/api/ws/parking-lot/java/rename", json={"src": "solution/a/Spot.java", "dst": "solution/Spot.java"}).status_code == 200
    assert c.post("/api/ws/parking-lot/java/delete", json={"path": "solution/Spot.java"}).status_code == 200
    c.put("/api/ws/parking-lot/java/file", json={"path": "solution/Solution.java", "content": "mine"})
    backup = c.post("/api/ws/parking-lot/java/reset").json()["backup"]
    assert (Path(backup) / "Solution.java").read_text() == "mine"
    assert "TODO" in (root / "parking-lot-java" / "solution" / "Solution.java").read_text()


@pytest.mark.docker
def test_judge_strips_hidden_details(client):
    c, root = client
    c.get("/api/ws/parking-lot/python")
    sol = root / "parking-lot-python" / "solution"
    shutil.rmtree(sol)
    shutil.copytree(ROOT / "tests/fixtures/parking-lot/python/naive/solution", sol)
    entry = c.post("/api/ws/parking-lot/python/judge", json={"mode": "submit"}).json()
    assert entry["passed"] < entry["total"]
    for suite in entry["result"]["suites"]:
        for case in suite["cases"]:
            if not suite["visible"] and case["status"] != "pass":
                assert not {"expected", "actual", "step"} & case.keys(), case
    assert c.get("/api/ws/parking-lot/python/history").json()[0]["id"] == entry["id"]


def test_concurrent_workspace_opens_never_see_partial_files(client):
    """Regression: the page fires several requests at once; each re-scaffolds the workspace."""
    from concurrent.futures import ThreadPoolExecutor

    c, _ = client
    c.get("/api/ws/parking-lot/java")
    urls = ["/api/ws/parking-lot/java", "/api/ws/parking-lot/java/history", "/api/ws/parking-lot/java/analysis"] * 16
    with ThreadPoolExecutor(16) as pool:
        codes = list(pool.map(lambda u: c.get(u).status_code, urls))
    assert set(codes) == {200}

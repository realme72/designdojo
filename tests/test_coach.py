"""Coach: prompt budget, output validation, caching, and Groq failure handling (no network)."""

import json
import shutil
from pathlib import Path

import httpx
import pytest

from designdojo.coach import CoachError, CoachUnavailable, review, validate
from designdojo.coach.prompt import INPUT_BUDGET, build, est_tokens, outline
from designdojo.coach.provider import Completion, GroqProvider
from designdojo.judge import Workspace

ROOT = Path(__file__).resolve().parents[1]
NAIVE_PY = ROOT / "tests/fixtures/parking-lot/python/naive"

GOOD = {
    "summary": "Works, but pricing and allocation are hard-coded.",
    "design_score": 48,
    "decision_points": [{"id": "pricing", "status": "missed", "note": "if/elif on vehicle type"},
                        {"id": "bogus", "status": "good"}],
    "comments": [
        {"file": "solution/__init__.py", "line_start": 43, "line_end": 48, "kind": "suggestion",
         "principle": "Open/Closed", "pattern": "Strategy", "decision_point": "pricing",
         "title": "Fee rule switches on vehicle type", "hints": ["What changes for weekend rates?", "OCP", "PricingPolicy"],
         "example": "class PricingPolicy(ABC): ...", "why_here": "Pricing will change.", "confidence": 0.9},
        {"file": "__init__.py", "line_start": 31, "line_end": 31, "kind": "warning", "title": "Race",
         "hints": ["Two gates at once?"], "confidence": 2},                     # basename only; conf clamped
        {"file": "solution/__init__.py", "line_start": 999, "hints": ["x"]},    # invented line -> dropped
        {"file": "solution/other.py", "line_start": 1, "hints": ["x"]},         # invented file -> dropped
        {"file": "solution/__init__.py", "line_start": 5, "hints": []},         # no hints -> dropped
    ],
}


class FakeProvider:
    name = "fake"

    def __init__(self, payload):
        self.payload = payload
        self.calls = 0
        self.last_user = ""

    def complete(self, system, user, max_tokens):
        self.calls += 1
        self.last_user = user
        return Completion(json.dumps(self.payload), "fake-model", est_tokens(user), 300)


@pytest.fixture
def ws(tmp_path):
    dst = tmp_path / "ws"
    shutil.copytree(NAIVE_PY, dst)
    return Workspace.open(dst)


def test_validate_keeps_only_anchored_comments():
    files = {"solution/__init__.py": (NAIVE_PY / "solution/__init__.py").read_text()}
    rev, dropped = validate(GOOD, files, ["pricing", "allocation"])
    assert dropped == 3
    assert [c["line_start"] for c in rev["comments"]] == [43, 31]
    assert rev["comments"][1]["file"] == "solution/__init__.py"
    assert rev["comments"][1]["confidence"] == 1.0
    assert rev["comments"][1]["kind"] == "warning"
    assert {d["id"]: d["status"] for d in rev["decision_points"]} == {"pricing": "missed", "allocation": "not_assessed"}
    assert rev["design_score"] == 48


def test_review_end_to_end_and_cache(ws):
    fake = FakeProvider(GOOD)
    out = review(ws, provider=fake)
    assert fake.calls == 1 and out["meta"]["cached"] is False
    assert out["review"]["comments"][0]["pattern"] == "Strategy"
    # the prompt carries the rubric, the parser's signals and numbered code
    assert "DECISION POINTS" in fake.last_user and "TYPE_SWITCH" in fake.last_user
    assert "43| " in fake.last_user
    again = review(ws, provider=fake)
    assert fake.calls == 1 and again["meta"]["cached"] is True
    (ws.solution_dir / "__init__.py").write_text((ws.solution_dir / "__init__.py").read_text() + "\n# edit\n")
    review(ws, provider=fake)
    assert fake.calls == 2, "a code change must invalidate the cache"


def test_big_solutions_are_outlined_to_fit_budget(ws):
    big = "\n".join(f"class C{i}:\n    def m(self):\n" + "        x = 1\n" * 60 for i in range(40))
    (ws.solution_dir / "big.py").write_text(big)
    from designdojo.analyzer import analyze
    files = {p.relative_to(ws.root).as_posix(): p.read_text() for p in ws.solution_dir.rglob("*.py")}
    a = analyze(ws.root, "python", concurrency=True)
    user, meta = build(title="t", statement="s", decision_points=[], analysis=a, files=files, tests="-")
    assert "solution/big.py" in meta["outlined"]
    assert meta["input_tokens_est"] <= INPUT_BUDGET + 50
    assert "solution/__init__.py" not in meta["outlined"], "flagged files keep full code first"


def test_outline_keeps_real_line_numbers():
    src = "class A:\n    def f(self):\n        a = 1\n        b = 2\n    def g(self):\n        pass\n"
    o = outline(src)
    assert "1| class A:" in o and "2|     def f(self):" in o and "5|     def g(self):" in o
    assert "a = 1" not in o


# ------------------------------------------------------------------ Groq handling


def groq(handler, tmp_path, models=("m1", "m2")):
    return GroqProvider("k", models, client=httpx.Client(transport=httpx.MockTransport(handler)),
                        state_path=tmp_path / "state.json", sleep=lambda s: None)


def ok(model):
    return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}],
                                     "usage": {"prompt_tokens": 100, "completion_tokens": 10}, "model": model})


def test_daily_limit_rotates_and_is_remembered(tmp_path):
    seen = []

    def handler(req):
        model = json.loads(req.content)["model"]
        seen.append(model)
        if model == "m1":
            return httpx.Response(429, text='{"error":{"message":"Rate limit reached on tokens per day (TPD): Limit 200000, Used 199000"}}')
        return ok(model)

    p = groq(handler, tmp_path)
    assert p.complete("s", "u", 10).model == "m2"
    assert p.complete("s", "u", 10).model == "m2"
    assert seen == ["m1", "m2", "m2"], "an exhausted model must not be retried the same day"
    assert p.usage_today()["exhausted"] == ["m1"]


def test_per_minute_limit_waits_once_then_retries(tmp_path):
    calls = []

    def handler(req):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, headers={"retry-after": "3"}, text="tokens per minute (TPM)")
        return ok("m1")

    assert groq(handler, tmp_path).complete("s", "u", 10).model == "m1"
    assert len(calls) == 2


def test_gpt_oss_gets_low_reasoning(tmp_path):
    bodies = []

    def handler(req):
        bodies.append(json.loads(req.content))
        return ok("x")

    groq(handler, tmp_path, models=("openai/gpt-oss-120b",)).complete("s", "u", 10)
    assert bodies[0]["reasoning_effort"] == "low"
    assert bodies[0]["response_format"] == {"type": "json_object"}


def test_all_exhausted_and_bad_key(tmp_path):
    p = groq(lambda r: httpx.Response(429, text="requests per day (RPD)"), tmp_path)
    with pytest.raises(CoachUnavailable, match="requests/day"):
        p.complete("s", "u", 10)
    with pytest.raises(CoachError, match="401"):
        groq(lambda r: httpx.Response(401, text="bad"), tmp_path / "x").complete("s", "u", 10)
    with pytest.raises(CoachError, match="GROQ_API_KEY"):
        GroqProvider("")


# ------------------------------------------------------------------ offline fallback


class ExhaustedProvider:
    name = "groq"

    def complete(self, system, user, max_tokens):
        raise CoachUnavailable("No coach model available right now. m1: daily limit reached (tokens/day)")


def test_falls_back_offline_when_groq_is_exhausted(ws):
    out = review(ws, provider=ExhaustedProvider())
    m, r = out["meta"], out["review"]
    assert m["source"] == "offline" and "daily limit" in m["reason"] and "05:30 IST" in m["reason"]
    assert r["design_score"] is None, "offline must not invent a score"
    status = {d["id"]: d["status"] for d in r["decision_points"]}
    assert status["pricing"] == status["compatibility"] == status["concurrency"] == "missed"
    assert status["time"] == "not_assessed", "absence of signals is not proof of good design"
    by_dp = {c["decision_point"]: c for c in r["comments"]}
    assert by_dp["pricing"]["line_start"] == 43 and by_dp["compatibility"]["line_start"] == 21
    assert r["comments"][0]["kind"] == "warning", "races first"
    assert all(len(c["hints"]) == 3 for c in r["comments"])


def test_offline_result_is_not_cached_as_ai(ws):
    review(ws, provider=ExhaustedProvider())
    fake = FakeProvider(GOOD)
    out = review(ws, provider=fake)
    assert fake.calls == 1 and out["meta"]["source"] == "ai"


def test_offline_without_key_and_strict_mode(ws, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert review(ws)["meta"]["reason"] == "AI coach not configured"
    with pytest.raises(CoachError):
        review(ws, allow_offline=False)


def test_offline_on_reference_flags_nothing_as_missed(tmp_path):
    dst = tmp_path / "ref"
    shutil.copytree(ROOT / "problems/lld/parking-lot/reference/java", dst)
    r = review(Workspace.open(dst), provider=ExhaustedProvider())["review"]
    assert all(d["status"] != "missed" for d in r["decision_points"])
    assert all(c["confidence"] < 0.5 for c in r["comments"])

"""LLM providers for the coach. Groq (free tier) first; anything else implements Provider.

Groq free-tier facts this code is built around (measured on this account, 2026-10):
- per model: 8k tokens/MINUTE, 200k tokens/DAY (the binding one, visible only in a 429 body)
- `prompt + max_tokens` is charged as a reservation, so max_tokens is kept tight
- daily exhaustion cannot be waited out: move to the next model, never retry
- a 429's body names which limit was hit; it is always logged
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import httpx

log = logging.getLogger("joinery.coach")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODELS = ("openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b")
STATE_PATH = Path(os.environ.get("JOINERY_COACH_STATE", Path.home() / ".cache" / "joinery" / "coach-state.json"))
MAX_SHORT_WAIT_S = 15


class CoachError(RuntimeError):
    """Configuration or permanent errors (no key, bad key)."""


class CoachUnavailable(RuntimeError):
    """Every model is rate-limited or failing right now."""


@dataclass
class Completion:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int


class Provider(Protocol):
    name: str

    def complete(self, system: str, user: str, max_tokens: int) -> Completion: ...


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class _State:
    """Per-model daily bookkeeping: exhausted flag and reserved tokens (estimate for display only)."""

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict:
        try:
            data = json.loads(self.path.read_text())
        except (OSError, ValueError):
            data = {}
        if data.get("day") != _today():
            data = {"day": _today(), "exhausted": [], "reserved": {}}
        return data

    def save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data))
        os.replace(tmp, self.path)

    def exhausted(self, model: str) -> bool:
        return model in self.load()["exhausted"]

    def mark_exhausted(self, model: str) -> None:
        d = self.load()
        if model not in d["exhausted"]:
            d["exhausted"].append(model)
        self.save(d)

    def reserve(self, model: str, tokens: int) -> None:
        d = self.load()
        d["reserved"][model] = d["reserved"].get(model, 0) + tokens
        self.save(d)


class GroqProvider:
    name = "groq"

    def __init__(self, api_key: str, models: tuple[str, ...] = DEFAULT_MODELS, *,
                 client: httpx.Client | None = None, state_path: Path = STATE_PATH, sleep=time.sleep):
        if not api_key:
            raise CoachError("GROQ_API_KEY is not set. Add it to joinery/.env (see .env.example).")
        self.api_key = api_key
        self.models = models
        self.client = client or httpx.Client(timeout=90)
        self.state = _State(state_path)
        self.sleep = sleep

    def _payload(self, model: str, system: str, user: str, max_tokens: int) -> dict:
        p = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        if model.startswith("openai/gpt-oss"):
            p["reasoning_effort"] = "low"  # otherwise reasoning eats the max_tokens reservation
        return p

    def complete(self, system: str, user: str, max_tokens: int) -> Completion:
        errors: list[str] = []
        for model in self.models:
            if self.state.exhausted(model):
                errors.append(f"{model}: daily token limit already reached today")
                continue
            for attempt in (1, 2):
                r = self.client.post(GROQ_URL, json=self._payload(model, system, user, max_tokens),
                                     headers={"Authorization": f"Bearer {self.api_key}"})
                if r.status_code == 200:
                    body = r.json()
                    usage = body.get("usage") or {}
                    self.state.reserve(model, int(usage.get("prompt_tokens", 0)) + max_tokens)
                    return Completion(body["choices"][0]["message"]["content"] or "", model,
                                      int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0)))
                text = r.text[:600]
                if r.status_code == 401:
                    raise CoachError("Groq rejected GROQ_API_KEY (401). Check the key in joinery/.env.")
                if r.status_code == 429:
                    log.warning("groq 429 on %s: %s", model, text)  # the body says WHICH limit
                    if "per day" in text.lower() or "(tpd)" in text.lower() or "(rpd)" in text.lower():
                        self.state.mark_exhausted(model)
                        errors.append(f"{model}: daily limit reached ({_limit_name(text)})")
                        break
                    wait = _retry_after(r)
                    if attempt == 1 and wait is not None and wait <= MAX_SHORT_WAIT_S:
                        self.sleep(wait)
                        continue
                    errors.append(f"{model}: rate limited ({_limit_name(text)}), retry in ~{wait or '?'}s")
                    break
                log.warning("groq %s on %s: %s", r.status_code, model, text)
                errors.append(f"{model}: HTTP {r.status_code}: {text[:200]}")
                break
        raise CoachUnavailable("No coach model available right now. " + " | ".join(errors))

    def usage_today(self) -> dict:
        d = self.state.load()
        return {"day": d["day"], "exhausted": d["exhausted"], "reserved_tokens": d["reserved"],
                "models": list(self.models)}


def _retry_after(r: httpx.Response) -> float | None:
    try:
        return float(r.headers.get("retry-after", ""))
    except ValueError:
        return None


def _limit_name(body: str) -> str:
    for key, name in (("(TPD)", "tokens/day"), ("(RPD)", "requests/day"), ("(TPM)", "tokens/minute"),
                      ("(RPM)", "requests/minute")):
        if key.lower() in body.lower():
            return name
    return "unknown limit"


def load_env(path: Path) -> None:
    """Minimal .env loader (KEY=VALUE lines); never overrides the real environment."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def default_provider() -> GroqProvider:
    models = tuple(m.strip() for m in os.environ.get("JOINERY_COACH_MODELS", "").split(",") if m.strip())
    return GroqProvider(os.environ.get("GROQ_API_KEY", ""), models or DEFAULT_MODELS)

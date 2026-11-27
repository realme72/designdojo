"""A disposable Postgres in Docker for judging SQL problems.

One long-lived container (`designdojo-pg`, data on tmpfs, fsync off) started on demand.
Every judge run gets its own database owned by an unprivileged role, dropped afterwards.
User SQL never runs as a superuser: it can't read files, run programs or touch other databases.
"""

from __future__ import annotations

import contextlib
import json
import secrets
import subprocess
import threading
import time
import uuid
from pathlib import Path

import psycopg
import psycopg.sql

from ..judge import JOBS_DIR, JudgeError, docker_bin

IMAGE = "postgres:17-alpine"
CONTAINER = "designdojo-pg"
STATE = JOBS_DIR.parent / "pg.json"
USER_ROLE = "dojo_user"
STATEMENT_TIMEOUT_MS = 3000

_ready_lock = threading.Lock()
_ready: dict | None = None


def _docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run([docker_bin(), *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise JudgeError(f"docker {' '.join(args[:2])} failed: {proc.stderr.strip()[-1500:]}")
    return proc


def _state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    STATE.parent.mkdir(parents=True, exist_ok=True)
    s = {"password": secrets.token_urlsafe(18), "user_password": secrets.token_urlsafe(18)}
    STATE.write_text(json.dumps(s))
    STATE.chmod(0o600)
    return s


def _running() -> bool:
    p = _docker("inspect", "-f", "{{.State.Running}}", CONTAINER, check=False)
    return p.returncode == 0 and p.stdout.strip() == "true"


def _start(state: dict) -> None:
    exists = _docker("inspect", CONTAINER, check=False).returncode == 0
    if exists:
        _docker("start", CONTAINER)
        return
    _docker("run", "-d", "--name", CONTAINER,
            "-e", f"POSTGRES_PASSWORD={state['password']}",
            "-p", "127.0.0.1::5432",
            "--tmpfs", "/var/lib/postgresql/data:rw,size=1g",
            "--memory", "1g", "--shm-size", "256m",
            IMAGE,
            "-c", "fsync=off", "-c", "synchronous_commit=off", "-c", "full_page_writes=off",
            "-c", "max_connections=60", "-c", f"statement_timeout={STATEMENT_TIMEOUT_MS * 4}")


def _port() -> int:
    out = _docker("port", CONTAINER, "5432/tcp").stdout.strip().splitlines()[0]
    return int(out.rsplit(":", 1)[1])


def ensure() -> dict:
    """Start the container if needed and make sure the unprivileged role exists."""
    global _ready
    with _ready_lock:
        if _ready and _running():
            return _ready
        state = _state()
        if not _running():
            _start(state)
        port = _port()
        admin = {"host": "127.0.0.1", "port": port, "user": "postgres", "password": state["password"]}
        deadline = time.monotonic() + 60
        while True:
            try:
                with psycopg.connect(**admin, dbname="postgres", autocommit=True, connect_timeout=3) as c:
                    exists = c.execute("select 1 from pg_roles where rolname = %s", (USER_ROLE,)).fetchone()
                    if not exists:
                        pw = psycopg.sql.Literal(state["user_password"])
                        c.execute(psycopg.sql.SQL("create role {} login nosuperuser nocreatedb nocreaterole "
                                                  "password {}").format(psycopg.sql.Identifier(USER_ROLE), pw))
                break
            except psycopg.OperationalError as e:
                if time.monotonic() > deadline:
                    raise JudgeError(f"Postgres did not become ready: {e}") from None
                time.sleep(0.4)
        _ready = {"admin": admin, "user": {**admin, "user": USER_ROLE, "password": state["user_password"]}}
        return _ready


@contextlib.contextmanager
def job_database():
    """A fresh database for one judge run, owned by the unprivileged role; dropped afterwards."""
    cfg = ensure()
    name = f"job_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(**cfg["admin"], dbname="postgres", autocommit=True) as c:
        c.execute(f'create database "{name}" owner {USER_ROLE}')
        c.execute(f'revoke connect on database "{name}" from public')
        c.execute(f'grant connect on database "{name}" to {USER_ROLE}')
    try:
        yield {**cfg["user"], "dbname": name}
    finally:
        with psycopg.connect(**cfg["admin"], dbname="postgres", autocommit=True) as c:
            c.execute(f'drop database if exists "{name}" with (force)')


def connect(dsn: dict) -> psycopg.Connection:
    return psycopg.connect(**dsn, options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS} -c lock_timeout=2000",
                           cursor_factory=psycopg.ClientCursor)

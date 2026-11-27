"""DB-design track: SQL scanner (pure) and the Postgres judge, analyzer, plans and console (Docker)."""

import shutil
from pathlib import Path

import pytest

from designdojo.judge import Workspace, judge, scaffold
from designdojo.problems import get_problem, lint_problem, list_problems
from designdojo.sql.params import is_blank, param_names, strip_comments, to_pyformat, transaction_control
from designdojo.sql.plan import clauses, is_read_only, single_statement

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "problems" / "db"


# ---------------------------------------------------------------- pure


def test_params_skip_strings_casts_and_comments():
    sql = "-- :nope\nselect :a::int, ':b', \"c:d\", $$ :e $$, x % 2 from t where y = :a and z = :f_2"
    assert param_names(sql) == ["a", "f_2"]
    out = to_pyformat(sql)
    assert "%(a)s::int" in out and "':b'" in out and "x %% 2" in out and "%(f_2)s" in out


def test_transaction_control_and_blank():
    assert transaction_control("select 1; COMMIT;") == "COMMIT"
    assert transaction_control("select 'commit'") is None
    assert transaction_control("-- begin\nselect 1") is None
    assert is_blank("-- only a comment\n  ;\n") and not is_blank("select 1")
    assert "x" not in strip_comments("select 1 -- x")


def test_statement_helpers():
    assert single_statement("-- hi\nselect 1;\n") == "select 1"
    assert single_statement("select ';'; select 2") is None
    assert is_read_only("with x as (select 1) select * from x")
    assert not is_read_only("with x as (insert into t values (1) returning *) select * from x")
    used = {c["clause"] for c in clauses("select a, count(*) from t join u on true where b group by a having count(*) > 1 order by 2 limit 3") if c["used"]}
    assert used == {"FROM", "JOIN", "WHERE", "GROUP BY", "HAVING", "SELECT", "ORDER BY", "LIMIT"}


def test_db_problems_lint_clean_and_live_only_in_db_track():
    db = list_problems("db")
    assert db and all(p.kind == "sql" and p.langs == ("sql",) for p in db)
    for p in db:
        assert lint_problem(p) == [], p.id
    assert not {p.id for p in db} & {p.id for p in list_problems("lld")}


# ---------------------------------------------------------------- postgres


def _ws(tmp_path, problem_id: str, schema: str | None = None) -> Workspace:
    p = get_problem(problem_id)
    dest = tmp_path / problem_id
    scaffold(p, "sql", dest)
    ref = p.root / "reference" / "sql" / "solution"
    for f in (ref / "ops").glob("*.sql"):
        shutil.copy(f, dest / "solution" / "ops" / f.name)
    (dest / "solution" / "schema.sql").write_text(schema if schema is not None else (ref / "schema.sql").read_text())
    return Workspace.open(dest)


NAIVE = """
create table customers (id serial, email varchar(100), name text);
create table products (id serial primary key, sku text, name text, price float, stock int, tag1 text, tag2 text);
create table orders (id serial primary key, customer_id int, status text default 'PLACED');
create table order_items (order_id int references orders(id), product_id int, quantity int, unit_price float);
"""


@pytest.mark.docker
def test_reference_passes_and_naive_schema_is_caught(tmp_path):
    good = judge(_ws(tmp_path / "a", "ecommerce-orders"), ["sample", "hidden"])
    assert good["status"] == "ok" and all(s["passed"] == s["total"] for s in good["suites"])
    bad = judge(_ws(tmp_path / "b", "ecommerce-orders", NAIVE), ["sample", "hidden"])
    failed = {c["name"]: c for s in bad["suites"] for c in s["cases"] if c["status"] != "pass"}
    assert "email_unique_ignoring_case" in failed and "domain_rules" in failed
    assert failed["email_unique_ignoring_case"]["kind"] == "expected_error"


@pytest.mark.docker
def test_schema_error_reports_line_and_blank_schema(tmp_path):
    r = judge(_ws(tmp_path / "a", "ecommerce-orders", "create table t (\n  id int,\n  oops nonsense_type\n);"), ["sample"])
    assert r["status"] == "compile_error" and r["diagnostics"][0]["line"] == 3
    r = judge(_ws(tmp_path / "b", "ecommerce-orders", "-- nothing yet\n"), ["sample"])
    assert r["status"] == "compile_error" and "empty" in r["diagnostics"][0]["message"]


@pytest.mark.docker
def test_unimplemented_op_and_transaction_control(tmp_path):
    ws = _ws(tmp_path, "ecommerce-orders")
    (ws.root / "solution" / "ops" / "add_customer.sql").write_text("-- todo\n")
    r = judge(ws, ["sample"])
    case = r["suites"][0]["cases"][0]
    assert case["kind"] == "missing_method" and "add_customer" in case["message"]
    (ws.root / "solution" / "ops" / "add_customer.sql").write_text(
        "begin; insert into customers (email, name) values (:email, :name) returning id; commit;")
    case = judge(ws, ["sample"])["suites"][0]["cases"][0]
    assert case["kind"] == "unexpected_error" and "BEGIN" in case["message"]


@pytest.mark.docker
def test_analyzer_reference_clean_naive_flagged(tmp_path):
    from designdojo.analyzer import analyze

    clean = analyze(_ws(tmp_path / "a", "ecommerce-orders").root, "sql")
    assert clean["smells"] == [] and clean["stats"]["tables"] == 4 and "erDiagram" in clean["mermaid"]
    ids = {s["id"] for s in analyze(_ws(tmp_path / "b", "ecommerce-orders", NAIVE).root, "sql")["smells"]}
    assert {"NO_PRIMARY_KEY", "FLOAT_MONEY", "REPEATING_GROUP", "MISSING_FK", "NO_NATURAL_KEY"} <= ids


@pytest.mark.docker
def test_sample_run_captures_query_plans(tmp_path):
    r = judge(_ws(tmp_path, "ecommerce-orders"), ["sample"])
    plans = [p for c in r["suites"][0]["cases"] for p in c.get("plans", [])]
    assert plans and {p["op"] for p in plans} == {"order_lines"}  # queries only, not inserts
    plan = plans[0]["plan"]
    assert plan["analyzed"] and plan["mermaid"].startswith("flowchart BT") and plan["tree"]["children"]
    hidden = judge(_ws(tmp_path / "h", "ecommerce-orders"), ["hidden"])
    assert not any("plans" in c for s in hidden["suites"] for c in s["cases"])  # hidden data never exposed


@pytest.mark.docker
def test_console_rows_plan_errors_and_rollback(tmp_path):
    from designdojo.sql.console import run_console

    ws = _ws(tmp_path, "ecommerce-orders")
    r = run_console(ws, "select email from customers order by email", "place_order_and_read_lines")
    assert r["rows"] == [["ann@shop.test"]] and r["plan"]["analyzed"]
    assert run_console(ws, "select nope from customers", None)["error"].startswith("undefined_column")
    w = run_console(ws, "insert into customers (email, name) values ('x@y', 'X')", None)
    assert "rolled back" in w["message"]
    assert run_console(ws, "select count(*) from customers", None)["rows"] == [[0]]


@pytest.mark.docker
def test_hotel_overlap_enforced_by_exclusion(tmp_path):
    r = judge(_ws(tmp_path, "hotel-reservations"), ["sample", "hidden"])
    assert all(s["passed"] == s["total"] for s in r["suites"])


# ---------------------------------------------------------------- interview questions


def test_questions_have_rubrics_and_hide_them_up_front():
    from designdojo.sql.questions import lint_questions, load_questions, public_questions

    for p in list_problems("db"):
        assert lint_questions(p) == [], p.id
        qs = load_questions(p)
        assert any(q["stage"] == "before" for q in qs)  # e.g. "relational or NoSQL?"
        pub = public_questions(p)
        assert all(set(q) == {"id", "stage", "question", "points"} for q in pub)  # no rubric text leaks


def test_offline_grading_is_honest(tmp_path, monkeypatch):
    from designdojo.coach.provider import CoachError
    from designdojo.sql import questions as qmod

    p = get_problem("ecommerce-orders")
    dest = tmp_path / "ws"
    scaffold(p, "sql", dest)
    ws = Workspace.open(dest)
    assert qmod.grade(ws)["source"] == "none"  # nothing answered yet
    qmod.save_answers(dest, {"overselling": "UPDATE ... WHERE stock >= qty, check the row count; a race otherwise",
                             "nope": "ignored by the API layer, harmless here"})

    def no_ai():
        raise CoachError("GROQ_API_KEY is not set.")

    monkeypatch.setattr("designdojo.coach.provider.default_provider", no_ai)
    r = qmod.grade(ws)
    assert r["source"] == "offline"
    a = r["answers"][0]
    assert a["id"] == "overselling" and a["verdict"] == "unassessed" and a["covered"] == []  # never claims "covered"
    assert a["partial"] and "keyword" in a["feedback"].lower()
    assert r["questions"]["overselling"]  # rubric revealed only with feedback


def test_answers_api(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from designdojo import server

    monkeypatch.setattr(server, "WORK_DIR", tmp_path)
    c = TestClient(server.app)
    q = c.get("/api/ws/ecommerce-orders/sql/questions").json()
    assert q["questions"] and q["answers"] == {}
    first = q["questions"][0]["id"]
    assert c.put("/api/ws/ecommerce-orders/sql/answers", json={"answers": {first: "Postgres: ACID", "bogus": "x"}}).json()["ok"]
    assert c.get("/api/ws/ecommerce-orders/sql/questions").json()["answers"] == {first: "Postgres: ACID"}
    assert c.get("/api/ws/parking-lot/java/questions").status_code == 404  # LLD has no interview Q&A here


@pytest.mark.docker
def test_schema_view_keeps_last_good_diagram_and_locates_errors(tmp_path):
    from designdojo.analyzer import analyze

    ws = _ws(tmp_path, "ecommerce-orders")
    good = analyze(ws.root, "sql")
    assert len(good["tables"]) == 4 and "order_items" in good["mermaid"]
    schema = ws.root / "solution" / "schema.sql"
    schema.write_text(schema.read_text() + "\ncreate table broken (id int references nowhere(id));\n")
    bad = analyze(ws.root, "sql")
    err = [s for s in bad["smells"] if s["id"] == "SCHEMA_ERROR"]
    assert err and "nowhere" in err[0]["evidence"]
    assert schema.read_text().splitlines()[err[0]["line_start"] - 1].startswith("create table broken")
    assert len(bad["tables"]) == 4  # the last schema that applied is still drawn


@pytest.mark.docker
def test_percent_signs_in_schema_and_ops_are_literal(tmp_path):
    """RAISE '... %' in a trigger and LIKE 'a%' in an operation must reach Postgres unchanged."""
    ws = _ws(tmp_path, "ecommerce-orders")
    schema = ws.root / "solution" / "schema.sql"
    schema.write_text(schema.read_text() + """
create function no_spaces() returns trigger language plpgsql as $$
begin if new.sku like '% %' then raise exception 'sku % has a space', new.sku; end if; return new; end $$;
create trigger products_sku before insert on products for each row execute function no_spaces();
""")
    r = judge(ws, ["sample"])
    assert r["status"] == "ok" and r["suites"][0]["passed"] == r["suites"][0]["total"]


@pytest.mark.docker
def test_reference_schemas_have_no_design_signals():
    """The analyzer must not nag about the model answers (guards against false positives)."""
    from designdojo.sql.analyze import analyze_workspace

    noisy = {p.id: [s["id"] for s in analyze_workspace(p.root / "reference" / "sql")["smells"]]
             for p in list_problems("db") if p.sql_spec.schema == "designed"}
    assert {k: v for k, v in noisy.items() if v} == {}


@pytest.mark.docker
def test_expression_only_indexes_dont_crash_the_analyzer(tmp_path):
    from designdojo.analyzer import analyze

    ws = _ws(tmp_path, "ecommerce-orders", """
create table t (id bigint primary key, a int not null, b int not null, parent_id bigint references t (id));
create unique index t_pair on t (least(a, b), greatest(a, b));
""")
    ids = {s["id"] for s in analyze(ws.root, "sql")["smells"]}
    assert "FK_NOT_INDEXED" in ids  # parent_id really is unindexed; the expression index didn't crash it


def test_db_track_has_fifty_problems_across_categories():
    from collections import Counter

    db = list_problems("db")
    assert len(db) == 50
    cats = Counter(p.meta["category"] for p in db)
    assert cats["SQL queries"] == 15 and len(cats) == 6

"""Each detector, in both languages, on small purpose-built snippets; plus the real solutions."""

from pathlib import Path

import pytest

from joinery.analyzer import analyze

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = {"ParkingLotApi", "Clock"}


def run(tmp_path, lang, files, concurrency=True):
    for rel, src in files.items():
        p = tmp_path / "solution" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(src)
    return analyze(tmp_path, lang, concurrency=concurrency, contract_types=CONTRACT)


def ids(a, level="warning"):
    return sorted(s["id"] for s in a["smells"] if s["level"] == level)


# ------------------------------------------------------------------ real solutions


@pytest.mark.parametrize("lang", ["java", "python"])
def test_reference_has_no_warnings(lang):
    a = analyze(ROOT / f"problems/parking-lot/reference/{lang}", lang, concurrency=True, contract_types=CONTRACT)
    assert ids(a) == []
    assert ids(a, "info") == ["SPECULATIVE_PATTERN", "SPECULATIVE_PATTERN"]  # single-impl Strategy interfaces
    assert "ParkingLotApi <|.. ParkingLot" in a["mermaid"]
    assert "SpotAllocator <|.. SmallestFitAllocator" in a["mermaid"]


@pytest.mark.parametrize("lang", ["java", "python"])
def test_naive_flags_type_switches_and_races(lang):
    a = analyze(ROOT / f"tests/fixtures/parking-lot/{lang}/naive", lang, concurrency=True, contract_types=CONTRACT)
    assert ids(a) == ["TYPE_SWITCH", "TYPE_SWITCH", "UNGUARDED_SHARED"]
    race = next(s for s in a["smells"] if s["id"] == "UNGUARDED_SHARED")
    for f in ("counter", "tickets", "plates"):
        assert f"`{f}`" in race["evidence"]


def test_unguarded_only_when_problem_is_concurrent():
    a = analyze(ROOT / "tests/fixtures/parking-lot/python/naive", "python", concurrency=False)
    assert "UNGUARDED_SHARED" not in ids(a)


# ------------------------------------------------------------------ java detectors


def test_java_detectors(tmp_path):
    a = run(tmp_path, "java", {
        "Shapes.java": """package solution;
import java.util.*;
public class Shapes {
    static Map<String, Integer> CACHE = new HashMap<>();
    enum State { IDLE, MOVING }
    private State state = State.IDLE;
    private int count;
    private final List<String> log = new ArrayList<>();
    double area(Object s) {
        switch (kind(s)) { case "circle": return 1; case "square": return 2; case "tri": return 3; default: return 0; }
    }
    String kind(Object s) {
        if (s instanceof Integer) return "a"; else if (s instanceof Long) return "b"; else return "c";
    }
    void start() { if (state == State.IDLE) { state = State.MOVING; } }
    void stop() { if (state == State.MOVING) { state = State.IDLE; } }
    void record(String x) { log.add(x); count++; long t = System.currentTimeMillis(); }
    void notify2() { Mailer m = new Mailer(); m.send(); }
}
""",
        "Mailer.java": "package solution;\npublic class Mailer { void send() {} }\n",
        "Ro.java": """package solution;
import java.util.List;
public class Ro extends java.util.AbstractList<String> {
    public Ro(int a, int b, int c, int d, int e, int f) {}
    public String get(int i) { return ""; }
    public int size() { return 0; }
    @Override public boolean add(String s) { throw new UnsupportedOperationException(); }
}
""",
        "Fat.java": """package solution;
interface Fat { void a(); void b(); void c(); void d(); void e(); void f(); void g(); }
""",
        "Single.java": """package solution;
public class Single {
    private static Single instance;
    private Single() {}
    public static Single getInstance() { return instance; }
}
""",
        "Safe.java": """package solution;
import java.util.*;
public class Safe {
    private final Map<String, Integer> m = new HashMap<>();
    private int n;
    public synchronized void a(String k) { m.put(k, 1); n++; }
    public void b(String k) { synchronized (this) { m.remove(k); } }
}
""",
    })
    got = ids(a)
    assert got.count("TYPE_SWITCH") == 2          # switch + instanceof chain
    for smell in ("GLOBAL_STATE", "STATE_FLAG", "DIRECT_TIME", "NEW_IN_LOGIC", "UNGUARDED_SHARED",
                  "TELESCOPING_CTOR", "REFUSED_BEQUEST", "FAT_INTERFACE"):
        assert smell in got, smell
    assert any("Singleton" in s["evidence"] for s in a["smells"])
    assert not any(s["symbol"] == "Safe" for s in a["smells"]), "synchronized code must not be flagged"


# ------------------------------------------------------------------ python detectors


def test_python_detectors(tmp_path):
    a = run(tmp_path, "python", {
        "__init__.py": "",
        "shapes.py": """import time
from abc import ABC, abstractmethod
from enum import Enum

registry = {}

class State(Enum):
    IDLE = 1
    MOVING = 2

class Mailer:
    def send(self):
        pass

class Shapes:
    history = []

    def __init__(self):
        self.state = State.IDLE
        self.count = 0
        self.log = []

    def area(self, s):
        match s.kind:
            case "circle": return 1
            case "square": return 2
            case _: return 0

    def describe(self, s):
        if isinstance(s, int):
            return "a"
        elif isinstance(s, float):
            return "b"
        else:
            return "c"

    def start(self):
        if self.state == State.IDLE:
            self.state = State.MOVING

    def stop(self):
        if self.state == State.MOVING:
            self.state = State.IDLE

    def record(self, x):
        self.log.append(x)
        self.count += 1
        return time.time()

    def notify(self):
        Mailer().send()


class Fat(ABC):
    @abstractmethod
    def a(self): ...
    @abstractmethod
    def b(self): ...
    @abstractmethod
    def c(self): ...
    @abstractmethod
    def d(self): ...
    @abstractmethod
    def e(self): ...
    @abstractmethod
    def f(self): ...
    @abstractmethod
    def g(self): ...


class Ro(list):
    def __init__(self, a, b, c, d, e, f):
        super().__init__()

    def append(self, x):
        raise NotImplementedError


class Single:
    _instance = None

    def __new__(cls):
        return cls._instance


class Safe:
    def __init__(self):
        import threading
        self._lock = threading.Lock()
        self.m = {}
        self.n = 0

    def a(self, k):
        with self._lock:
            self.m[k] = 1
            self.n += 1
""",
    })
    got = ids(a)
    assert got.count("TYPE_SWITCH") == 2          # match + isinstance chain
    assert got.count("GLOBAL_STATE") == 2         # module dict + class-level list
    for smell in ("STATE_FLAG", "DIRECT_TIME", "NEW_IN_LOGIC", "UNGUARDED_SHARED",
                  "TELESCOPING_CTOR", "REFUSED_BEQUEST", "FAT_INTERFACE"):
        assert smell in got, smell
    assert any("Singleton" in s["evidence"] for s in a["smells"])
    assert not any(s["symbol"] == "Safe" for s in a["smells"]), "lock-guarded code must not be flagged"


def test_god_class_by_cohesion(tmp_path):
    methods = "\n".join(f"    def m{i}(self):\n        self.f{i % 3} = self.f{i % 3}" for i in range(6))
    a = run(tmp_path, "python", {"g.py": f"class G:\n    def __init__(self):\n        self.f0 = self.f1 = self.f2 = 0\n{methods}\n"})
    god = [s for s in a["smells"] if s["id"] == "GOD_CLASS"]
    assert god and "3 groups" in god[0]["evidence"]


def test_mermaid_shapes(tmp_path):
    a = run(tmp_path, "java", {
        "A.java": "package solution;\nimport java.util.*;\npublic class A implements ParkingLotApi {\n"
                  "  private final List<B> bs = new ArrayList<>();\n  void f() { new C(); }\n}\n",
        "B.java": "package solution;\nclass B {}\n",
        "C.java": "package solution;\nclass C { void g() {} }\n",
    })
    m = a["mermaid"]
    assert 'A --> "*" B : bs' in m
    assert "A ..> C : creates" in m
    assert "ParkingLotApi <|.. A" in m and "<<contract>>" in m

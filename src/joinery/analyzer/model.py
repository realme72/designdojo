"""Language-neutral model of a solution's structure, plus the smell catalog."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Field:
    name: str
    type: str | None
    line: int
    static: bool = False
    final: bool = False
    init_type: str | None = None  # text of the initializer, e.g. "new ConcurrentHashMap<>()"


@dataclass
class Method:
    name: str
    line_start: int
    line_end: int
    params: list[str]
    static: bool = False
    abstract: bool = False
    ctor: bool = False
    private: bool = False
    synchronized: bool = False
    reads: set[str] = field(default_factory=set)        # own fields read
    writes: set[str] = field(default_factory=set)       # own fields assigned
    mutates: set[str] = field(default_factory=set)      # own fields mutated in place (add/put/++/x[k]=)
    branches_on: set[str] = field(default_factory=set)  # own fields used in if/switch/while conditions
    assigns_const: set[str] = field(default_factory=set)  # own fields assigned a literal/enum constant
    calls_self: set[str] = field(default_factory=set)   # own methods called
    instantiates: list[tuple[str, int]] = field(default_factory=list)  # (TypeName, line)
    unguarded: list[tuple[str, int]] = field(default_factory=list)  # in-place mutations outside any lock

    @property
    def touched(self) -> set[str]:
        return self.reads | self.writes | self.mutates


@dataclass
class ClassInfo:
    name: str
    kind: str  # class | abstract | interface | enum | record | dataclass | exception
    file: str
    line_start: int
    line_end: int
    extends: list[str] = field(default_factory=list)
    implements: list[str] = field(default_factory=list)
    fields: list[Field] = field(default_factory=list)
    methods: list[Method] = field(default_factory=list)

    @property
    def is_value(self) -> bool:
        return self.kind in ("enum", "record", "dataclass", "exception")

    @property
    def is_abstraction(self) -> bool:
        return self.kind in ("interface", "abstract")

    def method(self, name: str) -> Method | None:
        return next((m for m in self.methods if m.name == name), None)


@dataclass
class Smell:
    id: str
    file: str
    line_start: int
    line_end: int
    symbol: str
    evidence: str
    level: str = "warning"  # warning | info

    def to_json(self) -> dict:
        info = SMELLS[self.id]
        return {**asdict(self), "title": info["title"], "suggests": info["suggests"]}


# id -> what it is and what it usually calls for. The coach (M3) decides whether it applies.
SMELLS: dict[str, dict] = {
    "TYPE_SWITCH": {
        "title": "Branching on a type or kind",
        "suggests": ["Open/Closed", "Polymorphism", "Strategy"],
    },
    "STATE_FLAG": {
        "title": "Behaviour driven by a mutable status field",
        "suggests": ["State pattern"],
    },
    "NEW_IN_LOGIC": {
        "title": "Collaborator constructed inside business logic",
        "suggests": ["Dependency Inversion", "Constructor injection", "Factory"],
    },
    "DIRECT_TIME": {
        "title": "Reads the system clock directly",
        "suggests": ["Dependency Inversion", "Use the injected Clock"],
    },
    "GOD_CLASS": {
        "title": "Class with too many responsibilities",
        "suggests": ["Single Responsibility", "Extract class"],
    },
    "TELESCOPING_CTOR": {
        "title": "Constructor with many parameters",
        "suggests": ["Builder", "Parameter object"],
    },
    "GLOBAL_STATE": {
        "title": "Mutable global or shared class-level state",
        "suggests": ["Dependency injection", "Instance state"],
    },
    "REFUSED_BEQUEST": {
        "title": "Override that refuses to implement the method",
        "suggests": ["Liskov Substitution", "Interface Segregation", "Rethink the hierarchy"],
    },
    "FAT_INTERFACE": {
        "title": "Interface with many methods",
        "suggests": ["Interface Segregation"],
    },
    "UNGUARDED_SHARED": {
        "title": "Shared mutable state changed without synchronization",
        "suggests": ["Locks / synchronized", "Concurrent collections", "Atomics"],
    },
    "SPECULATIVE_PATTERN": {
        "title": "Abstraction or pattern without a second use (yet)",
        "suggests": ["YAGNI: justify it or simplify"],
    },
}

# Java/Python types that are not safe to mutate from several threads unguarded.
UNSAFE_MUTABLE_TYPES = {
    "HashMap", "ArrayList", "HashSet", "LinkedList", "TreeMap", "TreeSet", "ArrayDeque", "PriorityQueue",
    "LinkedHashMap", "LinkedHashSet", "EnumMap", "Map", "List", "Set", "Deque", "Queue",
    "dict", "list", "set", "deque", "defaultdict", "OrderedDict", "Counter",
}
JAVA_MUTATORS = {
    "put", "add", "remove", "clear", "poll", "pollFirst", "pollLast", "offer", "push", "pop", "set", "addAll",
    "removeAll", "removeIf", "compute", "computeIfAbsent", "computeIfPresent", "merge", "putIfAbsent", "putAll",
    "addFirst", "addLast", "removeFirst", "removeLast", "replace", "replaceAll", "retainAll", "sort",
}
PY_MUTATORS = {
    "append", "extend", "insert", "pop", "remove", "clear", "add", "discard", "update", "setdefault", "popitem",
    "appendleft", "popleft", "sort", "reverse",
}

package joinery.runner;

import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.lang.reflect.Proxy;
import java.lang.reflect.RecordComponent;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;

/**
 * Executes scenario suites against a Java solution.
 *
 * Inputs:  $JOB/contract.json, $JOB/scenarios.json, $JOB/contract/**.java (generated),
 *          $WORK/solution/**.java (user code, read-only).
 * Output:  $JOB/result.json
 *
 * Semantics must stay identical to runners/python/runner.py.
 */
@SuppressWarnings("unchecked")
public final class Runner {
    static final Path JOB = Paths.get(env("JOINERY_JOB", "/job"));
    static final Path WORK = Paths.get(env("JOINERY_WORK", "/work"));
    static final Path CLASSES = Paths.get(env("JOINERY_CLASSES", "/tmp/classes"));
    static final long START_TIME = 1_700_000_000L;
    static final long CASE_TIMEOUT_MS = Long.parseLong(env("JOINERY_CASE_TIMEOUT_MS", "5000"));

    static Map<String, Object> contract;
    static ClassLoader loader;
    static Set<String> errorNames;

    private static String env(String k, String d) { return Objects.requireNonNullElse(System.getenv(k), d); }

    public static void main(String[] args) throws Exception {
        Map<String, Object> result;
        try {
            contract = (Map<String, Object>) Json.parse(Files.readString(JOB.resolve("contract.json")));
            errorNames = new HashSet<>((List<String>) (List<?>) contract.get("errors"));
            Map<String, Object> plan = (Map<String, Object>) Json.parse(Files.readString(JOB.resolve("scenarios.json")));
            List<Object> diags = compile();
            if (!diags.isEmpty()) {
                result = map("status", "compile_error", "diagnostics", diags);
            } else {
                loader = new URLClassLoader(new URL[]{CLASSES.toUri().toURL()}, Runner.class.getClassLoader());
                List<Object> suites = new ArrayList<>();
                for (Object s : (List<Object>) plan.get("suites")) suites.add(runSuite((Map<String, Object>) s));
                result = map("status", "ok", "suites", suites);
            }
        } catch (Throwable t) {
            result = map("status", "harness_error", "message", stack(t));
        }
        Files.writeString(JOB.resolve("result.json"), Json.write(result));
        System.exit(0);
    }

    // ---------------------------------------------------------------- compile

    static List<Object> compile() throws Exception {
        List<Path> sources = new ArrayList<>();
        for (Path root : List.of(JOB.resolve("contract"), WORK.resolve("solution"))) {
            if (!Files.isDirectory(root)) continue;
            try (Stream<Path> w = Files.walk(root)) {
                w.filter(p -> p.toString().endsWith(".java")).forEach(sources::add);
            }
        }
        Files.createDirectories(CLASSES);
        JavaCompiler jc = ToolProvider.getSystemJavaCompiler();
        DiagnosticCollector<JavaFileObject> dc = new DiagnosticCollector<>();
        List<Object> out = new ArrayList<>();
        try (StandardJavaFileManager fm = jc.getStandardFileManager(dc, Locale.ROOT, StandardCharsets.UTF_8)) {
            Iterable<? extends JavaFileObject> units = fm.getJavaFileObjectsFromPaths(sources);
            StringWriter sink = new StringWriter();
            boolean ok = jc.getTask(sink, fm, dc,
                    List.of("-d", CLASSES.toString(), "-proc:none", "-Xlint:none", "-nowarn", "-encoding", "UTF-8"),
                    null, units).call();
            for (Diagnostic<? extends JavaFileObject> d : dc.getDiagnostics()) {
                if (d.getKind() != Diagnostic.Kind.ERROR) continue;
                String file = d.getSource() == null ? "" : displayPath(d.getSource().toUri().getPath());
                out.add(map("file", file, "line", d.getLineNumber(), "message", d.getMessage(Locale.ROOT)));
            }
            if (!ok && out.isEmpty()) out.add(map("file", "", "line", 0L, "message", "compilation failed: " + sink));
        }
        return out;
    }

    static String displayPath(String p) {
        for (String prefix : List.of(WORK.toString() + "/", JOB.toString() + "/")) {
            if (p.startsWith(prefix)) return p.substring(prefix.length());
        }
        return p;
    }

    // ---------------------------------------------------------------- suites

    static Map<String, Object> runSuite(Map<String, Object> suite) {
        List<Object> cases = new ArrayList<>();
        long passed = 0;
        for (Object o : (List<Object>) suite.get("scenarios")) {
            Map<String, Object> r = runRepeated((Map<String, Object>) o);
            if ("pass".equals(r.get("status"))) passed++;
            cases.add(r);
        }
        return map("name", suite.get("name"), "passed", passed, "total", (long) cases.size(), "cases", cases);
    }

    static Map<String, Object> runRepeated(Map<String, Object> sc) {
        long repeat = num(sc.getOrDefault("repeat", 1L));
        long t0 = System.nanoTime();
        for (long it = 1; it <= repeat; it++) {
            Failure f = runWithTimeout(sc);
            if (f != null) {
                Map<String, Object> r = f.toMap();
                r.put("name", sc.get("name"));
                r.put("status", "fail");
                if (repeat > 1) { r.put("iteration", it); r.put("repeat", repeat); }
                return r;
            }
        }
        return map("name", sc.get("name"), "status", "pass", "ms", (System.nanoTime() - t0) / 1_000_000);
    }

    static Failure runWithTimeout(Map<String, Object> sc) {
        CompletableFuture<Failure> fut = new CompletableFuture<>();
        Thread t = new Thread(() -> {
            try {
                fut.complete(new Scenario(sc).run());
            } catch (Throwable e) {
                fut.complete(Failure.of(0, "harness_error", stack(e)));
            }
        }, "scenario");
        t.setDaemon(true);
        t.start();
        try {
            return fut.get(CASE_TIMEOUT_MS, TimeUnit.MILLISECONDS);
        } catch (TimeoutException e) {
            return Failure.of(0, "timeout", "scenario exceeded " + CASE_TIMEOUT_MS + " ms (deadlock or infinite loop?)");
        } catch (Exception e) {
            return Failure.of(0, "harness_error", stack(e));
        }
    }

    // ---------------------------------------------------------------- scenario

    static final class Scenario {
        final Map<String, Object> sc;
        final AtomicLong now = new AtomicLong(START_TIME);
        final Map<String, Object> vars = new HashMap<>();
        Object system;

        Scenario(Map<String, Object> sc) { this.sc = sc; }

        Failure run() throws Exception {
            Map<String, Object> ep = (Map<String, Object>) contract.get("entrypoint");
            String epName = camel((String) ep.get("name"));
            Class<?> sol;
            try {
                sol = Class.forName("solution.Solution", true, loader);
            } catch (ClassNotFoundException e) {
                return Failure.of(0, "missing_entrypoint", "class solution.Solution not found");
            }
            List<Map<String, Object>> params = (List<Map<String, Object>>) ep.get("params");
            Method m = null;
            for (Method c : sol.getMethods()) {
                if (c.getName().equals(epName) && Modifier.isStatic(c.getModifiers()) && c.getParameterCount() == params.size()) m = c;
            }
            if (m == null) return Failure.of(0, "missing_entrypoint", "public static " + epName + "(...) not found in solution.Solution");
            Object[] args = new Object[params.size()];
            for (int k = 0; k < args.length; k++) {
                Map<String, Object> p = params.get(k);
                Map<String, Object> type = (Map<String, Object>) p.get("type");
                args[k] = provided(type) ? makeProvided((String) type.get("name")) : convert(sc.get(p.get("name")), type);
            }
            Outcome boot = invoke(m, null, args);
            if (boot.error != null) return Failure.of(0, "unexpected_error", epName + "(...) " + boot.describe());
            if (boot.value == null) return Failure.of(0, "unexpected_error", epName + "(...) returned null");
            system = boot.value;

            List<Object> steps = (List<Object>) sc.getOrDefault("steps", List.of());
            for (int k = 0; k < steps.size(); k++) {
                Failure f = step(k + 1, (Map<String, Object>) steps.get(k));
                if (f != null) return f;
            }
            return null;
        }

        Failure step(int n, Map<String, Object> st) throws Exception {
            if (st.containsKey("advance_clock")) {
                now.addAndGet(num(st.get("advance_clock")));
                return null;
            }
            if (st.containsKey("call")) {
                String call = (String) st.get("call");
                Outcome o = call(call, (Map<String, Object>) st.getOrDefault("args", Map.of()), -1);
                if (st.containsKey("expect_error")) {
                    String want = (String) st.get("expect_error");
                    if (want.equals(o.error)) return null;
                    return Failure.of(n, "expected_error", call + " should raise " + want + " but " + o.describe())
                            .with(map("error", want), o.json());
                }
                if (o.error != null) return Failure.of(n, "unexpected_error", call + " " + o.describe());
                if (st.containsKey("expect")) {
                    Object exp = resolve(st.get("expect"), -1);
                    if (!matches(exp, o.json)) return Failure.of(n, "wrong_result", call + " returned an unexpected value").with(exp, o.json);
                }
                if (st.containsKey("bind")) vars.put((String) st.get("bind"), o.json);
                return null;
            }
            if (st.containsKey("parallel")) return parallel((Map<String, Object>) st.get("parallel"));
            if (st.containsKey("assert")) return check(n, (Map<String, Object>) st.get("assert"));
            return Failure.of(n, "harness_error", "unknown step " + st.keySet());
        }

        Outcome call(String name, Map<String, Object> rawArgs, int i) throws Exception {
            Prepared p = prepare(name, rawArgs, i);
            return invoke(p.method, system, p.args);
        }

        record Prepared(Method method, Object[] args) {}

        Prepared prepare(String name, Map<String, Object> rawArgs, int i) throws Exception {
            Map<String, Object> ep = (Map<String, Object>) contract.get("entrypoint");
            String iface = (String) ((Map<String, Object>) ep.get("returns")).get("name");
            Map<String, Object> methods = (Map<String, Object>) ((Map<String, Object>) contract.get("interfaces")).get(iface);
            Map<String, Object> spec = (Map<String, Object>) methods.get(name);
            if (spec == null) throw new IllegalArgumentException("contract has no method " + name);
            List<Map<String, Object>> params = (List<Map<String, Object>>) spec.get("params");
            Class<?> cls = Class.forName("contract." + iface, true, loader);
            Method m = null;
            for (Method c : cls.getMethods()) {
                if (c.getName().equals(camel(name)) && c.getParameterCount() == params.size()) m = c;
            }
            if (m == null) throw new IllegalStateException("contract." + iface + "." + camel(name) + " missing");
            Map<String, Object> args = (Map<String, Object>) resolve(rawArgs, i);
            Object[] out = new Object[params.size()];
            for (int k = 0; k < out.length; k++) {
                out[k] = convert(args.get(params.get(k).get("name")), (Map<String, Object>) params.get(k).get("type"));
            }
            return new Prepared(m, out);
        }

        Failure parallel(Map<String, Object> p) throws Exception {
            int threads = (int) num(p.get("threads"));
            String call = (String) p.get("call");
            Map<String, Object> args = (Map<String, Object>) p.getOrDefault("args", Map.of());
            Prepared[] prepared = new Prepared[threads];
            for (int k = 0; k < threads; k++) prepared[k] = prepare(call, args, k);
            // Threads spin at the start line (rather than park on a latch, which wakes
            // them one by one) so they all hit the solution at the same instant.
            CountDownLatch ready = new CountDownLatch(threads);
            AtomicBoolean go = new AtomicBoolean(false);
            Object[] results = new Object[threads];
            Thread[] ts = new Thread[threads];
            for (int k = 0; k < threads; k++) {
                final int idx = k;
                ts[k] = new Thread(() -> {
                    ready.countDown();
                    while (!go.get()) Thread.yield();  // yield, not spin: 100 spinners on 4 CPUs starve thread creation
                    results[idx] = invoke(prepared[idx].method, system, prepared[idx].args).asResult();
                });
                ts[k].setDaemon(true);
                ts[k].start();
            }
            ready.await();
            go.set(true);
            for (Thread t : ts) t.join();
            if (p.containsKey("collect")) vars.put((String) p.get("collect"), new ArrayList<>(List.of(results)));
            return null;
        }

        Failure check(int n, Map<String, Object> a) {
            if (a.containsKey("distinct")) {
                List<Object> vals = (List<Object>) resolve(a.get("distinct"), -1);
                if (new HashSet<>(vals).size() != vals.size())
                    return Failure.of(n, "assertion", "values should all be distinct").with(map("distinct", true), vals);
            }
            if (!a.containsKey("of")) return null;
            List<Object> rs = (List<Object>) lookup("$" + a.get("of"));
            long ok = 0;
            Map<String, Object> errs = new LinkedHashMap<>();
            List<Map<String, Object>> oks = new ArrayList<>();
            for (Object r : rs) {
                Map<String, Object> m = (Map<String, Object>) r;
                if (m.containsKey("ok")) { ok++; if (m.get("ok") instanceof Map) oks.add((Map<String, Object>) m.get("ok")); }
                else errs.merge((String) m.get("error"), 1L, (x, y) -> (Long) x + (Long) y);
            }
            Map<String, Object> summary = map("ok_count", ok, "error_count", errs);
            if (a.containsKey("ok_count") && ok != num(a.get("ok_count")))
                return Failure.of(n, "assertion", "wrong number of successful calls").with(map("ok_count", a.get("ok_count")), summary);
            if (a.containsKey("error_count")) {
                for (Map.Entry<String, Object> e : ((Map<String, Object>) a.get("error_count")).entrySet()) {
                    long got = errs.containsKey(e.getKey()) ? (Long) errs.get(e.getKey()) : 0;
                    if (got != num(e.getValue()))
                        return Failure.of(n, "assertion", "wrong number of " + e.getKey() + " errors").with(map("error_count", a.get("error_count")), summary);
                }
            }
            if (a.containsKey("flat_count") || a.containsKey("flat_unique")) {
                List<Object> items = new ArrayList<>();
                for (Object r : rs) {
                    Map<String, Object> m = (Map<String, Object>) r;
                    if (m.containsKey("ok") && m.get("ok") instanceof List) items.addAll((List<Object>) m.get("ok"));
                }
                if (a.containsKey("flat_count") && items.size() != num(a.get("flat_count")))
                    return Failure.of(n, "assertion", "wrong total number of items across all results")
                            .with(map("flat_count", a.get("flat_count")), map("flat_count", (long) items.size()));
                if (a.containsKey("flat_unique")) {
                    String f = (String) a.get("flat_unique");
                    Set<String> seen = new HashSet<>();
                    for (Object x : items) {
                        Object v = ".".equals(f) ? x : ((Map<String, Object>) x).get(f);
                        if (!seen.add(Json.write(v)))
                            return Failure.of(n, "assertion", "items delivered more than once: " + Json.write(v))
                                    .with(map("flat_unique", f), map("duplicate", v));
                    }
                }
            }
            if (a.containsKey("value_count")) {
                Map<String, Object> counts = new LinkedHashMap<>();
                for (Object r : rs) {
                    Map<String, Object> m = (Map<String, Object>) r;
                    if (m.containsKey("ok")) counts.merge(Json.write(canonical(m.get("ok"))), 1L, (x, y) -> (Long) x + (Long) y);
                }
                for (Map.Entry<String, Object> e : ((Map<String, Object>) a.get("value_count")).entrySet()) {
                    long got = counts.containsKey(e.getKey()) ? (Long) counts.get(e.getKey()) : 0;
                    if (got != num(e.getValue()))
                        return Failure.of(n, "assertion", "wrong number of calls returning " + e.getKey())
                                .with(map("value_count", a.get("value_count")), map("value_count", counts));
                }
            }
            if (a.containsKey("unique")) {
                Object u = a.get("unique");
                List<Object> fields = u instanceof List ? (List<Object>) u : List.of(u);
                for (Object f : fields) {
                    Set<Object> seen = new HashSet<>();
                    for (Object r : rs) {
                        Map<String, Object> rm = (Map<String, Object>) r;
                        if (!rm.containsKey("ok")) continue;
                        Object okv = rm.get("ok");
                        Object v = ".".equals(f) ? okv : (okv instanceof Map ? ((Map<String, Object>) okv).get(f) : null);
                        String key = Json.write(v);
                        if (!seen.add(key))
                            return Failure.of(n, "assertion", "duplicate " + f + " among successful results: " + key)
                                    .with(map("unique", f), map("duplicate", v));
                    }
                }
            }
            return null;
        }

        // ---- references: "$name.field[0].x", with "{i}" templated first

        Object resolve(Object v, int i) {
            if (v instanceof String s) {
                if (i >= 0) {
                    Matcher tm = Pattern.compile("\\{i(?:\\+(\\d+))?}").matcher(s);
                    StringBuilder sb = new StringBuilder();
                    while (tm.find()) {
                        int off = tm.group(1) == null ? 0 : Integer.parseInt(tm.group(1));
                        tm.appendReplacement(sb, Integer.toString(i + off));
                    }
                    tm.appendTail(sb);
                    s = sb.toString();
                }
                return s.startsWith("$") ? lookup(s) : s;
            }
            if (v instanceof Map<?, ?> m) {
                Map<String, Object> out = new LinkedHashMap<>();
                for (Map.Entry<?, ?> e : m.entrySet()) out.put((String) e.getKey(), resolve(e.getValue(), i));
                return out;
            }
            if (v instanceof List<?> l) {
                List<Object> out = new ArrayList<>();
                for (Object o : l) out.add(resolve(o, i));
                return out;
            }
            return v;
        }

        static final Pattern TOKEN = Pattern.compile("\\.?([A-Za-z_][A-Za-z0-9_]*)|\\[(\\d+)]");

        Object lookup(String ref) {
            Matcher m = TOKEN.matcher(ref.substring(1));
            Object cur = null;
            boolean first = true;
            int pos = 0;
            while (m.find()) {
                if (m.start() != pos) throw new IllegalArgumentException("bad reference " + ref);
                pos = m.end();
                if (first) {
                    if (!vars.containsKey(m.group(1))) throw new IllegalArgumentException("unbound reference " + ref);
                    cur = vars.get(m.group(1));
                    first = false;
                } else if (m.group(1) != null) {
                    if (!(cur instanceof Map)) throw new IllegalArgumentException("cannot read ." + m.group(1) + " in " + ref);
                    cur = ((Map<String, Object>) cur).get(m.group(1));
                } else {
                    if (!(cur instanceof List)) throw new IllegalArgumentException("cannot index in " + ref);
                    cur = ((List<Object>) cur).get(Integer.parseInt(m.group(2)));
                }
            }
            if (pos != ref.length() - 1) throw new IllegalArgumentException("bad reference " + ref);
            return cur;
        }

        Object makeProvided(String name) throws Exception {
            Class<?> iface = Class.forName("contract." + name, true, loader);
            if (!name.equals("Clock")) throw new IllegalStateException("no harness implementation for provided " + name);
            return Proxy.newProxyInstance(loader, new Class<?>[]{iface}, (proxy, method, args) -> switch (method.getName()) {
                case "now" -> now.get();
                case "toString" -> "JudgeClock(" + now.get() + ")";
                case "hashCode" -> System.identityHashCode(proxy);
                case "equals" -> proxy == args[0];
                default -> throw new UnsupportedOperationException(method.getName());
            });
        }
    }

    // ---------------------------------------------------------------- invoke & convert

    static final class Outcome {
        Object value;
        Object json;
        String error;        // contract error name, or null
        String unexpected;   // description of a non-contract throwable

        String describe() {
            if (unexpected != null) return unexpected;
            if (error != null) return "raised " + error;
            return "returned " + Json.write(json);
        }

        Object json() { return error != null ? map("error", error) : json; }

        Object asResult() {
            if (unexpected != null) return map("error", "Unexpected", "detail", unexpected);
            return error != null ? map("error", error) : map("ok", json);
        }
    }

    static Outcome invoke(Method m, Object target, Object[] args) {
        Outcome o = new Outcome();
        try {
            m.setAccessible(true);
            o.value = m.invoke(target, args);
            o.json = toJson(o.value);
        } catch (InvocationTargetException e) {
            Throwable c = e.getCause();
            String name = contractError(c);
            if (name != null) o.error = name;
            else { o.error = "Unexpected"; o.unexpected = "threw " + c + where(c); }
        } catch (Throwable t) {
            o.error = "Unexpected";
            o.unexpected = "harness could not call " + m.getName() + ": " + t;
        }
        return o;
    }

    static String contractError(Throwable t) {
        for (Class<?> c = t.getClass(); c != null; c = c.getSuperclass()) {
            if (c.getName().startsWith("contract.") && errorNames.contains(c.getSimpleName())) return c.getSimpleName();
        }
        return null;
    }

    static String where(Throwable t) {
        for (StackTraceElement e : t.getStackTrace()) {
            if (e.getClassName().startsWith("solution.")) return " at " + e.getFileName() + ":" + e.getLineNumber();
        }
        return "";
    }

    static boolean provided(Map<String, Object> type) {
        return "iface".equals(type.get("kind")) && ((Map<String, Object>) contract.get("provided")).containsKey(type.get("name"));
    }

    static Object convert(Object v, Map<String, Object> t) throws Exception {
        String kind = (String) t.get("kind");
        if (v == null) return null;
        switch (kind) {
            case "str": return (String) v;
            case "int": return (int) num(v);
            case "long": return num(v);
            case "bool": return (Boolean) v;
            case "list": {
                List<Object> out = new ArrayList<>();
                for (Object e : (List<Object>) v) out.add(convert(e, (Map<String, Object>) t.get("of")));
                return out;
            }
            case "map": {
                Map<Object, Object> out = new LinkedHashMap<>();
                Map<String, Object> kt = (Map<String, Object>) t.get("key");
                for (Map.Entry<String, Object> e : ((Map<String, Object>) v).entrySet()) {
                    Object key = switch ((String) kt.get("kind")) {
                        case "int" -> Integer.parseInt(e.getKey());
                        case "long" -> Long.parseLong(e.getKey());
                        default -> convert(e.getKey(), kt);
                    };
                    out.put(key, convert(e.getValue(), (Map<String, Object>) t.get("value")));
                }
                return out;
            }
            case "enum": {
                Class<? extends Enum> c = (Class<? extends Enum>) Class.forName("contract." + t.get("name"), true, loader);
                return Enum.valueOf(c, (String) v);
            }
            case "dto": {
                Class<?> c = Class.forName("contract." + t.get("name"), true, loader);
                List<Map<String, Object>> fields = (List<Map<String, Object>>) ((Map<String, Object>) contract.get("dtos")).get(t.get("name"));
                RecordComponent[] rc = c.getRecordComponents();
                Class<?>[] types = new Class<?>[rc.length];
                for (int k = 0; k < rc.length; k++) types[k] = rc[k].getType();
                Object[] args = new Object[fields.size()];
                Map<String, Object> src = (Map<String, Object>) v;
                for (int k = 0; k < args.length; k++) {
                    args[k] = convert(src.get(fields.get(k).get("name")), (Map<String, Object>) fields.get(k).get("type"));
                }
                Constructor<?> ctor = c.getDeclaredConstructor(types);
                return ctor.newInstance(args);
            }
            default: throw new IllegalArgumentException("cannot convert to " + kind);
        }
    }

    static Object toJson(Object v) throws Exception {
        if (v == null || v instanceof String || v instanceof Boolean || v instanceof Long || v instanceof Double) return v;
        if (v instanceof Integer || v instanceof Short || v instanceof Byte) return ((Number) v).longValue();
        if (v instanceof Number n) return n.doubleValue();
        if (v instanceof Enum<?> e) return e.name();
        if (v instanceof Record) {
            Map<String, Object> m = new LinkedHashMap<>();
            for (RecordComponent rc : v.getClass().getRecordComponents()) {
                Method acc = rc.getAccessor();
                acc.setAccessible(true);
                m.put(snake(rc.getName()), toJson(acc.invoke(v)));
            }
            return m;
        }
        if (v instanceof Collection<?> c) {
            List<Object> l = new ArrayList<>();
            for (Object o : c) l.add(toJson(o));
            return l;
        }
        if (v instanceof Map<?, ?> mm) {
            Map<String, Object> m = new LinkedHashMap<>();
            for (Map.Entry<?, ?> e : mm.entrySet()) m.put(String.valueOf(toJson(e.getKey())), toJson(e.getValue()));
            return m;
        }
        return v.toString();
    }

    static boolean matches(Object exp, Object act) {
        if (exp instanceof Map<?, ?> em) {
            if (!(act instanceof Map<?, ?> am)) return false;
            for (Map.Entry<?, ?> e : em.entrySet()) {
                if (!am.containsKey(e.getKey()) || !matches(e.getValue(), am.get(e.getKey()))) return false;
            }
            return true;
        }
        if (exp instanceof List<?> el) {
            if (!(act instanceof List<?> al) || el.size() != al.size()) return false;
            for (int k = 0; k < el.size(); k++) if (!matches(el.get(k), al.get(k))) return false;
            return true;
        }
        if (exp instanceof Number en && act instanceof Number an) {
            if ((en instanceof Long) && (an instanceof Long)) return en.longValue() == an.longValue();
            return en.doubleValue() == an.doubleValue();
        }
        return Objects.equals(exp, act);
    }

    // ---------------------------------------------------------------- helpers

    static final class Failure {
        long step;
        String kind, message;
        Object expected, actual;
        boolean hasDetail;

        static Failure of(long step, String kind, String message) {
            Failure f = new Failure();
            f.step = step; f.kind = kind; f.message = message;
            return f;
        }

        Failure with(Object expected, Object actual) {
            this.expected = expected; this.actual = actual; this.hasDetail = true;
            return this;
        }

        Map<String, Object> toMap() {
            Map<String, Object> m = map("step", step, "kind", kind, "message", message);
            if (hasDetail) { m.put("expected", expected); m.put("actual", actual); }
            return m;
        }
    }

    /** Sorted map keys, recursively: Json.write of this matches Python's sort_keys + compact separators. */
    static Object canonical(Object v) {
        if (v instanceof Map<?, ?> m) {
            java.util.TreeMap<String, Object> out = new java.util.TreeMap<>();
            for (Map.Entry<?, ?> e : m.entrySet()) out.put(String.valueOf(e.getKey()), canonical(e.getValue()));
            return out;
        }
        if (v instanceof List<?> l) {
            List<Object> out = new ArrayList<>();
            for (Object o : l) out.add(canonical(o));
            return out;
        }
        return v;
    }

    static long num(Object o) {
        if (o instanceof String s) return Long.parseLong(s.trim());  // templated "{i+1}" args
        return ((Number) o).longValue();
    }

    static String camel(String s) {
        StringBuilder b = new StringBuilder();
        boolean up = false;
        for (char c : s.toCharArray()) {
            if (c == '_') { up = true; continue; }
            b.append(up ? Character.toUpperCase(c) : c);
            up = false;
        }
        return b.toString();
    }

    static String snake(String s) {
        StringBuilder b = new StringBuilder();
        for (char c : s.toCharArray()) {
            if (Character.isUpperCase(c)) b.append('_').append(Character.toLowerCase(c));
            else b.append(c);
        }
        return b.toString();
    }

    static Map<String, Object> map(Object... kv) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int k = 0; k < kv.length; k += 2) m.put((String) kv[k], kv[k + 1]);
        return m;
    }

    static String stack(Throwable t) {
        StringWriter w = new StringWriter();
        t.printStackTrace(new PrintWriter(w));
        String s = w.toString();
        return s.length() > 4000 ? s.substring(0, 4000) : s;
    }
}

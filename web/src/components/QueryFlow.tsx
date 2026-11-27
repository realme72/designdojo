import { AlertTriangle, ArrowRight, Info, Loader2, Play } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api, type ConsoleResult, type Lang, type PlanCapture, type PlanNode, type QueryPlan, type RunEntry } from '../api'
import { Diagram } from './DesignPanel'

function walk(n: PlanNode): PlanNode[] {
  return [n, ...n.children.flatMap(walk)]
}

export function PlanView({ plan, dark }: { plan: QueryPlan; dark: boolean }) {
  const kinds = useMemo(() => {
    const seen = new Map<string, string>()
    for (const n of walk(plan.tree)) if (n.explain && !seen.has(n.base)) seen.set(n.base, n.explain)
    return [...seen.entries()]
  }, [plan])
  return (
    <div className="plan">
      <div className="clause-strip" aria-label="Logical order of the SQL clauses">
        <span className="meta">Logical order:</span>
        {plan.clauses.map((c, i) => (
          <span key={c.clause} className="clause-wrap">
            {i > 0 && <ArrowRight size={11} className="clause-arrow" />}
            <span className={`clause ${c.used ? 'used' : ''}`} title={c.help}>
              {c.clause}
            </span>
          </span>
        ))}
      </div>
      <p className="note">
        That's the order SQL <em>means</em>. Below is the order Postgres actually <em>ran</em> it: data flows upward
        from the table scans to the result{plan.analyzed ? ', with the real row counts from your data' : ' (estimates only)'}.
        {plan.execution_ms != null && ` Executed in ${plan.execution_ms.toFixed(2)} ms.`}
      </p>
      <Diagram code={plan.mermaid} dark={dark} title="Query flow"
               legend="Bottom to top: scans → joins → grouping → sorting → limit → result. Edge labels are row counts." />
      {plan.insights.length > 0 && (
        <div className="insights">
          {plan.insights.map((s, i) => (
            <div key={i} className={`signal ${s.level}`}>
              <div className="signal-head">
                {s.level === 'warning' ? <AlertTriangle size={14} className="ic-warn" /> : <Info size={14} className="ic-info" />}
                <span className="signal-body">{s.text}</span>
              </div>
            </div>
          ))}
        </div>
      )}
      <details className="glossary">
        <summary>What each step does</summary>
        {kinds.map(([k, v]) => (
          <div key={k} className="gloss-row">
            <code>{k}</code> <span>{v}</span>
          </div>
        ))}
      </details>
    </div>
  )
}

type Captured = PlanCapture & { scenario: string; key: string }

function capturedFrom(entry: RunEntry | null): Captured[] {
  const out: Captured[] = []
  for (const s of entry?.result.suites ?? [])
    for (const c of s.cases)
      for (const p of c.plans ?? []) out.push({ ...p, scenario: c.name, key: `${c.name}#${p.step}` })
  return out
}

export default function QueryFlow({ problemId, lang, entry, dark, running }: {
  problemId: string
  lang: Lang
  entry: RunEntry | null
  dark: boolean
  running: boolean
}) {
  const [view, setView] = useState<'run' | 'console'>('run')
  const captured = useMemo(() => capturedFrom(entry), [entry])
  const [sel, setSel] = useState<string | null>(null)
  const current = captured.find((c) => c.key === sel) ?? captured.find((c) => c.plan) ?? null

  const [scenarios, setScenarios] = useState<string[]>([])
  const [scenario, setScenario] = useState<string>('')
  const [sql, setSql] = useState(() => {
    try {
      return localStorage.getItem(`dojo.console.${problemId}`) ?? 'select 1;'
    } catch {
      return 'select 1;'
    }
  })
  const [busy, setBusy] = useState(false)
  const [res, setRes] = useState<ConsoleResult | null>(null)

  useEffect(() => {
    api.consoleInfo(problemId, lang).then((i) => {
      setScenarios(i.scenarios)
      setScenario((s) => s || i.scenarios[0] || '')
    }, () => setScenarios([]))
  }, [problemId, lang])

  const run = async () => {
    if (busy) return
    setBusy(true)
    try {
      localStorage.setItem(`dojo.console.${problemId}`, sql)
    } catch {
      /* convenience only */
    }
    try {
      setRes(await api.console(problemId, lang, sql, scenario || null))
    } catch (e) {
      setRes({ error: (e as Error).message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="results">
      <div className="summary">
        <div className="segmented">
          <button className={view === 'run' ? 'on' : ''} onClick={() => setView('run')}>
            From your last run {captured.length > 0 && <span className="tab-badge">{captured.length}</span>}
          </button>
          <button className={view === 'console' ? 'on' : ''} onClick={() => setView('console')}>
            SQL console
          </button>
        </div>
      </div>

      {view === 'run' ? (
        running ? (
          <div className="running">
            <Loader2 size={18} className="spin" /> Running…
          </div>
        ) : captured.length === 0 ? (
          <div className="empty">
            <div>
              <h3>No query plans yet</h3>
              <div>
                Press <b>Run</b>. Every query in the sample scenarios is executed with <code>EXPLAIN ANALYZE</code> on that
                scenario's data and shown here as a flow.
              </div>
            </div>
          </div>
        ) : (
          <div className="flow-layout">
            <div className="flow-list">
              {captured.map((c) => (
                <button key={c.key} className={`flow-item ${current?.key === c.key ? 'on' : ''}`} onClick={() => setSel(c.key)}>
                  <span className="flow-op">{c.op}</span>
                  <span className="meta">{c.scenario.replaceAll('_', ' ')} · step {c.step}</span>
                </button>
              ))}
            </div>
            <div className="flow-main">
              {current && (
                <>
                  <div className="flow-call">
                    <code>{current.call}</code>
                  </div>
                  {current.plan ? <PlanView plan={current.plan} dark={dark} /> : <p className="meta">{current.note}</p>}
                </>
              )}
            </div>
          </div>
        )
      ) : (
        <div className="console">
          <div className="console-bar">
            <label className="meta">
              Data from sample scenario{' '}
              <select className="lang-select" value={scenario} onChange={(e) => setScenario(e.target.value)}>
                <option value="">(empty tables)</option>
                {scenarios.map((s) => (
                  <option key={s} value={s}>
                    {s.replaceAll('_', ' ')}
                  </option>
                ))}
              </select>
            </label>
            <span className="spacer" />
            <span className="meta">Runs on your schema; everything is rolled back.</span>
            <button className="btn primary small" onClick={run} disabled={busy} title="Run (⌘↵)">
              {busy ? <Loader2 size={13} className="spin" /> : <Play size={13} />} Run SQL
            </button>
          </div>
          <textarea
            className="console-input"
            value={sql}
            spellCheck={false}
            onChange={(e) => setSql(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                e.preventDefault()
                run()
              }
            }}
            aria-label="SQL to run"
          />
          {res && (
            <div className="console-out">
              {res.data_note && <p className="note">{res.data_note}</p>}
              {res.error && (
                <div className="banner bad">
                  <AlertTriangle size={15} /> {res.error}
                  {res.error_line ? ` (line ${res.error_line})` : ''}
                </div>
              )}
              {res.message && <div className="banner ok">{res.message}</div>}
              {res.columns && (
                <div className="table-wrap">
                  <table className="rows">
                    <thead>
                      <tr>
                        {res.columns.map((c) => (
                          <th key={c}>{c}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {res.rows?.map((r, i) => (
                        <tr key={i}>
                          {r.map((v, j) => (
                            <td key={j} className={v === null ? 'null' : ''}>
                              {v === null ? 'NULL' : typeof v === 'object' ? JSON.stringify(v) : String(v)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <div className="meta">
                    {res.rows?.length} row(s){res.truncated ? ' (first 200)' : ''}
                    {res.ms != null ? ` · ${res.ms} ms` : ''}
                  </div>
                </div>
              )}
              {res.plan_note && <p className="meta">{res.plan_note}</p>}
              {res.plan && <PlanView plan={res.plan} dark={dark} />}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

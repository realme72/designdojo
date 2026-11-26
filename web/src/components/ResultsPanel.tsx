import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, CircleMinus, EyeOff, Loader2, XCircle } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import type { CaseResult, Churn, JudgeResult, Mode, RunEntry, Suite } from '../api'

const KIND_LABELS: Record<string, string> = {
  wrong_result: 'wrong result',
  expected_error: 'missing or wrong error',
  unexpected_error: 'unexpected exception',
  assertion: 'invariant violated',
  timeout: 'timeout',
  missing_entrypoint: 'entry point missing',
  missing_method: 'method missing',
  harness_error: 'harness error',
  skipped: 'skipped',
}

const SUITE_BLURB: Record<string, string> = {
  sample: 'Visible examples from the statement',
  'curveball-1': 'Follow-up requirement 1',
  'curveball-2': 'Follow-up requirement 2',
  'curveball-3': 'Follow-up requirement 3',
  hidden: 'Edge cases. Names and failure kinds only',
  concurrency: 'Parallel calls, repeated to surface races',
}

type Jump = (file: string, line: number) => void

/** Turn "... at Lot.java:42" / "at solution/x.py:7" into clickable locations. */
function linkify(text: string, onJump: Jump): ReactNode[] {
  const parts: ReactNode[] = []
  const re = /([\w./-]+\.(?:java|py)):(\d+)/g
  let last = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(text))) {
    parts.push(text.slice(last, m.index))
    const [whole, file, line] = m
    parts.push(
      <a key={m.index} onClick={() => onJump(file, Number(line))}>
        {whole}
      </a>,
    )
    last = m.index + whole.length
  }
  parts.push(text.slice(last))
  return parts
}

const human = (name: string) => name.replaceAll('_', ' ')

function ScoreCard({ r }: { r: JudgeResult }) {
  if (!r.score) return null
  return (
    <div className="score-card">
      <div className="score-total">
        {r.score.total}
        <span>/100</span>
      </div>
      <div className="score-rows">
        {r.score.components.map((c) => (
          <div key={c.name} className={`score-row ${c.weight ? '' : 'muted'}`}>
            <span className="score-name">{c.name}</span>
            <span className="score-bar">
              <span style={{ width: c.weight && c.points !== null ? `${(c.points / c.weight) * 100}%` : '0%' }} />
            </span>
            <span className="score-pts">{c.points === null ? '—' : `${c.points}/${c.weight}`}</span>
            <span className="meta">{c.detail}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ChurnView({ ch }: { ch: Churn }) {
  const groups: [string, string[] | undefined, string][] = [
    ['added', ch.added, 'k-add'],
    ['extended', ch.extended, 'k-add'],
    ['modified', ch.modified, 'k-mod'],
    ['deleted', ch.deleted, 'k-del'],
    ['wiring', ch.wiring, 'k-wire'],
  ]
  return (
    <div className="suite">
      <div className="suite-head">
        Curveball {ch.curveball}: {ch.title}
        <span className="spacer" />
        <span className="hidden-note">extensibility {Math.round(ch.extensibility * 100)}%</span>
      </div>
      <div className="churn">
        {ch.error && <div className="meta">{ch.error}</div>}
        {groups
          .filter(([, xs]) => xs && xs.length)
          .map(([label, xs, cls]) => (
            <div key={label} className="churn-row">
              <span className={`churn-label ${cls}`}>{label}</span>
              <span className="churn-syms">{xs!.join(', ')}</span>
            </div>
          ))}
        <p className="note">
          Added/extended code is free; modified or deleted existing code costs twice. Wiring changes in{' '}
          <code>create</code> don't count: that's where new strategies are meant to be plugged in.
        </p>
      </div>
    </div>
  )
}

function CaseView({ c, visible, onJump }: { c: CaseResult; visible: boolean; onJump: Jump }) {
  const [open, setOpen] = useState(true)
  const hasDetail = !!c.message || 'expected' in c
  const icon =
    c.status === 'skipped' ? <CircleMinus size={15} className="ic-skip" /> : <XCircle size={15} className="ic-fail" />
  return (
    <div className="case">
      <div className="case-row" onClick={() => hasDetail && setOpen(!open)} style={{ cursor: hasDetail ? 'pointer' : 'default' }}>
        {hasDetail ? open ? <ChevronDown size={14} /> : <ChevronRight size={14} /> : <span style={{ width: 14 }} />}
        {icon}
        <span className="cname" title={c.name}>
          {human(c.name)}
        </span>
        <span className="kind">{KIND_LABELS[c.kind ?? ''] ?? c.kind}</span>
        {c.iteration && (
          <span className="iter">
            failed on run {c.iteration}/{c.repeat}
          </span>
        )}
      </div>
      {open && hasDetail && (
        <div className="case-detail">
          {c.message && (
            <div className="msg">
              {visible && c.step ? <span className="meta">step {c.step} · </span> : null}
              {linkify(c.message, onJump)}
            </div>
          )}
          {'expected' in c && (
            <div className="ea">
              <div>
                <div className="lbl">Expected</div>
                <pre>{JSON.stringify(c.expected, null, 2)}</pre>
              </div>
              <div>
                <div className="lbl">Actual</div>
                <pre>{JSON.stringify(c.actual, null, 2)}</pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function SuiteView({ s, onJump }: { s: Suite; onJump: Jump }) {
  const [showPassed, setShowPassed] = useState(false)
  const failed = s.cases.filter((c) => c.status !== 'pass')
  const passed = s.cases.filter((c) => c.status === 'pass')
  const ok = failed.length === 0
  return (
    <div className="suite">
      <div className="suite-head">
        {ok ? <CheckCircle2 size={15} className="ic-pass" /> : <XCircle size={15} className="ic-fail" />}
        {s.name}
        <span className="count">
          {s.passed}/{s.total}
        </span>
        <span className="spacer" />
        <span className="hidden-note">
          {!s.visible && <EyeOff size={12} />}
          {SUITE_BLURB[s.name] ?? ''}
        </span>
      </div>
      {failed.map((c) => (
        <CaseView key={c.name} c={c} visible={s.visible} onJump={onJump} />
      ))}
      {passed.length > 0 && (
        <>
          <button className="passed-toggle" onClick={() => setShowPassed(!showPassed)}>
            {showPassed ? <ChevronDown size={13} /> : <ChevronRight size={13} />} {passed.length} passed
          </button>
          {showPassed && (
            <div className="passed-list">
              {passed.map((c) => (
                <div key={c.name}>✓ {human(c.name)}</div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

type Props = { entry: RunEntry | null; running: Mode | null; elapsed: number; onJump: Jump; isLatest: boolean }

export default function ResultsPanel({ entry, running, elapsed, onJump, isLatest }: Props) {
  if (running) {
    return (
      <div className="running">
        <Loader2 size={18} className="spin" />
        {running === 'run' ? 'Running sample scenarios' : 'Submitting: sample, hidden and concurrency suites'}
        <span className="meta">{elapsed.toFixed(0)}s</span>
      </div>
    )
  }
  if (!entry) {
    return (
      <div className="empty">
        <div>
          <h3>No runs yet</h3>
          <div>Run checks the visible samples. Submit adds hidden edge cases and concurrency races.</div>
          <div className="keys">
            <kbd>⌘ ↵</kbd> <span>Run</span>
            <kbd>⌘ ⇧ ↵</kbd> <span>Submit</span>
            <kbd>⌘ S</kbd> <span>Save (autosaves anyway)</span>
          </div>
        </div>
      </div>
    )
  }

  const r = entry.result
  const when = new Date(entry.at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  const meta = (
    <span className="meta">
      {entry.mode} · {when} · {entry.seconds}s{!isLatest && ' · from history'}
    </span>
  )

  if (r.status === 'compile_error') {
    return (
      <div className="results">
        <div className="banner bad">
          <AlertTriangle size={16} /> Does not compile
          <span className="spacer" />
          {meta}
        </div>
        <div className="suite">
          {r.diagnostics?.map((d, i) => (
            <div key={i} className="diag" onClick={() => d.file && onJump(d.file, d.line)}>
              <span className="loc">
                {d.file || '?'}:{d.line}
              </span>
              <span>{d.message}</span>
            </div>
          ))}
        </div>
      </div>
    )
  }
  if (r.status !== 'ok') {
    return (
      <div className="results">
        <div className="banner bad">
          <AlertTriangle size={16} /> {r.status.replaceAll('_', ' ')}
          <span className="spacer" />
          {meta}
        </div>
        {r.message && <pre className="raw">{r.message}</pre>}
      </div>
    )
  }

  const allOk = entry.passed === entry.total
  return (
    <div className="results">
      <div className="summary">
        <span className={`score ${allOk ? 'ok' : 'bad'}`}>
          {entry.passed} / {entry.total}
        </span>
        <div className="chips">
          {r.suites?.map((s) => (
            <span key={s.name} className={`chip ${s.passed === s.total ? 'ok' : 'bad'}`}>
              {s.name} {s.passed}/{s.total}
            </span>
          ))}
        </div>
        <span className="spacer" />
        {meta}
      </div>
      {allOk && entry.mode === 'submit' && (
        <div className="banner ok">
          <CheckCircle2 size={16} /> Every scenario passes, including the races.
        </div>
      )}
      {allOk && entry.mode === 'run' && (
        <div className="banner ok">
          <CheckCircle2 size={16} /> Samples pass. Submit to face the hidden and concurrency suites.
        </div>
      )}
      <ScoreCard r={r} />
      {r.suites?.map((s) => (
        <SuiteView key={s.name} s={s} onJump={onJump} />
      ))}
      {r.churn?.map((ch) => (
        <ChurnView key={ch.curveball} ch={ch} />
      ))}
    </div>
  )
}

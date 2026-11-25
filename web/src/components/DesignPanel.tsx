import { AlertTriangle, Info, Loader2, Maximize2, RefreshCw, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { Analysis, CoachStatus, ReviewResult } from '../api'
import CoachView from './CoachView'

let mermaidReady: Promise<typeof import('mermaid').default> | null = null
function loadMermaid() {
  mermaidReady ??= import('mermaid').then((m) => m.default)
  return mermaidReady
}

let renderSeq = 0

function Diagram({ code, dark }: { code: string; dark: boolean }) {
  const ref = useRef<HTMLDivElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [full, setFull] = useState(false)

  useEffect(() => {
    if (!full) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setFull(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [full])

  useEffect(() => {
    let cancelled = false
    loadMermaid().then(async (mermaid) => {
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'strict',
        theme: dark ? 'dark' : 'neutral',
        fontFamily: 'ui-monospace, SF Mono, Menlo, monospace',
        class: { hideEmptyMembersBox: true },
      })
      try {
        const { svg } = await mermaid.render(`classdiag-${++renderSeq}`, code)
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg
          setError(null)
        }
      } catch (e) {
        if (!cancelled) setError((e as Error).message)
      }
    })
    return () => {
      cancelled = true
    }
  }, [code, dark])

  return (
    <>
      {error && <pre className="raw">Diagram failed to render: {error}</pre>}
      <div className={`diagram-wrap ${full ? 'full' : ''}`}>
        <div className="diagram-bar">
          {full && <strong>Class diagram</strong>}
          <span className="meta">Generated from your code. Arrows: ◁┄ implements · ◁─ extends · → holds · ┄&gt; creates</span>
          <span className="spacer" />
          <button className="btn small ghost" onClick={() => setFull(!full)} title={full ? 'Close (Esc)' : 'Expand'}>
            {full ? <X size={13} /> : <Maximize2 size={13} />} {full ? 'Close' : 'Expand'}
          </button>
        </div>
        <div className="diagram" ref={ref} />
      </div>
      {full && <div className="scrim" onClick={() => setFull(false)} />}
    </>
  )
}

type Props = {
  coach: {
    result: ReviewResult | null
    status: CoachStatus | null
    loading: boolean
    error: string | null
    locked: boolean
    onReview: (force: boolean) => void
  }
  analysis: Analysis | null
  loading: boolean
  error: string | null
  dark: boolean
  onRefresh: () => void
  onJump: (file: string, line: number) => void
}

export default function DesignPanel({ coach, analysis, loading, error, dark, onRefresh, onJump }: Props) {
  const [view, setView] = useState<'coach' | 'signals' | 'diagram'>('coach')
  if (!analysis) {
    return (
      <div className="running">
        {loading ? <Loader2 size={18} className="spin" /> : null}
        {error ? `Analysis failed: ${error}` : 'Analyzing your design…'}
      </div>
    )
  }
  const warnings = analysis.smells.filter((s) => s.level === 'warning')
  const infos = analysis.smells.filter((s) => s.level !== 'warning')
  const st = analysis.stats

  return (
    <div className="results">
      <div className="summary">
        <div className="segmented">
          <button className={view === 'coach' ? 'on' : ''} onClick={() => setView('coach')}>
            Coach
            {coach.result?.review && coach.result.review.comments.length > 0 && (
              <span className="tab-badge">{coach.result.review.comments.length}</span>
            )}
          </button>
          <button className={view === 'signals' ? 'on' : ''} onClick={() => setView('signals')}>
            Signals {analysis.smells.length > 0 && <span className="tab-badge">{analysis.smells.length}</span>}
          </button>
          <button className={view === 'diagram' ? 'on' : ''} onClick={() => setView('diagram')}>
            Class diagram
          </button>
        </div>
        <span className="meta">
          {st.classes} classes · {st.abstractions} abstractions · {st.methods} methods · {st.lines} lines
        </span>
        <span className="spacer" />
        <button className="btn small ghost" onClick={onRefresh} disabled={loading} title="Re-analyze">
          <RefreshCw size={13} className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {view === 'coach' ? (
        <CoachView {...coach} onJump={onJump} />
      ) : view === 'diagram' ? (
        <Diagram code={analysis.mermaid} dark={dark} />
      ) : (
        <>
          <p className="note">
            Static signals from your code's structure: nothing is run. They aren't verdicts. A type switch can be fine,
            a one-implementation interface can be exactly right. The coach (M3) will weigh them against this problem
            and explain which matter.
          </p>
          {analysis.smells.length === 0 && <div className="banner ok">No design smells detected.</div>}
          {[...warnings, ...infos].map((s, i) => (
            <div key={i} className={`signal ${s.level}`}>
              <div className="signal-head">
                {s.level === 'warning' ? (
                  <AlertTriangle size={15} className="ic-skip" />
                ) : (
                  <Info size={15} className="ic-info" />
                )}
                <span className="signal-title">{s.title}</span>
                <span className="spacer" />
                <a className="loc" onClick={() => onJump(s.file, s.line_start)}>
                  {s.file}:{s.line_start}
                </a>
              </div>
              <div className="signal-body">{s.evidence}</div>
              <div className="chips">
                {s.suggests.map((x) => (
                  <span key={x} className="chip">
                    {x}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  )
}

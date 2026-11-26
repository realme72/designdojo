import { CheckCircle2, ChevronRight, CloudOff, KeyRound, Lightbulb, Loader2, Lock, RotateCw, Sparkles, ThumbsUp, TriangleAlert, Wand2 } from 'lucide-react'
import { useState } from 'react'
import type { CoachComment, CoachStatus, ReviewResult } from '../api'

const KIND: Record<CoachComment['kind'], { label: string; icon: typeof Lightbulb; cls: string }> = {
  suggestion: { label: 'Suggestion', icon: Lightbulb, cls: 'k-suggestion' },
  praise: { label: 'Good call', icon: ThumbsUp, cls: 'k-praise' },
  warning: { label: 'Risk', icon: TriangleAlert, cls: 'k-warning' },
  overengineering: { label: 'Over-engineered', icon: Wand2, cls: 'k-over' },
}

const DP_LABEL: Record<string, string> = {
  good: 'good',
  partial: 'partial',
  missed: 'missed',
  not_applicable: 'n/a',
  not_assessed: 'not assessed',
}

function Comment({ c, onJump }: { c: CoachComment; onJump: (f: string, l: number) => void }) {
  const [shown, setShown] = useState(1)
  const [example, setExample] = useState(false)
  const k = KIND[c.kind]
  const Icon = k.icon
  return (
    <div className={`coach-comment ${k.cls}`}>
      <div className="signal-head">
        <Icon size={15} />
        <span className="kind-label">{k.label}</span>
        <span className="signal-title">{c.title}</span>
        <span className="spacer" />
        <a className="loc" onClick={() => onJump(c.file, c.line_start)}>
          {c.file}:{c.line_start}
          {c.line_end > c.line_start ? `–${c.line_end}` : ''}
        </a>
      </div>
      {(c.principle || c.pattern) && (
        <div className="chips tight">
          {c.principle && <span className="chip">{c.principle}</span>}
          {c.pattern && <span className="chip">{c.pattern}</span>}
          {c.confidence < 0.5 && <span className="chip dim" title="The coach is unsure about this one">low confidence</span>}
        </div>
      )}
      <ol className="hints">
        {c.hints.slice(0, shown).map((h, i) => (
          <li key={i}>{h}</li>
        ))}
      </ol>
      <div className="coach-actions">
        {shown < c.hints.length && (
          <button className="btn small" onClick={() => setShown(shown + 1)}>
            <ChevronRight size={13} /> Next hint ({shown + 1}/{c.hints.length})
          </button>
        )}
        {c.example && shown >= c.hints.length && !example && (
          <button className="btn small ghost" onClick={() => setExample(true)}>
            Show example
          </button>
        )}
      </div>
      {example && c.example && <pre className="example">{c.example}</pre>}
      {c.why_here && (
        <div className="why">
          <strong>Why it matters here:</strong> {c.why_here}
        </div>
      )}
    </div>
  )
}

type Props = {
  result: ReviewResult | null
  status: CoachStatus | null
  loading: boolean
  error: string | null
  locked: boolean
  onReview: (force: boolean) => void
  onJump: (file: string, line: number) => void
}

export default function CoachView({ result, status, loading, error, locked, onReview, onJump }: Props) {
  if (locked) {
    return (
      <div className="coming">
        <h3>
          <Lock size={15} /> Interview mode
        </h3>
        <p>The coach stays quiet while the interview timer runs. It unlocks after your first Submit, like a real round.</p>
      </div>
    )
  }

  const r = result?.review
  const m = result?.meta
  const offline = m?.source === 'offline'
  const notConfigured = status !== null && !status.configured
  const when = m ? new Date(m.at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''

  return (
    <div>
      <div className="coach-bar">
        <button className="btn primary" onClick={() => onReview(!!r)} disabled={loading}>
          {loading ? <Loader2 size={14} className="spin" /> : r ? <RotateCw size={14} /> : <Sparkles size={14} />}
          {loading ? 'Coach is reading your design…' : r ? 'Review again' : 'Review my design'}
        </button>
        {m && !offline && (
          <span className="meta">
            {m.cached ? 'cached · ' : ''}
            {when} · {m.model.split('/').pop()} · {m.prompt_tokens + m.completion_tokens} tokens
            {m.outlined.length > 0 && ` · ${m.outlined.length} file(s) summarized to fit`}
          </span>
        )}
        {m && offline && <span className="meta">{when} · static analysis · 0 tokens</span>}
      </div>
      {notConfigured && (
        <div className="offline-banner">
          <KeyRound size={15} />
          <div>
            <strong>AI coach not connected.</strong> Reviews come from static analysis until you add{' '}
            <code>GROQ_API_KEY</code> to <code>designdojo/.env</code> and restart <code>dojo serve</code>.
          </div>
        </div>
      )}
      {offline && !notConfigured && (
        <div className="offline-banner">
          <CloudOff size={15} />
          <div>
            <strong>Offline review:</strong> {m?.reason}. It can only comment where the parser found something, so
            treat a clean result as "nothing obvious", not "perfect". <em>Review again</em> uses the AI coach as soon as
            it's back.
          </div>
        </div>
      )}
      {error && <div className="banner bad">{error}</div>}
      {!r && !loading && !error && (
        <p className="note">
          Reviews your code against this problem's decision points: line-level comments naming the principle or pattern,
          why it matters here, and hints you reveal one at a time. An unchanged design is served from cache, so it doesn't
          use up your daily Groq tokens.
        </p>
      )}
      {r && (
        <>
          <div className="coach-summary">
            {r.design_score !== null && (
              <div className={`score-ring ${r.design_score >= 75 ? 'ok' : r.design_score >= 50 ? 'mid' : 'low'}`}>
                {r.design_score}
                <span>design</span>
              </div>
            )}
            <p>{r.summary}</p>
          </div>
          <div className="dp-list">
            {r.decision_points.map((d) => (
              <div key={d.id} className={`dp dp-${d.status}`} title={d.note ?? ''}>
                {d.status === 'good' ? <CheckCircle2 size={13} /> : <span className="dp-dot" />}
                <span className="dp-id">{d.id.replaceAll('_', ' ')}</span>
                <span className="dp-status">{DP_LABEL[d.status] ?? d.status}</span>
                {d.note && <span className="dp-note">{d.note}</span>}
              </div>
            ))}
          </div>
          {r.comments.map((c, i) => (
            <Comment key={`${m?.key}-${i}`} c={c} onJump={onJump} />
          ))}
          {r.comments.length === 0 && <div className="banner ok">No comments: the coach found nothing worth changing.</div>}
          {m && m.dropped_comments > 0 && (
            <p className="note">{m.dropped_comments} comment(s) were discarded because they pointed at lines that don't exist.</p>
          )}
        </>
      )}
    </div>
  )
}

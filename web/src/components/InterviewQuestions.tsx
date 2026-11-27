import { CheckCircle2, CircleDashed, Loader2, MessageSquareQuote, RefreshCw, Sparkles, XCircle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api, type Grading, type Lang, type Question } from '../api'

const STAGE_TITLE: Record<Question['stage'], string> = {
  before: 'Before you design',
  design: 'While designing',
  after: 'After the design: follow-ups',
}
const VERDICT: Record<string, string> = {
  strong: 'Strong',
  partial: 'Partly there',
  weak: 'Weak',
  missing: 'Not answered',
  unassessed: 'Not graded (offline)',
}

export default function InterviewQuestions({ problemId, lang, onCount }: {
  problemId: string
  lang: Lang
  onCount?: (answered: number, total: number) => void
}) {
  const [questions, setQuestions] = useState<Question[] | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [saveState, setSaveState] = useState<'saved' | 'saving' | 'error'>('saved')
  const [grading, setGrading] = useState<Grading | null>(null)
  const [busy, setBusy] = useState(false)
  const [revealed, setRevealed] = useState<Record<string, boolean>>({})
  const timer = useRef<number | null>(null)

  useEffect(() => {
    api.questions(problemId, lang).then((r) => {
      setQuestions(r.questions)
      setAnswers(r.answers)
    }, (e: Error) => setError(e.message))
  }, [problemId, lang])

  useEffect(() => {
    if (questions) onCount?.(questions.filter((q) => (answers[q.id] ?? '').trim()).length, questions.length)
  }, [answers, questions, onCount])

  const update = (id: string, text: string) => {
    const next = { ...answers, [id]: text }
    setAnswers(next)
    setSaveState('saving')
    if (timer.current) window.clearTimeout(timer.current)
    timer.current = window.setTimeout(() => {
      api.saveAnswers(problemId, lang, next).then(() => setSaveState('saved'), () => setSaveState('error'))
    }, 600)
  }

  const grade = async (force = false) => {
    setBusy(true)
    setError(null)
    try {
      if (timer.current) {
        window.clearTimeout(timer.current)
        await api.saveAnswers(problemId, lang, answers)
        setSaveState('saved')
      }
      setGrading(await api.gradeAnswers(problemId, lang, force))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  if (error && !questions) return <div className="banner bad">Could not load questions: {error}</div>
  if (!questions) return <div className="coming">Loading…</div>

  const byId = Object.fromEntries((grading?.answers ?? []).map((a) => [a.id, a]))
  const answered = questions.filter((q) => (answers[q.id] ?? '').trim()).length

  return (
    <div className="interview">
      <p className="note">
        What an interviewer would ask you about this design. Answer in your own words, like you would out loud:
        the choice <em>and the reason</em>. Then get feedback: each answer is checked against what a strong answer
        covers, and you get the follow-up the interviewer would ask next.
      </p>
      {(['before', 'design', 'after'] as const).map((stage) => {
        const qs = questions.filter((q) => q.stage === stage)
        if (!qs.length) return null
        return (
          <section key={stage} className="q-stage">
            <h3 className="q-stage-title">{STAGE_TITLE[stage]}</h3>
            {qs.map((q, i) => {
              const g = byId[q.id]
              const points = grading?.questions?.[q.id]
              return (
                <div key={q.id} className={`q-card ${g ? `v-${g.verdict}` : ''}`}>
                  <div className="q-text">
                    <span className="q-num">Q{questions.indexOf(q) + 1}</span> {q.question}
                  </div>
                  <textarea
                    className="q-answer"
                    value={answers[q.id] ?? ''}
                    onChange={(e) => update(q.id, e.target.value)}
                    placeholder={stage === 'before' ? 'Your choice, and why…' : 'Your answer…'}
                    aria-label={`Answer to question ${i + 1}`}
                  />
                  {g && (
                    <div className="q-feedback">
                      <span className={`verdict v-${g.verdict}`}>{VERDICT[g.verdict] ?? g.verdict}</span>
                      {g.feedback && <p>{g.feedback}</p>}
                      {g.follow_up && (
                        <p className="follow-up">
                          <MessageSquareQuote size={14} /> <b>Interviewer:</b> {g.follow_up}
                        </p>
                      )}
                      {points && (
                        revealed[q.id] ? (
                          <ul className="q-points">
                            {points.map((p, k) => {
                              const state = g.covered.includes(k) ? 'yes' : g.partial.includes(k) ? 'part' : 'no'
                              return (
                                <li key={k} className={`pt-${state}`}>
                                  {state === 'yes' ? <CheckCircle2 size={13} /> : state === 'part' ? <CircleDashed size={13} /> : <XCircle size={13} />}
                                  <span>{p}</span>
                                </li>
                              )
                            })}
                          </ul>
                        ) : (
                          <button className="btn small ghost" onClick={() => setRevealed({ ...revealed, [q.id]: true })}>
                            Show the key points ({q.points})
                          </button>
                        )
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </section>
        )
      })}
      <div className="q-actions">
        <span className="meta">
          {answered}/{questions.length} answered · {saveState === 'saving' ? 'saving…' : saveState === 'error' ? 'not saved' : 'saved'}
        </span>
        <span className="spacer" />
        {grading?.source === 'ai' && (
          <button className="btn small ghost" onClick={() => grade(true)} disabled={busy} title="Grade again (ignores the cache)">
            <RefreshCw size={13} /> Regrade
          </button>
        )}
        <button className="btn primary small" onClick={() => grade(false)} disabled={busy || answered === 0}>
          {busy ? <Loader2 size={13} className="spin" /> : <Sparkles size={13} />} Get feedback
        </button>
      </div>
      {error && <div className="banner bad">{error}</div>}
      {grading && grading.source !== 'none' && (
        <p className="meta">
          {grading.summary} {grading.source === 'ai' ? `(${grading.model}${grading.cached ? ', cached' : ''})` : ''}
        </p>
      )}
    </div>
  )
}

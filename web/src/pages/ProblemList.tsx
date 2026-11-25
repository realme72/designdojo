import { useEffect, useState } from 'react'
import { api, LANG_LABEL, type Lang, type Problem } from '../api'
import Brand from '../components/Brand'

const LANGS: Lang[] = ['java', 'python']

export default function ProblemList() {
  const [problems, setProblems] = useState<Problem[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    document.title = 'Joinery'
    api.problems().then(setProblems, (e: Error) => setError(e.message))
  }, [])

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <div className="topbar">
        <Brand />
      </div>
      <main className="home">
        <h1>Problems</h1>
        <p className="lede">
          Design the entities, implement the logic, then let the judge try to break it: hidden edge cases and real
          concurrency races. Your code is saved to <code>work/</code>, so you can switch to your own IDE anytime.
        </p>
        {error && <div className="banner bad">Could not load problems: {error}</div>}
        {!problems && !error && <div className="meta">Loading…</div>}
        {problems?.map((p) => (
          <div className="card" key={p.id}>
            <div>
              <h2>{p.title}</h2>
              <div className="tags">
                {p.difficulty && <span className={`pill ${p.difficulty}`}>{p.difficulty}</span>}
                {p.time_limit_min && <span className="meta">{p.time_limit_min} min</span>}
                {p.tags.map((t) => (
                  <span key={t} className="tag">
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <div className="actions">
              {LANGS.map((l) => (
                <a key={l} className="btn" href={`#/p/${p.id}/${l}`}>
                  {p.started?.includes(l) && <span className="started-dot" title="In progress" />}
                  {LANG_LABEL[l]}
                </a>
              ))}
            </div>
          </div>
        ))}
        {problems && problems.length < 5 && (
          <p className="soon">Elevator, Splitwise, BookMyShow and Rate Limiter arrive in milestone M6.</p>
        )}
      </main>
    </div>
  )
}

import { Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api, LANG_LABEL, preferredLang, TRACK_TITLE, wsHash, type Problem, type Track } from '../api'
import Brand from '../components/Brand'

const LEDE: Record<Track, string> = {
  lld: 'The low-level design problems interviewers ask most, solved in memory like the interview. Design the ' +
    'entities, implement the logic, then let the judge try to break it with hidden edge cases and real ' +
    'concurrency races.',
  db: 'Design the tables, keys, relationships and constraints for an application on a real PostgreSQL, then write ' +
    'the operations and reports in SQL. Hidden tests check that the database itself rejects bad data, and the ' +
    'Query flow tab shows how each query executes.',
  hld: 'System design problems. Coming soon.',
}
const SEARCH_HINT: Record<Track, string> = {
  lld: 'Search problems or tags (e.g. concurrency, strategy)',
  db: 'Search problems or tags (e.g. joins, constraints)',
  hld: 'Search problems',
}
const LEVELS = ['all', 'easy', 'medium', 'hard'] as const
type Level = (typeof LEVELS)[number]
const FILTER_KEY = 'dojo.problemFilter'

function loadFilter(track: Track): { q: string; level: Level } {
  try {
    const v = JSON.parse(localStorage.getItem(`${FILTER_KEY}.${track}`) || '{}')
    return { q: typeof v.q === 'string' ? v.q : '', level: LEVELS.includes(v.level) ? v.level : 'all' }
  } catch {
    return { q: '', level: 'all' }
  }
}

export default function ProblemList({ track }: { track: Track }) {
  const [problems, setProblems] = useState<Problem[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [{ q, level }, setFilter] = useState(() => loadFilter(track))

  useEffect(() => {
    document.title = `${TRACK_TITLE[track]} · DesignDojo`
    api.problems(track).then(setProblems, (e: Error) => setError(e.message))
  }, [track])

  useEffect(() => {
    try {
      localStorage.setItem(`${FILTER_KEY}.${track}`, JSON.stringify({ q, level }))
    } catch {
      /* per-viewer convenience only */
    }
  }, [q, level, track])

  const groups = useMemo(() => {
    const needle = q.trim().toLowerCase()
    const shown = (problems ?? []).filter(
      (p) =>
        (level === 'all' || p.difficulty === level) &&
        (!needle || p.title.toLowerCase().includes(needle) || p.tags.some((t) => t.includes(needle))),
    )
    const byCat = new Map<string, Problem[]>()
    for (const p of shown) {
      const c = p.category ?? 'Other'
      byCat.set(c, [...(byCat.get(c) ?? []), p])
    }
    const rank: Record<string, number> = { easy: 0, medium: 1, hard: 2 }
    for (const ps of byCat.values()) {
      ps.sort((a, b) => (rank[a.difficulty ?? ''] ?? 3) - (rank[b.difficulty ?? ''] ?? 3) || a.title.localeCompare(b.title))
    }
    return [...byCat.entries()].sort(([a], [b]) => a.localeCompare(b))
  }, [problems, q, level])

  const started = (problems ?? []).filter((p) => p.started?.length).length
  const shownCount = groups.reduce((n, [, ps]) => n + ps.length, 0)

  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <div className="topbar">
        <Brand />
        <span className="crumb-sep">/</span>
        <span className="title">{TRACK_TITLE[track]}</span>
      </div>
      <main className="home">
        <h1>{TRACK_TITLE[track]}</h1>
        <p className="lede">
          {LEDE[track]} Your work is saved to <code>work/{track}/</code>, so you can switch to your own editor anytime.
        </p>
        {error && <div className="banner bad">Could not load problems: {error}</div>}
        {!problems && !error && <div className="meta">Loading…</div>}
        {problems && (
          <div className="filters">
            <label className="search">
              <Search size={14} />
              <input
                value={q}
                onChange={(e) => setFilter({ q: e.target.value, level })}
                placeholder={SEARCH_HINT[track]}
                aria-label="Search problems"
              />
            </label>
            <div className="segmented" role="tablist" aria-label="Difficulty">
              {LEVELS.map((l) => (
                <button key={l} className={l === level ? 'on' : ''} onClick={() => setFilter({ q, level: l })}>
                  {l === 'all' ? 'All' : l[0].toUpperCase() + l.slice(1)}
                </button>
              ))}
            </div>
            <span className="meta">
              {shownCount} of {problems.length} · {started} started
            </span>
          </div>
        )}
        {problems && shownCount === 0 && <p className="meta">No problems match.</p>}
        {groups.map(([category, ps]) => (
          <section key={category} className="cat">
            <h2 className="cat-title">
              {category} <span className="meta">{ps.length}</span>
            </h2>
            {ps.map((p) => (
              <div
                className="card clickable"
                key={p.id}
                role="link"
                tabIndex={0}
                onClick={() => (window.location.hash = wsHash(track, p.id, preferredLang(p.id, p.started, p.langs)))}
                onKeyDown={(e) =>
                  e.key === 'Enter' && (window.location.hash = wsHash(track, p.id, preferredLang(p.id, p.started, p.langs)))
                }
              >
                <div>
                  <h3>{p.title}</h3>
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
                  {p.langs.length === 1 && p.started?.length ? <span className="started-dot" title="In progress" /> : null}
                  {p.langs.length > 1 && p.langs.map((l) => (
                    <a key={l} className="btn small" href={wsHash(track, p.id, l)} onClick={(e) => e.stopPropagation()}
                       title={`Open in ${LANG_LABEL[l]}`}>
                      {p.started?.includes(l) && <span className="started-dot" title="In progress" />}
                      {LANG_LABEL[l]}
                    </a>
                  ))}
                </div>
              </div>
            ))}
          </section>
        ))}
      </main>
    </div>
  )
}

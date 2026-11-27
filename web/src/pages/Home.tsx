import { Boxes, Database, Network } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { api, TRACK_TITLE, type Track, type TrackInfo } from '../api'
import Brand from '../components/Brand'

const ICON: Record<Track, ReactNode> = {
  lld: <Boxes size={22} />,
  db: <Database size={22} />,
  hld: <Network size={22} />,
}
const WHAT: Record<Track, string[]> = {
  lld: ['Entities & interfaces', 'SOLID & design patterns', 'Hidden tests + concurrency races', 'Curveballs'],
  db: ['Tables, keys & relationships', 'Constraints the database enforces', 'Joins, CTEs, window functions', 'See how each query runs'],
  hld: ['Components & data flow', 'Scaling & trade-offs', 'Capacity estimates'],
}

export default function Home() {
  const [tracks, setTracks] = useState<TrackInfo[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    document.title = 'DesignDojo'
    api.tracks().then(setTracks, (e: Error) => setError(e.message))
  }, [])
  const order: Track[] = ['lld', 'db', 'hld']
  return (
    <div style={{ height: '100%', overflow: 'auto' }}>
      <div className="topbar">
        <Brand />
      </div>
      <main className="home">
        <h1>Practice tracks</h1>
        <p className="lede">
          Three separate tracks, practised on their own: object design in memory, database design on a real
          PostgreSQL, and system design. Pick one.
        </p>
        {error && (
          <div className="banner bad">
            {/not found/i.test(error)
              ? <>The server you're running is older than this page (it doesn't know about tracks). Stop it and start it
                  again from the designdojo folder: <code>uv run dojo serve --open</code></>
              : <>Could not load tracks: {error}</>}
          </div>
        )}
        <div className="tracks">
          {order.map((id) => {
            const t = tracks?.find((x) => x.id === id)
            const soon = !!t && t.count === 0
            const body = (
              <>
                <div className="track-icon">{ICON[id]}</div>
                <h2>{t?.title ?? TRACK_TITLE[id]}</h2>
                <p>{t?.blurb}</p>
                <ul>
                  {WHAT[id].map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
                <div className="track-foot">
                  {soon ? <span className="pill">coming soon</span> : t ? <span className="meta">{t.count} problems</span> : null}
                </div>
              </>
            )
            return soon ? (
              <div key={id} className="track-card disabled" aria-disabled>
                {body}
              </div>
            ) : (
              <a key={id} className="track-card" href={`#/${id}`}>
                {body}
              </a>
            )
          })}
        </div>
      </main>
    </div>
  )
}

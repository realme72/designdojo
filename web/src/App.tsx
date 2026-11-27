import { useEffect, useState } from 'react'
import type { Lang, Track } from './api'
import Home from './pages/Home'
import ProblemList from './pages/ProblemList'
import WorkspacePage from './pages/WorkspacePage'

function useHash() {
  const [hash, setHash] = useState(() => window.location.hash)
  useEffect(() => {
    const on = () => setHash(window.location.hash)
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return hash
}

export default function App() {
  const hash = useHash()
  const legacy = hash.match(/^#\/p\/([\w-]+)\/(java|python)$/) // links from before the tracks existed
  if (legacy) {
    window.location.replace(`#/lld/p/${legacy[1]}/${legacy[2]}`)
    return null
  }
  const ws = hash.match(/^#\/(lld|db|hld)\/p\/([\w-]+)\/(java|python|sql)$/)
  if (ws) return <WorkspacePage key={hash} track={ws[1] as Track} problemId={ws[2]} lang={ws[3] as Lang} />
  const list = hash.match(/^#\/(lld|db|hld)\/?$/)
  if (list) return <ProblemList key={list[1]} track={list[1] as Track} />
  return <Home />
}

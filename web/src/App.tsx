import { useEffect, useState } from 'react'
import type { Lang } from './api'
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
  const m = hash.match(/^#\/p\/([\w-]+)\/(java|python)$/)
  if (m) return <WorkspacePage key={`${m[1]}/${m[2]}`} problemId={m[1]} lang={m[2] as Lang} />
  return <ProblemList />
}

import { Square, Timer as TimerIcon } from 'lucide-react'
import { useEffect, useState } from 'react'

const key = (id: string) => `dojo.interview.${id}`

function load(id: string): number | null {
  try {
    const v = localStorage.getItem(key(id))
    return v ? Number(v) : null
  } catch {
    return null
  }
}

function store(id: string, start: number | null) {
  try {
    if (start === null) localStorage.removeItem(key(id))
    else localStorage.setItem(key(id), String(start))
  } catch {
    /* storage unavailable: timer just won't survive a reload */
  }
}

const fmt = (s: number) => {
  const a = Math.abs(s)
  const m = Math.floor(a / 60)
  return `${s < 0 ? '+' : ''}${m}:${String(a % 60).padStart(2, '0')}`
}

/** Interview mode: a countdown from the problem's time limit. Survives reloads. */
export function interviewStart(problemId: string): number | null {
  return load(problemId)
}

type TimerProps = { problemId: string; limitMin: number; onChange?: (start: number | null) => void }

export default function Timer({ problemId, limitMin, onChange }: TimerProps) {
  const [start, setStartState] = useState<number | null>(() => load(problemId))
  const setStart = (v: number | null) => {
    setStartState(v)
    onChange?.(v)
  }
  const [now, setNow] = useState(() => Date.now())
  const [confirm, setConfirm] = useState(false)

  useEffect(() => {
    if (start === null) return
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [start])

  if (start === null) {
    return (
      <button
        className="btn ghost"
        title={`Start a ${limitMin}-minute interview timer`}
        onClick={() => {
          const s = Date.now()
          store(problemId, s)
          setNow(s)
          setStart(s)
        }}
      >
        <TimerIcon size={15} /> Interview
      </button>
    )
  }

  const left = Math.round(limitMin * 60 - (now - start) / 1000)
  const cls = left < 0 ? 'over' : left < 300 ? 'warn' : ''
  if (confirm) {
    return (
      <span className="timer">
        Stop timer?
        <button
          className="btn small danger"
          onClick={() => {
            store(problemId, null)
            setStart(null)
            setConfirm(false)
          }}
        >
          Stop
        </button>
        <button className="btn small ghost" onClick={() => setConfirm(false)}>
          Keep
        </button>
      </span>
    )
  }
  return (
    <span className={`timer ${cls}`} title={left < 0 ? 'Over time' : 'Time remaining'}>
      <TimerIcon size={15} />
      {fmt(left)}
      <button className="icon-btn" title="Stop interview timer" onClick={() => setConfirm(true)}>
        <Square size={12} />
      </button>
    </span>
  )
}

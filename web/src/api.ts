export type Lang = 'java' | 'python'

export type Problem = {
  id: string
  title: string
  difficulty?: string
  category?: string
  time_limit_min?: number
  tags: string[]
  started?: Lang[]
}

export type ProblemDetail = Problem & { statement: string; langs: Lang[] }

export type WsFile = { path: string; content: string; editable: boolean }
export type Workspace = { root: string; entry: string; files: WsFile[] }

export type CaseResult = {
  name: string
  status: 'pass' | 'fail' | 'skipped'
  kind?: string
  message?: string
  step?: number
  expected?: unknown
  actual?: unknown
  iteration?: number
  repeat?: number
  ms?: number
}

export type Suite = { name: string; passed: number; total: number; visible: boolean; cases: CaseResult[] }
export type Diagnostic = { file: string; line: number; message: string }
export type JudgeResult = { status: string; suites?: Suite[]; diagnostics?: Diagnostic[]; message?: string }
export type Mode = 'run' | 'submit'
export type RunEntry = {
  id: string
  at: number
  mode: Mode
  status: string
  passed: number
  total: number
  seconds: number
  result: JudgeResult
}

export type Smell = {
  id: string
  title: string
  suggests: string[]
  level: 'warning' | 'info'
  file: string
  line_start: number
  line_end: number
  symbol: string
  evidence: string
}
export type Analysis = {
  lang: Lang
  smells: Smell[]
  mermaid: string
  stats: { files: number; lines: number; classes: number; abstractions: number; methods: number }
}

export type CoachComment = {
  file: string
  line_start: number
  line_end: number
  kind: 'suggestion' | 'praise' | 'warning' | 'overengineering'
  principle: string | null
  pattern: string | null
  decision_point: string | null
  title: string
  hints: string[]
  example: string | null
  why_here: string | null
  confidence: number
}
export type Review = {
  summary: string
  design_score: number | null
  decision_points: { id: string; status: string; note: string | null }[]
  comments: CoachComment[]
}
export type ReviewMeta = {
  source: 'ai' | 'offline'
  reason?: string
  model: string
  cached: boolean
  seconds: number
  at: number
  prompt_tokens: number
  completion_tokens: number
  dropped_comments: number
  outlined: string[]
  key: string
}
export type ReviewResult = { review: Review | null; meta?: ReviewMeta }
export type CoachStatus = {
  configured: boolean
  message?: string
  provider?: string
  exhausted?: string[]
  models?: string[]
}

async function req<T>(method: string, url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`
    try {
      const j = await r.json()
      if (j?.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch {
      /* not json */
    }
    throw new Error(msg)
  }
  return r.json() as Promise<T>
}

const ws = (id: string, lang: Lang) => `/api/ws/${encodeURIComponent(id)}/${lang}`

export const api = {
  problems: () => req<Problem[]>('GET', '/api/problems'),
  problem: (id: string) => req<ProblemDetail>('GET', `/api/problems/${encodeURIComponent(id)}`),
  workspace: (id: string, lang: Lang) => req<Workspace>('GET', ws(id, lang)),
  save: (id: string, lang: Lang, path: string, content: string) =>
    req<{ ok: true }>('PUT', `${ws(id, lang)}/file`, { path, content }),
  create: (id: string, lang: Lang, path: string, content: string) =>
    req<{ ok: true }>('POST', `${ws(id, lang)}/file`, { path, content }),
  rename: (id: string, lang: Lang, src: string, dst: string) =>
    req<{ ok: true }>('POST', `${ws(id, lang)}/rename`, { src, dst }),
  remove: (id: string, lang: Lang, path: string) => req<{ ok: true }>('POST', `${ws(id, lang)}/delete`, { path }),
  reset: (id: string, lang: Lang) => req<{ ok: true; backup: string | null }>('POST', `${ws(id, lang)}/reset`),
  judge: (id: string, lang: Lang, mode: Mode) => req<RunEntry>('POST', `${ws(id, lang)}/judge`, { mode }),
  history: (id: string, lang: Lang) => req<RunEntry[]>('GET', `${ws(id, lang)}/history`),
  analysis: (id: string, lang: Lang) => req<Analysis>('GET', `${ws(id, lang)}/analysis`),
  review: (id: string, lang: Lang, force = false) => req<ReviewResult>('POST', `${ws(id, lang)}/review`, { force }),
  latestReview: (id: string, lang: Lang) => req<ReviewResult>('GET', `${ws(id, lang)}/review`),
  coachStatus: () => req<CoachStatus>('GET', '/api/coach/status'),
}

export const EXT: Record<Lang, string> = { java: '.java', python: '.py' }
export const LANG_LABEL: Record<Lang, string> = { java: 'Java', python: 'Python' }

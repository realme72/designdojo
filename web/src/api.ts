export type Lang = 'java' | 'python' | 'sql'
export type Track = 'lld' | 'db' | 'hld'
export type TrackInfo = { id: Track; title: string; kind: string; blurb: string; count: number }

export type Problem = {
  id: string
  track: Track
  kind: 'code' | 'sql' | 'hld'
  langs: Lang[]
  title: string
  difficulty?: string
  category?: string
  time_limit_min?: number
  tags: string[]
  started?: Lang[]
}

export type ProblemDetail = Problem & { statement: string; langs: Lang[] }

export type WsFile = { path: string; content: string; editable: boolean }
export type CurveballInfo = { index: number; id: string; title: string; statement: string }
export type Workspace = {
  root: string
  entry: string
  files: WsFile[]
  level: number
  curveballs_total: number
  curveballs: CurveballInfo[]
}

export type PlanNode = {
  id: string
  type: string
  base: string
  relation?: string | null
  alias?: string | null
  index?: string | null
  join?: string | null
  conds: Record<string, string>
  est_rows?: number
  rows?: number | null
  loops?: number | null
  ms?: number | null
  removed: number
  explain: string
  children: PlanNode[]
}
export type QueryPlan = {
  analyzed: boolean
  tree: PlanNode
  mermaid: string
  insights: { level: 'info' | 'warning'; node: string; text: string }[]
  clauses: { clause: string; used: boolean; help: string }[]
  planning_ms?: number
  execution_ms?: number
}
export type PlanCapture = { step: number; op: string; call: string; plan?: QueryPlan; note?: string }
export type Question = { id: string; stage: 'before' | 'design' | 'after'; question: string; points: number }
export type GradedAnswer = {
  id: string
  verdict: 'strong' | 'partial' | 'weak' | 'missing' | 'unassessed'
  covered: number[]
  partial: number[]
  feedback: string
  follow_up: string | null
}
export type Grading = {
  answers: GradedAnswer[]
  summary: string
  source: 'ai' | 'offline' | 'none'
  model?: string
  cached?: boolean
  questions?: Record<string, string[]>
}
export type ConsoleResult = {
  error?: string
  error_line?: number
  scenario?: string | null
  data_note?: string | null
  columns?: string[]
  rows?: unknown[][]
  truncated?: boolean
  message?: string
  ms?: number
  plan?: QueryPlan
  plan_note?: string
}

export type CaseResult = {
  plans?: PlanCapture[]
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
export type ScoreComponent = { name: string; weight: number; points: number | null; detail: string }
export type Churn = {
  curveball: number
  title: string
  added?: string[]
  extended?: string[]
  modified?: string[]
  deleted?: string[]
  wiring?: string[]
  extensibility: number
  error?: string
}
export type JudgeResult = {
  status: string
  suites?: Suite[]
  diagnostics?: Diagnostic[]
  message?: string
  score?: { total: number; components: ScoreComponent[] }
  churn?: Churn[]
}
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
export type CatalogTable = {
  name: string
  columns: { name: string; type: string; notnull: boolean; identity: boolean; default: string | null }[]
  constraints: { name: string; type: 'p' | 'u' | 'f' | 'c' | 'x' | 't' | 'n'; cols: string[] | null; ref: string | null;
    refcols: string[] | null; def: string }[]
  indexes: { unique: boolean; cols: string[] | null; def: string }[]
}
export type Analysis = {
  lang: Lang
  smells: Smell[]
  tables?: CatalogTable[]
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
  tracks: () => req<TrackInfo[]>('GET', '/api/tracks'),
  problems: (track: Track) => req<Problem[]>('GET', `/api/problems?track=${track}`),
  questions: (id: string, lang: Lang) =>
    req<{ questions: Question[]; answers: Record<string, string> }>('GET', `${ws(id, lang)}/questions`),
  saveAnswers: (id: string, lang: Lang, answers: Record<string, string>) =>
    req<{ ok: true }>('PUT', `${ws(id, lang)}/answers`, { answers }),
  gradeAnswers: (id: string, lang: Lang, force = false) =>
    req<Grading>('POST', `${ws(id, lang)}/answers/grade`, { force }),
  consoleInfo: (id: string, lang: Lang) => req<{ scenarios: string[] }>('GET', `${ws(id, lang)}/console`),
  console: (id: string, lang: Lang, sql: string, scenario: string | null) =>
    req<ConsoleResult>('POST', `${ws(id, lang)}/console`, { sql, scenario }),
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
  nextCurveball: (id: string, lang: Lang) => req<CurveballInfo>('POST', `${ws(id, lang)}/curveball`),
  analysis: (id: string, lang: Lang) => req<Analysis>('GET', `${ws(id, lang)}/analysis`),
  review: (id: string, lang: Lang, force = false) => req<ReviewResult>('POST', `${ws(id, lang)}/review`, { force }),
  latestReview: (id: string, lang: Lang) => req<ReviewResult>('GET', `${ws(id, lang)}/review`),
  coachStatus: () => req<CoachStatus>('GET', '/api/coach/status'),
}

const LANG_KEY = 'dojo.lang'

/** Remembered language: per problem first, then the last one used anywhere. */
export function preferredLang(problemId: string, started: Lang[] = [], langs: Lang[] = ['java', 'python']): Lang {
  if (langs.length === 1) return langs[0]
  try {
    const own = localStorage.getItem(`${LANG_KEY}.${problemId}`)
    if (own === 'java' || own === 'python') return own
  } catch {
    /* storage unavailable */
  }
  if (started.length === 1) return started[0]
  try {
    const last = localStorage.getItem(LANG_KEY)
    if (last === 'java' || last === 'python') return last
  } catch {
    /* storage unavailable */
  }
  return 'java'
}

export function rememberLang(problemId: string, lang: Lang) {
  try {
    localStorage.setItem(`${LANG_KEY}.${problemId}`, lang)
    localStorage.setItem(LANG_KEY, lang)
  } catch {
    /* storage unavailable: just not remembered */
  }
}

export const EXT: Record<Lang, string> = { java: '.java', python: '.py', sql: '.sql' }
export const LANG_LABEL: Record<Lang, string> = { java: 'Java', python: 'Python', sql: 'SQL' }
export const TRACK_TITLE: Record<Track, string> = { lld: 'Low-level design', db: 'Database design', hld: 'High-level design' }
export const wsHash = (track: Track, id: string, lang: Lang) => `#/${track}/p/${id}/${lang}`

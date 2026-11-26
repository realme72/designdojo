import Editor, { type OnMount } from '@monaco-editor/react'
import { Loader2, Lock, Play, Send, Sparkles, X, Zap } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import { Group, Panel, Separator } from 'react-resizable-panels'
import remarkGfm from 'remark-gfm'
import {
  api,
  EXT,
  LANG_LABEL,
  rememberLang,
  type CurveballInfo,
  type Analysis,
  type CoachStatus,
  type Lang,
  type Mode,
  type ProblemDetail,
  type ReviewResult,
  type RunEntry,
} from '../api'
import Brand from '../components/Brand'
import DesignPanel from '../components/DesignPanel'
import FileTree from '../components/FileTree'
import ResultsPanel from '../components/ResultsPanel'
import Timer, { interviewStart } from '../components/Timer'
import { monaco } from '../monaco'

type FileState = { content: string; saved: string; editable: boolean }
type Files = Record<string, FileState>

const AUTOSAVE_MS = 700

function usePrefersDark() {
  const q = '(prefers-color-scheme: dark)'
  const [dark, setDark] = useState(() => window.matchMedia(q).matches)
  useEffect(() => {
    const m = window.matchMedia(q)
    const on = () => setDark(m.matches)
    m.addEventListener('change', on)
    return () => m.removeEventListener('change', on)
  }, [])
  return dark
}

function template(path: string, lang: Lang): string {
  if (lang === 'python') return ''
  const parts = path.replace(/\.java$/, '').split('/')
  const name = parts.pop()!
  return `package ${parts.join('.')};\n\npublic class ${name} {\n}\n`
}

function ago(ts: number) {
  const s = Math.round(Date.now() / 1000 - ts)
  if (s < 60) return 'just now'
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`
  return new Date(ts * 1000).toLocaleDateString()
}

export default function WorkspacePage({ problemId, lang }: { problemId: string; lang: Lang }) {
  const [problem, setProblem] = useState<ProblemDetail | null>(null)
  const [files, setFiles] = useState<Files>({})
  const [tabs, setTabs] = useState<string[]>([])
  const [active, setActive] = useState<string | null>(null)
  const [saving, setSaving] = useState(0)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [running, setRunning] = useState<Mode | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [entry, setEntry] = useState<RunEntry | null>(null)
  const [history, setHistory] = useState<RunEntry[]>([])
  const [leftTab, setLeftTab] = useState<'problem' | 'history'>('problem')
  const [bottomTab, setBottomTab] = useState<'tests' | 'review'>('tests')
  const [toast, setToast] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [curveballs, setCurveballs] = useState<{ level: number; total: number; list: CurveballInfo[] }>({
    level: 0,
    total: 0,
    list: [],
  })
  const [unlocking, setUnlocking] = useState(false)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const [coachResult, setCoachResult] = useState<ReviewResult | null>(null)
  const [coachStatus, setCoachStatus] = useState<CoachStatus | null>(null)
  const [coaching, setCoaching] = useState(false)
  const [coachError, setCoachError] = useState<string | null>(null)
  const [timerStart, setTimerStart] = useState<number | null>(() => interviewStart(problemId))

  const filesRef = useRef(files)
  filesRef.current = files
  const timers = useRef<Record<string, number>>({})
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null)
  const reveal = useRef<{ path: string; line: number } | null>(null)
  const dark = usePrefersDark()

  // ---------------------------------------------------------------- load

  const loadWorkspace = useCallback(async () => {
    const ws = await api.workspace(problemId, lang)
    setCurveballs({ level: ws.level, total: ws.curveballs_total, list: ws.curveballs })
    rememberLang(problemId, lang)
    const next: Files = {}
    for (const f of ws.files) next[f.path] = { content: f.content, saved: f.content, editable: f.editable }
    setFiles(next)
    setTabs([ws.entry])
    setActive(ws.entry)
  }, [problemId, lang])

  useEffect(() => {
    let cancelled = false
    Promise.all([api.problem(problemId), loadWorkspace(), api.history(problemId, lang)])
      .then(([p, , h]) => {
        if (cancelled) return
        setProblem(p)
        setHistory(h)
        api.latestReview(problemId, lang).then((r) => r.review && setCoachResult(r), () => {})
        api.coachStatus().then(setCoachStatus, () => {})
        setEntry(h[0] ?? null)
        document.title = `${p.title} · ${LANG_LABEL[lang]} · DesignDojo`
      })
      .catch((e: Error) => !cancelled && setLoadError(e.message))
    return () => {
      cancelled = true
    }
  }, [problemId, lang, loadWorkspace])

  // ---------------------------------------------------------------- saving

  const saveFile = useCallback(
    async (path: string) => {
      const f = filesRef.current[path]
      if (!f || !f.editable || f.content === f.saved) return
      const content = f.content
      setSaving((n) => n + 1)
      try {
        await api.save(problemId, lang, path, content)
        setFiles((prev) => (prev[path] ? { ...prev, [path]: { ...prev[path], saved: content } } : prev))
        setSaveError(null)
      } catch (e) {
        setSaveError((e as Error).message)
      } finally {
        setSaving((n) => n - 1)
      }
    },
    [problemId, lang],
  )

  const flushAll = useCallback(async () => {
    for (const t of Object.values(timers.current)) clearTimeout(t)
    timers.current = {}
    const dirty = Object.entries(filesRef.current)
      .filter(([, f]) => f.editable && f.content !== f.saved)
      .map(([p]) => p)
    await Promise.all(dirty.map(saveFile))
  }, [saveFile])

  const runAnalysis = useCallback(async () => {
    setAnalyzing(true)
    try {
      await flushAll()
      setAnalysis(await api.analysis(problemId, lang))
      setAnalysisError(null)
    } catch (e) {
      setAnalysisError((e as Error).message)
    } finally {
      setAnalyzing(false)
    }
  }, [flushAll, problemId, lang])

  // Re-analyze when the review tab is opened, and after every run.
  useEffect(() => {
    if (bottomTab === 'review') runAnalysis()
  }, [bottomTab, runAnalysis])

  const runCoach = useCallback(
    async (force: boolean) => {
      setCoaching(true)
      setCoachError(null)
      try {
        await flushAll()
        setCoachResult(await api.review(problemId, lang, force))
        api.analysis(problemId, lang).then(setAnalysis, () => {})
      } catch (e) {
        setCoachError((e as Error).message)
      } finally {
        setCoaching(false)
      }
    },
    [flushAll, problemId, lang],
  )

  // Interview mode: the coach is locked until a Submit made after the timer started.
  const coachLocked =
    timerStart !== null && !history.some((h) => h.mode === 'submit' && h.at * 1000 >= timerStart)

  const onChange = (value: string | undefined) => {
    if (!active || value === undefined || !files[active]?.editable) return
    const path = active
    setFiles((prev) => ({ ...prev, [path]: { ...prev[path], content: value } }))
    clearTimeout(timers.current[path])
    timers.current[path] = window.setTimeout(() => saveFile(path), AUTOSAVE_MS)
  }

  // Last-chance save when the tab closes.
  useEffect(() => {
    const onHide = () => {
      for (const [path, f] of Object.entries(filesRef.current)) {
        if (f.editable && f.content !== f.saved) {
          fetch(`/api/ws/${problemId}/${lang}/file`, {
            method: 'PUT',
            keepalive: true,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path, content: f.content }),
          })
        }
      }
    }
    window.addEventListener('pagehide', onHide)
    return () => window.removeEventListener('pagehide', onHide)
  }, [problemId, lang])

  // ---------------------------------------------------------------- judging

  const judge = useCallback(
    async (mode: Mode) => {
      if (running) return
      await flushAll()
      setRunning(mode)
      setBottomTab('tests')
      const t0 = Date.now()
      setElapsed(0)
      const tick = window.setInterval(() => setElapsed((Date.now() - t0) / 1000), 250)
      try {
        const e = await api.judge(problemId, lang, mode)
        setEntry(e)
        setHistory((h) => [e, ...h])
        api.analysis(problemId, lang).then(setAnalysis, () => {})
      } catch (err) {
        setToast((err as Error).message)
      } finally {
        clearInterval(tick)
        setRunning(null)
      }
    },
    [running, flushAll, problemId, lang],
  )
  const judgeRef = useRef(judge)
  judgeRef.current = judge
  const flushRef = useRef(flushAll)
  flushRef.current = flushAll

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!(e.metaKey || e.ctrlKey)) return
      if (e.key === 'Enter') {
        e.preventDefault()
        judgeRef.current(e.shiftKey ? 'submit' : 'run')
      } else if (e.key === 's') {
        e.preventDefault()
        flushRef.current()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // ---------------------------------------------------------------- tabs & navigation

  const open = (path: string) => {
    setTabs((t) => (t.includes(path) ? t : [...t, path]))
    setActive(path)
  }

  const close = (path: string) => {
    setTabs((t) => {
      const next = t.filter((p) => p !== path)
      if (active === path) setActive(next[Math.max(0, t.indexOf(path) - 1)] ?? null)
      return next
    })
  }

  const applyReveal = useCallback(() => {
    const ed = editorRef.current
    const r = reveal.current
    if (!ed || !r || r.path !== active) return
    reveal.current = null
    ed.revealLineInCenter(r.line)
    ed.setPosition({ lineNumber: r.line, column: 1 })
    ed.focus()
  }, [active])

  const jump = (file: string, line: number) => {
    const paths = Object.keys(files)
    const target =
      paths.find((p) => p === file) ??
      paths.find((p) => p.endsWith('/' + file)) ??
      paths.find((p) => p.split('/').pop() === file.split('/').pop())
    if (!target) return setToast(`Can't find ${file} in this workspace`)
    reveal.current = { path: target, line }
    open(target)
    if (target === active) applyReveal()
  }

  useEffect(applyReveal, [active, applyReveal])

  // Compile errors as squiggles in the open file.
  useEffect(() => {
    const model = editorRef.current?.getModel()
    if (!model || !active) return
    const diags = entry?.result.status === 'compile_error' ? (entry.result.diagnostics ?? []) : []
    monaco.editor.setModelMarkers(
      model,
      'dojo',
      diags
        .filter((d) => d.file === active && d.line > 0)
        .map((d) => ({
          severity: monaco.MarkerSeverity.Error,
          message: d.message,
          startLineNumber: d.line,
          endLineNumber: d.line,
          startColumn: 1,
          endColumn: model.getLineMaxColumn(Math.min(d.line, model.getLineCount())),
        })),
    )
    monaco.editor.setModelMarkers(
      model,
      'dojo-design',
      (analysis?.smells ?? [])
        .filter((s) => s.file === active && s.line_start <= model.getLineCount())
        .map((s) => ({
          severity: s.level === 'warning' ? monaco.MarkerSeverity.Warning : monaco.MarkerSeverity.Info,
          message: `${s.title}: ${s.evidence}\nConsider: ${s.suggests.join(', ')}`,
          source: 'DesignDojo design signals',
          startLineNumber: s.line_start,
          endLineNumber: s.line_start,
          startColumn: model.getLineFirstNonWhitespaceColumn(s.line_start) || 1,
          endColumn: model.getLineMaxColumn(s.line_start),
        })),
    )
    monaco.editor.setModelMarkers(
      model,
      'dojo-coach',
      (coachLocked ? [] : (coachResult?.review?.comments ?? []))
        .filter((c) => c.file === active && c.line_start <= model.getLineCount())
        .map((c) => ({
          severity: c.kind === 'warning' ? monaco.MarkerSeverity.Warning : monaco.MarkerSeverity.Info,
          message: `Coach · ${c.title}${c.principle ? ` (${c.principle})` : ''}\n${c.hints[0]}`,
          source: 'DesignDojo coach',
          startLineNumber: c.line_start,
          endLineNumber: Math.min(c.line_end, model.getLineCount()),
          startColumn: model.getLineFirstNonWhitespaceColumn(c.line_start) || 1,
          endColumn: model.getLineMaxColumn(Math.min(c.line_end, model.getLineCount())),
        })),
    )
  }, [entry, active, files, analysis, coachResult, coachLocked])

  const onMount: OnMount = (ed, m) => {
    editorRef.current = ed
    // Monaco swallows these keys (⌘↵ = "insert line below"), so bind them as editor commands too.
    ed.addCommand(m.KeyMod.CtrlCmd | m.KeyCode.Enter, () => judgeRef.current('run'))
    ed.addCommand(m.KeyMod.CtrlCmd | m.KeyMod.Shift | m.KeyCode.Enter, () => judgeRef.current('submit'))
    ed.addCommand(m.KeyMod.CtrlCmd | m.KeyCode.KeyS, () => flushRef.current())
    applyReveal()
  }

  // ---------------------------------------------------------------- file ops

  const createFile = async (path: string) => {
    const content = template(path, lang)
    await api.create(problemId, lang, path, content)
    setFiles((prev) => ({ ...prev, [path]: { content, saved: content, editable: true } }))
    open(path)
  }

  const renameFile = async (src: string, dst: string) => {
    await flushAll()
    await api.rename(problemId, lang, src, dst)
    setFiles((prev) => {
      const { [src]: f, ...rest } = prev
      return { ...rest, [dst]: f }
    })
    setTabs((t) => t.map((p) => (p === src ? dst : p)))
    if (active === src) setActive(dst)
  }

  const deleteFile = async (path: string) => {
    clearTimeout(timers.current[path])
    await api.remove(problemId, lang, path)
    setFiles((prev) => {
      const { [path]: _, ...rest } = prev
      return rest
    })
    close(path)
  }

  const resetWorkspace = async () => {
    for (const t of Object.values(timers.current)) clearTimeout(t)
    timers.current = {}
    const r = await api.reset(problemId, lang)
    for (const m of monaco.editor.getModels()) m.dispose()
    await loadWorkspace()
    setToast(r.backup ? `Started over. Previous code moved to ${r.backup}` : 'Started over')
  }

  const unlockCurveball = async () => {
    if (unlocking || running) return
    setUnlocking(true)
    try {
      await flushAll()
      const info = await api.nextCurveball(problemId, lang)
      for (const m of monaco.editor.getModels()) if (m.uri.path.includes('contract')) m.dispose()
      await loadWorkspace()
      setLeftTab('problem')
      setToast(`Curveball ${info.index} unlocked: ${info.title}. Your code was snapshotted to measure the change.`)
    } catch (e) {
      setToast((e as Error).message)
    } finally {
      setUnlocking(false)
    }
  }

  const switchLang = async (l: Lang) => {
    if (l === lang) return
    await flushAll()
    window.location.hash = `#/p/${problemId}/${l}`
  }

  // ---------------------------------------------------------------- render

  const treeFiles = useMemo(
    () => Object.entries(files).map(([path, f]) => ({ path, editable: f.editable, dirty: f.content !== f.saved })),
    [files],
  )
  const dirty = treeFiles.some((f) => f.dirty)
  const current = active ? files[active] : null
  const saveLabel = saveError ? 'Save failed' : saving > 0 ? 'Saving…' : dirty ? 'Unsaved' : 'Saved'

  if (loadError) {
    return (
      <div className="loading">
        <div className="banner bad">
          Could not open workspace: {loadError} · <a href="#/">back</a>
        </div>
      </div>
    )
  }
  if (!problem) return <div className="loading">Loading…</div>

  return (
    <div className="ws">
      <header className="topbar">
        <Brand />
        <span className="crumb-sep">/</span>
        <span className="title">{problem.title}</span>
        {problem.difficulty && <span className={`pill ${problem.difficulty}`}>{problem.difficulty}</span>}
        <span className="spacer" />
        <span className={`save-state ${saveError ? 'error' : dirty ? 'dirty' : ''}`} title={saveError ?? ''}>
          {saveLabel}
        </span>
        {curveballs.total > 0 && (
          <span className="curveball-badge" title="Curveballs: follow-up requirements that test how well your design extends">
            <Zap size={13} /> {curveballs.level}/{curveballs.total}
            {curveballs.level < curveballs.total && (
              <button className="btn small" onClick={unlockCurveball} disabled={unlocking || !!running}
                      title="Needs every scenario passing; runs a full submit first">
                {unlocking ? <Loader2 size={12} className="spin" /> : null}
                Next curveball
              </button>
            )}
          </span>
        )}
        <select className="lang-select" value={lang} onChange={(e) => switchLang(e.target.value as Lang)}
                aria-label="Language">
          {problem.langs.map((l) => (
            <option key={l} value={l}>
              {LANG_LABEL[l]}
            </option>
          ))}
        </select>
        {problem.time_limit_min && (
          <Timer problemId={problemId} limitMin={problem.time_limit_min} onChange={setTimerStart} />
        )}
        <button className="btn" onClick={() => judge('run')} disabled={!!running} title="Run samples (⌘↵)">
          <Play size={14} /> Run
        </button>
        <button className="btn primary" onClick={() => judge('submit')} disabled={!!running} title="Submit (⌘⇧↵)">
          <Send size={14} /> Submit
        </button>
      </header>

      <div className="ws-body">
        <Group orientation="horizontal">
          <Panel defaultSize="32%" minSize="20%">
            <div className="pane">
              <div className="tabs">
                <button className={leftTab === 'problem' ? 'on' : ''} onClick={() => setLeftTab('problem')}>
                  Problem
                </button>
                <button className={leftTab === 'history' ? 'on' : ''} onClick={() => setLeftTab('history')}>
                  History {history.length > 0 && <span className="tab-badge">{history.length}</span>}
                </button>
              </div>
              <div className="pane-scroll">
                {leftTab === 'problem' ? (
                  <div className="markdown">
                    <Markdown remarkPlugins={[remarkGfm]}>{problem.statement}</Markdown>
                    {curveballs.list.map((c) => (
                      <section key={c.id} className="curveball-section">
                        <div className="curveball-label">
                          <Zap size={13} /> Curveball {c.index}
                        </div>
                        <Markdown remarkPlugins={[remarkGfm]}>{c.statement}</Markdown>
                      </section>
                    ))}
                  </div>
                ) : history.length === 0 ? (
                  <div className="coming">No runs yet.</div>
                ) : (
                  history.map((h) => (
                    <button
                      key={h.id}
                      className={`hist-row ${entry?.id === h.id ? 'on' : ''}`}
                      onClick={() => {
                        setEntry(h)
                        setBottomTab('tests')
                      }}
                    >
                      <span className="mode">{h.mode}</span>
                      {h.status === 'ok' ? (
                        <span className={`chip ${h.passed === h.total ? 'ok' : 'bad'}`}>
                          {h.passed}/{h.total}
                        </span>
                      ) : (
                        <span className="chip bad">{h.status.replaceAll('_', ' ')}</span>
                      )}
                      <span className="when">{ago(h.at)}</span>
                    </button>
                  ))
                )}
              </div>
            </div>
          </Panel>
          <Separator className="sep" />
          <Panel minSize="35%">
            <Group orientation="vertical">
              <Panel defaultSize="62%" minSize="20%">
                <div className="pane">
                  <div className="editor-area">
                    <FileTree
                      files={treeFiles}
                      active={active}
                      ext={EXT[lang]}
                      onOpen={open}
                      onCreate={createFile}
                      onRename={renameFile}
                      onDelete={deleteFile}
                      onReset={resetWorkspace}
                    />
                    <div className="editor-col">
                      <div className="file-tabs">
                        {tabs.map((p) => (
                          <button key={p} className={`file-tab ${p === active ? 'on' : ''}`} onClick={() => setActive(p)} title={p}>
                            {!files[p]?.editable && <Lock size={11} />}
                            {p.split('/').pop()}
                            {files[p] && files[p].content !== files[p].saved && <span className="dot" />}
                            <span
                              className="icon-btn x"
                              role="button"
                              aria-label={`Close ${p}`}
                              onClick={(e) => {
                                e.stopPropagation()
                                close(p)
                              }}
                            >
                              <X size={12} />
                            </span>
                          </button>
                        ))}
                      </div>
                      {current && !current.editable && (
                        <div className="readonly-bar">
                          <Lock size={12} /> Generated from the problem contract. Read-only; the judge calls only this API.
                        </div>
                      )}
                      <div className="editor-host">
                        {active && current ? (
                          <Editor
                            path={active}
                            language={lang}
                            value={current.content}
                            onChange={onChange}
                            onMount={onMount}
                            theme={dark ? 'dojo-dark' : 'dojo-light'}
                            options={{
                              readOnly: !current.editable,
                              fontSize: 13.5,
                              fontFamily: "ui-monospace, 'SF Mono', 'JetBrains Mono', Menlo, monospace",
                              minimap: { enabled: false },
                              scrollBeyondLastLine: false,
                              tabSize: 4,
                              automaticLayout: true,
                              padding: { top: 10 },
                              renderLineHighlight: 'line',
                              smoothScrolling: true,
                            }}
                          />
                        ) : (
                          <div className="empty">Open a file from the tree.</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Panel>
              <Separator className="sep" />
              <Panel minSize="12%">
                <div className="pane">
                  <div className="tabs">
                    <button className={bottomTab === 'tests' ? 'on' : ''} onClick={() => setBottomTab('tests')}>
                      Tests
                    </button>
                    <button className={bottomTab === 'review' ? 'on' : ''} onClick={() => setBottomTab('review')}>
                      <Sparkles size={13} /> Design review
                      {analysis && analysis.smells.some((s) => s.level === 'warning') && (
                        <span className="tab-badge">{analysis.smells.filter((s) => s.level === 'warning').length}</span>
                      )}
                    </button>
                  </div>
                  <div className="pane-scroll">
                    {bottomTab === 'tests' ? (
                      <ResultsPanel
                        entry={entry}
                        running={running}
                        elapsed={elapsed}
                        onJump={jump}
                        isLatest={!!entry && history[0]?.id === entry.id}
                      />
                    ) : (
                      <DesignPanel
                        coach={{
                          result: coachResult,
                          status: coachStatus,
                          loading: coaching,
                          error: coachError,
                          locked: coachLocked,
                          onReview: runCoach,
                        }}
                        analysis={analysis}
                        loading={analyzing}
                        error={analysisError}
                        dark={dark}
                        onRefresh={runAnalysis}
                        onJump={jump}
                      />
                    )}
                  </div>
                </div>
              </Panel>
            </Group>
          </Panel>
        </Group>
      </div>

      {toast && (
        <div className="toast" role="status">
          {toast}
          <button onClick={() => setToast(null)} aria-label="Dismiss">
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  )
}

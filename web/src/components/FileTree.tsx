import { FilePlus, FileCode2, Folder, Lock, Pencil, RotateCcw, Trash2 } from 'lucide-react'
import { useState } from 'react'

export type TreeFile = { path: string; editable: boolean; dirty: boolean }

type Row =
  | { kind: 'dir'; name: string; depth: number; key: string; readonly: boolean }
  | { kind: 'file'; name: string; depth: number; key: string; file: TreeFile }

function buildRows(files: TreeFile[]): Row[] {
  const rows: Row[] = []
  const seen = new Set<string>()
  const sorted = [...files].sort((a, b) => {
    // solution/ first, then contract/; within a folder, files before subfolders
    const ra = a.editable ? 0 : 1
    const rb = b.editable ? 0 : 1
    if (ra !== rb) return ra - rb
    const da = a.path.split('/').length
    const db = b.path.split('/').length
    const pa = a.path.slice(0, a.path.lastIndexOf('/'))
    const pb = b.path.slice(0, b.path.lastIndexOf('/'))
    if (pa === pb) return a.path.localeCompare(b.path)
    if (pa.startsWith(pb + '/') || pb.startsWith(pa + '/')) return da - db
    return a.path.localeCompare(b.path)
  })
  for (const f of sorted) {
    const parts = f.path.split('/')
    for (let i = 1; i < parts.length; i++) {
      const key = parts.slice(0, i).join('/')
      if (!seen.has(key)) {
        seen.add(key)
        rows.push({ kind: 'dir', name: parts[i - 1], depth: i - 1, key, readonly: !f.editable })
      }
    }
    rows.push({ kind: 'file', name: parts[parts.length - 1], depth: parts.length - 1, key: f.path, file: f })
  }
  return rows
}

type Props = {
  files: TreeFile[]
  active: string | null
  ext: string
  onOpen: (path: string) => void
  onCreate: (path: string) => Promise<void>
  onRename: (src: string, dst: string) => Promise<void>
  onDelete: (path: string) => Promise<void>
  onReset: () => Promise<void>
}

const VALID = /^solution\/([A-Za-z_][\w]*\/)*[A-Za-z_][\w]*$/

export default function FileTree({ files, active, ext, onOpen, onCreate, onRename, onDelete, onReset }: Props) {
  const [creating, setCreating] = useState(false)
  const [renaming, setRenaming] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)
  const [confirmReset, setConfirmReset] = useState(false)
  const [draft, setDraft] = useState('')
  const [err, setErr] = useState<string | null>(null)

  const rows = buildRows(files)

  function validate(path: string): string | null {
    const stem = path.endsWith(ext) ? path.slice(0, -ext.length) : path
    if (!VALID.test(stem)) return `Use solution/<name>${ext} (letters, digits, _; folders allowed)`
    if (files.some((f) => f.path === stem + ext)) return 'A file with that name exists'
    return null
  }

  async function submit(kind: 'create' | 'rename') {
    const path = draft.trim().endsWith(ext) ? draft.trim() : draft.trim() + ext
    const problem = validate(path)
    if (problem) return setErr(problem)
    try {
      if (kind === 'create') await onCreate(path)
      else if (renaming) await onRename(renaming, path)
      setCreating(false)
      setRenaming(null)
      setErr(null)
    } catch (e) {
      setErr((e as Error).message)
    }
  }

  function startCreate() {
    setRenaming(null)
    setCreating(true)
    setDraft('solution/')
    setErr(null)
  }

  const input = (kind: 'create' | 'rename') => (
    <>
      <input
        className="tree-input"
        autoFocus
        value={draft}
        spellCheck={false}
        onChange={(e) => {
          setDraft(e.target.value)
          setErr(null)
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter') submit(kind)
          if (e.key === 'Escape') {
            setCreating(false)
            setRenaming(null)
            setErr(null)
          }
        }}
        onBlur={() => {
          if (!err) {
            setCreating(false)
            setRenaming(null)
          }
        }}
        placeholder={`solution/Name${ext}`}
      />
      {err && <div className="tree-hint">{err}</div>}
    </>
  )

  return (
    <div className="tree">
      <div className="tree-head">
        Files
        <span style={{ display: 'flex', gap: 2 }}>
          <button className="icon-btn" title={`New file (${ext})`} onClick={startCreate}>
            <FilePlus size={15} />
          </button>
          <button className="icon-btn" title="Start over from the stub" onClick={() => setConfirmReset(true)}>
            <RotateCcw size={14} />
          </button>
        </span>
      </div>
      {confirmReset && (
        <div className="tree-confirm" style={{ flexWrap: 'wrap' }}>
          <span style={{ width: '100%' }}>Start over? Current code is moved to a backup, not deleted.</span>
          <button
            className="btn small danger"
            onClick={async () => {
              setConfirmReset(false)
              await onReset()
            }}
          >
            Start over
          </button>
          <button className="btn small ghost" onClick={() => setConfirmReset(false)}>
            Cancel
          </button>
        </div>
      )}
      <div className="tree-list">
        {creating && input('create')}
        {rows.map((r) =>
          r.kind === 'dir' ? (
            <div key={'d:' + r.key} className="tree-row dir" style={{ paddingLeft: 10 + r.depth * 14 }}>
              <Folder size={14} />
              <span className="name">{r.name}</span>
              {r.readonly && r.depth === 0 && <span className="meta">generated</span>}
            </div>
          ) : renaming === r.key ? (
            <div key={'r:' + r.key}>{input('rename')}</div>
          ) : (
            <div key={r.key}>
              <div
                className={`tree-row ${active === r.key ? 'active' : ''} ${r.file.editable ? '' : 'readonly'}`}
                style={{ paddingLeft: 10 + r.depth * 14 }}
                onClick={() => onOpen(r.key)}
                title={r.file.editable ? r.key : `${r.key} (generated, read-only)`}
              >
                {r.file.editable ? <FileCode2 size={14} /> : <Lock size={13} />}
                <span className="name">{r.name}</span>
                {r.file.dirty && <span className="dot" title="Unsaved" />}
                {r.file.editable && (
                  <span className="row-actions">
                    <button
                      className="icon-btn"
                      title="Rename"
                      onClick={(e) => {
                        e.stopPropagation()
                        setCreating(false)
                        setRenaming(r.key)
                        setDraft(r.key)
                        setErr(null)
                      }}
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      className="icon-btn"
                      title="Delete"
                      onClick={(e) => {
                        e.stopPropagation()
                        setConfirmDelete(r.key)
                      }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </span>
                )}
              </div>
              {confirmDelete === r.key && (
                <div className="tree-confirm">
                  Delete {r.name}?
                  <span className="spacer" />
                  <button
                    className="btn small danger"
                    onClick={async () => {
                      setConfirmDelete(null)
                      await onDelete(r.key)
                    }}
                  >
                    Delete
                  </button>
                  <button className="btn small ghost" onClick={() => setConfirmDelete(null)}>
                    Cancel
                  </button>
                </div>
              )}
            </div>
          ),
        )}
      </div>
      <div className="tree-foot">Your design goes in solution/. The contract is regenerated on every run.</div>
    </div>
  )
}

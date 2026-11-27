import { AlertTriangle, KeyRound, Link2, Loader2, ShieldCheck } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api, type Analysis, type CatalogTable, type Lang } from '../api'
import { Diagram } from './DesignPanel'

/** Relationship sentences, e.g. "customers 1 → many orders (orders.customer_id, required)". */
function relationships(tables: CatalogTable[]) {
  const out: { from: string; to: string; text: string; detail: string }[] = []
  for (const t of tables) {
    const uniques = t.constraints.filter((c) => c.type === 'p' || c.type === 'u').map((c) => c.cols ?? [])
    for (const c of t.constraints) {
      if (c.type !== 'f' || !c.ref) continue
      const cols = c.cols ?? []
      const optional = cols.some((n) => !t.columns.find((x) => x.name === n)?.notnull)
      const oneToOne = uniques.some((u) => u.length && u.every((x) => cols.includes(x)))
      const onDelete = /on delete (cascade|set null|set default|restrict)/i.exec(c.def)?.[1]?.toUpperCase()
      out.push({
        from: c.ref,
        to: t.name,
        text: `${c.ref} 1 → ${oneToOne ? '0..1' : 'many'} ${t.name}`,
        detail: `${t.name}(${cols.join(', ')}) → ${c.ref}(${(c.refcols ?? []).join(', ')})` +
          `${optional ? ', optional' : ', required'}${onDelete ? `, on delete ${onDelete.toLowerCase()}` : ''}`,
      })
    }
  }
  // many-to-many: a table with two FKs that together form its key is a junction table
  for (const t of tables) {
    const fks = t.constraints.filter((c) => c.type === 'f' && c.ref)
    const pk = t.constraints.find((c) => c.type === 'p')?.cols ?? []
    const uq = t.constraints.filter((c) => c.type === 'u').map((c) => c.cols ?? [])
    if (fks.length === 2) {
      const keyCols = fks.flatMap((f) => f.cols ?? [])
      const keyed = [pk, ...uq].some((k) => k.length && keyCols.every((c) => k.includes(c)))
      if (keyed) {
        out.push({ from: fks[0].ref!, to: fks[1].ref!, text: `${fks[0].ref} many ↔ many ${fks[1].ref}`,
          detail: `through the junction table ${t.name}` })
      }
    }
  }
  return out
}

export default function SchemaView({ problemId, lang, schemaVersion, dark }: {
  problemId: string
  lang: Lang
  schemaVersion: string
  dark: boolean
}) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const seq = useRef(0)

  useEffect(() => {
    const mine = ++seq.current
    const t = window.setTimeout(() => {
      setLoading(true)
      api.analysis(problemId, lang).then(
        (a) => mine === seq.current && (setAnalysis(a), setError(null)),
        (e: Error) => mine === seq.current && setError(e.message),
      ).finally(() => mine === seq.current && setLoading(false))
    }, 400)
    return () => window.clearTimeout(t)
  }, [problemId, lang, schemaVersion])

  const schemaError = analysis?.smells.find((s) => s.id === 'SCHEMA_ERROR')
  const tables = analysis?.tables ?? []
  const rels = relationships(tables)

  return (
    <div className="results schema-view">
      <div className="summary">
        <strong>Schema</strong>
        <span className="meta">
          {tables.length} table(s) · {rels.length} relationship(s) · redraws as you edit schema.sql
        </span>
        <span className="spacer" />
        {loading && <Loader2 size={14} className="spin" />}
      </div>
      {error && <div className="banner bad">{error}</div>}
      {schemaError && (
        <div className="banner bad">
          <AlertTriangle size={15} /> schema.sql doesn't apply yet: {schemaError.evidence} (line {schemaError.line_start}).
          The diagram shows the last version that worked.
        </div>
      )}
      {analysis && tables.length === 0 && !schemaError && (
        <div className="empty">
          <div>
            <h3>No tables yet</h3>
            <div>Write <code>CREATE TABLE</code> statements in schema.sql: each table appears here, connected by its foreign keys.</div>
          </div>
        </div>
      )}
      {tables.length > 0 && (
        <>
          <Diagram
            code={analysis!.mermaid}
            dark={dark}
            title="Schema diagram"
            legend="Tables and how they connect. ||--o{ one-to-many · ||--o| one-to-one · |o optional parent. PK primary key · FK foreign key · UK unique"
          />
          {rels.length > 0 && (
            <div className="rels">
              <h4><Link2 size={13} /> Relationships</h4>
              {rels.map((r, i) => (
                <div key={i} className="rel-row">
                  <b>{r.text}</b> <span className="meta">{r.detail}</span>
                </div>
              ))}
            </div>
          )}
          <div className="table-cards">
            {tables.map((t) => {
              const keyCols = new Set(t.constraints.filter((c) => c.type === 'p').flatMap((c) => c.cols ?? []))
              const fkCols = new Map(t.constraints.filter((c) => c.type === 'f').flatMap((c) => (c.cols ?? []).map((n) => [n, c.ref] as const)))
              const rules = t.constraints.filter((c) => c.type !== 'f' && c.type !== 'n')
              const extraIdx = t.indexes.filter((ix) => !t.constraints.some((c) => (c.type === 'p' || c.type === 'u' || c.type === 'x') && ix.def.includes(c.name)))
              return (
                <div key={t.name} className="tcard">
                  <div className="tcard-head">{t.name}</div>
                  <table className="tcols">
                    <tbody>
                      {t.columns.map((c) => (
                        <tr key={c.name}>
                          <td className="tc-name">
                            {keyCols.has(c.name) && <KeyRound size={11} className="ic-key" />} {c.name}
                          </td>
                          <td className="tc-type">{c.type}</td>
                          <td className="tc-flags">
                            {c.notnull ? 'NOT NULL' : <span className="meta">null</span>}
                            {fkCols.has(c.name) && <span className="fk"> → {fkCols.get(c.name)}</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {(rules.length > 0 || extraIdx.length > 0) && (
                    <div className="trules">
                      {rules.map((c) => (
                        <div key={c.name}>
                          <ShieldCheck size={11} /> <code>{c.def}</code>
                        </div>
                      ))}
                      {extraIdx.map((ix, i) => (
                        <div key={i}>
                          <span className="rk">INDEX</span> <code>{ix.def.replace(/^CREATE (UNIQUE )?INDEX \S+ ON \S+ USING \w+ /, '$1')}</code>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}

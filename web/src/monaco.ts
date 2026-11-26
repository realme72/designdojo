// Bundle Monaco locally (no CDN) so the playground works offline.
import { loader } from '@monaco-editor/react'
import * as monaco from 'monaco-editor'
import EditorWorker from 'monaco-editor/editor/editor.worker?worker'

self.MonacoEnvironment = {
  getWorker: () => new EditorWorker(),
}

loader.config({ monaco })

monaco.editor.defineTheme('dojo-dark', {
  base: 'vs-dark',
  inherit: true,
  rules: [],
  colors: {
    'editor.background': '#15181c',
    'editorGutter.background': '#15181c',
    'editor.lineHighlightBackground': '#1d2126',
    'editorLineNumber.foreground': '#4b525c',
  },
})

monaco.editor.defineTheme('dojo-light', {
  base: 'vs',
  inherit: true,
  rules: [],
  colors: {
    'editor.background': '#ffffff',
    'editor.lineHighlightBackground': '#f6f7f9',
    'editorLineNumber.foreground': '#a3a9b2',
  },
})

export { monaco }

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dev: `npm run dev` proxies the API to `joinery serve` on 8765.
// Prod: `npm run build` -> dist/, served by `joinery serve` itself.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: { '/api': 'http://127.0.0.1:8765' },
  },
  build: {
    chunkSizeWarningLimit: 6000,
  },
})

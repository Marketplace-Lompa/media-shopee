import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const host = process.env.VITE_HOST ?? '127.0.0.1'
const port = Number(process.env.VITE_PORT ?? 5173)
const proxyTarget = process.env.VITE_PROXY_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    host,
    port,
    strictPort: true,
    proxy: {
      '/generate': proxyTarget,
      '/marketplace': proxyTarget,
      '/pool': proxyTarget,
      '/outputs': proxyTarget,
      '/health': proxyTarget,
      '/history': proxyTarget,
      '/edit': proxyTarget,
      '/review': proxyTarget,
    },
    watch: {
      ignored: ['**/outputs/**', '**/.venv/**', '**/.git/**'],
    },
  },
})

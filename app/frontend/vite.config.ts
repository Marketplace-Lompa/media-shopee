import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/generate': 'http://localhost:8000',
      '/pool': 'http://localhost:8000',
      '/outputs': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/history': 'http://localhost:8000',
      '/edit': 'http://localhost:8000',
    },
    watch: {
      ignored: ['**/outputs/**', '**/.venv/**', '**/.git/**'],
    },
  },
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/admin/',
  server: {
    port: 3001,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/socket.io': { target: 'http://127.0.0.1:8000', ws: true },
    },
  },
})

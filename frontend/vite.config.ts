import { defineConfig } from 'vite'
// Keep your existing imports here if you have them (e.g., import react from '@vitejs/plugin-react')

export default defineConfig({
  // Keep your existing plugins here if you have them
  
  server: {
    port: 3000, // You can change this to 5173 or anything else
    proxy: {
      // Route all /api requests to your FastAPI backend
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // Route WebSocket connections to your backend
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      }
    }
  }
})
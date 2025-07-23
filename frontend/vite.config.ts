import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Proxy for WebSocket Gateway
      '/socket.io': {
        target: 'http://localhost:8080',
        ws: true, // Enable WebSocket proxying
      },
      // Proxy for FastAPI Upload Endpoint
      '/upload-api': {
        target: 'http://localhost:8000', // CORRECTED: Target our FastAPI server
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/upload-api/, ''),
      },
    },
  },
});

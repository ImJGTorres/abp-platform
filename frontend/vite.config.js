import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// En producción Django sirve los archivos compilados bajo /static/ (whitenoise) y devuelve
// index.html para las rutas de la app, por eso el build usa base '/static/'. En desarrollo
// la app se sirve en '/', igual que las rutas de producción (/login, /admin, ...).
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/' : '/',
  build: { sourcemap: false },
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    port: 5173,
    proxy: {
      '/api':   { target: 'http://localhost:8000', changeOrigin: true },
      '/media': { target: 'http://localhost:8000', changeOrigin: true },
    }
  },
  test: { globals: true, environment: 'jsdom' }
}))
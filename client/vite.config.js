// client/vite.config.js
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
export default defineConfig({
  base: '/transp_expr_webapp/',      // must match your repo path
  plugins: [react()],
  build: { outDir: 'dist', sourcemap: true }
})

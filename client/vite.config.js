import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  base: '/transp_expr_webapp/',
  plugins: [react()],
  build: { outDir: 'dist'} 
})


  ?

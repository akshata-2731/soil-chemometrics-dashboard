import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// `vite build --mode research` builds the Scispectrum research edition served at /research on the ArkaShine site
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  base: mode === 'research' ? '/research/' : '/',
  server: {
    proxy: { '/api': 'http://127.0.0.1:5000' },
  },
}))

import react from '@vitejs/plugin-react'
import { defineConfig, type Plugin } from 'vite'
import fs from 'node:fs'
import path from 'node:path'

// Middleware para servir os livros e documentos oficiais da pasta raw
const rawBooksPlugin = (): Plugin => ({
  name: 'serve-raw-books',
  configureServer(server) {
    server.middlewares.use('/raw-books', (req, res, next) => {
      const rawDir = path.resolve(import.meta.dirname, '../.arcanum/sources/raw')
      const reqUrl = req.url ? decodeURIComponent(req.url.split('?')[0]) : ''
      const fileName = reqUrl.replace(/^\//, '')
      const filePath = path.join(rawDir, fileName)

      if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
        const ext = path.extname(filePath).toLowerCase()
        if (ext === '.pdf') {
          res.setHeader('Content-Type', 'application/pdf')
          res.setHeader('Content-Disposition', 'inline')
        } else if (ext === '.json') {
          res.setHeader('Content-Type', 'application/json; charset=utf-8')
        } else if (ext === '.txt') {
          res.setHeader('Content-Type', 'text/plain; charset=utf-8')
        }
        fs.createReadStream(filePath).pipe(res)
        return
      }
      next()
    })
  },
})

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), rawBooksPlugin()],
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

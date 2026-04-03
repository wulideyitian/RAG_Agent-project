import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // 确保正确代理 API 路径
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('[proxy error]', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('[proxyReq]', req.method, req.url, '->', proxyReq.path);
          });
        },
      },
    },
  },
})

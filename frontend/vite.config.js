import { defineConfig } from 'vite'
import path from 'path'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '~': path.resolve(__dirname, './'),
      '@': path.resolve(__dirname, './src')
    },
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json', '.vue'],
    // 如果你手动配置了这个，确保 'development' 在里面
    conditions: ['development', 'browser'],
  },
  server: {
    port: 8088,
    host: true,
    open: true,
    proxy: {
      '/api':{
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:5019',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
        ws: p => p.includes('/ws/'), // 仅对包含/ws/的路径启用WebSocket
        configure: (proxy, options) => {
          // 修正：在响应中添加CORS头部
          proxy.on('proxyRes', (proxyRes, req, res) => {
            // 设置代理响应头，禁用缓冲
            proxyRes.headers['Cache-Control'] = 'no-cache';
            proxyRes.headers['Transfer-Encoding'] = 'chunked';

            proxyRes.headers['Access-Control-Allow-Origin'] = '*';
            proxyRes.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
            proxyRes.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization';
          });

          // 处理OPTIONS请求
          proxy.on('proxyReq', (proxyReq, req, res) => {
            if (req.method === 'OPTIONS') {
              res.writeHead(200, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': 86400
              });
              res.end();
            }
          });
        }
      },
      '/chat-api':{
        // target:'http://10.1.85.118:8000',
        // target:'http://localhost:5019',
        target:'http://120.26.174.121',
        // target:'http://47.100.37.20:5012',
        // target:'http://47.100.37.20:5019',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/chat-api/, ''),
        ws: p => p.includes('/ws/'), // 仅对包含/ws/的路径启用WebSocket
        configure: (proxy, options) => {
          // 修正：在响应中添加CORS头部
          proxy.on('proxyRes', (proxyRes, req, res) => {
            // 设置代理响应头，禁用缓冲
            proxyRes.headers['Cache-Control'] = 'no-cache';
            proxyRes.headers['Transfer-Encoding'] = 'chunked';

            proxyRes.headers['Access-Control-Allow-Origin'] = '*';
            proxyRes.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
            proxyRes.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization';
          });

          // 处理OPTIONS请求
          proxy.on('proxyReq', (proxyReq, req, res) => {
            if (req.method === 'OPTIONS') {
              res.writeHead(200, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': 86400
              });
              res.end();
            }
          });
        }
      },
      '/chatimage-api':{
        // target:'http://10.1.85.118:8000',
        // target:'http://localhost:5019',
        target:'http://120.26.174.121',
        // target:'http://47.100.37.20:5006',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/chatimage-api/, ''),
        ws: p => p.includes('/ws/'), // 仅对包含/ws/的路径启用WebSocket
        configure: (proxy, options) => {
          // 修正：在响应中添加CORS头部
          proxy.on('proxyRes', (proxyRes, req, res) => {
            // 设置代理响应头，禁用缓冲
            proxyRes.headers['Cache-Control'] = 'no-cache';
            proxyRes.headers['Transfer-Encoding'] = 'chunked';

            proxyRes.headers['Access-Control-Allow-Origin'] = '*';
            proxyRes.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
            proxyRes.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization';
          });

          // 处理OPTIONS请求
          proxy.on('proxyReq', (proxyReq, req, res) => {
            if (req.method === 'OPTIONS') {
              res.writeHead(200, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': 86400
              });
              res.end();
            }
          });
        }
      },
      '/chatdiff-api':{
        // target:'http://10.1.85.118:8000',
        // target:'http://localhost:5019',
        target:'http://120.26.174.121',
        // target:'http://47.100.37.20:5015',
        // target:'http://47.100.37.20:5017',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/chatdiff-api/, ''),
        ws: p => p.includes('/ws/'), // 仅对包含/ws/的路径启用WebSocket
        configure: (proxy, options) => {
          // 修正：在响应中添加CORS头部
          proxy.on('proxyRes', (proxyRes, req, res) => {
            // 设置代理响应头，禁用缓冲
            proxyRes.headers['Cache-Control'] = 'no-cache';
            proxyRes.headers['Transfer-Encoding'] = 'chunked';

            proxyRes.headers['Access-Control-Allow-Origin'] = '*';
            proxyRes.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
            proxyRes.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization';
          });

          // 处理OPTIONS请求
          proxy.on('proxyReq', (proxyReq, req, res) => {
            if (req.method === 'OPTIONS') {
              res.writeHead(200, {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': 86400
              });
              res.end();
            }
          });
        }
      }
    }
  }
})

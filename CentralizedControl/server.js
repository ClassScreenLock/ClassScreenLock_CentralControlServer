const express = require('express');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');
const fs = require('fs').promises;
const path = require('path');
const http = require('http');

const app = express();
const PORT = 5173; // 统一使用 5173 端口
const VITE_PORT = 5174; // Vite 开发服务器使用 5174 端口
const BACKEND_PORT = 5000; // Python 后端端口

// 中间件 - 必须在最前面
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 添加日志中间件（在 express.json 之后）
app.use((req, res, next) => {
  if (req.url.startsWith('/api/')) {
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
    if ((req.method === 'POST' || req.method === 'PUT') && req.body) {
      console.log(`Request body:`, JSON.stringify(req.body));
    }
  }
  next();
});

// ========== WebSocket 代理到 Python 后端 ==========
// WebSocket 连接代理（Socket.IO）
const wsProxy = createProxyMiddleware({
  target: `http://localhost:${BACKEND_PORT}`,
  changeOrigin: true,
  ws: true,  // 启用 WebSocket 代理
  pathRewrite: {
    '^/socket.io': '/socket.io'  // Socket.IO 路径
  }
});

// 代理 Socket.IO WebSocket 连接
app.use('/socket.io', wsProxy);

// ========== API 代理到 Python 后端 ==========

// 通用代理函数
function proxyRequest(req, res) {
  const path = req.url; 
  const method = req.method;
  
  console.log(`[代理] ${method} ${path}`);
  
  const options = {
    hostname: 'localhost',
    port: BACKEND_PORT,
    path: '/api' + path, 
    method: method,
    headers: req.headers
  };
  
  const proxyReq = http.request(options, (proxyRes) => {
    console.log(`[代理] 后端响应状态码：${proxyRes.statusCode}`);
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });
  
  proxyReq.on('error', (err) => {
    console.error('[代理] 代理请求失败:', err);
    res.status(500).json({ error: '后端服务不可用' });
  });
  
  // 如果有请求体，转发请求体
  if (req.body) {
    proxyReq.write(JSON.stringify(req.body));
  }
  
  proxyReq.end();
}

// 代理所有 API 请求到 Python 后端
app.use('/api', proxyRequest);

// 开发模式：代理前端请求到 Vite 服务器
if (process.env.NODE_ENV !== 'production') {
  // 创建代理实例（只创建一次）- 使用 filter 选项跳过 API 和 WebSocket 请求
  const viteProxy = createProxyMiddleware({
    target: `http://localhost:${VITE_PORT}`,
    changeOrigin: true,
    ws: true,
    filter: (req) => {
      // 跳过所有 /api/ 和 /socket.io 请求
      return !req.url.startsWith('/api/') && !req.url.startsWith('/socket.io');
    }
  });
  
  // 使用代理中间件
  app.use(viteProxy);
} else {
  // 生产环境：提供静态文件
  const distPath = path.join(__dirname, 'dist');
  app.use(express.static(distPath));
}

// ========== 启动服务器 ==========

async function startServer() {
  // 监听所有网络接口（0.0.0.0），允许局域网访问
  const server = app.listen(PORT, '0.0.0.0', () => {
    console.log('='.repeat(50));
    console.log('ClassScreenLock Control Center API Server');
    console.log('='.repeat(50));
    console.log(`服务器地址：http://localhost:${PORT}`);
    console.log(`局域网访问：http://<本机IP>:${PORT}`);
    console.log(`前端代理：http://localhost:${VITE_PORT}`);
    console.log(`后端代理：http://localhost:${BACKEND_PORT}`);
    console.log(`WebSocket：ws://localhost:${PORT}/socket.io`);
    console.log('='.repeat(50));
  });
  
  // 处理 WebSocket 连接升级
  server.on('upgrade', (req, socket, head) => {
    if (req.url.startsWith('/socket.io')) {
      console.log('[WebSocket] 连接升级请求:', req.url);
      wsProxy.upgrade(req, socket, head);
    }
  });
}

startServer();

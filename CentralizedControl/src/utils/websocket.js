/**
 * WebSocket实时通信服务
 * 替代HTTP轮询，实现高敏感度实时推送
 */

import { io } from 'socket.io-client'
import { ref, reactive } from 'vue'
import { notify } from './notification'

class WebSocketService {
  constructor() {
    this.socket = null
    this.isConnected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10
    this.reconnectDelay = 1000
    this.heartbeatInterval = null
    
    // 状态数据
    this.state = reactive({
      connected: false,
      authenticated: false,
      lastHeartbeat: null,
      reconnectCount: 0
    })
    
    // 事件回调
    this.callbacks = {
      onDeviceStatusUpdate: [],
      onActivityLog: [],
      onConfigUpdate: [],
      onNotification: [],
      onDeviceList: [],
      onMessageSent: []
    }
  }
  
  /**
   * 连接WebSocket
   */
  connect() {
    if (this.socket && this.isConnected) {
      return
    }
    
    // 开发模式使用 Vite 代理，生产模式直接连接后端
    const isDev = import.meta.env.DEV
    let socketUrl

    if (isDev) {
      // 开发模式：使用当前页面 host + 后端端口（绕过 Vite 代理，因为代理对长轮询不够稳定）
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.hostname
      const config = localStorage.getItem('systemSettings')
      const port = config ? (JSON.parse(config).backendPort || 5000) : 5000
      socketUrl = `${protocol}//${host}:${port}`
    } else {
      // 生产模式：直接连接后端服务器
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.hostname
      const config = localStorage.getItem('systemSettings')
      const port = config ? (JSON.parse(config).backendPort || 5000) : 5000
      socketUrl = `${protocol}//${host}:${port}`
    }

    // Socket.IO连接
    this.socket = io(socketUrl, {
      path: '/socket.io',
      transports: ['polling'],  // 后端 threading 模式仅支持长轮询
      upgrade: false,  // 禁止升级到 WebSocket
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      forceNew: false
    })
    
    this._registerEvents()
  }
  
  /**
   * 注册Socket.IO事件
   */
  _registerEvents() {
    // 连接成功
    this.socket.on('connect', () => {
      console.log('[WebSocket] 连接成功')
      this.isConnected = true
      this.state.connected = true
      this.reconnectAttempts = 0
      
      // 自动认证
      this._autoAuthenticate()
      
      notify.success('实时连接已建立')
    })
    
    // 连接断开
    this.socket.on('disconnect', (reason) => {
      console.log('[WebSocket] 连接断开:', reason)
      this.isConnected = false
      this.state.connected = false
      this.state.authenticated = false
      
      if (reason === 'io server disconnect') {
        // 服务器主动断开，需要重新连接
        this.socket.connect()
      }
      
      notify.warning('实时连接已断开，正在重连...')
    })
    
    // 连接错误
    this.socket.on('connect_error', (error) => {
      console.error('[WebSocket] 连接错误:', error)
      this.reconnectAttempts++
      this.state.reconnectCount = this.reconnectAttempts
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        notify.error('实时连接失败，请检查网络')
      }
    })
    
    // 重连尝试
    this.socket.on('reconnect_attempt', (attempt) => {
      console.log('[WebSocket] 重连尝试:', attempt)
    })
    
    // 重连成功
    this.socket.on('reconnect', (attempt) => {
      console.log('[WebSocket] 重连成功:', attempt)
      this.isConnected = true
      this.state.connected = true
      this.reconnectAttempts = 0
      
      // 重新认证
      this._autoAuthenticate()
      
      notify.success('实时连接已恢复')
    })
    
    // 服务器确认连接
    this.socket.on('connected', (data) => {
      console.log('[WebSocket] 服务器确认:', data)
      this.state.lastHeartbeat = data.timestamp
    })
    
    // 前端认证成功
    this.socket.on('frontend_authenticated', (data) => {
      console.log('[WebSocket] 前端认证成功:', data)
      this.state.authenticated = true
      
      // 订阅设备状态更新
      this.subscribeDevices()
      
      // 订阅活动日志
      this.subscribeActivityLogs()
    })
    
    // 设备状态更新（实时推送）
    this.socket.on('device_status_update', (data) => {
      console.log('[WebSocket] 设备状态更新:', data)
      this._triggerCallbacks('onDeviceStatusUpdate', data)
    })
    
    // 活动日志推送
    this.socket.on('activity_log', (data) => {
      console.log('[WebSocket] 活动日志:', data)
      this._triggerCallbacks('onActivityLog', data)
    })
    
    // 配置更新推送
    this.socket.on('config_update', (data) => {
      console.log('[WebSocket] 配置更新:', data)
      this._triggerCallbacks('onConfigUpdate', data)
    })
    
    // 通知推送
    this.socket.on('notification', (data) => {
      console.log('[WebSocket] 通知:', data)
      this._triggerCallbacks('onNotification', data)
      
      if (data.type === 'success') {
        notify.success(data.message)
      } else if (data.type === 'error') {
        notify.error(data.message)
      } else if (data.type === 'warning') {
        notify.warning(data.message)
      } else {
        notify.info(data.message)
      }
    })
    
    // 设备列表响应
    this.socket.on('device_list', (data) => {
      console.log('[WebSocket] 设备列表:', data)
      this._triggerCallbacks('onDeviceList', data)
    })
    
    // 订阅确认
    this.socket.on('subscribed', (data) => {
      console.log('[WebSocket] 订阅成功:', data.room)
    })

    // 消息发送结果（集控端 -> 被控设备 转发结果）
    this.socket.on('message_sent', (data) => {
      console.log('[WebSocket] 消息发送结果:', data)
      this._triggerCallbacks('onMessageSent', data)
    })

    // 错误消息
    this.socket.on('error', (data) => {
      console.error('[WebSocket] 错误:', data)
      notify.error(data.message || 'WebSocket错误')
    })
  }
  
  /**
   * 自动认证
   */
  _autoAuthenticate() {
    const user = localStorage.getItem('user')
    if (user) {
      try {
        const userData = JSON.parse(user)
        if (userData.token) {
          this.authenticate(userData.token)
        }
      } catch (e) {
        console.error('[WebSocket] 解析用户数据失败:', e)
      }
    }
  }
  
  /**
   * 前端认证
   */
  authenticate(token, organizationId = null) {
    if (!this.socket || !this.isConnected) {
      console.warn('[WebSocket] 未连接，无法认证')
      return
    }
    
    this.socket.emit('frontend_auth', {
      token: token,
      organizationId: organizationId
    })
  }
  
  /**
   * 订阅设备状态更新
   */
  subscribeDevices(organizationId = null) {
    if (!this.socket || !this.isConnected) {
      return
    }
    
    this.socket.emit('subscribe_devices', {
      organizationId: organizationId
    })
  }
  
  /**
   * 订阅活动日志
   */
  subscribeActivityLogs() {
    if (!this.socket || !this.isConnected) {
      return
    }
    
    this.socket.emit('subscribe_activity_logs', {})
  }
  
  /**
   * 请求设备列表
   */
  requestDeviceList(organizationId = null) {
    if (!this.socket || !this.isConnected) {
      return
    }

    this.socket.emit('request_device_list', {
      organizationId: organizationId
    })
  }

  /**
   * 向指定设备发送消息（通过WebSocket转发到被控设备）
   * @param {string} deviceId 设备ID
   * @param {string} message 消息内容
   * @param {boolean} readAloud 是否在被控端朗读
   */
  sendMessage(deviceId, message, readAloud = false, options = {}) {
    if (!this.socket || !this.isConnected) {
      notify.warning('实时连接未建立，无法发送消息')
      return false
    }

    if (!deviceId) {
      notify.warning('缺少设备ID')
      return false
    }

    if (!message || !String(message).trim()) {
      notify.warning('消息内容不能为空')
      return false
    }

    // 附加发送者信息
    let sender = ''
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        const userData = JSON.parse(userStr)
        sender = userData.username || ''
      }
    } catch (e) {
      // 忽略解析错误
    }

    this.socket.emit('send_message', {
      deviceId: deviceId,
      message: message,
      readAloud: !!readAloud,
      sender: sender,
      // 横幅尺寸: small | medium | large | xlarge（默认 small）
      size: options.size || 'small',
      // 文字大小: small | medium | large | xlarge（默认 medium，独立于尺寸）
      fontSize: options.fontSize || 'medium',
      // 持续时间模式: auto | short | medium | long | custom | persistent（默认 auto）
      durationMode: options.durationMode || 'auto',
      // 自定义持续秒数（仅 durationMode=custom 时使用）
      customDurationSeconds: options.customDurationSeconds || 10,
      // 是否在通知时段禁止关闭窗口（默认 false）
      lockWindow: !!options.lockWindow
    })
    return true
  }
  
  /**
   * 注册回调函数
   */
  on(event, callback) {
    if (this.callbacks[event]) {
      this.callbacks[event].push(callback)
    }
  }
  
  /**
   * 移除回调函数
   */
  off(event, callback) {
    if (this.callbacks[event]) {
      const index = this.callbacks[event].indexOf(callback)
      if (index > -1) {
        this.callbacks[event].splice(index, 1)
      }
    }
  }
  
  /**
   * 触发回调
   */
  _triggerCallbacks(event, data) {
    if (this.callbacks[event]) {
      this.callbacks[event].forEach(callback => {
        try {
          callback(data)
        } catch (e) {
          console.error(`[WebSocket] 回调执行失败 (${event}):`, e)
        }
      })
    }
  }
  
  /**
   * 断开连接
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.isConnected = false
      this.state.connected = false
      this.state.authenticated = false
    }
  }
  
  /**
   * 获取连接状态
   */
  getState() {
    return this.state
  }
}

// 单例实例
const wsService = new WebSocketService()

export default wsService
export { WebSocketService }
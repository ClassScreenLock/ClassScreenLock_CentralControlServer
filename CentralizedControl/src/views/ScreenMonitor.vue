<template>
  <div class="screen-monitor-page" :class="{ 'is-fullscreen': isFullscreen }">
    <!-- 顶部工具栏 -->
    <div class="monitor-toolbar">
      <div class="toolbar-left">
        <FluentIcons name="desktop" :size="22" class="toolbar-icon" />
        <span class="toolbar-title">屏幕监控</span>

        <!-- 组织筛选 -->
        <div class="toolbar-dropdown-wrap">
          <MonitorDropdown
            v-model="filterOrgId"
            :options="orgOptions"
            placeholder="全部组织"
          />
        </div>

        <!-- 设备下拉 -->
        <div class="toolbar-dropdown-wrap toolbar-dropdown-wrap--device">
          <MonitorDropdown
            v-model="selectedDeviceId"
            :options="deviceOptions"
            placeholder="— 选择被控端 —"
          />
        </div>

        <span class="toolbar-badge">{{ streamingCount }} / {{ filteredDevices.length }} 在线</span>
        <button class="toolbar-btn-icon" @click="refreshDeviceList" title="刷新">
          <FluentIcons name="refresh" :size="16" />
        </button>
      </div>

      <div class="toolbar-right">
        <!-- 帧信息 -->
        <span v-if="selectedDevice" class="toolbar-info">
          <template v-if="latestFrame">
            {{ latestFrame.width }}×{{ latestFrame.height }}
            <span class="sep">|</span>
            {{ estimatedFps.toFixed(1) }} FPS
            <span class="sep">|</span>
            {{ framesReceived }} 帧
          </template>
          <span class="status-dot" :class="isStreaming ? 'dot-streaming' : 'dot-idle'"></span>
          {{ isStreaming ? '推流中' : '待命中' }}
        </span>

        <!-- 锁屏状态 + 控制 -->
        <span v-if="selectedDevice" class="toolbar-info">
          <span class="lock-indicator" :class="!!selectedDevice.isLocked ? 'is-locked' : 'is-unlocked'" :title="!!selectedDevice.isLocked ? '已锁屏' : '未锁屏'">
            <FluentIcons name="lock" :size="12" />
            {{ !!selectedDevice.isLocked ? '已锁' : '未锁' }}
          </span>
          <button
            v-if="canLock"
            class="toolbar-btn toolbar-btn--lock"
            @click="toggleLock"
            :disabled="pendingAction !== null"
          >
            <FluentIcons :name="!!selectedDevice.isLocked ? 'unlock' : 'lock'" :size="14" />
            {{ !!selectedDevice.isLocked ? '解锁' : '锁屏' }}
          </button>
        </span>

        <!-- 控制 -->
        <button
          v-if="selectedDevice && canStart"
          class="toolbar-btn"
          :class="{ 'is-pending': pendingAction === 'start' }"
          :disabled="pendingAction !== null"
          @click="startMonitor"
        >
          <FluentIcons name="play" :size="14" />
          {{ pendingAction === 'start' ? '发起中…' : '开始监控' }}
        </button>
        <button
          v-if="isStreaming && canStop"
          class="toolbar-btn toolbar-btn--danger"
          :class="{ 'is-pending': pendingAction === 'stop' }"
          :disabled="pendingAction !== null"
          @click="stopMonitor"
        >
          <FluentIcons name="stop" :size="14" />
          {{ pendingAction === 'stop' ? '停止中…' : '停止' }}
        </button>
        <button
          v-if="isStreaming && canAdjust"
          class="toolbar-btn"
          :class="{ 'is-pending': pendingAction === 'settings' }"
          :disabled="pendingAction !== null"
          @click="applySettings"
        >
          <FluentIcons name="save" :size="14" />
          {{ pendingAction === 'settings' ? '应用中…' : '应用参数' }}
        </button>

        <!-- 发送消息 -->
        <button v-if="selectedDevice && canSendMsg" class="toolbar-btn" @click="openSendMessageModal">
          <FluentIcons name="message" :size="14" />
          发送消息
        </button>

        <!-- 全屏 -->
        <button class="toolbar-btn-icon" @click="toggleFullscreen" :title="isFullscreen ? '退出全屏' : '全屏'">
          <FluentIcons :name="isFullscreen ? 'collapse' : 'expand'" :size="16" />
        </button>
      </div>
    </div>

    <!-- 参数设置行（可折叠） -->
    <div v-if="selectedDevice && showSettings" class="monitor-settings">
      <div class="settings-row">
        <div class="setting-item">
          <label>画质</label>
          <MonitorDropdown v-model="qualityPreset" :options="qualityOptions" placeholder="自定义" />
        </div>
        <div class="setting-item">
          <label>分辨率</label>
          <MonitorDropdown v-model="resolutionPreset" :options="resolutionOptions" placeholder="自定义" />
        </div>
        <div class="setting-item">
          <label>帧率</label>
          <MonitorDropdown v-model.number="params.fps" :options="fpsOptions" placeholder="10" />
        </div>
        <div class="setting-item">
          <label>显示器</label>
          <input v-model.number="params.monitorIndex" type="number" min="0" max="8" class="input-sm" />
        </div>
        <template v-if="!qualityPreset && !resolutionPreset">
          <div class="setting-item">
            <label>JPEG质量</label>
            <input v-model.number="params.jpegQuality" type="number" min="1" max="100" class="input-sm" />
          </div>
          <div class="setting-item">
            <label>最大宽度</label>
            <input v-model.number="params.maxWidth" type="number" min="0" max="7680" class="input-sm" />
          </div>
        </template>
      </div>
      <button class="settings-toggle" @click="showSettings = false">收起 ▲</button>
    </div>
    <div v-if="selectedDevice && !showSettings && canAdjust" class="settings-peek">
      <button class="settings-toggle" @click="showSettings = true">参数设置 ▼</button>
    </div>

    <!-- 主画面区域 -->
    <div class="monitor-stage">
      <!-- 未选择设备 -->
      <div v-if="!selectedDevice" class="stage-empty">
        <FluentIcons name="desktop" :size="80" class="empty-icon" />
        <p>在上方下拉框中选择被控端，开始屏幕监控</p>
      </div>

      <!-- 已选择设备 -->
      <template v-else>
        <img
          v-if="latestFrame"
          :src="frameUrl"
          class="stage-image"
          alt="实时屏幕画面"
        />
        <div v-else class="stage-waiting">
          <FluentIcons name="image" :size="56" class="empty-icon" />
          <p>{{ isStreaming ? '等待首帧画面…' : '点击「开始监控」启动推流' }}</p>
        </div>

        <!-- 设备错误提示 -->
        <div v-if="selectedDevice.lastError" class="stage-error">
          <FluentIcons name="error" :size="16" />
          {{ selectedDevice.lastError }}
        </div>
      </template>
    </div>

    <!-- 发送消息对话框 -->
    <Transition name="modal-overlay" appear>
      <div v-if="sendMessageVisible" class="modal-overlay" @click="closeSendMessageModal">
        <Transition name="modal-content" appear>
          <div v-if="sendMessageVisible" class="modal-content" @click.stop>
            <div class="modal-glass"></div>
            <div class="modal-refraction"></div>
            <div class="modal-header">
              <h3>发送消息到设备</h3>
              <button class="close-btn" @click="closeSendMessageModal">×</button>
            </div>
            <div class="modal-body">
              <div class="send-message-target">
                <FluentIcons name="computer" :size="16" class="target-icon" />
                <span class="target-name">{{ sendMessageDevice?.name }}</span>
                <span class="target-status" :class="sendMessageDevice?.status">{{ formatStatus(sendMessageDevice?.status) }}</span>
              </div>
              <div class="form-group">
                <label class="form-label">消息内容</label>
                <textarea
                  v-model="sendMessageText"
                  class="input-field message-textarea"
                  placeholder="请输入要发送的消息内容..."
                  rows="5"
                  maxlength="500"
                ></textarea>
                <div class="char-count">{{ sendMessageText.length }} / 500</div>
              </div>
              <div class="form-group">
                <label class="form-label">显示尺寸</label>
                <div class="option-row">
                  <label class="option-chip" :class="{ active: sendMessageSize === 'small' }">
                    <input type="radio" v-model="sendMessageSize" value="small" />
                    <span>小</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageSize === 'medium' }">
                    <input type="radio" v-model="sendMessageSize" value="medium" />
                    <span>中</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageSize === 'large' }">
                    <input type="radio" v-model="sendMessageSize" value="large" />
                    <span>大</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageSize === 'xlarge' }">
                    <input type="radio" v-model="sendMessageSize" value="xlarge" />
                    <span>超大（两倍）</span>
                  </label>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">文字大小</label>
                <div class="option-row">
                  <label class="option-chip" :class="{ active: sendMessageFontSize === 'small' }">
                    <input type="radio" v-model="sendMessageFontSize" value="small" />
                    <span>小</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageFontSize === 'medium' }">
                    <input type="radio" v-model="sendMessageFontSize" value="medium" />
                    <span>中</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageFontSize === 'large' }">
                    <input type="radio" v-model="sendMessageFontSize" value="large" />
                    <span>大</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageFontSize === 'xlarge' }">
                    <input type="radio" v-model="sendMessageFontSize" value="xlarge" />
                    <span>超大</span>
                  </label>
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">持续时间</label>
                <div class="option-row">
                  <label class="option-chip" :class="{ active: sendMessageDurationMode === 'auto' }">
                    <input type="radio" v-model="sendMessageDurationMode" value="auto" />
                    <span>自动</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageDurationMode === 'short' }">
                    <input type="radio" v-model="sendMessageDurationMode" value="short" />
                    <span>短 (3秒)</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageDurationMode === 'medium' }">
                    <input type="radio" v-model="sendMessageDurationMode" value="medium" />
                    <span>中 (6秒)</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageDurationMode === 'long' }">
                    <input type="radio" v-model="sendMessageDurationMode" value="long" />
                    <span>长 (10秒)</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageDurationMode === 'custom' }">
                    <input type="radio" v-model="sendMessageDurationMode" value="custom" />
                    <span>自定义</span>
                  </label>
                  <label class="option-chip" :class="{ active: sendMessageDurationMode === 'persistent' }">
                    <input type="radio" v-model="sendMessageDurationMode" value="persistent" />
                    <span>持久</span>
                  </label>
                </div>
                <div v-if="sendMessageDurationMode === 'custom'" class="custom-duration-input">
                  <input
                    type="number"
                    v-model.number="sendMessageCustomSeconds"
                    min="5"
                    max="60"
                    class="input-field custom-duration-field"
                  />
                  <span class="custom-duration-suffix">秒</span>
                </div>
                <div v-if="sendMessageDurationMode === 'persistent'" class="custom-duration-input persistent-hint">
                  <span>持久通知：不自动关闭，60 秒后用户可手动关闭</span>
                </div>
              </div>
              <div class="read-aloud-row">
                <div class="read-aloud-label">
                  <FluentIcons name="message" :size="18" class="read-aloud-icon" />
                  <div>
                    <div class="read-aloud-title">朗读消息</div>
                    <div class="read-aloud-desc">被控设备将调用 Windows 内置语音模块朗读此消息</div>
                  </div>
                </div>
                <CustomSwitch v-model="sendMessageReadAloud" />
              </div>
              <div class="read-aloud-row">
                <div class="read-aloud-label">
                  <FluentIcons name="lock" :size="18" class="read-aloud-icon" />
                  <div>
                    <div class="read-aloud-title">通知期间禁止关闭窗口</div>
                    <div class="read-aloud-desc">开启后被控端的关闭按钮将失效，到达持续时间或（持久模式下）60 秒后才可关闭</div>
                  </div>
                </div>
                <CustomSwitch v-model="sendMessageLockWindow" />
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" @click="closeSendMessageModal" :disabled="sendingMessage">取消</button>
              <button
                class="btn btn-primary"
                @click="confirmSendMessage"
                :disabled="sendingMessage || !sendMessageText.trim()"
              >
                <FluentIcons v-if="sendingMessage" name="sync" :size="16" class="spin-icon" />
                {{ sendingMessage ? '发送中...' : '发送' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onBeforeUnmount, watch } from 'vue'
import FluentIcons from '@/components/FluentIcons.vue'
import MonitorDropdown from '@/components/MonitorDropdown.vue'
import CustomSwitch from '@/components/CustomSwitch.vue'
import wsService from '@/utils/websocket'
import { notify } from '@/utils/notification'
import api from '@/api'
import { organizationAPI } from '@/api/organization'
import { usePermissions } from '@/composables/usePermissions'

const { hasActionPermission } = usePermissions()

const canStart = computed(() => hasActionPermission('screenMonitor', 'startMonitor'))
const canStop = computed(() => hasActionPermission('screenMonitor', 'stopMonitor'))
const canLock = computed(() => hasActionPermission('screenMonitor', 'remoteLock'))
const canSendMsg = computed(() => hasActionPermission('screenMonitor', 'sendMessage'))
const canAdjust = computed(() => hasActionPermission('screenMonitor', 'adjustSettings'))

// ===== 状态 =====
const devices = ref([])
const organizations = ref([])
const filterOrgId = ref('')
const selectedDeviceId = ref('')
const latestFrame = ref(null)
const framesReceived = ref(0)
const estimatedFps = ref(0)
const isStreaming = ref(false)
const isFullscreen = ref(false)
const showSettings = ref(false)
const pendingAction = ref(null) // 'start' | 'stop' | 'settings' | null

// 发送消息相关状态
const sendMessageVisible = ref(false)
const sendMessageDevice = ref(null)
const sendMessageText = ref('')
const sendMessageReadAloud = ref(false)
const sendMessageSize = ref('small')
const sendMessageFontSize = ref('medium')
const sendMessageDurationMode = ref('auto')
const sendMessageCustomSeconds = ref(10)
const sendMessageLockWindow = ref(false)
const sendingMessage = ref(false)

let lastFrameTs = 0

const params = reactive({
  fps: 10,
  jpegQuality: 60,
  maxWidth: 1280,
  monitorIndex: 0
})

const qualityPreset = ref('')
const resolutionPreset = ref('')

// ===== 计算属性 =====
const selectedDevice = computed(() =>
  devices.value.find(d => d.id === selectedDeviceId.value) || null
)

const filteredDevices = computed(() => {
  let list = devices.value.filter(d => d.status === 'online')
  if (filterOrgId.value) {
    list = list.filter(d => d.organizationId === filterOrgId.value)
  }
  return list
})

const streamingCount = computed(() => filteredDevices.value.filter(d => d.isStreaming).length)

const frameUrl = computed(() => {
  if (!latestFrame.value || !latestFrame.value.data) return ''
  return `data:image/${latestFrame.value.format || 'jpeg'};base64,${latestFrame.value.data}`
})

// ===== 下拉选项 =====
const orgOptions = computed(() =>
  organizations.value.map(o => ({ value: o.id, label: o.name, iconName: 'building' }))
)

const deviceOptions = computed(() =>
  filteredDevices.value.map(d => ({
    value: d.id,
    label: `${d.name || d.id} · ${d.ipAddress || '—'}${d.isStreaming ? ' [推流中]' : ''}`,
    iconName: d.isStreaming ? 'online' : 'computer'
  }))
)

const qualityOptions = [
  { value: '', label: '自定义' },
  { value: 'low', label: '低码率 · 流畅优先', iconName: 'speed' },
  { value: 'medium', label: '中等码率 · 均衡', iconName: 'network' },
  { value: 'high', label: '高码率 · 画质优先', iconName: 'eye' },
]

const resolutionOptions = [
  { value: '', label: '自定义' },
  { value: '720p', label: '720P · 1280px', iconName: 'image' },
  { value: '1080p', label: '1080P · 1920px', iconName: 'image' },
  { value: '2k', label: '2K · 2560px', iconName: 'image' },
  { value: '4k', label: '4K · 3840px', iconName: 'image' },
  { value: 'original', label: '原分辨率', iconName: 'image' },
]

const fpsOptions = [
  { value: 10, label: '10 FPS · 省带宽', iconName: 'speed' },
  { value: 15, label: '15 FPS · 流畅', iconName: 'speed' },
  { value: 30, label: '30 FPS · 实时', iconName: 'speed' },
]

// 挡位预设
const RESOLUTION_MAP = {
  '720p': 1280,
  '1080p': 1920,
  '2k': 2560,
  '4k': 3840,
  'original': 0
}
const QUALITY_MAP = {
  low: { jpegQuality: 50, maxWidth: 1280 },
  medium: { jpegQuality: 70, maxWidth: 1920 },
  high: { jpegQuality: 90, maxWidth: 0 }
}

// ===== 挡位 watcher =====
watch(qualityPreset, (val) => {
  const q = QUALITY_MAP[val]
  if (q) {
    params.jpegQuality = q.jpegQuality
    if (!resolutionPreset.value) params.maxWidth = q.maxWidth
  }
})

watch(resolutionPreset, (val) => {
  if (val && RESOLUTION_MAP[val] !== undefined) {
    params.maxWidth = RESOLUTION_MAP[val]
  }
})

// 组织筛选：切换组织时清空已选设备
watch(filterOrgId, () => {
  selectedDeviceId.value = ''
})

// 设备选择
watch(selectedDeviceId, (id) => {
  if (!id) return
  const d = selectedDevice.value
  if (!d) return
  latestFrame.value = null
  framesReceived.value = 0
  estimatedFps.value = 0
  isStreaming.value = !!d.isStreaming
  lastFrameTs = 0
})

// ===== 设备数据 =====
function findOrCreateDevice(payload) {
  const id = payload.deviceId
  let d = devices.value.find(x => x.id === id)
  if (!d) {
    d = {
      id,
      name: payload.deviceName || id,
      ipAddress: payload.ipAddress || '',
      organizationId: payload.organizationId || null,
      status: 'online',
      isStreaming: false,
      isLocked: false,
      lastError: null
    }
    devices.value.push(d)
  } else {
    if (payload.deviceName) d.name = payload.deviceName
    if (payload.ipAddress) d.ipAddress = payload.ipAddress
    if (payload.organizationId) d.organizationId = payload.organizationId
  }
  return d
}

// ===== API =====
async function refreshDeviceList() {
  try { wsService.requestDeviceList() } catch (e) { /* */ }

  // 加载组织
  try {
    const orgRes = await organizationAPI.getAll()
    organizations.value = Array.isArray(orgRes.data) ? orgRes.data : (orgRes.data?.organizations || [])
  } catch (e) {
    console.warn('[ScreenMonitor] 加载组织失败:', e)
  }

  // 加载设备
  try {
    const res = await api.get('/devices', { params: { limit: 500 } })
    const list = Array.isArray(res?.data?.devices) ? res.data.devices
      : Array.isArray(res?.data) ? res.data : []
    list.forEach(d => {
      const ex = devices.value.find(x => x.id === d.id)
      if (ex) {
        ex.name = d.name || ex.name
        ex.organizationId = d.organization_id || d.organizationId || ex.organizationId
        ex.ipAddress = d.ip_address || d.ipAddress || ex.ipAddress
        ex.status = d.status || ex.status
      } else {
        devices.value.push({
          id: d.id,
          name: d.name || d.id,
          ipAddress: d.ip_address || d.ipAddress || '',
          organizationId: d.organization_id || d.organizationId || null,
          status: d.status || 'online',
          isStreaming: false,
          isLocked: false,
          lastError: null
        })
      }
    })
  } catch (err) {
    console.warn('[ScreenMonitor] 加载设备失败:', err)
  }
}

// ===== 控制 =====
function startMonitor() {
  if (!selectedDevice.value) { notify.warning('请先选择被控端'); return }
  if (pendingAction.value) return
  pendingAction.value = 'start'
  const ok = wsService.startScreenMonitor(selectedDevice.value.id, {
    fps: params.fps, jpegQuality: params.jpegQuality,
    maxWidth: params.maxWidth, monitorIndex: params.monitorIndex
  })
  if (!ok) { pendingAction.value = null; notify.warning('发起失败，请检查连接') }
  // 5s 超时兜底
  setTimeout(() => { if (pendingAction.value === 'start') pendingAction.value = null }, 5000)
}
function stopMonitor() {
  if (!selectedDevice.value || pendingAction.value) return
  pendingAction.value = 'stop'
  const ok = wsService.stopScreenMonitor(selectedDevice.value.id)
  if (!ok) { pendingAction.value = null; notify.warning('停止失败，请检查连接') }
  setTimeout(() => { if (pendingAction.value === 'stop') pendingAction.value = null }, 5000)
}
function applySettings() {
  if (!selectedDevice.value || pendingAction.value) return
  pendingAction.value = 'settings'
  const ok = wsService.updateScreenMonitorSettings(selectedDevice.value.id, {
    fps: params.fps, jpegQuality: params.jpegQuality, maxWidth: params.maxWidth
  })
  if (!ok) { pendingAction.value = null; notify.warning('应用失败，请检查连接') }
  setTimeout(() => { if (pendingAction.value === 'settings') pendingAction.value = null }, 5000)
}

// ===== 全屏 =====
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  if (isFullscreen.value) {
    document.addEventListener('keydown', onEscKey)
  } else {
    document.removeEventListener('keydown', onEscKey)
  }
}
function onEscKey(e) {
  if (e.key === 'Escape') { isFullscreen.value = false; document.removeEventListener('keydown', onEscKey) }
}

// ===== 远程锁屏 =====
function toggleLock() {
  if (!selectedDevice.value || pendingAction.value) return
  pendingAction.value = 'lock'
  const locked = !!selectedDevice.value.isLocked
  const ok = locked
    ? wsService.remoteUnlock(selectedDevice.value.id)
    : wsService.remoteLock(selectedDevice.value.id)
  if (!ok) {
    pendingAction.value = null
    notify.warning('操作失败，请检查连接')
  }
  setTimeout(() => { if (pendingAction.value === 'lock') pendingAction.value = null }, 5000)
}

function onLockState(data) {
  if (!data || !data.deviceId) return
  const d = findOrCreateDevice(data)
  d.isLocked = !!data.isLocked
  if (selectedDevice.value && selectedDevice.value.id === d.id) {
    pendingAction.value = null
    notify.info(d.isLocked ? '设备已锁屏' : '设备已解锁')
  }
}

// ===== 发送消息功能 =====
const formatStatus = (status) => {
  const statusMap = { online: '在线', offline: '离线', logged_out: '已退出' }
  return statusMap[status] || status || '未知'
}

const openSendMessageModal = () => {
  const device = selectedDevice.value
  if (!device) return
  if (device.status !== 'online') {
    notify.warning('设备不在线，无法发送消息')
    return
  }
  sendMessageDevice.value = device
  sendMessageText.value = ''
  sendMessageReadAloud.value = false
  sendMessageSize.value = 'small'
  sendMessageFontSize.value = 'medium'
  sendMessageDurationMode.value = 'auto'
  sendMessageCustomSeconds.value = 10
  sendMessageLockWindow.value = false
  sendingMessage.value = false
  sendMessageVisible.value = true
}

const closeSendMessageModal = () => {
  if (sendingMessage.value) return
  sendMessageVisible.value = false
  sendMessageDevice.value = null
  sendMessageText.value = ''
  sendMessageReadAloud.value = false
  sendMessageSize.value = 'small'
  sendMessageFontSize.value = 'medium'
  sendMessageDurationMode.value = 'auto'
  sendMessageCustomSeconds.value = 10
  sendMessageLockWindow.value = false
}

const confirmSendMessage = () => {
  if (!sendMessageDevice.value) return
  const text = sendMessageText.value.trim()
  if (!text) {
    notify.warning('消息内容不能为空')
    return
  }

  sendingMessage.value = true
  const device = sendMessageDevice.value
  const readAloud = sendMessageReadAloud.value
  const size = sendMessageSize.value
  const fontSize = sendMessageFontSize.value
  const durationMode = sendMessageDurationMode.value
  const lockWindow = sendMessageLockWindow.value
  let customSeconds = 10
  if (durationMode === 'custom') {
    customSeconds = Math.max(5, Math.min(60, Number(sendMessageCustomSeconds.value) || 10))
  } else if (durationMode === 'short') {
    customSeconds = 3
  } else if (durationMode === 'medium') {
    customSeconds = 6
  } else if (durationMode === 'long') {
    customSeconds = 10
  } else if (durationMode === 'persistent') {
    customSeconds = 10
  }

  const sent = wsService.sendMessage(device.id, text, readAloud, {
    size,
    fontSize,
    durationMode,
    customDurationSeconds: customSeconds,
    lockWindow
  })
  if (!sent) {
    sendingMessage.value = false
    return
  }

  const onResult = (data) => {
    if (data.deviceId && data.deviceId !== device.id) return
    wsService.off('onMessageSent', onResult)
    sendingMessage.value = false

    if (data.success) {
      notify.success(`消息已发送到设备 "${device.name}"`)
      closeSendMessageModal()
    } else {
      notify.error(data.message || `发送到设备 "${device.name}" 失败`)
    }
  }
  wsService.on('onMessageSent', onResult)

  setTimeout(() => {
    if (sendingMessage.value) {
      wsService.off('onMessageSent', onResult)
      sendingMessage.value = false
      notify.warning('发送消息超时，请检查设备连接状态')
    }
  }, 10000)
}

// ===== WebSocket =====
function onFrame(data) {
  if (!data || !data.deviceId) return
  const d = findOrCreateDevice(data)
  if (selectedDevice.value && selectedDevice.value.id === d.id) {
    // 帧到达时自动修正状态（处理页面刷新后状态丢失）
    if (!isStreaming.value) { isStreaming.value = true; d.isStreaming = true }
    latestFrame.value = { data: data.data, width: data.width, height: data.height, format: data.format, timestamp: data.timestamp }
    const now = data.timestamp || Date.now()
    if (lastFrameTs > 0) {
      const delta = (now - lastFrameTs) / 1000
      if (delta > 0.0001) {
        const inst = 1.0 / delta
        estimatedFps.value = estimatedFps.value <= 0 ? inst : estimatedFps.value * 0.7 + inst * 0.3
      }
    }
    lastFrameTs = now
    framesReceived.value++
  }
}

function onStatus(data) {
  if (!data || !data.deviceId) return
  const d = findOrCreateDevice(data)
  d.isStreaming = !!data.isStreaming
  d.lastError = data.error || null
  if (selectedDevice.value && selectedDevice.value.id === d.id) {
    isStreaming.value = d.isStreaming
    if (!isStreaming.value) { latestFrame.value = null; framesReceived.value = 0 }
  }
}

function onDeviceStatusUpdate(data) {
  if (!data || !data.deviceId) return
  const d = findOrCreateDevice(data)
  if (data.status) d.status = data.status
  if (data.deviceName) d.name = data.deviceName
  if (data.organizationId) d.organizationId = data.organizationId
}

// ===== 生命周期 =====
onMounted(() => {
  wsService.on('onScreenMonitorFrame', onFrame)
  wsService.on('onScreenMonitorStatus', onStatus)
  wsService.on('onDeviceStatusUpdate', onDeviceStatusUpdate)
  wsService.on('onScreenMonitorStartAck', (data) => {
    pendingAction.value = null
    if (data?.success) {
      notify.success(`已开始监控 ${data.deviceId || ''}`)
    } else if (data?.message) {
      notify.error(data.message)
    }
  })
  wsService.on('onScreenMonitorStopAck', (data) => {
    pendingAction.value = null
    if (data?.success) {
      notify.info(`已停止监控`)
    } else if (data?.message) {
      notify.error(data.message)
    }
  })
  wsService.on('onScreenMonitorSettingsAck', (data) => {
    // 仅后端确认转发，不清 pending（等 settings_applied）
    if (data && data.message && !data.success) {
      pendingAction.value = null
      notify.error(data.message)
    }
  })
  wsService.on('onScreenMonitorSettingsApplied', (data) => {
    pendingAction.value = null
    if (data?.success) {
      notify.success(`参数已切换 · ${data.width || data.maxWidth}px · Q${data.jpegQuality} · ${data.fps}FPS`)
    }
  })
  wsService.on('onLockState', onLockState)
  refreshDeviceList()
  setTimeout(() => { try { wsService.requestDeviceList() } catch (e) { /* */ } }, 600)
})

onBeforeUnmount(() => {
  wsService.off('onScreenMonitorFrame', onFrame)
  wsService.off('onScreenMonitorStatus', onStatus)
  wsService.off('onDeviceStatusUpdate', onDeviceStatusUpdate)
  wsService.off('onLockState', onLockState)
  document.removeEventListener('keydown', onEscKey)
})
</script>

<style scoped>
.screen-monitor-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #111;
  position: relative;
}

/* 全屏模式 */
.is-fullscreen {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 9999;
  border-radius: 0;
}

/* 顶部工具栏 */
.monitor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
  flex-wrap: wrap;
  gap: 8px;
  z-index: 10;
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-icon { color: var(--fui-primary, #0078d4); }
.toolbar-title {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin-right: 12px;
}

.toolbar-select {
  padding: 6px 10px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #2a2a2a;
  color: #eee;
  font-size: 13px;
  outline: none;
  min-width: 140px;
}
.toolbar-select:focus { border-color: var(--fui-primary, #0078d4); }
.toolbar-select--device { min-width: 220px; }

.toolbar-dropdown-wrap { width: 180px; }
.toolbar-dropdown-wrap--device { width: 260px; }

.toolbar-badge {
  font-size: 11px;
  color: #888;
  white-space: nowrap;
}

.toolbar-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #aaa;
  font-family: 'Consolas', monospace;
}
.toolbar-info .sep { color: #555; }

.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
}
.dot-streaming { background: #4caf50; box-shadow: 0 0 6px #4caf50; animation: pulse 1s infinite; }
.dot-idle { background: #666; }

.lock-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}
.lock-indicator.is-locked { color: #f0a030; background: rgba(240, 160, 48, 0.12); }
.lock-indicator.is-unlocked { color: #4caf50; background: rgba(76, 175, 80, 0.1); }

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.toolbar-btn, .toolbar-btn-icon {
  padding: 6px 12px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #2a2a2a;
  color: #eee;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: background 0.15s, border-color 0.15s, opacity 0.15s;
  white-space: nowrap;
}
.toolbar-btn:hover:not(:disabled), .toolbar-btn-icon:hover:not(:disabled) { background: #3a3a3a; border-color: #555; }
.toolbar-btn:disabled, .toolbar-btn-icon:disabled { opacity: 0.5; cursor: not-allowed; }
.toolbar-btn-icon { padding: 6px 8px; }
.toolbar-btn--danger { color: #f44336; border-color: #f44336; }
.toolbar-btn--danger:hover:not(:disabled) { background: #f44336; color: #fff; }
.toolbar-btn--lock { border-color: #f0a030; color: #f0a030; }
.toolbar-btn--lock:hover:not(:disabled) { background: #f0a030; color: #111; }

/* 操作进行中 */
.toolbar-btn.is-pending {
  animation: btn-pulse 0.8s ease-in-out infinite;
  border-color: #0078d4;
  color: #0078d4;
}
@keyframes btn-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* 参数设置 */
.monitor-settings {
  padding: 8px 16px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
  z-index: 5;
}
.settings-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: flex-end;
}
.setting-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.setting-item label {
  font-size: 10px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.input-sm {
  padding: 5px 8px;
  border: 1px solid #444;
  border-radius: 3px;
  background: #2a2a2a;
  color: #eee;
  font-size: 12px;
  width: 90px;
  outline: none;
}
.input-sm:focus { border-color: var(--fui-primary, #0078d4); }

.settings-peek {
  padding: 2px 16px;
  background: #1a1a1a;
  flex-shrink: 0;
}
.settings-toggle {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 11px;
  padding: 2px 0;
}
.settings-toggle:hover { color: #ccc; }

/* 主画面 */
.monitor-stage {
  flex: 1;
  min-height: 0;
  background: #0a0a0a;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.stage-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
  filter: contrast(1) saturate(1);
   image-rendering: auto;
}

.stage-empty, .stage-waiting {
  text-align: center;
  color: #555;
}
.stage-empty p {
  margin-top: 16px;
  font-size: 14px;
}
.stage-waiting p {
  margin-top: 12px;
  font-size: 13px;
  color: #666;
}
.empty-icon { color: #333; }

.stage-error {
  position: absolute;
  bottom: 16px;
  left: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(244, 67, 54, 0.92);
  color: #fff;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
}

/* ========= 发送消息弹窗（与 Devices 保持一致） ========= */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-overlay-enter-active,
.modal-overlay-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-overlay-enter-from,
.modal-overlay-leave-to {
  opacity: 0;
}

.modal-content {
  position: relative;
  background: transparent;
  border-radius: 16px;
  overflow: hidden;
  max-width: 800px;
  width: 90%;
  max-height: 85vh;
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.2),
    0 8px 32px rgba(0, 0, 0, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.modal-glass {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(30, 30, 30, 0.85) !important;
  backdrop-filter: blur(24px) saturate(120%);
  -webkit-backdrop-filter: blur(24px) saturate(120%);
  z-index: 0;
  border-radius: 16px;
}

.modal-refraction {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(ellipse at 20% 20%, rgba(255, 255, 255, 0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(0, 120, 212, 0.12) 0%, transparent 50%) !important;
  z-index: 1;
  pointer-events: none;
  border-radius: 16px;
}

.modal-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 16px;
  padding: 2px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.2) 0%,
    rgba(255, 255, 255, 0.06) 50%,
    rgba(255, 255, 255, 0.03) 100%
  ) !important;
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  z-index: 4;
}

.modal-content-enter-active {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-content-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 1, 1);
}

.modal-content-enter-from {
  opacity: 0;
  transform: translateY(-30px) scale(0.9);
}

.modal-content-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.modal-header {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.05) 0%,
    transparent 100%
  );
}

.modal-header h3 {
  margin: 0;
  font-size: 1.125em;
  font-weight: 600;
  color: #eee;
}

.close-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #aaa;
  cursor: pointer;
  font-size: 1.25em;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #eee;
  transform: rotate(90deg);
}

.close-btn:active {
  transform: rotate(180deg) scale(0.9);
}

.modal-body {
  position: relative;
  z-index: 2;
  padding: 28px;
  max-height: calc(85vh - 120px);
  overflow-y: auto;
}

.modal-footer {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding: 0 28px 28px;
}

.send-message-target {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-bottom: 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 0.9em;
}

.send-message-target .target-icon {
  opacity: 0.7;
  flex-shrink: 0;
}

.send-message-target .target-name {
  font-weight: 600;
  color: #eee;
}

.send-message-target .target-status {
  margin-left: auto;
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 0.75em;
  font-weight: 600;
}

.send-message-target .target-status.online {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.25);
}

.send-message-target .target-status.offline {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.send-message-target .target-status.logged_out {
  background: rgba(156, 163, 175, 0.15);
  color: #6b7280;
  border: 1px solid rgba(156, 163, 175, 0.25);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.form-label {
  font-size: 0.8125em;
  font-weight: 600;
  color: #aaa;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.message-textarea {
  width: 100%;
  height: auto;
  min-height: 120px;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: #eee;
  font-size: 0.9375em;
  font-family: inherit;
  line-height: 1.5;
  resize: vertical;
  outline: none;
  transition: all 0.2s ease;
}

.message-textarea:focus {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(0, 120, 212, 0.5);
  box-shadow: 0 0 0 3px rgba(0, 120, 212, 0.1);
}

.message-textarea::placeholder {
  color: #777;
  opacity: 1;
}

.char-count {
  text-align: right;
  font-size: 0.75em;
  color: #aaa;
  opacity: 0.7;
}

.read-aloud-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.read-aloud-label {
  display: flex;
  align-items: center;
  gap: 12px;
}

.read-aloud-icon {
  color: #0078d4;
  opacity: 0.8;
  flex-shrink: 0;
}

.read-aloud-title {
  font-size: 0.9375em;
  font-weight: 600;
  color: #eee;
}

.read-aloud-desc {
  font-size: 0.75em;
  color: #aaa;
  margin-top: 2px;
}

.option-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.option-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  min-width: 60px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 0.875em;
  color: #aaa;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s;
}

.option-chip:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
}

.option-chip input[type="radio"] {
  display: none;
}

.option-chip.active {
  background: rgba(0, 120, 212, 0.15);
  border-color: var(--fui-primary, #0078d4);
  color: var(--fui-primary, #0078d4);
  font-weight: 600;
}

.custom-duration-input {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.custom-duration-input.persistent-hint {
  color: #aaa;
  font-size: 0.85em;
  padding: 8px 12px;
  background: rgba(252, 211, 77, 0.08);
  border: 1px dashed rgba(252, 211, 77, 0.35);
  border-radius: 6px;
}

.custom-duration-field {
  width: 100px;
  text-align: center;
}

.custom-duration-suffix {
  font-size: 0.875em;
  color: #aaa;
}

.modal-footer .btn {
  min-width: 100px;
  padding: 9px 22px;
  border-radius: 8px;
  font-size: 0.875em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
}

.modal-footer .btn-secondary {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.15);
  color: #eee;
}

.modal-footer .btn-secondary:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
}

.modal-footer .btn-primary {
  background: #0078d4;
  border-color: #0078d4;
  color: white;
}

.modal-footer .btn-primary:hover:not(:disabled) {
  background: #106ebe;
  border-color: #106ebe;
  box-shadow: 0 4px 12px rgba(0, 120, 212, 0.3);
}

.modal-footer .btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===== 响应式 - 移动端 (<= 768px) ===== */
@media (max-width: 768px) {
  .monitor-toolbar {
    padding: 8px 10px;
    gap: 6px;
  }

  .toolbar-left, .toolbar-right {
    flex-wrap: wrap;
    gap: 6px;
    width: 100%;
  }

  .toolbar-left {
    flex: 1;
    min-width: 0;
  }

  .toolbar-right {
    justify-content: flex-start;
  }

  .toolbar-title {
    font-size: 13px;
    margin-right: 4px;
    display: none;
  }

  .toolbar-dropdown-wrap {
    width: 140px;
  }

  .toolbar-dropdown-wrap--device {
    width: 180px;
  }

  .toolbar-badge {
    font-size: 10px;
  }

  .toolbar-info {
    font-size: 10px;
    flex-wrap: wrap;
  }

  .toolbar-btn, .toolbar-btn-icon {
    padding: 5px 8px;
    font-size: 11px;
    gap: 3px;
  }

  .toolbar-btn-icon {
    padding: 5px 6px;
  }

  /* 参数设置 */
  .monitor-settings {
    padding: 8px 10px;
  }

  .settings-row {
    gap: 8px;
  }

  .setting-item {
    flex: 1;
    min-width: 80px;
  }

  .input-sm {
    width: 100%;
    min-width: 60px;
    padding: 4px 6px;
    font-size: 11px;
  }

  .settings-peek {
    padding: 2px 10px;
  }

  /* 模态框 */
  .modal-content {
    width: 95%;
    max-width: 95%;
    max-height: 90vh;
    border-radius: 12px;
  }

  .modal-glass,
  .modal-refraction,
  .modal-content::before {
    border-radius: 12px;
  }

  .modal-header {
    padding: 16px 18px;
  }

  .modal-header h3 {
    font-size: 1em;
  }

  .modal-body {
    padding: 18px;
    max-height: calc(90vh - 110px);
  }

  .modal-footer {
    padding: 0 18px 18px;
    gap: 10px;
  }

  .modal-footer .btn {
    min-width: 80px;
    padding: 8px 16px;
    font-size: 0.8em;
  }

  .option-row {
    gap: 6px;
  }

  .option-chip {
    padding: 6px 10px;
    font-size: 0.75em;
    min-width: 50px;
  }

  .read-aloud-row {
    padding: 10px 12px;
    gap: 10px;
    flex-wrap: wrap;
  }

  .read-aloud-label {
    gap: 8px;
  }

  .read-aloud-title {
    font-size: 0.85em;
  }

  .read-aloud-desc {
    font-size: 0.7em;
  }

  /* 主画面 */
  .stage-empty p {
    font-size: 13px;
    padding: 0 20px;
  }

  .stage-waiting p {
    font-size: 12px;
  }

  .stage-error {
    bottom: 8px;
    left: 8px;
    right: 8px;
    padding: 8px 10px;
    font-size: 11px;
  }

  .send-message-target {
    padding: 8px 10px;
    font-size: 0.8em;
  }

  .form-group {
    margin-bottom: 14px;
  }

  .form-label {
    font-size: 0.7em;
  }

  .message-textarea {
    min-height: 100px;
    font-size: 0.85em;
  }
}

/* ===== 响应式 - 平板 (769px - 1024px) ===== */
@media (min-width: 769px) and (max-width: 1024px) {
  .toolbar-dropdown-wrap {
    width: 160px;
  }

  .toolbar-dropdown-wrap--device {
    width: 220px;
  }

  .modal-content {
    max-width: 700px;
  }
}
</style>

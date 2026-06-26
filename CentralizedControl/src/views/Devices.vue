<template>
  <div class="devices-page">
    <div class="page-header">
      <div class="page-title">
        <FluentIcons name="device" :size="28" class="page-icon" />
        <h2>设备管理</h2>
      </div>
      <div class="header-actions">
        <div class="search-box">
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="搜索设备" 
            class="input-field search-input"
          />
        </div>
        <div class="filter-group">
          <CustomDropdown
            v-model="filterStatus"
            :options="statusOptions"
            placeholder="所有状态"
          />
          <CustomDropdown
            v-model="filterOrg"
            :options="orgOptions"
            placeholder="所有组织"
          />
        </div>
      </div>
    </div>

    <div class="devices-list">
      <div v-if="filteredDevices.length === 0" class="empty-state">
        <FluentIcons name="device" :size="48" class="empty-icon" />
        <p>暂无设备数据</p>
      </div>
      <div v-else class="devices-table">
        <table>
          <thead>
            <tr>
              <th>
                <div class="th-content">
                  <FluentIcons name="computer" :size="18" class="th-icon" />
                  设备名称
                </div>
              </th>
              <th>
                <div class="th-content">
                  <FluentIcons name="globe" :size="18" class="th-icon" />
                  IP 地址
                </div>
              </th>
              <th>
                <div class="th-content">
                  <FluentIcons name="building" :size="18" class="th-icon" />
                  所属组织
                </div>
              </th>
              <th>
                <div class="th-content">
                  <FluentIcons name="check_circle" :size="18" class="th-icon" />
                  状态
                </div>
              </th>
              <th>
                <div class="th-content">
                  <FluentIcons name="clock" :size="18" class="th-icon" />
                  最后在线
                </div>
              </th>
              <th>
                <div class="th-content">
                  <FluentIcons name="settings" :size="18" class="th-icon" />
                  操作
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="device in filteredDevices" :key="device.id">
              <td>
                <div class="device-name">
                  <FluentIcons name="computer" :size="18" class="device-icon" />
                  {{ device.name }}
                </div>
              </td>
              <td>{{ device.ipAddress }}</td>
              <td>
                <div class="org-name">
                  <FluentIcons name="building" :size="16" class="org-icon" />
                  {{ getOrganizationName(device.organizationId) }}
                </div>
              </td>
              <td>
                <div class="status-badge" :class="device.status">
                  <span class="status-dot" :class="device.status"></span>
                  {{ formatStatus(device.status) }}
                </div>
              </td>
              <td class="time-cell">{{ device.status === 'online' ? '刚刚' : formatDate(device.lastHeartbeat || device.lastSeen, true) }}</td>
              <td>
                <div class="action-buttons">
                  <button class="button-icon" @click="viewDevice(device)" title="查看详情" :disabled="!devicePermissions.viewDetail">
                    <FluentIcons name="view" :size="18" />
                  </button>
                  <button
                    class="button-icon message-btn"
                    @click="openSendMessageModal(device)"
                    title="发送消息"
                    :disabled="device.status !== 'online'"
                  >
                    <FluentIcons name="message" :size="18" />
                  </button>
                  <button class="button-icon delete-btn" @click="showDeleteConfirm(device)" title="删除设备" :disabled="!devicePermissions.delete">
                    <FluentIcons name="delete" :size="18" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 设备详情模态框 -->
    <Transition name="modal-overlay" appear>
      <div v-if="selectedDevice" class="modal-overlay" @click="closeDeviceModal">
        <Transition name="modal-content" appear>
          <div v-if="selectedDevice" class="modal-content modal-content-large" @click.stop>
            <div class="modal-glass"></div>
            <div class="modal-refraction"></div>
            <div class="modal-header">
              <h3>设备详情</h3>
              <button class="close-btn" @click="closeDeviceModal">×</button>
            </div>
            
            <div class="modal-tabs">
              <button 
                class="tab-btn" 
                :class="{ active: activeTab === 'info' }" 
                @click="activeTab = 'info'"
              >
                <FluentIcons name="info" :size="16" />
                基本信息
              </button>
              <button 
                v-if="devicePermissions.viewSoftware"
                class="tab-btn" 
                :class="{ active: activeTab === 'software' }" 
                @click="activeTab = 'software'; loadDeviceSoftware()"
              >
                <FluentIcons name="app_folder" :size="16" />
                已安装软件
                <span v-if="softwareCount > 0" class="software-count">{{ softwareCount }}</span>
              </button>
            </div>
            
            <div class="modal-body">
              <div v-if="activeTab === 'info'" class="device-detail">
                <div class="detail-section">
                  <h4 class="section-title">基本信息</h4>
                  <div class="detail-row">
                    <strong>设备名称:</strong>
                    <span>{{ selectedDevice.name }}</span>
                  </div>
                  <div class="detail-row">
                    <strong>设备 ID:</strong>
                    <span class="mono-font">{{ selectedDevice.id }}</span>
                  </div>
                  <div class="detail-row">
                    <strong>IP 地址:</strong>
                    <span>{{ selectedDevice.ipAddress }}</span>
                  </div>
                  <div class="detail-row">
                    <strong>MAC 地址:</strong>
                    <span class="mono-font">{{ selectedDevice.macAddress || 'N/A' }}</span>
                  </div>
                </div>

                <div class="detail-section">
                  <h4 class="section-title">系统信息</h4>
                  <div class="detail-row">
                    <strong>操作系统:</strong>
                    <span>{{ selectedDevice.osVersion || 'N/A' }}</span>
                  </div>
                  <div class="detail-row">
                    <strong>软件版本:</strong>
                    <span>{{ selectedDevice.appVersion || '1.0.0' }}</span>
                  </div>
                  <div class="detail-row">
                    <strong>.NET 版本:</strong>
                    <span>{{ selectedDevice.dotnetVersion || 'N/A' }}</span>
                  </div>
                </div>

                <div class="detail-section">
                  <h4 class="section-title">组织信息</h4>
                  <div class="detail-row">
                    <strong>所属组织:</strong>
                    <span>{{ getOrganizationName(selectedDevice.organizationId) }}</span>
                  </div>
                  <div class="detail-row">
                    <strong>组织 ID:</strong>
                    <span class="mono-font">{{ selectedDevice.organizationId || 'N/A' }}</span>
                  </div>
                  <div class="detail-row">
                    <strong>注册时间:</strong>
                    <span>{{ formatDate(selectedDevice.registeredAt, false) }}</span>
                  </div>
                </div>

                <div class="detail-section">
                  <h4 class="section-title">登记信息</h4>
                  <div class="detail-row">
                    <strong>联系电话:</strong>
                    <span>{{ selectedDevice.contactPhone || '未登记' }}</span>
                  </div>
                  <div class="detail-row">
                    <strong>班级:</strong>
                    <span>{{ selectedDevice.className || '未登记' }}</span>
                  </div>
                  <div class="detail-row">
                    <strong>负责人:</strong>
                    <span>{{ selectedDevice.personInCharge || '未登记' }}</span>
                  </div>
                </div>

                <div class="detail-section">
                  <h4 class="section-title">运行状态</h4>
                  <div class="detail-row">
                    <strong>状态:</strong>
                    <span class="status-badge" :class="selectedDevice.status">
                      {{ formatStatus(selectedDevice.status) }}
                    </span>
                  </div>
                  <div class="detail-row">
                    <strong>最后在线:</strong>
                    <span>{{ selectedDevice.status === 'online' ? '刚刚' : formatDate(selectedDevice.lastHeartbeat || selectedDevice.lastSeen, true) }}</span>
                  </div>
                  <div class="detail-row" v-if="selectedDevice.exitTime">
                    <strong>退出时间:</strong>
                    <span>{{ formatDate(selectedDevice.exitTime, false) }}</span>
                  </div>
                  <div class="detail-row" v-if="selectedDevice.offlineReason">
                    <strong>{{ selectedDevice.status === 'logged_out' ? '退出原因' : '离线原因' }}:</strong>
                    <span>{{ formatOfflineReason(selectedDevice.offlineReason) }}</span>
                  </div>
                  <div class="detail-row" v-if="selectedDevice.cpuUsage !== undefined">
                    <strong>CPU 使用率:</strong>
                    <span class="metric-value">{{ selectedDevice.cpuUsage }}%</span>
                  </div>
                  <div class="detail-row" v-if="selectedDevice.memoryUsage !== undefined">
                    <strong>内存使用率:</strong>
                    <span class="metric-value">{{ selectedDevice.memoryUsage }}%</span>
                  </div>
                  <div class="detail-row" v-if="selectedDevice.diskUsage !== undefined">
                    <strong>磁盘使用率:</strong>
                    <span class="metric-value">{{ selectedDevice.diskUsage }}%</span>
                  </div>
                </div>
              </div>
              
              <div v-if="activeTab === 'software'" class="software-tab">
                <div class="software-header">
                  <div class="software-search">
                    <input 
                      v-model="softwareSearchQuery" 
                      type="text" 
                      placeholder="搜索软件名称或发布者..." 
                      class="input-field"
                      @input="filterSoftware"
                    />
                  </div>
                  <div class="software-filters">
                    <label class="filter-checkbox">
                      <input type="checkbox" v-model="includeSystemSoftware" @change="loadDeviceSoftware" />
                      <span>显示系统软件</span>
                    </label>
                  </div>
                </div>
                
                <div v-if="loadingSoftware" class="software-loading">
                  <FluentIcons name="sync" :size="24" class="spin-icon" />
                  <span>正在加载软件列表...</span>
                </div>
                
                <div v-else-if="filteredSoftware.length === 0" class="software-empty">
                  <FluentIcons name="app_folder" :size="48" class="empty-icon" />
                  <p v-if="softwareSearchQuery">未找到匹配的软件</p>
                  <p v-else>暂无软件数据</p>
                </div>
                
                <div v-else class="software-list">
                  <div class="software-count-info">
                    共 {{ filteredSoftware.length }} 个软件
                    <span v-if="softwareSearchQuery">（搜索结果）</span>
                  </div>
                  <table class="software-table">
                    <thead>
                      <tr>
                        <th>软件名称</th>
                        <th>发布者</th>
                        <th>版本</th>
                        <th>安装日期</th>
                        <th>大小</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="sw in filteredSoftware" :key="sw.id">
                        <td class="software-name">
                          <FluentIcons :name="sw.isSystemSoftware ? 'system' : 'app_default'" :size="16" class="software-icon" />
                          {{ sw.name }}
                        </td>
                        <td>{{ sw.publisher || '-' }}</td>
                        <td>{{ sw.version || '-' }}</td>
                        <td>{{ sw.installDate || '-' }}</td>
                        <td>{{ sw.estimatedSize || '-' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>

    <!-- 确认删除对话框 -->
    <ConfirmDialog
      v-model:visible="showConfirmDialog"
      :title="'确认删除'"
      :message="confirmMessage"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />

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
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
import { useRoute } from 'vue-router'
import { deviceAPI, organizationAPI } from '@/api/organization'
import CustomDropdown from '@/components/CustomDropdown.vue'
import CustomSwitch from '@/components/CustomSwitch.vue'
import FluentIcons from '@/components/FluentIcons.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { notify } from '@/utils/notification'
import { getPermissions } from '@/stores/permissions'
import wsService from '@/utils/websocket'

const route = useRoute()
const devices = ref([])
const organizations = ref([])
const selectedDeviceId = ref(null)
const searchQuery = ref('')
const filterStatus = ref('')
const filterOrg = ref('')
const showConfirmDialog = ref(false)
const confirmMessage = ref('')
const currentDevice = ref(null)

const activeTab = ref('info')
const softwareList = ref([])
const filteredSoftware = ref([])
const softwareSearchQuery = ref('')
const includeSystemSoftware = ref(false)
const loadingSoftware = ref(false)
const softwareCount = ref(0)

// 发送消息相关状态
const sendMessageVisible = ref(false)
const sendMessageDevice = ref(null)
const sendMessageText = ref('')
const sendMessageReadAloud = ref(false)
const sendMessageSize = ref('small')         // small | medium | large | xlarge（默认 small）
const sendMessageFontSize = ref('medium')    // small | medium | large | xlarge（默认 medium）
const sendMessageDurationMode = ref('auto')  // auto | short | medium | long | custom | persistent
const sendMessageCustomSeconds = ref(10)     // 自定义秒数
const sendMessageLockWindow = ref(false)     // 是否在通知时段禁止关闭窗口
const sendingMessage = ref(false)

// WebSocket 设备状态更新回调
const handleDeviceStatusUpdate = (data) => {
  console.log('[Devices] 收到设备状态更新:', data)
  const deviceIndex = devices.value.findIndex(d => d.id === data.deviceId)
  if (deviceIndex !== -1) {
    // 更新设备状态
    const device = devices.value[deviceIndex]
    devices.value[deviceIndex] = {
      ...device,
      status: data.status,
      lastHeartbeat: data.timestamp || new Date().toISOString(),
      lastSeen: data.timestamp || new Date().toISOString(),
      cpuUsage: data.cpu_usage ?? device.cpuUsage,
      memoryUsage: data.memory_usage ?? device.memoryUsage,
      diskUsage: data.disk_usage ?? device.diskUsage,
      deviceName: data.deviceName ?? device.name,
      ipAddress: data.ip_address ?? device.ipAddress
    }
  } else if (data.status === 'online') {
    // 新设备上线，刷新列表
    loadDevices()
  }
}

const currentUserRole = computed(() => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      const userData = JSON.parse(userStr)
      return userData.role || 'user'
    } catch {
      return 'user'
    }
  }
  return 'user'
})

const devicePermissions = computed(() => {
  const permissions = getPermissions()
  const role = currentUserRole.value
  
  if (role === 'super_admin') {
    return {
      viewDetail: true,
      viewSoftware: true,
      delete: true
    }
  }
  
  const actionPerms = permissions?.[role]?.actionPermissions?.device
  if (!actionPerms) {
    return {
      viewDetail: false,
      viewSoftware: false,
      delete: false
    }
  }
  
  return {
    viewDetail: actionPerms.viewDetail ?? false,
    viewSoftware: actionPerms.viewSoftware ?? false,
    delete: actionPerms.delete ?? false
  }
})

const selectedDevice = computed(() => {
  if (!selectedDeviceId.value) return null
  return devices.value.find(device => device.id === selectedDeviceId.value) || null
})

const filteredDevices = computed(() => {
  let result = devices.value
  
  // 按组织过滤
  if (filterOrg.value) {
    result = result.filter(d => d.organizationId === filterOrg.value)
  }
  
  // 按状态过滤
  if (filterStatus.value) {
    result = result.filter(d => d.status === filterStatus.value)
  }
  
  // 按关键字搜索
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(d => 
      d.name.toLowerCase().includes(query) || 
      d.ipAddress.toLowerCase().includes(query) ||
      (d.macAddress && d.macAddress.toLowerCase().includes(query))
    )
  }
  
  return result
})

const formatStatus = (status) => {
  const statusMap = {
    online: '在线',
    offline: '离线',
    logged_out: '已退出'
  }
  return statusMap[status] || '未知'
}

const formatOfflineReason = (reason) => {
  const reasonMap = {
    heartbeat_timeout: '心跳超时',
    ws_timeout: 'WebSocket超时',
    ws_disconnect: 'WebSocket断开',
    network_error: '网络错误',
    user_logout: '用户主动退出',
    shutdown: '正常关机',
    unknown: '未知原因'
  }
  return reasonMap[reason] || reason
}

const statusOptions = computed(() => [
  { value: '', label: '所有状态', iconName: 'list' },
  { value: 'online', label: '在线', iconName: 'check_circle' },
  { value: 'offline', label: '离线', iconName: 'error' },
  { value: 'logged_out', label: '已退出', iconName: 'logout' }
])

const orgOptions = computed(() => [
  { value: '', label: '所有组织', iconName: 'building' },
  ...organizations.value.map(org => ({
    value: org.id,
    label: org.name,
    iconName: 'group'
  }))
])

const loadDevices = async () => {
  try {
    const data = await deviceAPI.getAll()
    devices.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('Failed to load devices:', error)
    devices.value = []
  }
}

const loadOrganizations = async () => {
  try {
    const data = await organizationAPI.getAll()
    organizations.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('Failed to load organizations:', error)
    organizations.value = []
  }
}

const getOrganizationName = (orgId) => {
  const org = organizations.value.find(o => o.id === orgId)
  return org ? org.name : '未知组织'
}

const viewDevice = (device) => {
  selectedDeviceId.value = device.id
  activeTab.value = 'info'
  softwareList.value = []
  filteredSoftware.value = []
  softwareSearchQuery.value = ''
  softwareCount.value = 0
}

const closeDeviceModal = () => {
  selectedDeviceId.value = null
  softwareList.value = []
  filteredSoftware.value = []
  softwareCount.value = 0
}

const loadDeviceSoftware = async () => {
  if (!selectedDeviceId.value || loadingSoftware.value) return
  
  loadingSoftware.value = true
  try {
    const data = await deviceAPI.getSoftware(selectedDeviceId.value, {
      includeSystem: includeSystemSoftware.value
    })
    softwareList.value = data.software || []
    softwareCount.value = data.totalCount || 0
    filterSoftware()
  } catch (error) {
    console.error('Failed to load device software:', error)
    softwareList.value = []
    filteredSoftware.value = []
    softwareCount.value = 0
  } finally {
    loadingSoftware.value = false
  }
}

const filterSoftware = () => {
  if (!softwareSearchQuery.value.trim()) {
    filteredSoftware.value = softwareList.value
    return
  }
  
  const query = softwareSearchQuery.value.toLowerCase()
  filteredSoftware.value = softwareList.value.filter(sw => 
    sw.name?.toLowerCase().includes(query) ||
    sw.publisher?.toLowerCase().includes(query)
  )
}

const showDeleteConfirm = (device) => {
  currentDevice.value = device
  confirmMessage.value = `确定要删除设备 "${device.name}" 吗？`
  showConfirmDialog.value = true
}

const confirmDelete = async () => {
  if (currentDevice.value) {
    try {
      await deviceAPI.delete(currentDevice.value.id)
      await loadDevices()
      // 如果删除的是当前查看的设备，关闭模态框
      if (selectedDeviceId.value === currentDevice.value.id) {
        selectedDeviceId.value = null
      }
      notify.success('设备删除成功！')
    } catch (error) {
      console.error('删除设备失败:', error)
      notify.error('删除设备失败，请重试')
    } finally {
      showConfirmDialog.value = false
      currentDevice.value = null
    }
  }
}

const cancelDelete = () => {
  showConfirmDialog.value = false
  currentDevice.value = null
}

// ===== 发送消息功能 =====
const openSendMessageModal = (device) => {
  if (device.status !== 'online') {
    notify.warning('设备不在线，无法发送消息')
    return
  }
  sendMessageDevice.value = device
  sendMessageText.value = ''
  sendMessageReadAloud.value = false
  sendMessageSize.value = 'small'         // 默认小
  sendMessageFontSize.value = 'medium'    // 默认中
  sendMessageDurationMode.value = 'auto'  // 默认自动
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
    // 持久模式：customDurationSeconds 在后端不再使用，但仍传递一个合法值
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

  // 监听一次性的发送结果
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

  // 超时兜底：10 秒未收到结果
  setTimeout(() => {
    if (sendingMessage.value) {
      wsService.off('onMessageSent', onResult)
      sendingMessage.value = false
      notify.warning('发送消息超时，请检查设备连接状态')
    }
  }, 10000)
}

const formatDate = (date, showSeconds = false) => {
  if (!date) return '从未在线'
  const d = new Date(date)
  const now = new Date()
  const diff = now - d
  
  // 小于 1 分钟
  if (diff < 60000) {
    return showSeconds ? `${Math.floor(diff / 1000)}秒前` : '刚刚'
  }
  // 小于 1 小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }
  // 小于 24 小时
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  // 超过 24 小时，显示具体日期
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 定时刷新定时器
let refreshTimer = null

onMounted(async () => {
  if (route?.query?.org) {
    filterOrg.value = parseInt(route.query.org)
  }
  await Promise.all([loadDevices(), loadOrganizations()])
  
  // 订阅 WebSocket 设备状态更新
  wsService.on('onDeviceStatusUpdate', handleDeviceStatusUpdate)
  
  // 每 1 秒自动刷新设备列表
  refreshTimer = setInterval(() => {
    loadDevices()
  }, 1000)
})

onUnmounted(() => {
  // 移除 WebSocket 回调
  wsService.off('onDeviceStatusUpdate', handleDeviceStatusUpdate)
  
  // 清除定时器
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.devices-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.05);
  min-height: 100vh;
  animation: pageFadeIn 0.5s ease-out;
}

@keyframes pageFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 4px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-icon {
  color: var(--fui-text);
  opacity: 0.9;
}

.page-title h2 {
  margin: 0;
  font-size: 1.25em;
  font-weight: 600;
  color: var(--fui-text);
  letter-spacing: -0.3px;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-box {
  display: flex;
  align-items: center;
}

.search-input {
  width: 280px;
  height: 40px;
  padding: 0 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1.5px solid rgba(255, 255, 255, 0.15);
  border-radius: 40px;
  color: var(--fui-text);
  font-size: 1em;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}

.search-input:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.2);
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.08);
}

.search-input::placeholder {
  color: var(--fui-text-secondary);
  opacity: 0.6;
}

.filter-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-group :deep(.custom-dropdown) {
  min-width: 180px;
  flex: 1;
}

.input-field {
  height: 36px;
  padding: 0 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.5);
  border-radius: 8px;
  color: var(--fui-text);
  font-size: 1em;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}

.input-field:hover {
  background: rgba(0, 0, 0, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
}

.input-field:focus {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.06);
}

.input-field::placeholder {
  color: var(--fui-text-secondary);
  opacity: 0.6;
}

select.input-field {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 36px;
  cursor: pointer;
  border-radius: 8px !important;
}

.devices-list {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  overflow: hidden;
  animation: containerFadeIn 0.4s ease-out 0.1s both;
  padding: 3px; 
  font-size: var(--fui-font-size-base);
}

@keyframes containerFadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--fui-text-secondary);
  gap: 16px;
}

.empty-icon {
  opacity: 0.4;
}

.empty-state p {
  margin: 0;
  font-size: 0.9375em;
  opacity: 0.8;
}

.devices-table {
  width: 100%;
  overflow-x: auto;
}

table {
  width: 100%;
  border-spacing: 0;
  border: 1.5px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  overflow: hidden;
}

thead th {
  text-align: left;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: var(--fui-text);
  font-weight: 600;
  font-size: 0.75em;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.th-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.th-icon {
  opacity: 0.7;
}

tbody td {
  padding: 12px 16px;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--fui-text);
  font-size: 0.875em;
  vertical-align: middle;
}

tbody td:last-child {
  border-right: none;
}

tbody tr {
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0;
  animation: rowFadeIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  border-radius: 4px;
}

tbody tr:nth-child(even) {
  background: rgba(255, 255, 255, 0.02); /* 斑马纹效果 */
}

/* 最后一行圆角 */
tbody tr:last-child td:first-child {
  border-bottom-left-radius: 6px;
}

tbody tr:last-child td:last-child {
  border-bottom-right-radius: 6px;
}

tbody tr:nth-child(1) { animation-delay: 0.03s; }
tbody tr:nth-child(2) { animation-delay: 0.06s; }
tbody tr:nth-child(3) { animation-delay: 0.09s; }
tbody tr:nth-child(4) { animation-delay: 0.12s; }
tbody tr:nth-child(5) { animation-delay: 0.15s; }

@keyframes rowFadeIn {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

tbody tr:hover {
  background-color: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  transform: translateX(4px) scale(1.01);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.device-name {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
}

.device-icon {
  opacity: 0.7;
  flex-shrink: 0;
}

.org-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.org-icon {
  opacity: 0.6;
  flex-shrink: 0;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 99px;
  font-size: 0.75em;
  font-weight: 600;
  letter-spacing: 0.2px;
  transition: all 0.2s ease;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  position: relative;
}

.status-dot.online {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.15), 0 0 8px rgba(16, 185, 129, 0.4);
}

.status-dot.offline {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.15), 0 0 8px rgba(239, 68, 68, 0.4);
}

.status-dot.logged_out {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  box-shadow: 0 0 0 2px rgba(156, 163, 175, 0.15), 0 0 8px rgba(156, 163, 175, 0.3);
}

.status-badge.online {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.08) 100%);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.status-badge.offline {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(220, 38, 38, 0.08) 100%);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.status-badge.logged_out {
  background: linear-gradient(135deg, rgba(156, 163, 175, 0.12) 0%, rgba(107, 114, 128, 0.08) 100%);
  color: #6b7280;
  border: 1px solid rgba(156, 163, 175, 0.2);
}

.time-cell {
  color: var(--fui-text-secondary);
  font-size: 0.8125em;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.button-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: var(--fui-text);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.button-icon:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.button-icon.delete-btn {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.2);
}

.button-icon.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.2);
}

.button-icon.message-btn {
  color: #0078d4;
  border-color: rgba(0, 120, 212, 0.2);
}

.button-icon.message-btn:hover {
  background: rgba(0, 120, 212, 0.1);
  border-color: rgba(0, 120, 212, 0.3);
  box-shadow: 0 2px 8px rgba(0, 120, 212, 0.2);
}

.button-icon:active {
  transform: scale(0.98);
}

.button-icon svg {
  width: 18px;
  height: 18px;
}

/* 模态框样式 */
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
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(24px) saturate(120%);
  -webkit-backdrop-filter: blur(24px) saturate(120%);
  z-index: 0;
  border-radius: 16px;
}

[data-theme='dark'] .modal-glass {
  background: rgba(40, 40, 40, 0.15);
}

.modal-refraction {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(255, 255, 255, 0.3) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(0, 120, 212, 0.1) 0%, transparent 50%);
  z-index: 1;
  pointer-events: none;
  border-radius: 16px;
}

[data-theme='dark'] .modal-refraction {
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(0, 120, 212, 0.15) 0%, transparent 50%);
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
    rgba(255, 255, 255, 0.8) 0%,
    rgba(255, 255, 255, 0.2) 50%,
    rgba(255, 255, 255, 0.1) 100%
  );
  -webkit-mask: 
    linear-gradient(#fff 0 0) content-box, 
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  z-index: 4;
}

[data-theme='dark'] .modal-content::before {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.3) 0%,
    rgba(255, 255, 255, 0.1) 50%,
    rgba(255, 255, 255, 0.05) 100%
  );
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

@keyframes modalShimmer {
  0% {
    left: -100%;
  }
  50%, 100% {
    left: 100%;
  }
}

.modal-header {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.5) 0%,
    transparent 100%
  );
}

[data-theme='dark'] .modal-header {
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
  color: var(--fui-text);
}

.close-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--fui-text-secondary);
  cursor: pointer;
  font-size: 1.25em;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--fui-text);
  transform: rotate(90deg);
}

[data-theme='dark'] .close-btn:hover {
  background: rgba(255, 255, 255, 0.15);
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

.device-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  margin: 0 0 4px 0;
  font-size: 0.8125em;
  font-weight: 600;
  color: var(--fui-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row strong {
  color: var(--fui-text-secondary);
  font-weight: 500;
  font-size: 0.875em;
}

.detail-row span {
  color: var(--fui-text);
  font-size: 0.875em;
}

.mono-font {
  font-family: 'LINE Seed KR', 'Clear Sans', 'HarmonyOS Sans TC', 'Segoe UI', 'Consolas', monospace;
  font-size: 0.8125em;
}

.metric-value {
  font-weight: 600;
  color: var(--fui-text);
}

.modal-content-large {
  max-width: 1000px;
}

.modal-tabs {
  position: relative;
  z-index: 2;
  display: flex;
  gap: 4px;
  padding: 0 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--fui-text-secondary);
  font-size: 0.875em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: var(--fui-text);
  background: rgba(255, 255, 255, 0.05);
}

.tab-btn.active {
  color: var(--fui-text);
  border-bottom-color: var(--fui-accent, #0078d4);
}

.software-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  font-size: 0.75em;
  font-weight: 600;
}

.software-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.software-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.software-search {
  flex: 1;
  min-width: 200px;
}

.software-search .input-field {
  width: 100%;
  height: 36px;
  padding: 0 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--fui-text);
  font-size: 0.875em;
  outline: none;
  transition: all 0.2s ease;
}

.software-search .input-field:focus {
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.06);
}

.software-filters {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.875em;
  color: var(--fui-text-secondary);
}

.filter-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--fui-accent, #0078d4);
}

.software-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 12px;
  color: var(--fui-text-secondary);
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.software-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--fui-text-secondary);
  gap: 12px;
}

.software-empty .empty-icon {
  opacity: 0.4;
}

.software-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.software-count-info {
  font-size: 0.8125em;
  color: var(--fui-text-secondary);
}

.software-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9375em;
}

.software-table thead th {
  text-align: left;
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--fui-text-secondary);
  font-weight: 600;
  font-size: 0.8125em;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.software-table tbody td {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: var(--fui-text);
  font-size: 0.9375em;
}

.software-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.03);
}

.software-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 0.9375em;
}

.software-icon {
  opacity: 0.6;
  flex-shrink: 0;
}

/* 移动端响应式 */
@media (max-width: 1024px) {
  .devices-page {
    padding: 16px;
    gap: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .header-actions {
    flex-direction: column;
    width: 100%;
    gap: 10px;
  }

  .search-box {
    width: 100%;
  }

  .search-input {
    width: 100%;
  }

  .filter-group {
    flex-direction: column;
    width: 100%;
  }

  .filter-group :deep(.custom-dropdown) {
    width: 100%;
    min-width: auto;
  }

  .devices-list {
    overflow-x: auto;
  }

  table {
    font-size: 0.8125em;
  }

  thead th,
  tbody td {
    padding: 10px 12px;
  }
}

@media (max-width: 768px) {
  .devices-page {
    padding: 12px;
  }

  .page-title h2 {
    font-size: 1.125em;
  }

  .devices-table {
    overflow-x: scroll;
    -webkit-overflow-scrolling: touch;
  }

  .status-badge {
    padding: 4px 8px;
    font-size: 0.6875em;
  }

  .status-dot {
    width: 5px;
    height: 5px;
  }

  .button-icon {
    width: 30px;
    height: 30px;
  }

  .button-icon svg {
    width: 16px;
    height: 16px;
  }

  .modal-content {
    width: 95%;
    max-height: 90vh;
  }

  .modal-header {
    padding: 16px 20px;
  }

  .modal-body {
    padding: 20px;
  }

  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .detail-row strong {
    font-size: 0.8125em;
  }

  .detail-row span {
    font-size: 0.8125em;
    text-align: left;
    max-width: 100%;
    word-break: break-word;
  }
}

@media (max-width: 480px) {
  .devices-page {
    padding: 8px;
  }

  .page-title h2 {
    font-size: 1em;
  }

  .input-field {
    font-size: 0.8125em;
  }

  thead th {
    font-size: 0.6875em;
    padding: 8px 10px;
  }

  tbody td {
    font-size: 0.75em;
    padding: 8px 10px;
  }

  .device-name {
    font-size: 0.8125em;
  }

  .th-icon {
    width: 14px;
    height: 14px;
  }
}

/* ===== 发送消息对话框 ===== */
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
  color: var(--fui-text);
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
  color: var(--fui-text-secondary);
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
  color: var(--fui-text);
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
  color: var(--fui-text-secondary);
  opacity: 0.6;
}

.char-count {
  text-align: right;
  font-size: 0.75em;
  color: var(--fui-text-secondary);
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
  color: var(--fui-text);
}

.read-aloud-desc {
  font-size: 0.75em;
  color: var(--fui-text-secondary);
  margin-top: 2px;
}

/* 尺寸/时长选项芯片 */
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
  color: var(--fui-text-secondary);
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
  color: var(--fui-text-secondary);
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
  color: var(--fui-text-secondary);
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
  color: var(--fui-text);
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

</style>

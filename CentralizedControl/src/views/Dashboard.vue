<template>
  <div class="dashboard">
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">
          <div class="icon-glow"></div>
          <FluentIcons name="organization" :size="28" />
        </div>
        <div class="stat-info">
          <h3 class="count-up">{{ animatedStats.organizations }}</h3>
          <p>组织数量</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <div class="icon-glow"></div>
          <FluentIcons name="device" :size="28" />
        </div>
        <div class="stat-info">
          <h3 class="count-up">{{ animatedStats.devices }}</h3>
          <p>设备数量</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <div class="icon-glow"></div>
          <FluentIcons name="online" :size="28" />
        </div>
        <div class="stat-info">
          <h3 class="count-up">{{ animatedStats.onlineDevices }}</h3>
          <p>在线设备</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">
          <div class="icon-glow"></div>
          <FluentIcons name="security" :size="28" />
        </div>
        <div class="stat-info">
          <h3 class="count-up">{{ animatedStats.securityPolicies }}</h3>
          <p>安全策略</p>
        </div>
      </div>
    </div>

    <div class="recent-activity card">
      <h2 class="section-title">
        <span class="title-glow"></span>
        最近活动
      </h2>
      <div v-if="hasActivityPermission" class="activity-list">
        <div v-for="activity in recentActivities" :key="activity.id" class="activity-item" @click="showActivityDetail(activity)">
          <div class="activity-icon-wrapper">
            <FluentIcons :name="activity.icon" :size="16" />
          </div>
          <div class="activity-time">{{ activity.time }}</div>
          <div class="activity-content">{{ activity.content }}</div>
          <div class="activity-arrow">
            <FluentIcons name="chevron_right" :size="16" />
          </div>
        </div>
        <div v-if="recentActivities.length === 0" class="empty-activity">
          <FluentIcons name="security" :size="48" />
          <p>暂无活动记录</p>
        </div>
      </div>
      <div v-else class="no-permission-activity">
        <FluentIcons name="shield" :size="48" class="no-permission-icon" />
        <p>你没有权限查看</p>
      </div>
    </div>

    <Transition name="modal-overlay" appear>
      <div v-if="selectedActivity" class="modal-overlay" @click="closeActivityDetail">
        <Transition name="modal-content" appear>
          <div v-if="selectedActivity" class="modal-content" @click.stop>
            <div class="modal-glass"></div>
            <div class="modal-refraction"></div>
            <div class="modal-header">
              <h3>活动详情</h3>
              <button class="close-btn" @click="closeActivityDetail">×</button>
            </div>
            <div class="modal-body">
              <div class="detail-row">
                <strong>操作类型:</strong>
                <span>{{ selectedActivity.actionType }}</span>
              </div>
              <div class="detail-row">
                <strong>操作分类:</strong>
                <span>{{ getCategoryLabel(selectedActivity.category) }}</span>
              </div>
              <div class="detail-row">
                <strong>操作人:</strong>
                <span>{{ selectedActivity.accountUsername || '系统' }}</span>
              </div>
              <div class="detail-row">
                <strong>操作时间:</strong>
                <span>{{ selectedActivity.fullTime }}</span>
              </div>
              <div class="detail-row">
                <strong>IP地址:</strong>
                <span>{{ selectedActivity.ipAddress || '未知' }}</span>
              </div>
              <div class="detail-row full-width">
                <strong>操作描述:</strong>
                <span>{{ selectedActivity.content }}</span>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch, computed } from 'vue'
import { onActivated } from 'vue'
import { organizationAPI, deviceAPI } from '@/api/organization'
import { activityLogAPI } from '@/api/activityLog'
import FluentIcons from '@/components/FluentIcons.vue'
import { usePermissions } from '@/composables/usePermissions'
import { refreshPermissions } from '@/stores/permissions'

const { hasActionPermission } = usePermissions()
const hasActivityPermission = computed(() => hasActionPermission('systemLogs', 'view'))

const stats = ref({
  organizations: 0,
  devices: 0,
  onlineDevices: 0,
  securityPolicies: 0
})

const animatedStats = reactive({
  organizations: 0,
  devices: 0,
  onlineDevices: 0,
  securityPolicies: 0
})

const recentActivities = ref([])
const selectedActivity = ref(null)

let refreshInterval = null
let animationFrameId = null

const formatFullTime = (dateString) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '未知时间'
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`
}

const getCategoryLabel = (category) => {
  const labelMap = {
    'auth': '认证',
    'device': '设备',
    'organization': '组织',
    'account': '账号'
  }
  return labelMap[category] || category
}

const getActionTypeLabel = (type) => {
  const labelMap = {
    'login': '登录',
    'logout': '退出',
    'register': '注册',
    'create': '创建',
    'update': '更新',
    'delete': '删除'
  }
  return labelMap[type] || type
}

const formatActivityTime = (dateString) => {
  if (!dateString) return '未知时间'
  
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '未知时间'
  
  const now = new Date()
  const diffMs = now - date
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffSecs < 10) return '刚刚'
  if (diffMins < 1) return `${diffSecs}秒前`
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const getActivityIcon = (category) => {
  const iconMap = {
    'auth': 'security',
    'device': 'device',
    'organization': 'organization',
    'account': 'organization'
  }
  return iconMap[category] || 'security'
}

const loadActivities = async () => {
  if (!hasActivityPermission.value) {
    recentActivities.value = []
    return
  }
  
  try {
    const response = await activityLogAPI.getRecent(20)
    const logs = response.logs || response || []
    const logsArray = Array.isArray(logs) ? logs : []
    recentActivities.value = logsArray.slice(0, 20).map(log => ({
      id: log.id,
      time: formatActivityTime(log.createdAt),
      fullTime: formatFullTime(log.createdAt),
      content: log.description,
      category: log.actionCategory,
      actionType: getActionTypeLabel(log.actionType),
      accountUsername: log.accountUsername,
      ipAddress: log.ipAddress,
      icon: getActivityIcon(log.actionCategory)
    }))
  } catch (error) {
    console.error('Failed to load activity logs:', error)
    recentActivities.value = []
  }
}

const showActivityDetail = (activity) => {
  selectedActivity.value = activity
}

const closeActivityDetail = () => {
  selectedActivity.value = null
}

const animateValue = (start, end, duration, onUpdate) => {
  const startTime = performance.now()
  
  const animate = (currentTime) => {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    
    const easeOutQuart = 1 - Math.pow(1 - progress, 4)
    const currentValue = Math.floor(start + (end - start) * easeOutQuart)
    
    onUpdate(currentValue)
    
    if (progress < 1) {
      animationFrameId = requestAnimationFrame(animate)
    }
  }
  
  animationFrameId = requestAnimationFrame(animate)
}

const animateStats = (newStats) => {
  Object.keys(newStats).forEach(key => {
    const startValue = animatedStats[key]
    const endValue = newStats[key]
    
    if (startValue !== endValue) {
      animateValue(startValue, endValue, 1200, (value) => {
        animatedStats[key] = value
      })
    }
  })
}

const loadStats = async () => {
  try {
    const [orgs, devices] = await Promise.all([
      organizationAPI.getAll(),
      deviceAPI.getAll()
    ])
    const newStats = {
      organizations: orgs.length || 0,
      devices: devices.length || 0,
      onlineDevices: devices.filter(d => d.status === 'online').length || 0,
      securityPolicies: 0
    }
    
    animateStats(newStats)
  } catch (error) {
    console.error('Failed to load stats:', error)
    animateStats({
      organizations: 0,
      devices: 0,
      onlineDevices: 0,
      securityPolicies: 0
    })
  }
}

const startAutoRefresh = () => {
  if (refreshInterval) return
  refreshInterval = setInterval(async () => {
    await loadStats()
    await loadActivities()
  }, 2000)
}

const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
    animationFrameId = null
  }
}

onMounted(async () => {
  await loadStats()
  await loadActivities()
  startAutoRefresh()
})

onActivated(async () => {
  await refreshPermissions()
  await loadStats()
  await loadActivities()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: pageFadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: var(--fui-font-size-base);
}

@keyframes pageFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.stat-card {
  animation: cardFadeIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  animation-fill-mode: both;
}

.stat-card:nth-child(1) { animation-delay: 0.1s; }
.stat-card:nth-child(2) { animation-delay: 0.2s; }
.stat-card:nth-child(3) { animation-delay: 0.3s; }
.stat-card:nth-child(4) { animation-delay: 0.4s; }

@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.stat-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--fui-radius);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0.9;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  transition: left 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover::before {
  left: 100%;
}

.stat-card:hover {
  transform: translateY(-8px) scale(1.02);
  opacity: 1;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2), 0 0 20px rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
}

.stat-icon {
  font-size: 40px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: visible;
}

.icon-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(255, 255, 255, 0.4) 0%,
    transparent 70%
  );
  opacity: 0;
  animation: glowPulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes glowPulse {
  0%, 100% {
    transform: translate(-50%, -50%) scale(0.8);
    opacity: 0;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.5);
    opacity: 0.6;
  }
}

.stat-card:hover .stat-icon {
  transform: scale(1.15);
  background: rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15), 0 0 16px rgba(255, 255, 255, 0.3);
}

.stat-card:hover .icon-glow {
  animation: glowPulseIntense 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes glowPulseIntense {
  0%, 100% {
    transform: translate(-50%, -50%) scale(0.8);
    opacity: 0;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.8);
    opacity: 0.8;
  }
}

.stat-info h3 {
  font-size: 2.25em;
  font-weight: 700;
  color: var(--fui-text);
  margin: 0 0 4px 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.count-up {
  animation: numberPop 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes numberPop {
  0% {
    transform: scale(0.9);
    opacity: 0.7;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.stat-card:hover .stat-info h3 {
  transform: scale(1.05);
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
}

.stat-info p {
  font-size: 0.94em;
  color: var(--fui-text-secondary);
  margin: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.stat-card:hover .stat-info p {
  color: var(--fui-text);
  letter-spacing: 0.3px;
}

.recent-activity {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--fui-radius);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 24px;
  animation: containerFadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  animation-delay: 0.5s;
  animation-fill-mode: both;
  position: relative;
  overflow: hidden;
  font-size: var(--fui-font-size-base);
}

.recent-activity::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: shimmer 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@keyframes containerFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-title {
  font-size: 1.5em;
  font-weight: 700;
  margin-bottom: 20px;
  color: var(--fui-text);
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.title-glow {
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.2));
  border-radius: 50%;
  animation: titleGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.5);
}

@keyframes titleGlow {
  0%, 100% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.3);
    opacity: 1;
    box-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
  }
}

.recent-activity h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--fui-text);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

.no-permission-activity {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 12px;
}

.no-permission-activity p {
  color: var(--fui-text-secondary);
  font-size: 0.9rem;
  margin: 0;
}

.no-permission-icon {
  color: var(--fui-text-secondary);
  opacity: 0.4;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0;
  transform: translateX(-20px);
  animation: activityFadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  animation-fill-mode: both;
  position: relative;
}

.activity-item:nth-child(1) { animation-delay: 0.6s; }
.activity-item:nth-child(2) { animation-delay: 0.7s; }
.activity-item:nth-child(3) { animation-delay: 0.8s; }
.activity-item:nth-child(4) { animation-delay: 0.9s; }

.activity-icon-wrapper {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  flex-shrink: 0;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.activity-item:hover .activity-icon-wrapper {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.empty-activity {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  color: var(--fui-text-secondary);
  opacity: 0.6;
}

.activity-arrow {
  margin-left: auto;
  color: var(--fui-text-secondary);
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.activity-item:hover .activity-arrow {
  opacity: 1;
  transform: translateX(4px);
}

.activity-item {
  cursor: pointer;
}

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
  max-width: 600px;
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
  padding: 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  max-height: calc(85vh - 80px);
}

.detail-row {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 12px;
  align-items: start;
}

.detail-row.full-width {
  grid-template-columns: 1fr;
}

.detail-row strong {
  font-size: 13px;
  font-weight: 600;
  color: var(--fui-text-secondary);
  padding-top: 8px;
}

.detail-row span {
  font-size: 14px;
  color: var(--fui-text);
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  word-break: break-word;
}

[data-theme='dark'] .detail-row span {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
}

.empty-activity p {
  margin-top: 16px;
  font-size: 0.94em;
}

@keyframes activityFadeIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 0.8;
    transform: translateX(0);
  }
}

.activity-item:hover {
  background: rgba(255, 255, 255, 0.05);
  padding-left: 16px;
  padding-right: 16px;
  padding-top: 16px;
  padding-bottom: 16px;
  border-radius: 8px;
  opacity: 1;
  transform: translateX(8px);
  border-bottom-color: transparent;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.activity-time {
  font-size: 0.81em;
  color: var(--fui-text-secondary);
  flex-shrink: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.activity-content {
  font-size: 0.94em;
  color: var(--fui-text);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.activity-item:hover .activity-time {
  color: var(--fui-text);
  letter-spacing: 0.2px;
}

.activity-item:hover .activity-content {
  font-weight: 500;
  letter-spacing: 0.2px;
}
</style>

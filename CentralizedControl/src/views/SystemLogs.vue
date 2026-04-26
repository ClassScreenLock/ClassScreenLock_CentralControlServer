<template>
  <div class="system-logs-container">
    <div v-if="!hasViewPermission" class="no-permission-container">
      <FluentIcons name="shield" :size="64" class="no-permission-icon" />
      <h3>你没有权限查看</h3>
      <p>请联系管理员获取系统日志查看权限</p>
    </div>

    <template v-else>
      <div class="logs-header">
        <div class="filters">
          <div class="filter-group">
            <label>操作分类</label>
            <CustomDropdown
              v-model="filters.category"
              :options="categoryOptions"
              placeholder="全部"
            />
          </div>
          <div class="filter-group">
            <label>操作类型</label>
            <CustomDropdown
              v-model="filters.actionType"
              :options="actionTypeOptions"
              placeholder="全部"
            />
          </div>
          <div class="filter-group search-group">
            <label>搜索</label>
            <div v-if="hasSearchPermission" class="search-input-wrapper">
              <FluentIcons name="search" :size="16" class="search-icon" />
              <input
                v-model="filters.keyword"
                @input="handleSearchInput"
                placeholder="搜索操作人或描述..."
                class="input-field search-input"
              />
            </div>
            <div v-else class="search-input-wrapper disabled">
              <FluentIcons name="search" :size="16" class="search-icon" />
              <input
                disabled
                placeholder="你没有搜索权限"
                class="input-field search-input"
              />
            </div>
          </div>
          <div class="filter-actions">
            <button class="btn btn-primary" @click="loadLogs" :disabled="loading">
              <FluentIcons name="refresh" :size="16" />
              <span>刷新</span>
            </button>
            <button v-if="hasClearAllPermission" class="btn btn-danger" @click="confirmClearAll" :disabled="loading || total === 0">
              <FluentIcons name="delete" :size="16" />
              <span>清空日志</span>
            </button>
          </div>
        </div>
      </div>

      <div class="logs-table-container">
        <table class="logs-table">
          <thead>
            <tr>
              <th v-if="hasBatchDeletePermission" class="checkbox-col">
                <input type="checkbox" v-model="selectAll" @change="handleSelectAll" />
              </th>
              <th>操作时间</th>
              <th>操作类型</th>
              <th>操作分类</th>
              <th>操作人</th>
              <th>IP地址</th>
              <th>操作描述</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.id" class="log-row">
              <td v-if="hasBatchDeletePermission" class="checkbox-col">
                <input type="checkbox" :checked="selectedLogs.includes(log.id)" @change="toggleSelect(log.id)" />
              </td>
              <td>{{ formatTime(log.createdAt) }}</td>
              <td>
                <span class="action-badge" :class="log.actionType">
                  {{ getActionTypeLabel(log.actionType) }}
                </span>
              </td>
              <td>{{ getCategoryLabel(log.actionCategory) }}</td>
              <td>{{ log.accountUsername || '系统' }}</td>
              <td>{{ log.ipAddress || '未知' }}</td>
              <td class="description-cell" :title="log.description">{{ log.description }}</td>
              <td class="actions-col">
                <button class="icon-btn" @click="showDetail(log)" title="查看详情">
                  <FluentIcons name="view" :size="16" />
                </button>
                <button v-if="hasDeleteSinglePermission" class="icon-btn delete-icon" @click="confirmDeleteLog(log)" title="删除日志">
                  <FluentIcons name="delete" :size="16" />
                </button>
              </td>
            </tr>
            <tr v-if="logs.length === 0 && !loading">
              <td :colspan="hasBatchDeletePermission ? 8 : 7" class="empty-state">暂无日志记录</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination" v-if="totalPages > 1">
        <button class="btn btn-outline" @click="goToPage(currentPage - 1)" :disabled="currentPage === 1">
          <FluentIcons name="arrow_up" :size="16" />
          上一页
        </button>
        <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页 (共 {{ total }} 条)</span>
        <button class="btn btn-outline" @click="goToPage(currentPage + 1)" :disabled="currentPage === totalPages">
          下一页
          <FluentIcons name="arrow_down" :size="16" />
        </button>
      </div>

      <div v-if="hasBatchDeletePermission && selectedLogs.length > 0" class="batch-actions">
        <span class="selected-count">已选择 {{ selectedLogs.length }} 条</span>
        <button class="btn btn-danger" @click="confirmBatchDelete">
          <FluentIcons name="delete" :size="16" />
          批量删除
        </button>
      </div>

      <Transition name="modal-overlay" appear>
        <div v-if="selectedLog" class="modal-overlay" @click="closeDetail">
          <Transition name="modal-content" appear>
            <div v-if="selectedLog" class="modal-content" @click.stop>
              <div class="modal-glass"></div>
              <div class="modal-refraction"></div>
              <div class="modal-header">
                <h3>日志详情</h3>
                <button class="close-btn" @click="closeDetail">×</button>
              </div>
              <div class="modal-body">
                <div class="detail-row">
                  <strong>操作类型:</strong>
                  <span>{{ getActionTypeLabel(selectedLog.actionType) }}</span>
                </div>
                <div class="detail-row">
                  <strong>操作分类:</strong>
                  <span>{{ getCategoryLabel(selectedLog.actionCategory) }}</span>
                </div>
                <div class="detail-row">
                  <strong>操作人:</strong>
                  <span>{{ selectedLog.accountUsername || '系统' }}</span>
                </div>
                <div class="detail-row">
                  <strong>操作时间:</strong>
                  <span>{{ formatFullTime(selectedLog.createdAt) }}</span>
                </div>
                <div class="detail-row">
                  <strong>IP地址:</strong>
                  <span>{{ selectedLog.ipAddress || '未知' }}</span>
                </div>
                <div class="detail-row" v-if="selectedLog.userAgent">
                  <strong>User Agent:</strong>
                  <span class="mono-font">{{ selectedLog.userAgent }}</span>
                </div>
                <div class="detail-row full-width">
                  <strong>操作描述:</strong>
                  <span>{{ selectedLog.description }}</span>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>

      <Transition name="modal-overlay" appear>
        <div v-if="showDeleteConfirm" class="modal-overlay" @click="cancelDelete">
          <Transition name="modal-content" appear>
            <div v-if="showDeleteConfirm" class="modal-content confirm-modal" @click.stop>
              <div class="modal-glass"></div>
              <div class="modal-refraction"></div>
              <div class="modal-header">
                <div class="modal-title-row">
                  <FluentIcons name="warning" :size="24" class="warning-icon" />
                  <h3>确认删除</h3>
                </div>
                <button class="close-btn" @click="cancelDelete">×</button>
              </div>
              <div class="modal-body confirm-body">
                <p>{{ deleteMessage }}</p>
              </div>
              <div class="modal-footer">
                <button class="btn btn-outline" @click="cancelDelete">取消</button>
                <button class="btn btn-danger" @click="executeDelete">删除</button>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { onActivated } from 'vue'
import { activityLogAPI } from '@/api/activityLog'
import FluentIcons from '@/components/FluentIcons.vue'
import CustomDropdown from '@/components/CustomDropdown.vue'
import { notify } from '@/utils/notification'
import { usePermissions } from '@/composables/usePermissions'
import { refreshPermissions } from '@/stores/permissions'

const { hasActionPermission } = usePermissions()

const hasViewPermission = computed(() => hasActionPermission('systemLogs', 'view'))
const hasSearchPermission = computed(() => hasActionPermission('systemLogs', 'search'))
const hasDeleteSinglePermission = computed(() => hasActionPermission('systemLogs', 'deleteSingle'))
const hasBatchDeletePermission = computed(() => hasActionPermission('systemLogs', 'batchDelete'))
const hasClearAllPermission = computed(() => hasActionPermission('systemLogs', 'clearAll'))

const logs = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filters = ref({
  category: '',
  actionType: '',
  keyword: ''
})
const selectedLog = ref(null)
const selectedLogs = ref([])
const selectAll = ref(false)
const showDeleteConfirm = ref(false)
const deleteAction = ref(null)
const deleteMessage = ref('')
let searchTimeout = null

const categoryOptions = [
  { value: '', label: '全部' },
  { value: 'auth', label: '认证' },
  { value: 'device', label: '设备' },
  { value: 'organization', label: '组织' },
  { value: 'account', label: '账号' }
]

const actionTypeOptions = [
  { value: '', label: '全部' },
  { value: 'login', label: '登录' },
  { value: 'logout', label: '退出' },
  { value: 'register', label: '注册' },
  { value: 'create', label: '创建' },
  { value: 'update', label: '更新' },
  { value: 'delete', label: '删除' }
]

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

watch(() => filters.value.category, () => {
  currentPage.value = 1
  loadLogs()
})

watch(() => filters.value.actionType, () => {
  currentPage.value = 1
  loadLogs()
})

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

const formatTime = (dateString) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '未知时间'
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}:${String(date.getSeconds()).padStart(2, '0')}`
}

const formatFullTime = (dateString) => {
  return formatTime(dateString)
}

const handleSearchInput = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadLogs()
  }, 300)
}

const loadLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value
    }
    if (filters.value.category) {
      params.category = filters.value.category
    }
    if (filters.value.actionType) {
      params.actionType = filters.value.actionType
    }
    if (filters.value.keyword) {
      params.keyword = filters.value.keyword
    }
    const response = await activityLogAPI.getAll(params)
    logs.value = response.logs || []
    total.value = response.total || 0
    selectedLogs.value = []
    selectAll.value = false
  } catch (error) {
    console.error('Failed to load logs:', error)
    notify.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadLogs()
  }
}

const handleSelectAll = () => {
  if (selectAll.value) {
    selectedLogs.value = logs.value.map(log => log.id)
  } else {
    selectedLogs.value = []
  }
}

const toggleSelect = (logId) => {
  const index = selectedLogs.value.indexOf(logId)
  if (index > -1) {
    selectedLogs.value.splice(index, 1)
  } else {
    selectedLogs.value.push(logId)
  }
  selectAll.value = selectedLogs.value.length === logs.value.length && logs.value.length > 0
}

const showDetail = (log) => {
  selectedLog.value = log
}

const closeDetail = () => {
  selectedLog.value = null
}

const confirmDeleteLog = (log) => {
  deleteAction.value = { type: 'single', id: log.id }
  deleteMessage.value = `确定要删除这条日志记录吗？此操作不可恢复。`
  showDeleteConfirm.value = true
}

const confirmBatchDelete = () => {
  deleteAction.value = { type: 'batch', ids: [...selectedLogs.value] }
  deleteMessage.value = `确定要删除选中的 ${selectedLogs.value.length} 条日志记录吗？此操作不可恢复。`
  showDeleteConfirm.value = true
}

const confirmClearAll = () => {
  deleteAction.value = { type: 'all' }
  deleteMessage.value = `确定要清空所有 ${total.value} 条日志记录吗？此操作不可恢复。`
  showDeleteConfirm.value = true
}

const cancelDelete = () => {
  showDeleteConfirm.value = false
  deleteAction.value = null
}

const executeDelete = async () => {
  try {
    if (deleteAction.value.type === 'single') {
      await activityLogAPI.delete(deleteAction.value.id)
      notify.success('日志已删除')
    } else if (deleteAction.value.type === 'batch') {
      await activityLogAPI.batchDelete(deleteAction.value.ids)
      notify.success(`已删除 ${deleteAction.value.ids.length} 条日志`)
    } else if (deleteAction.value.type === 'all') {
      await activityLogAPI.clearAll()
      notify.success('所有日志已清空')
    }
    loadLogs()
  } catch (error) {
    console.error('Failed to delete logs:', error)
    notify.error('删除日志失败')
  } finally {
    showDeleteConfirm.value = false
    deleteAction.value = null
  }
}

onMounted(() => {
  loadLogs()
})

onActivated(async () => {
  await refreshPermissions()
  loadLogs()
})
</script>

<style scoped>
.system-logs-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
}

.no-permission-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  background: var(--fui-surface);
  border-radius: 12px;
  padding: 40px;
  border: 1px solid var(--fui-border);
}

.no-permission-icon {
  color: var(--fui-text-secondary);
  opacity: 0.4;
}

.no-permission-container h3 {
  font-size: 1.2rem;
  color: var(--fui-text);
  margin: 0;
}

.no-permission-container p {
  font-size: 0.9rem;
  color: var(--fui-text-secondary);
  margin: 0;
}

.logs-header {
  background: var(--fui-surface);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--fui-border);
}

.filters {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.filter-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--fui-text-secondary);
}

.search-group {
  flex: 1;
  min-width: 200px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: var(--fui-text-secondary);
  pointer-events: none;
  z-index: 1;
}

.search-input {
  padding-left: 36px;
  height: 36px;
  padding: 0 14px 0 36px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.5);
  border-radius: 8px;
  color: var(--fui-text);
  font-size: 1em;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  outline: none;
}

.search-input:hover {
  background: rgba(0, 0, 0, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
}

.search-input:focus {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(0, 0, 0, 0.2);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.06);
}

.search-input::placeholder {
  color: var(--fui-text-secondary);
  opacity: 0.6;
}

[data-theme="dark"] .search-input {
  background: rgba(40, 40, 40, 0.4);
  border-color: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
}

[data-theme="dark"] .search-input:hover {
  background: rgba(50, 50, 50, 0.5);
  border-color: rgba(255, 255, 255, 0.25);
}

[data-theme="dark"] .search-input:focus {
  background: rgba(60, 60, 60, 0.6);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.08);
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--fui-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--fui-primary-dark, #006cbd);
}

.btn-outline {
  background: var(--fui-background);
  border: 1px solid var(--fui-border);
  color: var(--fui-text);
}

.btn-outline:hover:not(:disabled) {
  background: var(--fui-primary);
  color: white;
  border-color: var(--fui-primary);
}

.btn-danger {
  background: transparent;
  color: var(--error-fill-default, #e81123);
  border: 1px solid var(--error-stroke-default, #e81123);
}

.btn-danger:hover:not(:disabled) {
  background: var(--error-fill-default, #e81123);
  color: white;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.logs-table-container {
  flex: 1;
  overflow: auto;
  background: var(--fui-surface);
  border-radius: 12px;
  border: 1px solid var(--fui-border);
}

.logs-table {
  width: 100%;
  border-collapse: collapse;
}

.logs-table thead {
  position: sticky;
  top: 0;
  background: var(--fui-surface);
  z-index: 1;
}

.logs-table th {
  padding: 14px 16px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  color: var(--fui-text-secondary);
  border-bottom: 2px solid var(--fui-border);
  white-space: nowrap;
}

.logs-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--fui-border-light);
  font-size: 14px;
  color: var(--fui-text);
}

.checkbox-col {
  width: 40px;
  text-align: center;
}

.checkbox-col input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--fui-primary);
}

.log-row:hover {
  background: var(--fui-background-hover);
}

.action-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.action-badge.login {
  background: rgba(0, 120, 212, 0.1);
  color: #0078d4;
}

.action-badge.logout {
  background: rgba(107, 107, 107, 0.1);
  color: #6b6b6b;
}

.action-badge.register {
  background: rgba(16, 124, 16, 0.1);
  color: #107c10;
}

.action-badge.create {
  background: rgba(0, 120, 212, 0.1);
  color: #0078d4;
}

.action-badge.update {
  background: rgba(255, 185, 0, 0.1);
  color: #b8860b;
}

.action-badge.delete {
  background: rgba(232, 17, 35, 0.1);
  color: #e81123;
}

.description-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.actions-col {
  display: flex;
  gap: 4px;
  align-items: center;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--fui-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.icon-btn:hover {
  background: var(--fui-background-hover);
  border-color: var(--fui-border);
  color: var(--fui-text);
}

.icon-btn.delete-icon:hover {
  background: rgba(232, 17, 35, 0.1);
  border-color: var(--error-stroke-default, #e81123);
  color: var(--error-fill-default, #e81123);
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--fui-text-secondary);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--fui-surface);
  border-radius: 12px;
  border: 1px solid var(--fui-border);
}

.page-info {
  font-size: 14px;
  color: var(--fui-text-secondary);
}

.batch-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--fui-surface);
  border-radius: 12px;
  border: 1px solid var(--fui-border);
}

.selected-count {
  font-size: 14px;
  color: var(--fui-text-secondary);
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

.modal-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.warning-icon {
  color: var(--error-fill-default, #e81123);
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

.mono-font {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 12px;
}

.confirm-body {
  padding: 24px 28px;
}

.confirm-body p {
  margin: 0;
  font-size: 14px;
  color: var(--fui-text);
  line-height: 1.5;
}

.modal-footer {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 28px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(255, 255, 255, 0.3) 100%
  );
}

[data-theme='dark'] .modal-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(255, 255, 255, 0.05) 100%
  );
}
</style>

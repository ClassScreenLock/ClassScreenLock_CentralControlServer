<template>
  <div class="schedule-page">
    <div class="page-header">
      <div class="page-title">
        <FluentIcons name="calendar" :size="28" class="page-icon" />
        <h2>课表控制</h2>
      </div>
    </div>

    <!-- 模式切换 + 目标选择 -->
    <div class="control-bar card">
      <div class="mode-tabs">
        <button class="tab-btn" :class="{ active: mode === 'org' }" @click="mode = 'org'">
          <FluentIcons name="building" :size="16" />
          组织课表
        </button>
        <button class="tab-btn" :class="{ active: mode === 'device' }" @click="mode = 'device'">
          <FluentIcons name="computer" :size="16" />
          设备课表
        </button>
      </div>
      <div class="target-selector">
        <template v-if="mode === 'org'">
          <CustomDropdown
            v-model="selectedOrgId"
            :options="orgOptions"
            placeholder="选择组织"
            class="target-dropdown"
            @change="onOrgSelected"
          />
        </template>
        <template v-if="mode === 'device'">
          <CustomDropdown
            v-model="selectedDeviceId"
            :options="deviceOptions"
            placeholder="选择设备"
            class="target-dropdown"
            @change="onDeviceSelected"
          />
          <button
            v-if="selectedDeviceId && scheduleSource === 'device' && canEdit"
            class="btn btn-secondary btn-sm"
            @click="clearDeviceSchedule"
          >
            清除设备课表
          </button>
        </template>
      </div>
    </div>

    <div v-if="!scheduleData" class="empty-state">
      <FluentIcons name="calendar" :size="48" class="empty-icon" />
      <p>请选择一个组织或设备来管理课表</p>
    </div>

    <template v-if="scheduleData">
      <!-- 课表来源提示 -->
      <div v-if="scheduleSource === 'device'" class="source-banner device-source">
        <FluentIcons name="info" :size="16" />
        <span>当前显示设备专属课表（已覆盖组织默认课表）</span>
      </div>
      <div v-else-if="scheduleSource === 'organization'" class="source-banner org-source">
        <FluentIcons name="building" :size="16" />
        <span>当前显示组织默认课表</span>
      </div>

      <!-- 全局设置 -->
      <div class="settings-panel card">
        <h3 class="section-title">基本设置</h3>
        <div class="settings-row">
          <div class="setting-item">
            <label>循环周数</label>
            <select v-model.number="scheduleData.weeklyCycleCount" class="input-field" @change="onCycleCountChanged">
              <option v-for="n in 6" :key="n" :value="n">{{ n }} 周循环</option>
            </select>
          </div>
          <div class="setting-item">
            <label>学期开始日期</label>
            <div class="date-picker-wrapper" @click="openDatePicker">
              <FluentIcons name="calendar" :size="16" class="date-icon" />
              <span class="date-text" :class="{ placeholder: !scheduleData.termStartDate }">
                {{ scheduleData.termStartDate || '选择日期' }}
              </span>
              <input
                ref="dateInputRef"
                type="date"
                v-model="scheduleData.termStartDate"
                class="date-input-hidden"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 周选择Tabs -->
      <div class="week-selector">
        <div class="week-tabs">
          <button
            v-for="w in scheduleData.weeklyCycleCount"
            :key="w"
            class="week-tab"
            :class="{ active: selectedWeek === w }"
            @click="selectedWeek = w"
          >
            第{{ w }}周
          </button>
        </div>
        <div v-if="scheduleData.termStartDate" class="week-date-hint">
          起始：{{ formatStartDate(selectedWeek) }}
        </div>
      </div>

      <!-- 当前周的课表编辑 -->
      <div v-if="currentWeekly" class="weekly-editor">
        <!-- 科目管理 -->
        <div class="subjects-panel card">
          <div class="subjects-header">
            <h3 class="section-title">科目列表</h3>
            <button v-if="canEdit" class="btn btn-sm btn-primary" @click="addSubject">+ 添加科目</button>
          </div>
          <div class="subjects-list">
            <div v-for="(subj, idx) in currentWeekly.subjects" :key="idx" class="subject-item">
              <input v-model="subj.name" class="input-field subject-name" placeholder="科目名称" />
              <input v-model="subj.simplifiedName" class="input-field subject-short" placeholder="简称" />
              <input v-model="subj.teacher" class="input-field subject-teacher" placeholder="教师" />
              <input v-model="subj.room" class="input-field subject-room" placeholder="教室" />
              <button v-if="canEdit" class="btn-icon delete-btn" @click="removeSubject(idx)" title="删除科目">
                 <FluentIcons name="delete" :size="14" />
              </button>
            </div>
            <div v-if="!currentWeekly.subjects || currentWeekly.subjects.length === 0" class="empty-hint">
              暂无科目，点击"+ 添加科目"添加
            </div>
          </div>
        </div>

        <!-- 日期选择 -->
        <div class="day-tabs">
          <button
            v-for="day in daysOfWeek"
            :key="day.index"
            class="day-tab"
            :class="{ active: selectedDay === day.index }"
            @click="selectedDay = day.index"
          >
            {{ day.label }}
          </button>
        </div>

        <!-- 当日时间点列表 -->
        <div class="day-editor card">
          <div class="day-editor-header">
            <h3 class="section-title">{{ getDayName(selectedDay) }} - 时间点</h3>
            <div class="day-editor-actions">
              <button v-if="canEdit" class="btn btn-sm btn-primary" @click="addTimePoint('Class')">+ 上课</button>
              <button v-if="canEdit" class="btn btn-sm btn-accent" @click="addTimePoint('Break')">+ 课间</button>
              <button v-if="canEdit" class="btn btn-sm" @click="addTimePoint('Divider')">+ 分割线</button>
              <button v-if="canEdit" class="btn btn-sm btn-warning" @click="addTimePoint('Action')">+ 行动点</button>
            </div>
          </div>

          <div class="timepoints-list">
            <div v-for="(tp, idx) in currentDayClasses" :key="idx" class="timepoint-item" :class="'tp-' + tp.type?.toLowerCase()">
              <div class="tp-type-badge" :class="tp.type?.toLowerCase()">{{ typeLabel(tp.type) }}</div>
              <div class="tp-time">
                <input v-model="tp.startTime" class="input-field time-input" placeholder="08:00" />
                <span class="time-sep">-</span>
                <input v-model="tp.endTime" class="input-field time-input" placeholder="08:45" />
              </div>

              <!-- 上课类型：科目下拉选择 -->
              <template v-if="tp.type === 'Class'">
                <CustomDropdown
                  :modelValue="getTpSubjectValue(tp)"
                  :options="subjectOptions"
                  placeholder="选择科目"
                  class="tp-subject-dropdown"
                  @change="(val) => onTpSubjectChange(tp, val)"
                />
                <input
                  v-if="isCustomSubjectLabel(tp.label)"
                  v-model="tp.label"
                  class="input-field tp-label"
                  placeholder="输入课程名称"
                />
              </template>

              <!-- 非上课类型：标签输入 -->
              <input v-else v-model="tp.label" class="input-field tp-label" placeholder="标签" />

              <input v-model="tp.description" class="input-field tp-desc" placeholder="备注" />
              <div class="tp-actions">
                <button v-if="canEdit" class="btn-icon" @click="moveTimePoint(idx, -1)" :disabled="idx === 0" title="上移">
                  <FluentIcons name="arrow_up" :size="14" />
                </button>
                <button v-if="canEdit" class="btn-icon" @click="moveTimePoint(idx, 1)" :disabled="idx >= currentDayClasses.length - 1" title="下移">
                  <FluentIcons name="arrow_down" :size="14" />
                </button>
                <button v-if="canEdit" class="btn-icon delete-btn" @click="removeTimePoint(idx)" title="删除">
                  <FluentIcons name="delete" :size="14" />
                </button>
              </div>
            </div>
            <div v-if="!currentDayClasses || currentDayClasses.length === 0" class="empty-hint">
              暂无时间点，请点击上方按钮添加
            </div>
          </div>
        </div>
      </div>

      <!-- 操作栏 -->
      <div class="action-bar">
        <button v-if="canEdit" class="btn btn-primary btn-lg" @click="saveSchedule" :disabled="saving">
          <FluentIcons v-if="saving" name="sync" :size="16" class="spin-icon" />
          <FluentIcons v-else name="save" :size="16" />
          {{ saving ? '保存中...' : '保存并推送到设备' }}
        </button>
        <button v-if="canEdit" class="btn btn-accent btn-lg" @click="saveAndPushNow" :disabled="saving">
          <FluentIcons name="send" :size="16" />
          仅推送（不保存配置变更）
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { organizationAPI, deviceAPI } from '@/api/organization'
import CustomDropdown from '@/components/CustomDropdown.vue'
import FluentIcons from '@/components/FluentIcons.vue'
import { notify } from '@/utils/notification'
import wsService from '@/utils/websocket'
import { usePermissions } from '@/composables/usePermissions'

const { hasActionPermission } = usePermissions()
const canEditOrg = computed(() => hasActionPermission('schedule', 'editOrg'))
const canEditDevice = computed(() => hasActionPermission('schedule', 'editDevice'))

// 根据当前 mode 返回是否可编辑
const canEdit = computed(() => {
  if (mode.value === 'org') return canEditOrg.value
  if (mode.value === 'device') return canEditDevice.value
  return false
})

const mode = ref('org')
const selectedOrgId = ref('')
const selectedDeviceId = ref('')
const organizations = ref([])
const devices = ref([])
const scheduleData = ref(null)
const scheduleSource = ref('default')
const saving = ref(false)
const selectedWeek = ref(1)
const selectedDay = ref(1)
const dateInputRef = ref(null)

const daysOfWeek = [
  { index: 1, label: '周一' },
  { index: 2, label: '周二' },
  { index: 3, label: '周三' },
  { index: 4, label: '周四' },
  { index: 5, label: '周五' },
  { index: 6, label: '周六' },
  { index: 7, label: '周日' }
]

const orgOptions = computed(() => [
  { value: '', label: '选择组织', iconName: 'building' },
  ...organizations.value.map(o => ({ value: o.id, label: o.name, iconName: 'building' }))
])

const deviceOptions = computed(() => [
  { value: '', label: '选择设备', iconName: 'computer' },
  ...devices.value.map(d => ({ value: d.id, label: d.name, iconName: 'computer' }))
])

const currentWeekly = computed(() => {
  if (!scheduleData.value || !scheduleData.value.weeklies) return null
  let w = scheduleData.value.weeklies.find(wk => wk.weekNumber === selectedWeek.value)
  if (!w) {
    w = createDefaultWeekly(selectedWeek.value)
    scheduleData.value.weeklies.push(w)
  }
  return w
})

const currentDay = computed(() => {
  if (!currentWeekly.value) return null
  if (!currentWeekly.value.days) currentWeekly.value.days = []
  let day = currentWeekly.value.days.find(d => d.enableDay === selectedDay.value)
  if (!day) {
    day = { enableDay: selectedDay.value, classes: [] }
    currentWeekly.value.days.push(day)
  }
  return day
})

const currentDayClasses = computed(() => {
  if (!currentDay.value) return []
  if (!currentDay.value.classes) currentDay.value.classes = []
  return currentDay.value.classes
})

function createDefaultWeekly(weekNum) {
  const days = []
  for (let d = 1; d <= 7; d++) {
    days.push({ enableDay: d, classes: [] })
  }
  return {
    id: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(),
    name: `第${weekNum}周课表`,
    weekNumber: weekNum,
    defaultClassDuration: 45,
    defaultBreakDuration: 10,
    subjects: [],
    days
  }
}

function ensureScheduleData() {
  if (!scheduleData.value) {
    scheduleData.value = {
      weeklyCycleCount: 4,
      termStartDate: null,
      weeklies: []
    }
  }
  if (!scheduleData.value.weeklies) scheduleData.value.weeklies = []
  if (!scheduleData.value.weeklyCycleCount) scheduleData.value.weeklyCycleCount = 4

  for (let w = 1; w <= scheduleData.value.weeklyCycleCount; w++) {
    if (!scheduleData.value.weeklies.find(wk => wk.weekNumber === w)) {
      scheduleData.value.weeklies.push(createDefaultWeekly(w))
    }
  }
}

function onCycleCountChanged() {
  if (!scheduleData.value) return
  const count = scheduleData.value.weeklyCycleCount
  if (selectedWeek.value > count) selectedWeek.value = count
  for (let w = 1; w <= count; w++) {
    if (!scheduleData.value.weeklies.find(wk => wk.weekNumber === w)) {
      scheduleData.value.weeklies.push(createDefaultWeekly(w))
    }
  }
  scheduleData.value.weeklies = scheduleData.value.weeklies.filter(wk => wk.weekNumber <= count)
}

function addSubject() {
  if (!currentWeekly.value) return
  if (!currentWeekly.value.subjects) currentWeekly.value.subjects = []
  currentWeekly.value.subjects.push({ name: '', simplifiedName: '', teacher: '', room: '' })
}

function removeSubject(idx) {
  if (!currentWeekly.value) return
  currentWeekly.value.subjects.splice(idx, 1)
}

const CUSTOM_SUBJECT_VALUE = '__custom__'

const subjectOptions = computed(() => {
  const opts = [{ value: '', label: '选择科目', iconName: 'book' }]
  if (currentWeekly.value?.subjects) {
    for (const s of currentWeekly.value.subjects) {
      if (s.name) {
        opts.push({ value: s.name, label: s.simplifiedName ? `${s.name} (${s.simplifiedName})` : s.name, iconName: 'book' })
      }
    }
  }
  opts.push({ value: CUSTOM_SUBJECT_VALUE, label: '自定义...', iconName: 'edit' })
  return opts
})

function getTpSubjectValue(tp) {
  if (!tp.label) return ''
  if (currentWeekly.value?.subjects?.some(s => s.name === tp.label)) return tp.label
  return CUSTOM_SUBJECT_VALUE
}

function onTpSubjectChange(tp, val) {
  if (val === CUSTOM_SUBJECT_VALUE) {
    tp.label = ''
  } else {
    tp.label = val || ''
  }
}

function isCustomSubjectLabel(label) {
  if (!label) return false
  if (!currentWeekly.value || !currentWeekly.value.subjects) return true
  return !currentWeekly.value.subjects.some(s => s.name === label)
}

function addTimePoint(type) {
  if (!currentDay.value) return
  if (!currentDay.value.classes) currentDay.value.classes = []

  const lastTp = currentDay.value.classes[currentDay.value.classes.length - 1]
  let startTime = '08:00'
  let endTime = '08:45'

  if (lastTp) {
    startTime = lastTp.endTime || lastTp.startTime || '08:00'
    const [h, m] = startTime.split(':').map(Number)
    let totalMin = h * 60 + m + (type === 'Break' ? 10 : 45)
    const newH = Math.floor(totalMin / 60) % 24
    const newM = totalMin % 60
    endTime = `${String(newH).padStart(2, '0')}:${String(newM).padStart(2, '0')}`
  }

  if (type === 'Divider' || type === 'Action') {
    endTime = startTime
  }

  currentDay.value.classes.push({
    type,
    subject: type === 'Class' ? '' : null,
    label: '',
    description: '',
    startTime,
    endTime
  })
}

function removeTimePoint(idx) {
  if (!currentDay.value) return
  currentDay.value.classes.splice(idx, 1)
}

function moveTimePoint(idx, direction) {
  if (!currentDay.value) return
  const arr = currentDay.value.classes
  const newIdx = idx + direction
  if (newIdx < 0 || newIdx >= arr.length) return
  const item = arr.splice(idx, 1)[0]
  arr.splice(newIdx, 0, item)
}

function typeLabel(type) {
  const map = { Class: '上课', Break: '课间', Divider: '分割线', Action: '行动' }
  return map[type] || type || ''
}

function getDayName(dayIndex) {
  const day = daysOfWeek.find(d => d.index === dayIndex)
  return day ? day.label : '未知'
}

function formatStartDate(weekNum) {
  if (!scheduleData.value?.termStartDate) return ''
  try {
    const start = new Date(scheduleData.value.termStartDate + 'T00:00:00')
    const d = new Date(start)
    d.setDate(d.getDate() + (weekNum - 1) * 7)
    return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return ''
  }
}

function openDatePicker() {
  if (dateInputRef.value) {
    dateInputRef.value.showPicker()
  }
}

// ===== 数据加载 =====

async function loadOrganizations() {
  try {
    const data = await organizationAPI.getAll()
    organizations.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error('加载组织失败:', e)
  }
}

async function loadDevices() {
  try {
    const data = await deviceAPI.getAll()
    devices.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error('加载设备失败:', e)
  }
}

async function loadOrgSchedule(orgId) {
  try {
    const data = await organizationAPI.getScheduleConfig(orgId)
    scheduleData.value = data
    scheduleSource.value = data._source || 'organization'
    ensureScheduleData()
  } catch (e) {
    console.error('加载组织课表失败:', e)
    scheduleData.value = null
    notify.error('加载组织课表失败')
  }
}

async function loadDeviceSchedule(deviceId) {
  try {
    const data = await deviceAPI.getScheduleConfig(deviceId)
    scheduleData.value = data
    scheduleSource.value = data._source || 'default'
    ensureScheduleData()
  } catch (e) {
    console.error('加载设备课表失败:', e)
    scheduleData.value = null
    notify.error('加载设备课表失败')
  }
}

async function onOrgSelected() {
  selectedDeviceId.value = ''
  if (selectedOrgId.value) {
    await loadOrgSchedule(selectedOrgId.value)
  } else {
    scheduleData.value = null
  }
}

async function onDeviceSelected() {
  if (selectedDeviceId.value) {
    await loadDeviceSchedule(selectedDeviceId.value)
  } else {
    scheduleData.value = null
  }
}

async function clearDeviceSchedule() {
  if (!selectedDeviceId.value) return
  try {
    await deviceAPI.deleteScheduleConfig(selectedDeviceId.value)
    notify.success('设备课表已清除，恢复使用组织默认课表')
    await loadDeviceSchedule(selectedDeviceId.value)
  } catch (e) {
    notify.error('清除设备课表失败')
  }
}

// ===== 保存和推送 =====

function sanitizeForSave() {
  if (!scheduleData.value) return null
  const data = JSON.parse(JSON.stringify(scheduleData.value))
  // 清理自定义科目标记
  if (data.weeklies) {
    for (const w of data.weeklies) {
      if (w.days) {
        for (const d of w.days) {
          if (d.classes) {
            for (const c of d.classes) {
              if (c.label === '__custom__') c.label = ''
            }
          }
        }
      }
    }
  }
  delete data._source
  return data
}

async function saveSchedule() {
  if (!scheduleData.value) return
  saving.value = true
  try {
    const data = sanitizeForSave()

    if (mode.value === 'org' && selectedOrgId.value) {
      await organizationAPI.updateScheduleConfig(selectedOrgId.value, data)
      notify.success('组织课表已保存并推送到设备')
    } else if (mode.value === 'device' && selectedDeviceId.value) {
      await deviceAPI.updateScheduleConfig(selectedDeviceId.value, data)
      notify.success('设备课表已保存并推送')
    }
  } catch (e) {
    console.error('保存课表失败:', e)
    notify.error('保存课表失败')
  } finally {
    saving.value = false
  }
}

function saveAndPushNow() {
  if (!scheduleData.value) return
  saving.value = true
  try {
    const data = sanitizeForSave()
    if (mode.value === 'org' && selectedOrgId.value) {
      wsService.pushScheduleToOrg(selectedOrgId.value, data)
      notify.success('课表已通过WebSocket推送到组织设备')
    } else if (mode.value === 'device' && selectedDeviceId.value) {
      wsService.pushScheduleToDevice(selectedDeviceId.value, data)
      notify.success('课表已通过WebSocket推送到设备')
    }
  } catch (e) {
    notify.error('推送失败')
  } finally {
    saving.value = false
  }
}

// 监听模式切换清空选择
watch(mode, () => {
  scheduleData.value = null
  scheduleSource.value = 'default'
  selectedOrgId.value = ''
  selectedDeviceId.value = ''
})

onMounted(async () => {
  await Promise.all([loadOrganizations(), loadDevices()])
})
</script>

<style scoped>
.schedule-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  min-height: 100vh;
  animation: pageFadeIn 0.5s ease-out;
}

@keyframes pageFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
}

/* ===== 控制栏 ===== */
.control-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  padding: 16px 20px;
}

.mode-tabs {
  display: flex;
  background: var(--fui-background);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--fui-border);
}

.mode-tabs .tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: transparent;
  border: none;
  color: var(--fui-text-secondary);
  font-size: 0.875em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-tabs .tab-btn.active {
  background: #0078d4;
  color: white;
}

.mode-tabs .tab-btn:hover:not(.active) {
  background: rgba(0, 0, 0, 0.04);
}
[data-theme='dark'] .mode-tabs .tab-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.06);
}

.target-selector {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.target-dropdown {
  min-width: 280px;
  max-width: 400px;
}

/* ===== 来源提示横幅 ===== */
.source-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 0.85em;
}

.source-banner.device-source {
  background: rgba(240, 160, 48, 0.08);
  border: 1px solid rgba(240, 160, 48, 0.2);
  color: #d88a00;
}
[data-theme='dark'] .source-banner.device-source { color: #f0a030; }

.source-banner.org-source {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: #0e8a60;
}
[data-theme='dark'] .source-banner.org-source { color: #10b981; }

/* ===== 卡片 ===== */
.card {
  background: var(--fui-surface);
  border: 1px solid var(--fui-border);
  border-radius: 8px;
  padding: 20px;
}

.section-title {
  margin: 0 0 12px 0;
  font-size: 0.85em;
  font-weight: 600;
  color: var(--fui-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ===== 设置面板 ===== */
.settings-row {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  align-items: flex-end;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.setting-item label {
  font-size: 0.8em;
  color: var(--fui-text-secondary);
  font-weight: 500;
}

/* ===== 日期选择器 ===== */
.date-picker-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 12px;
  background: var(--fui-background);
  border: 1px solid var(--fui-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  min-width: 180px;
}

.date-picker-wrapper:hover {
  border-color: #0078d4;
}

.date-icon {
  color: var(--fui-text-secondary);
  flex-shrink: 0;
}

.date-text {
  font-size: 0.9em;
  color: var(--fui-text);
  user-select: none;
}

.date-text.placeholder {
  color: var(--fui-text-secondary);
  opacity: 0.6;
}

.date-input-hidden {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

/* ===== 周选择 ===== */
.week-selector {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.week-tabs {
  display: flex;
  gap: 4px;
}

.week-tab {
  padding: 8px 18px;
  background: var(--fui-surface);
  border: 1px solid var(--fui-border);
  border-radius: 8px;
  color: var(--fui-text-secondary);
  font-size: 0.875em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.week-tab.active {
  background: #0078d4;
  color: white;
  border-color: #0078d4;
}

.week-tab:hover:not(.active) {
  background: var(--fui-background);
  border-color: #0078d4;
  color: #0078d4;
}

.week-date-hint {
  font-size: 0.8em;
  color: var(--fui-text-secondary);
  opacity: 0.7;
}

/* ===== 日期选择 ===== */
.day-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.day-tab {
  padding: 8px 14px;
  background: var(--fui-surface);
  border: 1px solid var(--fui-border);
  border-radius: 8px;
  color: var(--fui-text-secondary);
  font-size: 0.85em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.day-tab.active {
  background: rgba(16, 185, 129, 0.1);
  color: #0e8a60;
  border-color: rgba(16, 185, 129, 0.3);
  font-weight: 600;
}
[data-theme='dark'] .day-tab.active { color: #10b981; }

.day-tab:hover:not(.active) {
  background: var(--fui-background);
}

/* ===== 科目面板 ===== */
.subjects-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.subjects-header .section-title {
  margin-bottom: 0;
}

.subjects-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.subject-item {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.subject-name { flex: 2; min-width: 100px; }
.subject-short { flex: 1; min-width: 60px; max-width: 100px; }
.subject-teacher { flex: 1; min-width: 80px; }
.subject-room { flex: 1; min-width: 80px; }

/* ===== 时间点编辑器 ===== */
.weekly-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.day-editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
  gap: 8px;
}

.day-editor-header .section-title {
  margin-bottom: 0;
}

.day-editor-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.timepoints-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.timepoint-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--fui-background);
  border: 1px solid var(--fui-border);
  border-radius: 8px;
  transition: all 0.2s;
}

.timepoint-item:hover {
  border-color: #0078d4;
  box-shadow: 0 1px 4px rgba(0, 120, 212, 0.08);
}

.tp-type-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.7em;
  font-weight: 600;
  min-width: 48px;
  justify-content: center;
  flex-shrink: 0;
}

.tp-type-badge.class { background: rgba(0, 120, 212, 0.1); color: #0078d4; }
.tp-type-badge.break { background: rgba(16, 185, 129, 0.1); color: #0e8a60; }
[data-theme='dark'] .tp-type-badge.break { color: #10b981; }
.tp-type-badge.divider { background: rgba(156, 163, 175, 0.1); color: #6b7280; }
.tp-type-badge.action { background: rgba(240, 160, 48, 0.1); color: #d88a00; }
[data-theme='dark'] .tp-type-badge.action { color: #f0a030; }

.tp-time {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.time-input {
  width: 68px;
  text-align: center;
  font-family: monospace;
}

.time-sep {
  color: var(--fui-text-secondary);
  margin: 0 2px;
}

.tp-subject-dropdown { flex: 1.2; min-width: 150px; }
.tp-label { flex: 1; min-width: 80px; }
.tp-desc { flex: 1.2; min-width: 100px; }

.tp-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

/* ===== 操作栏 ===== */
.action-bar {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 0;
  border-top: 1px solid var(--fui-border);
  margin-top: 8px;
}

/* ===== 通用输入框 ===== */
.input-field {
  height: 36px;
  padding: 0 10px;
  background: var(--fui-background);
  border: 1px solid var(--fui-border);
  border-radius: 6px;
  color: var(--fui-text);
  font-size: 0.85em;
  outline: none;
  transition: all 0.2s;
  font-family: inherit;
}

.input-field:focus {
  border-color: #0078d4;
  box-shadow: 0 0 0 3px rgba(0, 120, 212, 0.1);
}

.input-field::placeholder {
  color: var(--fui-text-secondary);
  opacity: 0.5;
}

select.input-field {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  padding-right: 32px;
  cursor: pointer;
}

/* ===== 空状态 ===== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--fui-text-secondary);
  gap: 16px;
}

.empty-icon { opacity: 0.4; }
.empty-hint {
  padding: 20px;
  text-align: center;
  color: var(--fui-text-secondary);
  opacity: 0.6;
  font-size: 0.85em;
}

/* ===== 按钮样式 ===== */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 0.85em;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid var(--fui-border);
  transition: all 0.2s;
  background: var(--fui-surface);
  color: var(--fui-text);
}

.btn:hover { background: var(--fui-background); }

.btn-primary { background: #0078d4; border-color: #0078d4; color: white; }
.btn-primary:hover { background: #106ebe; }

.btn-accent { background: #10b981; border-color: #10b981; color: white; }
.btn-accent:hover { background: #059669; }

.btn-warning { background: #f0a030; border-color: #f0a030; color: white; }
.btn-warning:hover { background: #d88a00; }

.btn-secondary { background: var(--fui-background); border-color: var(--fui-border); color: var(--fui-text); }

.btn-sm { padding: 5px 12px; font-size: 0.8em; }
.btn-lg { padding: 10px 24px; font-size: 0.9em; }

.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: 1px solid var(--fui-border);
  border-radius: 6px;
  color: var(--fui-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-icon:hover { background: var(--fui-background); color: var(--fui-text); }
.btn-icon:disabled { opacity: 0.3; cursor: not-allowed; }
.btn-icon.delete-btn { color: #ef4444; border-color: rgba(239, 68, 68, 0.2); }
.btn-icon.delete-btn:hover { background: rgba(239, 68, 68, 0.08); }

.spin-icon { animation: spin 1s linear infinite; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .schedule-page { padding: 12px; gap: 12px; }
  .control-bar { flex-direction: column; align-items: stretch; }
  .target-selector { flex-direction: column; }
  .target-dropdown { min-width: auto; width: 100%; max-width: none; }
  .timepoint-item { flex-wrap: wrap; }
  .subject-item { flex-direction: column; }
  .subject-short { max-width: none; }
}
</style>

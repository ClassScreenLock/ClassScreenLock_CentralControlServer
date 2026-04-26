<template>
  <div class="organizations-page">
    <div class="page-header">
      <h2>组织管理</h2>
      <button class="button-primary" @click="openAddModal">添加组织</button>
    </div>

    <div class="organizations-list card">
      <div v-if="organizations.length === 0" class="empty-state">
        暂无组织数据，请点击上方按钮添加组织
      </div>
      <div v-else class="organization-grid">
        <div v-for="org in organizations" :key="org.id" class="organization-card">
          <div class="org-header">
            <h3>{{ org.name }}</h3>
            <div class="org-actions">
              <button class="button-primary" @click="editOrganization(org)">编辑</button>
              <button class="button-primary" @click="viewDevices(org)">查看设备</button>
            </div>
          </div>
          <div class="org-details">
            <p><strong>组织 ID:</strong> <code class="org-id">{{ org.id }}</code></p>
            <p><strong>描述:</strong> {{ org.description || '暂无描述' }}</p>
            <p><strong>创建时间:</strong> {{ formatDate(org.createdAt) }}</p>
            <p><strong>设备数量:</strong> {{ org.deviceCount || 0 }}</p>
          </div>
          <div class="org-footer">
            <button class="button-primary" @click="showDeleteConfirm(org)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑组织模态框 -->
    <Transition name="modal-overlay" appear>
      <div v-if="showModal" class="modal-overlay" @click="closeModal">
        <Transition name="modal-content" appear>
          <div v-if="showModal" class="modal-content" @click.stop>
            <div class="modal-glass"></div>
            <div class="modal-refraction"></div>
            <div class="modal-header">
              <h3>{{ modalTitle }}</h3>
              <button class="close-btn" @click="closeModal">×</button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="saveOrganization">
                <div class="form-group">
                  <label>组织名称 *</label>
                  <input 
                    :key="'org-name-' + modalTitle"
                    type="text" 
                    v-model="currentOrg.name" 
                    class="input-field" 
                    placeholder="请输入组织名称"
                    required
                    autocomplete="off"
                  >
                </div>

                <div class="form-group">
                  <label>描述</label>
                  <textarea 
                    v-model="currentOrg.description" 
                    class="input-field" 
                    placeholder="请输入组织描述"
                    rows="3"
                  ></textarea>
                </div>
                <div class="form-actions">
                  <button type="button" class="button-primary" @click="closeModal">取消</button>
                  <button type="submit" class="button-primary">保存</button>
                </div>
              </form>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
    </div>

    <!-- 确认删除对话框 -->
    <ConfirmDialog
      v-model:visible="showConfirmDialog"
      :title="'确认删除'"
      :message="confirmMessage"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { organizationAPI } from '@/api/organization'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { notify } from '@/utils/notification'

const router = useRouter()
const organizations = ref([])
const showModal = ref(false)
const modalTitle = ref('')
const currentOrg = ref({
  name: '',
  description: ''
})
const showConfirmDialog = ref(false)
const confirmMessage = ref('')
const currentDeleteOrg = ref(null)

const showNotification = inject('showNotification')

const loadOrganizations = async () => {
  try {
    const data = await organizationAPI.getAllWithDeviceCounts()
    organizations.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('Failed to load organizations:', error)
    organizations.value = []
  }
}

const openAddModal = () => {
  currentOrg.value = { 
    name: '', 
    description: ''
  }
  modalTitle.value = '添加组织'
  showModal.value = true
}

const editOrganization = (org) => {
  currentOrg.value = { 
    ...org
  }
  modalTitle.value = '编辑组织'
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const saveOrganization = async () => {
  try {
    if (modalTitle.value === '编辑组织') {
      await organizationAPI.update(currentOrg.value.id, currentOrg.value)
    } else {
      await organizationAPI.create({
        name: currentOrg.value.name,
        description: currentOrg.value.description
      })
    }
    await loadOrganizations()
    closeModal()
  } catch (error) {
    console.error('Failed to save organization:', error)
    notify.error('保存失败，请重试')
  }
}

const showDeleteConfirm = (org) => {
  currentDeleteOrg.value = org
  confirmMessage.value = `确定要删除组织 "${org.name}" 吗？`
  showConfirmDialog.value = true
}

const confirmDelete = async () => {
  if (currentDeleteOrg.value) {
    try {
      await organizationAPI.delete(currentDeleteOrg.value.id)
      await loadOrganizations()
      notify.success('组织删除成功')
    } catch (error) {
      console.error('Failed to delete organization:', error)
      notify.error('删除失败，请重试')
    } finally {
      showConfirmDialog.value = false
      currentDeleteOrg.value = null
    }
  }
}

const cancelDelete = () => {
  showConfirmDialog.value = false
  currentDeleteOrg.value = null
}

const viewDevices = (org) => {
  router.push(`/devices?org=${org.id}`)
}

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(() => {
  loadOrganizations()
})
</script>

<style scoped>
.organizations-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: pageFadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
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

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  color: var(--fui-text);
}

.organizations-list {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--fui-radius);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 24px;
  animation: containerFadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  animation-delay: 0.2s;
  animation-fill-mode: both;
  font-size: var(--fui-font-size-base);
}

[data-theme='dark'] .organizations-list {
  background: rgba(30, 30, 30, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
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

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--fui-text-secondary);
  font-size: 1em;
}

.organization-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.organization-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--fui-radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0;
  transform: translateY(20px) scale(0.95);
  animation: cardFadeIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  animation-fill-mode: both;
}

[data-theme='dark'] .organization-card {
  background: rgba(45, 45, 45, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.organization-card:nth-child(1) { animation-delay: 0.3s; }
.organization-card:nth-child(2) { animation-delay: 0.4s; }
.organization-card:nth-child(3) { animation-delay: 0.5s; }
.organization-card:nth-child(4) { animation-delay: 0.6s; }
.organization-card:nth-child(5) { animation-delay: 0.7s; }
.organization-card:nth-child(6) { animation-delay: 0.8s; }

@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.org-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.org-header h3 {
  margin: 0;
  color: var(--fui-text);
  font-size: 1.125em;
}

.org-actions {
  display: flex;
  gap: 8px;
}

.organization-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
}

[data-theme='dark'] .organization-card:hover {
  background: rgba(55, 55, 55, 0.6);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
  border-color: rgba(255, 255, 255, 0.15);
}

.org-details p {
  margin: 4px 0;
  font-size: 0.875em;
  color: var(--fui-text);
}

.org-details .org-id {
  font-family: 'LINE Seed KR', 'Clear Sans', 'HarmonyOS Sans TC', 'Segoe UI', 'Consolas', monospace;
  background: var(--fui-background);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 1em;
  font-weight: 500;
  letter-spacing: 0.5px;
}

[data-theme='dark'] .org-details .org-id {
  background: rgba(60, 60, 60, 0.8);
  color: #e0e0e0;
}

.org-footer {
  margin-top: auto;
  display: flex;
  justify-content: flex-end;
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
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
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
  color: var(--fui-text);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5em;
  cursor: pointer;
  color: var(--fui-text-secondary);
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.close-btn:hover {
  color: var(--fui-text);
  background: rgba(0, 0, 0, 0.05);
  transform: rotate(90deg);
}

[data-theme='dark'] .close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.close-btn:active {
  transform: rotate(180deg) scale(0.9);
}

.modal-body {
  position: relative;
  z-index: 2;
  padding: 28px;
}

.modal-footer {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding: 0 28px 28px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #333;
}

[data-theme='dark'] .form-group label {
  color: #e0e0e0;
}

textarea.input-field {
  resize: vertical;
  min-height: 80px;
}

[data-theme='dark'] .input-field {
  background-color: rgba(60, 60, 60, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
  color: #e0e0e0;
}

[data-theme='dark'] .input-field:focus {
  background-color: rgba(70, 70, 70, 0.9);
}

[data-theme='dark'] .btn-primary {
  background-color: #0078d4;
}

[data-theme='dark'] .btn-primary:hover {
  background-color: #1084d8;
}

[data-theme='dark'] .btn-secondary {
  background-color: rgba(255, 255, 255, 0.1);
  color: #e0e0e0;
}

[data-theme='dark'] .btn-secondary:hover {
  background-color: rgba(255, 255, 255, 0.15);
}

.form-actions {
  display: flex;
  gap: 16px;
  margin-top: 20px;
  justify-content: center;
}

.form-actions .button-primary {
  flex: 0 0 auto;
  width: 140px;
  padding: 12px 24px;
}
</style>

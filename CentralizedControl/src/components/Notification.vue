<template>
  <Teleport to="body">
    <TransitionGroup name="notification-list" tag="div" class="notification-container">
      <div 
        v-for="notification in notifications" 
        :key="notification.id"
        :class="['notification', `notification-${notification.type}`]"
      >
        <div class="notification-glass"></div>
        <div class="notification-shimmer"></div>
        <div class="notification-content-wrapper">
          <div class="notification-icon">
            <FluentIcons 
              :name="getNotificationIcon(notification.type)" 
              :size="20" 
            />
          </div>
          <div class="notification-content">
            <div class="notification-title">{{ notification.title }}</div>
            <div class="notification-message">{{ notification.message }}</div>
          </div>
          <button class="notification-close" @click="closeNotification(notification.id)">
            <FluentIcons name="close" :size="16" />
          </button>
        </div>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import FluentIcons from './FluentIcons.vue'

const notifications = ref([])
let notificationId = 0

const getNotificationIcon = (type) => {
  const iconMap = {
    success: 'check_circle',
    error: 'error',
    warning: 'warning',
    info: 'info'
  }
  return iconMap[type] || 'info'
}

const showNotification = (message, type = 'info', title = null) => {
  const id = ++notificationId
  const defaultTitles = {
    success: '成功',
    error: '错误',
    warning: '警告',
    info: '提示'
  }
  
  notifications.value.push({
    id,
    type,
    title: title || defaultTitles[type],
    message
  })
  
  setTimeout(() => {
    closeNotification(id)
  }, 5000)
}

const closeNotification = (id) => {
  const index = notifications.value.findIndex(n => n.id === id)
  if (index > -1) {
    notifications.value.splice(index, 1)
  }
}

defineExpose({
  showNotification,
  success: (message, title) => showNotification(message, 'success', title),
  error: (message, title) => showNotification(message, 'error', title),
  warning: (message, title) => showNotification(message, 'warning', title),
  info: (message, title) => showNotification(message, 'info', title)
})
</script>

<style>
.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 550px;
  min-width: 400px;
}

.notification {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 4px;
  border-radius: 12px;
  animation: slideInRight 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  overflow: hidden;
  min-width: 400px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.notification-glass {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(255, 255, 255, 0.85) 50%,
    rgba(255, 255, 255, 0.75) 100%
  );
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  z-index: 0;
  border-radius: 12px;
}

[data-theme='dark'] .notification-glass {
  background: linear-gradient(
    135deg,
    rgba(45, 45, 45, 0.95) 0%,
    rgba(35, 35, 35, 0.85) 50%,
    rgba(25, 25, 25, 0.75) 100%
  );
}

.notification-shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.3) 50%,
    transparent 100%
  );
  animation: shimmer 3s infinite;
  z-index: 1;
  pointer-events: none;
}

[data-theme='dark'] .notification-shimmer {
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.1) 50%,
    transparent 100%
  );
}

.notification-content-wrapper {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px 18px;
  width: 100%;
}

.notification::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 12px;
  padding: 1.5px;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.5),
    rgba(255, 255, 255, 0.1)
  );
  -webkit-mask: 
    linear-gradient(#fff 0 0) content-box, 
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  z-index: 3;
}

[data-theme='dark'] .notification::before {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.2),
    rgba(255, 255, 255, 0.05)
  );
}

.notification-success {
  border-left: 4px solid #10b981;
}

.notification-success .notification-glass {
  background: linear-gradient(
    135deg,
    rgba(16, 185, 129, 0.15) 0%,
    rgba(255, 255, 255, 0.85) 50%,
    rgba(255, 255, 255, 0.75) 100%
  );
}

[data-theme='dark'] .notification-success .notification-glass {
  background: linear-gradient(
    135deg,
    rgba(16, 185, 129, 0.2) 0%,
    rgba(45, 45, 45, 0.85) 50%,
    rgba(25, 25, 25, 0.75) 100%
  );
}

.notification-error {
  border-left: 4px solid #ef4444;
}

.notification-error .notification-glass {
  background: linear-gradient(
    135deg,
    rgba(239, 68, 68, 0.15) 0%,
    rgba(255, 255, 255, 0.85) 50%,
    rgba(255, 255, 255, 0.75) 100%
  );
}

[data-theme='dark'] .notification-error .notification-glass {
  background: linear-gradient(
    135deg,
    rgba(239, 68, 68, 0.2) 0%,
    rgba(45, 45, 45, 0.85) 50%,
    rgba(25, 25, 25, 0.75) 100%
  );
}

.notification-warning {
  border-left: 4px solid #f59e0b;
}

.notification-warning .notification-glass {
  background: linear-gradient(
    135deg,
    rgba(245, 158, 11, 0.15) 0%,
    rgba(255, 255, 255, 0.85) 50%,
    rgba(255, 255, 255, 0.75) 100%
  );
}

[data-theme='dark'] .notification-warning .notification-glass {
  background: linear-gradient(
    135deg,
    rgba(245, 158, 11, 0.2) 0%,
    rgba(45, 45, 45, 0.85) 50%,
    rgba(25, 25, 25, 0.75) 100%
  );
}

.notification-info {
  border-left: 4px solid #3b82f6;
}

.notification-info .notification-glass {
  background: linear-gradient(
    135deg,
    rgba(59, 130, 246, 0.15) 0%,
    rgba(255, 255, 255, 0.85) 50%,
    rgba(255, 255, 255, 0.75) 100%
  );
}

[data-theme='dark'] .notification-info .notification-glass {
  background: linear-gradient(
    135deg,
    rgba(59, 130, 246, 0.2) 0%,
    rgba(45, 45, 45, 0.85) 50%,
    rgba(25, 25, 25, 0.75) 100%
  );
}

.notification-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  color: #323130;
}

[data-theme='dark'] .notification-icon {
  color: #ffffff;
}

.notification-success .notification-icon {
  color: #10b981;
}

.notification-error .notification-icon {
  color: #ef4444;
}

.notification-warning .notification-icon {
  color: #f59e0b;
}

.notification-info .notification-icon {
  color: #3b82f6;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-weight: 600;
  font-size: 16px;
  color: #323130;
  margin-bottom: 6px;
}

[data-theme='dark'] .notification-title {
  color: #ffffff;
}

.notification-message {
  font-size: 15px;
  color: #605e5c;
  line-height: 1.5;
  word-wrap: break-word;
}

[data-theme='dark'] .notification-message {
  color: #b0b0b0;
}

.notification-close {
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.05);
  border: none;
  cursor: pointer;
  color: #605e5c;
  padding: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
}

.notification-close:hover {
  background: rgba(0, 0, 0, 0.1);
  color: #323130;
  transform: scale(1.05);
}

[data-theme='dark'] .notification-close {
  background: rgba(255, 255, 255, 0.1);
  color: #b0b0b0;
}

[data-theme='dark'] .notification-close:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  50%, 100% {
    left: 100%;
  }
}

.notification-list-enter-active,
.notification-list-leave-active {
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.notification-list-enter-from {
  opacity: 0;
  transform: translateX(100%) scale(0.9);
}

.notification-list-leave-to {
  opacity: 0;
  transform: translateX(100%) scale(0.95);
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}
</style>

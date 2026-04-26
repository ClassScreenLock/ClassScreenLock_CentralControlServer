<template>
  <Teleport to="body">
    <Transition name="confirm-overlay" appear>
      <div v-if="visible" class="confirm-overlay" @click="handleOverlayClick">
        <Transition name="confirm-dialog" appear>
          <div v-if="visible" class="confirm-dialog" @click.stop>
            <div class="confirm-glass"></div>
            <div class="confirm-refraction"></div>
            <div class="confirm-content-wrapper">
              <div class="confirm-header">
                <h3>{{ title }}</h3>
              </div>
              <div class="confirm-body">
                <p>{{ message }}</p>
              </div>
              <div class="confirm-footer">
                <button class="btn btn-secondary" @click="handleCancel">取消</button>
                <button class="btn btn-primary" @click="handleConfirm">确定</button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '确认操作'
  },
  message: {
    type: String,
    default: '您确定要执行此操作吗？'
  }
})

const emit = defineEmits(['update:visible', 'confirm', 'cancel'])

const handleConfirm = () => {
  emit('confirm')
  emit('update:visible', false)
}

const handleCancel = () => {
  emit('cancel')
  emit('update:visible', false)
}

const handleOverlayClick = () => {
  emit('cancel')
  emit('update:visible', false)
}
</script>

<style>
.confirm-overlay {
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

.confirm-overlay-enter-active,
.confirm-overlay-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.confirm-overlay-enter-from,
.confirm-overlay-leave-to {
  opacity: 0;
}

.confirm-dialog {
  position: relative;
  background: transparent;
  border-radius: 16px;
  overflow: hidden;
  max-width: 450px;
  width: 90%;
  box-shadow: 
    0 24px 80px rgba(0, 0, 0, 0.2),
    0 8px 32px rgba(0, 0, 0, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.confirm-glass {
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

[data-theme='dark'] .confirm-glass {
  background: rgba(40, 40, 40, 0.15);
}

.confirm-refraction {
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

[data-theme='dark'] .confirm-refraction {
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(0, 120, 212, 0.15) 0%, transparent 50%);
}

.confirm-dialog::before {
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

[data-theme='dark'] .confirm-dialog::before {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.3) 0%,
    rgba(255, 255, 255, 0.1) 50%,
    rgba(255, 255, 255, 0.05) 100%
  );
}

.confirm-content-wrapper {
  position: relative;
  z-index: 2;
}

.confirm-header {
  padding: 24px 28px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.5) 0%,
    transparent 100%
  );
}

[data-theme='dark'] .confirm-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.05) 0%,
    transparent 100%
  );
}

.confirm-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--fui-text);
  letter-spacing: 0.3px;
}

.confirm-body {
  padding: 28px;
}

.confirm-body p {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: var(--fui-text-secondary);
}

.confirm-footer {
  display: flex;
  gap: 16px;
  padding: 0 28px 28px;
  justify-content: center;
  align-items: center;
}

.confirm-footer .btn {
  flex: 0 0 auto;
  min-width: 120px;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.confirm-footer .btn-secondary {
  background: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.15);
  color: var(--fui-text);
}

.confirm-footer .btn-secondary:hover {
  background: rgba(0, 0, 0, 0.1);
  border-color: rgba(0, 0, 0, 0.25);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.confirm-footer .btn-secondary:active {
  transform: translateY(0);
  box-shadow: none;
}

[data-theme='dark'] .confirm-footer .btn-secondary {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

[data-theme='dark'] .confirm-footer .btn-secondary:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
}

.confirm-footer .btn-primary {
  background: #0078d4;
  border-color: #0078d4;
  color: white;
}

.confirm-footer .btn-primary:hover {
  background: #106ebe;
  border-color: #106ebe;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 120, 212, 0.3);
}

.confirm-footer .btn-primary:active {
  transform: translateY(0);
  box-shadow: none;
}

[data-theme='dark'] .confirm-footer .btn-primary {
  background: #0078d4;
  border-color: #0078d4;
}

[data-theme='dark'] .confirm-footer .btn-primary:hover {
  background: #1a8ae8;
  border-color: #1a8ae8;
}

.confirm-dialog-enter-active {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.confirm-dialog-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 1, 1);
}

.confirm-dialog-enter-from {
  opacity: 0;
  transform: translateY(-30px) scale(0.9);
}

.confirm-dialog-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  50%, 100% {
    left: 100%;
  }
}
</style>

<template>
  <div class="custom-dropdown" ref="dropdownRef" :class="{ 'disabled': disabled }">
    <div class="dropdown-btn" @click="toggleDropdown" :class="{ 'disabled': disabled }">
      <FluentIcons v-if="selectedIconName" :name="selectedIconName" :size="18" />
      <span class="dropdown-label">{{ selectedLabel }}</span>
      <span class="arrow">
        <FluentIcons :name="isOpen ? 'arrow_up' : 'arrow_down'" :size="14" />
      </span>
    </div>

    <teleport to="body">
      <transition name="dropdown-fade">
        <div v-if="isOpen && !disabled" class="dropdown-panel-wrapper" :style="panelStyle">
          <ul 
            class="dropdown-panel" 
            @click="handlePanelClick"
          >
            <li
              v-for="option in options"
              :key="option.value"
              :class="{ selected: modelValue === option.value }"
              @click="selectOption(option)"
            >
              <FluentIcons v-if="option.iconName" :name="option.iconName" :size="18" />
              <span>{{ option.label }}</span>
            </li>
          </ul>
          <div class="panel-glass"></div>
          <div class="panel-refraction"></div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import FluentIcons from './FluentIcons.vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  options: {
    type: Array,
    required: true,
    default: () => []
  },
  placeholder: {
    type: String,
    default: '请选择'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const dropdownRef = ref(null)

const selectedOption = computed(() => {
  const found = props.options.find(opt => opt.value === props.modelValue)
  return found !== undefined ? found : null
})

const selectedLabel = computed(() => {
  if (selectedOption.value) {
    return selectedOption.value.label
  }
  return props.placeholder
})

const selectedIconName = computed(() => {
  if (selectedOption.value) {
    return selectedOption.value.iconName
  }
  return null
})

const panelStyle = computed(() => {
  if (!isOpen.value || !dropdownRef.value) {
    return {}
  }
  
  const rect = dropdownRef.value.getBoundingClientRect()
  return {
    position: 'fixed',
    top: `${rect.bottom + window.scrollY}px`,
    left: `${rect.left + window.scrollX}px`,
    width: `${rect.width}px`,
    zIndex: '9999',
  }
})

const toggleDropdown = () => {
  if (props.disabled) return
  isOpen.value = !isOpen.value
}

const selectOption = (option) => {
  if (props.disabled) return
  emit('update:modelValue', option.value)
  isOpen.value = false
}

const handlePanelClick = (event) => {
  event.stopPropagation()
}

const handleClickOutside = (event) => {
  const isClickInsideDropdown = dropdownRef.value && dropdownRef.value.contains(event.target)
  const isClickOnPanel = event.target.closest('.dropdown-panel')
  
  if (!isClickInsideDropdown && !isClickOnPanel) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.custom-dropdown {
  position: relative;
  width: 100%;
  min-width: 180px;
  z-index: 1;
}

.dropdown-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  height: 40px;
  padding: 0 1rem;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.9) 0%,
    rgba(255, 255, 255, 0.7) 100%
  );
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  font-size: 0.9rem;
  color: var(--fui-text);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.04),
    0 1px 2px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.dropdown-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.5) 0%,
    transparent 50%
  );
  pointer-events: none;
  border-radius: 8px;
}

[data-theme="dark"] .dropdown-btn {
  background: linear-gradient(
    135deg,
    rgba(50, 50, 50, 0.9) 0%,
    rgba(40, 40, 40, 0.7) 100%
  );
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.3),
    0 1px 2px rgba(0, 0, 0, 0.4);
}

[data-theme="dark"] .dropdown-btn::before {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.1) 0%,
    transparent 50%
  );
}

.dropdown-btn :deep(.fluent-icon:first-child) {
  position: relative;
  z-index: 1;
  color: #0078d4;
  font-size: 1rem;
  width: 1.5rem;
  text-align: center;
}

[data-theme="dark"] .dropdown-btn :deep(.fluent-icon:first-child) {
  color: #1a8ae8;
}

.dropdown-label {
  position: relative;
  z-index: 1;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-btn .arrow {
  position: relative;
  z-index: 1;
  font-size: 0.7rem;
  color: var(--fui-text-secondary);
  background: rgba(0, 0, 0, 0.05);
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

[data-theme="dark"] .dropdown-btn .arrow {
  background: rgba(255, 255, 255, 0.1);
}

.dropdown-btn:hover {
  border-color: rgba(0, 120, 212, 0.3);
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.95) 0%,
    rgba(255, 255, 255, 0.8) 100%
  );
  box-shadow: 
    0 4px 12px rgba(0, 120, 212, 0.15),
    0 2px 4px rgba(0, 0, 0, 0.06);
}

.dropdown-btn:hover .arrow {
  background: rgba(0, 120, 212, 0.1);
  color: #0078d4;
}

[data-theme="dark"] .dropdown-btn:hover {
  border-color: rgba(26, 138, 232, 0.4);
  background: linear-gradient(
    135deg,
    rgba(60, 60, 60, 0.95) 0%,
    rgba(50, 50, 50, 0.8) 100%
  );
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.4),
    0 2px 4px rgba(0, 0, 0, 0.5);
}

[data-theme="dark"] .dropdown-btn:hover .arrow {
  background: rgba(26, 138, 232, 0.2);
  color: #1a8ae8;
}

.dropdown-panel-wrapper {
  position: fixed;
  z-index: 9999;
  border-radius: 12px;
  overflow: hidden;
}

.dropdown-fade-enter-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.dropdown-fade-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}

.dropdown-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}

.dropdown-panel {
  position: relative;
  width: 100%;
  list-style: none;
  background: transparent;
  border-radius: 12px;
  padding: 0.5rem 0;
  box-shadow: 
    0 16px 48px rgba(0, 0, 0, 0.12),
    0 4px 12px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(0, 0, 0, 0.05);
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
  margin-top: 0;
}

.dropdown-panel::-webkit-scrollbar {
  width: 8px;
}

.dropdown-panel::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 0 12px 12px 0;
}

.dropdown-panel::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 4px;
}

.dropdown-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.25);
}

[data-theme="dark"] .dropdown-panel::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
}

[data-theme="dark"] .dropdown-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}

.panel-glass {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(24px) saturate(120%);
  -webkit-backdrop-filter: blur(24px) saturate(120%);
  z-index: 0;
  border-radius: 12px;
  pointer-events: none;
}

[data-theme="dark"] .panel-glass {
  background: rgba(40, 40, 40, 0.25);
}

.panel-refraction {
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
  border-radius: 12px;
}

[data-theme="dark"] .panel-refraction {
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(0, 120, 212, 0.15) 0%, transparent 50%);
}

.dropdown-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 12px;
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

[data-theme="dark"] .dropdown-panel::before {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.3) 0%,
    rgba(255, 255, 255, 0.1) 50%,
    rgba(255, 255, 255, 0.05) 100%
  );
}

.dropdown-panel li {
  position: relative;
  z-index: 2;
  padding: 0.6rem 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
  font-size: 0.9rem;
  color: var(--fui-text);
  cursor: pointer;
  transition: all 0.18s ease;
  margin: 0.15rem 0.5rem;
  border-radius: 8px;
}

.dropdown-panel li :deep(.fluent-icon) {
  position: relative;
  z-index: 2;
  width: 1.4rem;
  font-size: 1rem;
  color: var(--fui-text-secondary);
  text-align: center;
  transition: color 0.2s ease;
}

.dropdown-panel li span {
  position: relative;
  z-index: 2;
}

.dropdown-panel li:hover {
  background: rgba(0, 120, 212, 0.08);
}

.dropdown-panel li:hover :deep(.fluent-icon) {
  color: #0078d4;
}

[data-theme="dark"] .dropdown-panel li:hover {
  background: rgba(26, 138, 232, 0.15);
}

[data-theme="dark"] .dropdown-panel li:hover :deep(.fluent-icon) {
  color: #1a8ae8;
}

.dropdown-panel li.selected {
  position: relative;
  background: rgba(0, 120, 212, 0.12);
  font-weight: 500;
  color: #0078d4;
}

.dropdown-panel li.selected::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: #0078d4;
  border-radius: 2px;
}

.dropdown-panel li.selected :deep(.fluent-icon) {
  color: #0078d4;
}

[data-theme="dark"] .dropdown-panel li.selected {
  background: rgba(26, 138, 232, 0.2);
  color: #1a8ae8;
}

[data-theme="dark"] .dropdown-panel li.selected::before {
  background: #1a8ae8;
}

[data-theme="dark"] .dropdown-panel li.selected :deep(.fluent-icon) {
  color: #1a8ae8;
}

.custom-dropdown.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.dropdown-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
  background: linear-gradient(
    135deg,
    rgba(200, 200, 200, 0.5) 0%,
    rgba(180, 180, 180, 0.3) 100%
  );
}

[data-theme="dark"] .dropdown-btn.disabled {
  background: linear-gradient(
    135deg,
    rgba(80, 80, 80, 0.5) 0%,
    rgba(60, 60, 60, 0.3) 100%
  );
}
</style>
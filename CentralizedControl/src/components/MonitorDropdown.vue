<template>
  <div class="monitor-dropdown" ref="dropdownRef" :class="{ 'is-open': isOpen, 'has-value': modelValue !== '' }">
    <button class="md-trigger" @click="toggle" type="button">
      <FluentIcons v-if="selectedIcon" :name="selectedIcon" :size="16" class="md-icon" />
      <span class="md-label">{{ selectedLabel }}</span>
      <span class="md-arrow">
        <FluentIcons :name="isOpen ? 'arrow_up' : 'arrow_down'" :size="12" />
      </span>
    </button>

    <teleport to="body">
      <transition name="md-fade">
        <div v-if="isOpen" class="md-panel-wrap" :style="panelStyle">
          <ul class="md-panel" @click.stop>
            <li
              v-for="opt in options"
              :key="opt.value"
              class="md-option"
              :class="{ active: modelValue === opt.value }"
              @click="select(opt)"
            >
              <FluentIcons v-if="opt.iconName" :name="opt.iconName" :size="14" />
              <span>{{ opt.label }}</span>
            </li>
          </ul>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import FluentIcons from './FluentIcons.vue'

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  options: { type: Array, required: true },
  placeholder: { type: String, default: '请选择' }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const dropdownRef = ref(null)

const selectedLabel = computed(() => {
  const found = props.options.find(o => o.value === props.modelValue)
  return found ? found.label : props.placeholder
})

const selectedIcon = computed(() => {
  const found = props.options.find(o => o.value === props.modelValue)
  return found?.iconName || null
})

const panelStyle = computed(() => {
  if (!dropdownRef.value) return {}
  const r = dropdownRef.value.getBoundingClientRect()
  return {
    position: 'fixed',
    top: r.bottom + window.scrollY + 4 + 'px',
    left: r.left + window.scrollX + 'px',
    minWidth: r.width + 'px',
    zIndex: 10000
  }
})

function toggle() { isOpen.value = !isOpen.value }

function select(opt) {
  emit('update:modelValue', opt.value)
  isOpen.value = false
}

function onClickOutside(e) {
  if (!dropdownRef.value) return
  if (dropdownRef.value.contains(e.target)) return
  if (e.target.closest('.md-panel')) return
  isOpen.value = false
}

onMounted(() => document.addEventListener('click', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.monitor-dropdown {
  position: relative;
  user-select: none;
}

.md-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  height: 34px;
  padding: 0 10px;
  background: #1e1e1e;
  border: 1px solid #404040;
  border-radius: 5px;
  color: #ccc;
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  white-space: nowrap;
}
.md-trigger:hover { border-color: #555; background: #252525; }
.is-open .md-trigger { border-color: #0078d4; background: #252525; }
.has-value .md-trigger { color: #eee; }

.md-icon { color: #0078d4; flex-shrink: 0; }
.md-label { flex: 1; overflow: hidden; text-overflow: ellipsis; text-align: left; }
.md-arrow { color: #666; flex-shrink: 0; transition: transform 0.15s; }

/* 下拉面板 */
.md-panel-wrap {
  position: fixed;
  z-index: 10000;
  animation: md-in 0.12s ease-out;
}

.md-panel {
  list-style: none;
  margin: 0;
  padding: 4px 0;
  background: #1e1e1e;
  border: 1px solid #404040;
  border-radius: 6px;
  max-height: 260px;
  overflow-y: auto;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}

.md-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  color: #bbb;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
}
.md-option:hover { background: #2a2a2a; color: #eee; }
.md-option.active { color: #0078d4; background: rgba(0,120,212,0.12); }

/* 动画 */
.md-fade-enter-active { animation: md-in 0.12s ease-out; }
.md-fade-leave-active { animation: md-in 0.1s ease-in reverse; }
@keyframes md-in {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* 滚动条 */
.md-panel::-webkit-scrollbar { width: 5px; }
.md-panel::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
</style>

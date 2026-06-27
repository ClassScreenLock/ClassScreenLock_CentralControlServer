<template>
  <div class="profile-page">
    <!-- 页头 -->
    <div class="page-header">
      <div class="page-title">
        <FluentIcons name="person" :size="28" class="page-icon" />
        <h2>个人资料</h2>
      </div>
    </div>

    <div class="profile-content">
      <!-- 头像区域 -->
      <div class="profile-card">
        <h3>头像设置</h3>
        <p class="card-desc">选择默认头像或上传自定义图片 (JPG/PNG/GIF/WebP, 最大2MB)</p>
        <div class="avatar-section">
          <!-- 当前头像预览 -->
          <div class="avatar-preview">
            <div class="avatar-img-wrap">
              <img v-if="previewUrl" :src="previewUrl" class="avatar-img" alt="头像" />
              <svg v-else viewBox="0 0 24 24" fill="currentColor" class="avatar-placeholder">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
              </svg>
            </div>
            <div class="avatar-actions">
              <label class="upload-btn">
                <FluentIcons name="upload" :size="14" />
                上传图片
                <input type="file" accept="image/*" hidden @change="onFileSelect" />
              </label>
              <button v-if="previewUrl && previewUrl !== currentAvatarUrl" class="save-btn" @click="saveAvatar">
                <FluentIcons name="save" :size="14" />
                保存头像
              </button>
              <button v-if="previewUrl" class="reset-btn" @click="resetAvatar">重置</button>
            </div>
          </div>

          <!-- 默认头像选择 -->
          <div class="default-avatars">
            <span class="section-label">默认头像</span>
            <div class="avatar-grid">
              <button
                v-for="(dav, idx) in defaultAvatars"
                :key="idx"
                class="default-avatar-btn"
                :class="{ selected: previewUrl === dav.url && !customFile }"
                @click="selectDefaultAvatar(dav)"
              >
                <div class="default-avatar-circle" :style="{ background: dav.bg }">
                  <span class="default-avatar-letter">{{ dav.letter }}</span>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 昵称 -->
      <div class="profile-card">
        <h3>显示昵称</h3>
        <p class="card-desc">设置后在界面中显示的名称</p>
        <div class="nickname-row">
          <input v-model="nickname" class="input-field" placeholder="输入昵称（留空则使用用户名）" maxlength="20" />
          <button class="save-btn" @click="saveNickname" :disabled="nickname === (user?.nickname || '')">
            <FluentIcons name="save" :size="14" />
            保存
          </button>
        </div>
      </div>

      <!-- 修改密码 -->
      <div class="profile-card">
        <h3>修改密码</h3>
        <p class="card-desc">定期更换密码以保护账户安全</p>
        <div class="password-form">
          <div class="form-row">
            <label>当前密码</label>
            <div class="pwd-input-wrap">
              <input :type="showCurrent ? 'text' : 'password'" v-model="pwd.current" class="input-field" placeholder="输入当前密码" />
              <button class="pwd-toggle" @click="showCurrent = !showCurrent">
                <FluentIcons :name="showCurrent ? 'eye_off' : 'eye'" :size="16" />
              </button>
            </div>
          </div>
          <div class="form-row">
            <label>新密码</label>
            <div class="pwd-input-wrap">
              <input :type="showNew ? 'text' : 'password'" v-model="pwd.newPass" class="input-field" placeholder="至少6位" />
              <button class="pwd-toggle" @click="showNew = !showNew">
                <FluentIcons :name="showNew ? 'eye_off' : 'eye'" :size="16" />
              </button>
            </div>
          </div>
          <div class="form-row">
            <label>确认密码</label>
            <input :type="showNew ? 'text' : 'password'" v-model="pwd.confirm" class="input-field" placeholder="再次输入新密码" />
          </div>
          <button class="save-btn" @click="changePassword" :disabled="!canChangePwd">
            <FluentIcons name="lock" :size="14" />
            修改密码
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import FluentIcons from '@/components/FluentIcons.vue'
import { authAPI } from '@/api/auth'
import { notify } from '@/utils/notification'

const user = ref(null)
const nickname = ref('')
const currentAvatarUrl = ref('')
const previewUrl = ref('')
const customFile = ref(null)
const showCurrent = ref(false)
const showNew = ref(false)
const pwd = ref({ current: '', newPass: '', confirm: '' })

const canChangePwd = computed(() =>
  pwd.value.current && pwd.value.newPass.length >= 6 && pwd.value.newPass === pwd.value.confirm
)

const defaultAvatars = [
  { url: '', bg: '#0078d4', letter: user.value?.username?.[0]?.toUpperCase() || 'U' },
  { url: '', bg: '#10b981', letter: '' },
  { url: '', bg: '#f59e0b', letter: '' },
  { url: '', bg: '#ef4444', letter: '' },
  { url: '', bg: '#8b5cf6', letter: '' },
  { url: '', bg: '#06b6d4', letter: '' },
]

// 加载用户信息
const loadUser = async () => {
  const userData = localStorage.getItem('user')
  if (!userData) return
  try {
    const parsed = JSON.parse(userData)
    const fresh = await authAPI.getCurrentUser()
    user.value = { ...parsed, ...fresh }
    nickname.value = fresh.nickname || ''
    currentAvatarUrl.value = fresh.avatarUrl || ''
    previewUrl.value = fresh.avatarUrl || ''
    // 更新 localStorage
    localStorage.setItem('user', JSON.stringify({ ...parsed, avatarUrl: fresh.avatarUrl, nickname: fresh.nickname }))
  } catch {
    user.value = JSON.parse(userData)
    nickname.value = user.value.nickname || ''
    previewUrl.value = user.value.avatarUrl || ''
  }
}

// 更新默认头像的第一个字母
const updateDefaultAvatars = () => {
  if (user.value?.username) {
    defaultAvatars[0].letter = user.value.username[0].toUpperCase()
  }
}

// 文件选择
const onFileSelect = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    notify.warning('图片大小不能超过 2MB')
    return
  }
  if (!['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)) {
    notify.warning('仅支持 JPG/PNG/GIF/WebP 格式')
    return
  }
  customFile.value = file
  const reader = new FileReader()
  reader.onload = () => { previewUrl.value = reader.result }
  reader.readAsDataURL(file)
}

// 选择默认头像
const selectDefaultAvatar = (dav) => {
  customFile.value = null
  previewUrl.value = `__default__${dav.bg}`
}

// 重置
const resetAvatar = () => {
  customFile.value = null
  previewUrl.value = currentAvatarUrl.value
}

// 保存头像
const saveAvatar = async () => {
  if (!customFile.value && previewUrl.value === currentAvatarUrl.value) {
    return
  }
  try {
    let imageB64 = previewUrl.value
    if (customFile.value) {
      // 使用已有预览的 data URL
    } else if (previewUrl.value.startsWith('__default__')) {
      // 默认头像：生成一个纯色 SVG
      const color = previewUrl.value.replace('__default__', '')
      const letter = user.value?.username?.[0]?.toUpperCase() || 'U'
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="${color}"/><text x="100" y="130" text-anchor="middle" fill="white" font-size="100" font-family="sans-serif">${letter}</text></svg>`
      imageB64 = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)))
    }
    const res = await authAPI.uploadAvatar(imageB64)
    currentAvatarUrl.value = res.avatarUrl
    previewUrl.value = res.avatarUrl
    customFile.value = null
    updateLocalUser({ avatarUrl: res.avatarUrl })
    notify.success('头像已更新')
  } catch (e) {
    notify.error(e?.response?.data?.error || '头像上传失败')
  }
}

// 保存昵称
const saveNickname = async () => {
  try {
    await authAPI.updateProfile({ nickname: nickname.value })
    updateLocalUser({ nickname: nickname.value })
    notify.success('昵称已更新')
  } catch (e) {
    notify.error('保存失败')
  }
}

// 修改密码
const changePassword = async () => {
  if (!canChangePwd.value) return
  try {
    await authAPI.changePassword({
      currentPassword: pwd.value.current,
      newPassword: pwd.value.newPass
    })
    pwd.value = { current: '', newPass: '', confirm: '' }
    notify.success('密码已修改，请重新登录')
    setTimeout(() => {
      localStorage.removeItem('user')
      window.location.href = '/login'
    }, 1500)
  } catch (e) {
    notify.error(e?.response?.data?.error || '修改密码失败')
  }
}

const updateLocalUser = (update) => {
  const stored = localStorage.getItem('user')
  if (stored) {
    const parsed = JSON.parse(stored)
    localStorage.setItem('user', JSON.stringify({ ...parsed, ...update }))
  }
}

onMounted(() => {
  loadUser().then(updateDefaultAvatars)
})
</script>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  max-width: 700px;
  margin: 0 auto;
  width: 100%;
}

.page-header { padding: 8px 0; }
.page-title { display: flex; align-items: center; gap: 12px; }
.page-icon { color: var(--fui-text); opacity: 0.9; }
.page-title h2 { margin: 0; font-size: 1.25em; font-weight: 600; color: var(--fui-text); }

.profile-content { display: flex; flex-direction: column; gap: 16px; }

.profile-card {
  background: var(--fui-surface);
  border: 1px solid var(--fui-border);
  border-radius: 12px;
  padding: 24px;
}

.profile-card h3 { margin: 0 0 4px; font-size: 1em; color: var(--fui-text); }
.card-desc { margin: 0 0 16px; font-size: 0.8em; color: var(--fui-text-secondary); }

/* 头像区域 */
.avatar-section { display: flex; gap: 32px; align-items: flex-start; flex-wrap: wrap; }
.avatar-preview { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.avatar-img-wrap {
  width: 100px; height: 100px; border-radius: 50%; overflow: hidden;
  background: linear-gradient(135deg, #0078d4, #106ebe);
  display: flex; align-items: center; justify-content: center;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder { width: 50px; height: 50px; color: rgba(255,255,255,0.6); }

.avatar-actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }

.upload-btn, .save-btn, .reset-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer;
  transition: all 0.15s; border: 1px solid var(--fui-border);
  background: var(--fui-background); color: var(--fui-text);
}
.upload-btn:hover, .reset-btn:hover { background: var(--fui-border); }
.save-btn { background: #0078d4; border-color: #0078d4; color: white; }
.save-btn:hover { background: #106ebe; }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* 默认头像 */
.default-avatars { display: flex; flex-direction: column; gap: 10px; }
.section-label { font-size: 0.8em; color: var(--fui-text-secondary); font-weight: 500; }
.avatar-grid { display: flex; gap: 10px; flex-wrap: wrap; }
.default-avatar-btn {
  width: 56px; height: 56px; border-radius: 50%; border: 3px solid transparent;
  background: transparent; cursor: pointer; padding: 0; transition: border-color 0.2s;
}
.default-avatar-btn:hover { border-color: var(--fui-border); }
.default-avatar-btn.selected { border-color: #0078d4; box-shadow: 0 0 0 2px rgba(0,120,212,0.3); }
.default-avatar-circle {
  width: 100%; height: 100%; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.default-avatar-letter {
  color: white; font-size: 22px; font-weight: 700; user-select: none;
}

/* 昵称 */
.nickname-row { display: flex; gap: 10px; }
.nickname-row .input-field { flex: 1; }

/* 密码 */
.password-form { display: flex; flex-direction: column; gap: 12px; max-width: 360px; }
.form-row { display: flex; flex-direction: column; gap: 4px; }
.form-row label { font-size: 0.8em; font-weight: 500; color: var(--fui-text-secondary); }
.pwd-input-wrap { position: relative; }
.pwd-input-wrap .input-field { padding-right: 36px; }
.pwd-toggle {
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  background: none; border: none; color: var(--fui-text-secondary);
  cursor: pointer; padding: 4px; border-radius: 4px;
}
.pwd-toggle:hover { color: var(--fui-text); background: var(--fui-background); }

.input-field {
  width: 100%; padding: 10px 14px; border: 1px solid var(--fui-border);
  border-radius: 8px; font-size: 14px; background: var(--fui-background);
  color: var(--fui-text); outline: none; transition: border-color 0.2s;
}
.input-field:focus { border-color: var(--fui-primary); }

@media (max-width: 768px) {
  .profile-page { padding: 12px; }
  .profile-card { padding: 16px; }
  .avatar-section { gap: 20px; }
  .nickname-row { flex-direction: column; }
}
</style>

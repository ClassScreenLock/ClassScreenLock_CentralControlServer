<template>
  <div class="login-container">
    <div class="login-bg"></div>
    <div class="login-bg-overlay"></div>
    
    <Transition name="login-fade" appear>
      <div class="login-card">
        <div class="card-glass"></div>
        <div class="card-refraction"></div>
        <div class="card-content">
          <div class="login-header">
            <div class="logo-wrapper">
              <div class="logo-icon">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor" opacity="0.9"/>
                  <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            <h1>ClassScreenLock</h1>
            <p>集控管理平台</p>
          </div>
          
          <div class="login-body">
            <form @submit.prevent="handleLogin">
              <div class="form-group">
                <label>用户名</label>
                <div class="input-wrapper">
                  <span class="input-icon">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
                    </svg>
                  </span>
                  <input 
                    type="text" 
                    v-model="username" 
                    class="input-field" 
                    placeholder="请输入用户名"
                    required
                    autocomplete="off"
                  >
                </div>
              </div>
              
              <div class="form-group">
                <label>密码</label>
                <div class="input-wrapper">
                  <span class="input-icon">
                    <svg viewBox="0 0 20 20" fill="currentColor">
                      <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd"/>
                    </svg>
                  </span>
                  <input 
                    type="password" 
                    v-model="password" 
                    class="input-field" 
                    placeholder="请输入密码"
                    required
                    autocomplete="off"
                  >
                </div>
              </div>
              
              <div class="form-group" v-if="error">
                <div class="error-message">{{ error }}</div>
              </div>
              
              <button type="submit" class="login-button" :disabled="loading">
                <span v-if="!loading">登录</span>
                <span v-else class="loading-spinner">
                  <svg class="spinner-icon" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity="0.3"/>
                    <path d="M12 2a10 10 0 0110 10" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                  </svg>
                  <span>登录中...</span>
                </span>
              </button>
            </form>
            
            <div class="login-footer">
              <p class="hint">请使用您的账户和密码登录</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authAPI } from '@/api/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const user = await authAPI.login({
      username: username.value,
      password: password.value
    })
    
    localStorage.removeItem('user')
    localStorage.removeItem('tokenExpiresAt')
    
    localStorage.setItem('user', JSON.stringify(user))
    if (user.expiresAt) {
      localStorage.setItem('tokenExpiresAt', user.expiresAt)
    }
    
    await router.push('/dashboard')
  } catch (err) {
    console.error('登录失败:', err)
    error.value = err.response?.data?.error || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(0, 120, 212, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(0, 120, 212, 0.1) 0%, transparent 50%),
    linear-gradient(135deg, #f0f4f8 0%, #e8eef5 50%, #dde5ed 100%);
  z-index: 0;
}

[data-theme='dark'] .login-bg {
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(26, 138, 232, 0.2) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(26, 138, 232, 0.15) 0%, transparent 50%),
    linear-gradient(135deg, #0a1929 0%, #152238 50%, #1a2d45 100%);
}

.login-bg-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%230078d4' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.5;
  z-index: 1;
}

.login-card {
  position: relative;
  width: 100%;
  max-width: 440px;
  margin: 20px;
  z-index: 2;
}

.card-glass {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(40px) saturate(150%);
  -webkit-backdrop-filter: blur(40px) saturate(150%);
  border-radius: 20px;
  box-shadow: 
    0 32px 64px rgba(0, 0, 0, 0.12),
    0 12px 24px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.3) inset;
}

[data-theme='dark'] .card-glass {
  background: rgba(30, 30, 30, 0.6);
  box-shadow: 
    0 32px 64px rgba(0, 0, 0, 0.4),
    0 12px 24px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
}

.card-refraction {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(ellipse at 30% 20%, rgba(255, 255, 255, 0.4) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(0, 120, 212, 0.08) 0%, transparent 50%);
  border-radius: 20px;
  pointer-events: none;
}

[data-theme='dark'] .card-refraction {
  background: 
    radial-gradient(ellipse at 30% 20%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 80%, rgba(26, 138, 232, 0.1) 0%, transparent 50%);
}

.card-content {
  position: relative;
  z-index: 1;
  padding: 48px 40px;
}

.login-fade-enter-active {
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-fade-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.98);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.logo-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #0078d4 0%, #106ebe 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 
    0 8px 16px rgba(0, 120, 212, 0.3),
    0 2px 4px rgba(0, 120, 212, 0.2);
}

.logo-icon svg {
  width: 32px;
  height: 32px;
}

.login-header h1 {
  font-size: 26px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

[data-theme='dark'] .login-header h1 {
  color: #ffffff;
}

.login-header p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

[data-theme='dark'] .login-header p {
  color: #999;
}

.login-body {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #444;
}

[data-theme='dark'] .form-group label {
  color: #ccc;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  height: 44px;
}

.input-icon {
  position: absolute;
  left: 14px;
  width: 18px;
  height: 18px;
  color: #888;
  pointer-events: none;
  transition: color 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.input-icon svg {
  width: 18px;
  height: 18px;
  display: block;
}

.input-field {
  width: 100%;
  padding: 12px 14px 12px 44px;
  font-size: 14px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.3);
  color: #1a1a1a;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
  position: relative;
  z-index: 0;
}

.input-field::placeholder {
  color: #999;
}

.input-field:focus {
  outline: none;
  border-color: #0078d4;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 
    0 0 0 3px rgba(0, 120, 212, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.05);
}

.input-field:focus + .input-icon,
.input-wrapper:focus-within .input-icon {
  color: #0078d4;
}

[data-theme='dark'] .input-field {
  background: rgba(50, 50, 50, 0.6);
  border-color: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

[data-theme='dark'] .input-field::placeholder {
  color: #777;
}

[data-theme='dark'] .input-field:focus {
  background: rgba(60, 60, 60, 0.8);
  border-color: #1a8ae8;
  box-shadow: 
    0 0 0 3px rgba(26, 138, 232, 0.2),
    0 2px 8px rgba(0, 0, 0, 0.3);
}

[data-theme='dark'] .input-wrapper:focus-within .input-icon {
  color: #1a8ae8;
}

.error-message {
  padding: 10px 14px;
  background: rgba(220, 53, 69, 0.08);
  color: #dc3545;
  border-radius: 8px;
  font-size: 13px;
  border: 1px solid rgba(220, 53, 69, 0.2);
}

[data-theme='dark'] .error-message {
  background: rgba(220, 53, 69, 0.15);
  color: #ff6b7a;
  border-color: rgba(220, 53, 69, 0.3);
}

.login-button {
  width: 100%;
  padding: 13px 24px;
  font-size: 14px;
  font-weight: 600;
  background: #0078d4;
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 
    0 4px 12px rgba(0, 120, 212, 0.3),
    0 2px 4px rgba(0, 120, 212, 0.2);
}

.login-button:hover:not(:disabled) {
  background: #106ebe;
  transform: translateY(-1px);
  box-shadow: 
    0 6px 16px rgba(0, 120, 212, 0.35),
    0 3px 6px rgba(0, 120, 212, 0.25);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 
    0 2px 8px rgba(0, 120, 212, 0.3),
    0 1px 2px rgba(0, 120, 212, 0.2);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.spinner-icon {
  width: 18px;
  height: 18px;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.login-footer {
  text-align: center;
}

.hint {
  font-size: 12px;
  color: #888;
  margin: 0;
}

[data-theme='dark'] .hint {
  color: #777;
}

@media (max-width: 480px) {
  .card-content {
    padding: 36px 28px;
  }
  
  .login-card {
    margin: 16px;
  }
}
</style>

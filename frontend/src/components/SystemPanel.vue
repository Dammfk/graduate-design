<template>
  <section class="system-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">系统与权限</p>
        <h2>系统与权限管理</h2>
      </div>
      <span class="summary-badge">活跃用户 {{ summary.active_users || 0 }} 人</span>
    </div>

    <div v-if="feedback.message" class="feedback" :class="feedback.type">
      {{ feedback.message }}
    </div>

    <div class="summary-grid">
      <div><span>系统用户</span><strong>{{ summary.user_count || 0 }}</strong></div>
      <div><span>角色类型</span><strong>{{ summary.role_count || 0 }}</strong></div>
      <div><span>活跃用户</span><strong>{{ summary.active_users || 0 }}</strong></div>
      <div><span>操作日志</span><strong>{{ summary.log_count || 0 }}</strong></div>
    </div>

    <div class="system-grid">
      <div class="records-box">
        <h3>用户管理</h3>
        <div class="user-list">
          <article v-for="user in users" :key="user.id" class="user-card">
            <div class="card-top">
              <strong>{{ user.username }}</strong>
              <span class="status-tag" :class="user.is_active ? 'completed' : 'pending'">
                {{ user.is_active ? '启用中' : '已停用' }}
              </span>
            </div>
            <p>{{ user.email }}</p>
            <div class="user-actions">
              <select :value="user.role" :disabled="busyUserId === user.id" @change="updateUser(user.id, { role: $event.target.value })">
                <option value="admin">管理员</option>
                <option value="manager">技术人员</option>
                <option value="operator">基础工作人员</option>
                <option value="viewer">访客</option>
              </select>
              <button class="ghost-btn" :disabled="busyUserId === user.id" @click="updateUser(user.id, { is_active: !user.is_active })">
                {{ busyUserId === user.id ? '提交中...' : user.is_active ? '停用' : '启用' }}
              </button>
            </div>
          </article>
        </div>
      </div>

      <div class="records-box">
        <h3>角色权限</h3>
        <div class="permission-list">
          <article v-for="item in rolePermissions" :key="item.role" class="permission-card">
            <strong>{{ roleLabel(item.role) }}</strong>
            <p>{{ item.permissions.join(' / ') }}</p>
          </article>
        </div>
      </div>

      <div class="records-box">
        <h3>最近操作日志</h3>
        <div class="log-list">
          <article v-for="log in operationLogs" :key="log.id" class="log-card">
            <div class="card-top">
              <strong>{{ log.username }}</strong>
              <span>{{ log.module_name }}</span>
            </div>
            <p>{{ log.action }} / {{ log.target || '未指定对象' }}</p>
            <small>{{ log.detail || '无详细说明' }}</small>
            <small>{{ formatDateTime(log.created_at) }}</small>
          </article>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'

const props = defineProps({
  summary: { type: Object, default: () => ({}) },
  users: { type: Array, default: () => [] },
  rolePermissions: { type: Array, default: () => [] },
  operationLogs: { type: Array, default: () => [] },
  onUpdateUser: { type: Function, required: true }
})

const feedback = reactive({ type: '', message: '' })
const busyUserId = ref(null)

function setFeedback(type, message) {
  feedback.type = type
  feedback.message = message
}

function normalizeError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback
}

function roleLabel(role) {
  return { admin: '管理员', manager: '技术人员', operator: '基础工作人员', viewer: '访客' }[role] || role
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}

async function updateUser(userId, payload) {
  busyUserId.value = userId
  try {
    await props.onUpdateUser(userId, payload)
    setFeedback('success', '用户信息已更新。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '用户信息更新失败。'))
  } finally {
    busyUserId.value = null
  }
}
</script>

<style scoped lang="scss">
.system-panel{display:flex;flex-direction:column;gap:16px}.panel-header{display:flex;justify-content:space-between;gap:12px}.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}h2,h3{margin:0;color:#f3f7fa}.summary-badge{align-self:flex-start;padding:6px 12px;border-radius:999px;background:rgba(125,207,116,.12);color:#d6f2cf}
.feedback{padding:12px 14px;border-radius:14px;font-size:14px}.feedback.success{background:rgba(79,169,143,.18);color:#c8f0e6}.feedback.error{background:rgba(255,107,107,.16);color:#ffd3d3}
.summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.summary-grid div,.records-box{padding:14px;border-radius:16px;background:rgba(10,33,39,.88)}.summary-grid span{display:block;color:#87a5ac;font-size:12px;margin-bottom:6px}.summary-grid strong{font-size:20px}
.system-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.user-list,.permission-list,.log-list{display:grid;gap:10px}
.user-card,.permission-card,.log-card{padding:14px;border-radius:14px;background:rgba(7,24,29,.88)}.card-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.user-card p,.permission-card p,.log-card p,.log-card small{margin:0;color:#98b0b5}
.user-actions{display:flex;gap:10px;margin-top:12px}.user-actions select,.ghost-btn{height:38px;padding:0 12px;border-radius:12px}.user-actions select{border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8}.ghost-btn{border:1px solid rgba(164,215,210,.18);background:transparent;color:#eaf3f5;cursor:pointer}.ghost-btn:disabled,.user-actions select:disabled{opacity:.6;cursor:not-allowed}
.status-tag{padding:4px 8px;border-radius:999px;font-size:12px}.status-tag.pending{background:rgba(255,200,87,.12);color:#ffe2a4}.status-tag.completed{background:rgba(125,207,116,.12);color:#d6f2cf}
@media (max-width:1100px){.summary-grid,.system-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>

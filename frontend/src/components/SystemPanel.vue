<template>
  <section class="system-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">System Access</p>
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
      <div><span>最近日志</span><strong>{{ summary.log_count || 0 }}</strong></div>
    </div>

    <div class="system-grid">
      <div class="records-box">
        <h3>用户管理</h3>
        <div class="user-list">
          <article v-for="user in displayUsers" :key="user.id" class="user-card">
            <div class="card-top">
              <strong>{{ user.username }}</strong>
              <span class="status-tag" :class="user.is_active ? 'completed' : 'pending'">
                {{ user.is_active ? '已启用' : '已停用' }}
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
              <button class="ghost-btn" :disabled="logLoadingUserId === user.id" @click="openUserLogs(user)">
                {{ logLoadingUserId === user.id ? '加载中...' : '查看日志' }}
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

    <div v-if="showLogModal" class="modal-mask" @click.self="closeLogModal">
      <div class="modal-card">
        <div class="detail-header">
          <div>
            <h3>{{ currentLogUser?.username || '用户' }} 的操作日志</h3>
            <p class="modal-subtitle">{{ currentLogUser?.email || '' }}</p>
          </div>
          <button class="ghost-btn" type="button" @click="closeLogModal">关闭</button>
        </div>

        <div v-if="logModalError" class="feedback error">
          {{ logModalError }}
        </div>

        <div v-if="userLogs.length" class="log-list modal-log-list">
          <article v-for="log in userLogs" :key="log.id" class="log-card">
            <div class="card-top">
              <strong>{{ log.action }}</strong>
              <span>{{ log.module_name }}</span>
            </div>
            <p>{{ log.target || '未指定对象' }}</p>
            <small>{{ log.detail || '无详细说明' }}</small>
            <small>{{ formatDateTime(log.created_at) }}</small>
          </article>
        </div>
        <p v-else-if="!logModalLoading" class="empty-text">该用户暂时没有历史操作日志。</p>
        <p v-if="logModalLoading" class="empty-text">正在加载历史日志...</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  summary: { type: Object, default: () => ({}) },
  users: { type: Array, default: () => [] },
  rolePermissions: { type: Array, default: () => [] },
  operationLogs: { type: Array, default: () => [] },
  onUpdateUser: { type: Function, required: true },
  onViewUserLogs: { type: Function, required: true }
})

const feedback = reactive({ type: '', message: '' })
const busyUserId = ref(null)
const logLoadingUserId = ref(null)
const showLogModal = ref(false)
const logModalLoading = ref(false)
const logModalError = ref('')
const currentLogUser = ref(null)
const userLogs = ref([])
const optimisticUsers = ref([])

const displayUsers = computed(() => optimisticUsers.value)

watch(
  () => props.users,
  (value) => {
    optimisticUsers.value = (value || []).map(user => ({ ...user }))
  },
  { immediate: true, deep: true }
)

function setFeedback(type, message) {
  feedback.type = type
  feedback.message = message
}

function normalizeError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback
}

function roleLabel(role) {
  return {
    admin: '管理员',
    manager: '技术人员',
    operator: '基础工作人员',
    viewer: '访客'
  }[role] || role
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}

function closeLogModal() {
  showLogModal.value = false
  logModalLoading.value = false
  logModalError.value = ''
  currentLogUser.value = null
  userLogs.value = []
}

async function updateUser(userId, payload) {
  busyUserId.value = userId
  const index = optimisticUsers.value.findIndex(user => user.id === userId)
  const previousUser = index >= 0 ? { ...optimisticUsers.value[index] } : null

  if (index >= 0) {
    optimisticUsers.value[index] = {
      ...optimisticUsers.value[index],
      ...payload
    }
  }

  try {
    await props.onUpdateUser(userId, payload)
    setFeedback('success', '用户信息已更新。')
  } catch (error) {
    if (previousUser && index >= 0) {
      optimisticUsers.value[index] = previousUser
    }
    setFeedback('error', normalizeError(error, '用户信息更新失败。'))
  } finally {
    busyUserId.value = null
  }
}

async function openUserLogs(user) {
  currentLogUser.value = user
  showLogModal.value = true
  logModalLoading.value = true
  logModalError.value = ''
  userLogs.value = []
  logLoadingUserId.value = user.id
  try {
    const result = await props.onViewUserLogs(user.id, 30)
    userLogs.value = result.logs || []
  } catch (error) {
    logModalError.value = normalizeError(error, '查询用户历史操作日志失败。')
  } finally {
    logModalLoading.value = false
    logLoadingUserId.value = null
  }
}
</script>

<style scoped lang="scss">
.system-panel{display:flex;flex-direction:column;gap:16px}
.panel-header,.card-top,.detail-header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}
h2,h3{margin:0;color:#f3f7fa}
.modal-subtitle{margin:6px 0 0;color:#8ea9af;font-size:13px}
.summary-badge{align-self:flex-start;padding:6px 12px;border-radius:999px;background:rgba(125,207,116,.12);color:#d6f2cf}
.feedback{padding:12px 14px;border-radius:14px;font-size:14px}
.feedback.success{background:rgba(79,169,143,.18);color:#c8f0e6}
.feedback.error{background:rgba(255,107,107,.16);color:#ffd3d3}
.summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.summary-grid div,.records-box{padding:14px;border-radius:16px;background:rgba(10,33,39,.88)}
.summary-grid span{display:block;color:#87a5ac;font-size:12px;margin-bottom:6px}
.summary-grid strong{font-size:20px}
.system-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.user-list,.permission-list,.log-list{display:grid;gap:10px}
.user-card,.permission-card,.log-card{padding:14px;border-radius:14px;background:rgba(7,24,29,.88)}
.user-card p,.permission-card p,.log-card p,.log-card small,.empty-text{margin:0;color:#98b0b5}
.user-actions{display:flex;gap:10px;margin-top:12px;flex-wrap:wrap}
.user-actions select,.ghost-btn{height:38px;padding:0 12px;border-radius:12px}
.user-actions select{border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8}
.ghost-btn{border:1px solid rgba(164,215,210,.18);background:transparent;color:#eaf3f5;cursor:pointer}
.ghost-btn:disabled,.user-actions select:disabled{opacity:.6;cursor:not-allowed}
.status-tag{padding:4px 8px;border-radius:999px;font-size:12px}
.status-tag.pending{background:rgba(255,200,87,.12);color:#ffe2a4}
.status-tag.completed{background:rgba(125,207,116,.12);color:#d6f2cf}
.modal-mask{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(2,10,13,.66);backdrop-filter:blur(8px);z-index:30}
.modal-card{width:min(760px,100%);display:grid;gap:16px;padding:22px;border-radius:24px;background:rgba(9,27,32,.98);border:1px solid rgba(176,224,221,.14);box-shadow:0 24px 60px rgba(0,0,0,.35)}
.modal-log-list{max-height:420px;overflow:auto}
@media (max-width:1100px){.summary-grid,.system-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:720px){.summary-grid,.system-grid{grid-template-columns:1fr}}
</style>

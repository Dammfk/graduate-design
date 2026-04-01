<template>
  <section class="system-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">System Access</p>
        <h2>系统与权限管理</h2>
        <p class="panel-subtitle">用户管理、角色权限和近期操作记录分区展示，页面更清晰。</p>
      </div>
      <span class="summary-badge">活跃用户 {{ summary.active_users || 0 }} 人</span>
    </div>

    <div v-if="feedback.message" class="feedback" :class="feedback.type">
      {{ feedback.message }}
    </div>

    <div class="summary-grid compact">
      <div class="summary-card">
        <span>系统用户</span>
        <strong>{{ summary.user_count || 0 }}</strong>
      </div>
      <div class="summary-card">
        <span>角色类型</span>
        <strong>{{ summary.role_count || 0 }}</strong>
      </div>
      <div class="summary-card">
        <span>活跃用户</span>
        <strong>{{ summary.active_users || 0 }}</strong>
      </div>
      <div class="summary-card">
        <span>日志总数</span>
        <strong>{{ summary.log_count || 0 }}</strong>
      </div>
    </div>

    <div class="top-grid">
      <section class="records-box">
        <div class="section-head">
          <div>
            <p class="eyebrow">Users</p>
            <h3>用户管理</h3>
            <p>支持启用、停用、切换角色和查看个人操作日志。</p>
          </div>
          <span class="count-tag">{{ displayUsers.length }}</span>
        </div>

        <div class="user-list compact-scroll">
          <article v-for="user in displayUsers" :key="user.id" class="user-card">
            <div class="user-top">
              <div>
                <strong>{{ user.username }}</strong>
                <p>{{ user.email }}</p>
              </div>
              <span class="status-tag" :class="user.is_active ? 'completed' : 'pending'">
                {{ user.is_active ? '已启用' : '已停用' }}
              </span>
            </div>

            <div class="user-role-row">
              <span>当前角色：{{ roleLabel(user.role) }}</span>
              <span>用户 ID：{{ user.id }}</span>
            </div>

            <div class="user-actions">
              <select :value="user.role" :disabled="isUserPending(user.id)" @change="updateUser(user.id, { role: $event.target.value })">
                <option value="admin">管理员</option>
                <option value="manager">技术人员</option>
                <option value="operator">基础工作人员</option>
                <option value="viewer">访客</option>
              </select>
              <button class="ghost-btn" :disabled="isUserPending(user.id)" @click="updateUser(user.id, { is_active: !user.is_active })">
                {{ isUserPending(user.id) ? '提交中...' : (user.is_active ? '停用' : '启用') }}
              </button>
              <button class="ghost-btn" :disabled="logLoadingUserId === user.id" @click="openUserLogs(user)">
                {{ logLoadingUserId === user.id ? '加载中...' : '查看日志' }}
              </button>
            </div>
          </article>
        </div>
      </section>

      <section class="records-box">
        <div class="section-head">
          <div>
            <p class="eyebrow">Permissions</p>
            <h3>角色权限</h3>
            <p>不同角色可访问的模块和操作能力一目了然。</p>
          </div>
        </div>

        <div class="permission-list compact-scroll">
          <article v-for="item in rolePermissions" :key="item.role" class="permission-card">
            <div class="permission-top">
              <strong>{{ roleLabel(item.role) }}</strong>
              <span class="permission-badge">{{ item.permissions.length }} 项</span>
            </div>
            <p>{{ item.permissions.join(' / ') }}</p>
          </article>
        </div>
      </section>
    </div>

    <section class="history-panel compact-panel">
      <div class="panel-header">
        <div>
          <p class="eyebrow">Operation Logs</p>
          <h2>近期操作日志</h2>
        </div>
        <span class="history-count">{{ operationLogs.length }}</span>
      </div>

      <div v-if="pagedLogs.length === 0" class="empty-state">暂无操作日志。</div>

      <template v-else>
        <div class="history-list compact-history">
          <article v-for="log in pagedLogs" :key="log.id" class="history-card">
            <div class="history-top">
              <strong>{{ log.username }}</strong>
              <span class="mode">{{ log.module_name }}</span>
            </div>
            <p>{{ log.action }} / {{ log.target || '未指定对象' }}</p>
            <small>{{ log.detail || '无详细说明' }}</small>
            <time>{{ formatDateTime(log.created_at) }}</time>
          </article>
        </div>

        <div class="pagination-bar">
          <button class="ghost-btn" type="button" :disabled="currentPage === 1" @click="currentPage -= 1">上一页</button>
          <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
          <button class="ghost-btn" type="button" :disabled="currentPage >= totalPages" @click="currentPage += 1">下一页</button>
        </div>
      </template>
    </section>

    <div v-if="showLogModal" class="modal-mask" @click.self="closeLogModal">
      <div class="modal-card">
        <div class="detail-header">
          <div>
            <h3>{{ currentLogUser?.username || '用户' }} 的历史日志</h3>
            <p class="modal-subtitle">{{ currentLogUser?.email || '' }}</p>
          </div>
          <button class="ghost-btn" type="button" @click="closeLogModal">关闭</button>
        </div>

        <div v-if="logModalError" class="feedback error">
          {{ logModalError }}
        </div>

        <div v-if="userLogs.length" class="history-list modal-log-list">
          <article v-for="log in userLogs" :key="log.id" class="history-card">
            <div class="history-top">
              <strong>{{ log.action }}</strong>
              <span class="mode">{{ log.module_name }}</span>
            </div>
            <p>{{ log.target || '未指定对象' }}</p>
            <small>{{ log.detail || '无详细说明' }}</small>
            <time>{{ formatDateTime(log.created_at) }}</time>
          </article>
        </div>
        <p v-else-if="!logModalLoading" class="empty-state">该用户暂时没有历史操作日志。</p>
        <p v-if="logModalLoading" class="empty-state">正在加载历史日志...</p>
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
const logLoadingUserId = ref(null)
const showLogModal = ref(false)
const logModalLoading = ref(false)
const logModalError = ref('')
const currentLogUser = ref(null)
const userLogs = ref([])
const optimisticUsers = ref([])
const currentPage = ref(1)
const pendingUserIds = ref([])
const pageSize = 6

const displayUsers = computed(() => optimisticUsers.value)
const totalPages = computed(() => Math.max(1, Math.ceil((props.operationLogs?.length || 0) / pageSize)))
const pagedLogs = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return (props.operationLogs || []).slice(start, start + pageSize)
})

watch(
  () => props.users,
  (value) => {
    optimisticUsers.value = (value || []).map((user) => ({ ...user }))
  },
  { immediate: true, deep: true }
)

watch(
  () => props.operationLogs,
  () => {
    if (currentPage.value > totalPages.value) {
      currentPage.value = totalPages.value
    }
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
  if (!value) return '--'
  const normalizedValue = /z$|[+-]\d{2}:\d{2}$/i.test(value) ? value : `${value}Z`
  const date = new Date(normalizedValue)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN')
}

function closeLogModal() {
  showLogModal.value = false
  logModalLoading.value = false
  logModalError.value = ''
  currentLogUser.value = null
  userLogs.value = []
}

function isUserPending(userId) {
  return pendingUserIds.value.includes(userId)
}

async function updateUser(userId, payload) {
  if (isUserPending(userId)) return
  const index = optimisticUsers.value.findIndex((user) => user.id === userId)
  const previousUser = index >= 0 ? { ...optimisticUsers.value[index] } : null

  if (index >= 0) {
    optimisticUsers.value[index] = {
      ...optimisticUsers.value[index],
      ...payload
    }
  }

  pendingUserIds.value = [...pendingUserIds.value, userId]
  setFeedback('success', '正在同步用户状态...')

  try {
    await Promise.resolve(props.onUpdateUser(userId, payload))
    setFeedback('success', '用户信息已更新。')
  } catch (error) {
    if (previousUser && index >= 0) {
      optimisticUsers.value[index] = previousUser
    }
    setFeedback('error', normalizeError(error, '用户信息更新失败。'))
  } finally {
    pendingUserIds.value = pendingUserIds.value.filter((id) => id !== userId)
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
.system-panel{display:flex;flex-direction:column;gap:14px}
.panel-header,.detail-header,.section-head,.user-top,.history-top,.permission-top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}
h2,h3{margin:0;color:#f3f7fa}
.panel-subtitle,.modal-subtitle,.section-head p{margin:8px 0 0;color:#8ea9af;font-size:13px;line-height:1.6}
.summary-badge,.count-tag,.history-count,.permission-badge{align-self:flex-start;padding:6px 12px;border-radius:999px;background:rgba(95,211,188,.12);color:#bfece3;font-size:12px}
.feedback{padding:12px 14px;border-radius:14px;font-size:14px}
.feedback.success{background:rgba(79,169,143,.18);color:#c8f0e6}
.feedback.error{background:rgba(255,107,107,.16);color:#ffd3d3}
.summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.summary-card,.records-box,.history-card,.empty-state{padding:14px;border-radius:16px;background:rgba(10,33,39,.88);border:1px solid rgba(164,215,210,.1)}
.summary-grid.compact .summary-card{padding:12px 14px}
.summary-card span{display:block;color:#87a5ac;font-size:12px;margin-bottom:6px}
.summary-card strong{font-size:18px}
.top-grid{display:grid;grid-template-columns:minmax(0,1.02fr) minmax(320px,.98fr);gap:12px}
.records-box,.history-panel{display:flex;flex-direction:column;gap:14px}
.user-list,.permission-list,.history-list{display:grid;gap:10px}
.user-card,.permission-card{padding:14px;border-radius:14px;background:rgba(7,24,29,.88)}
.user-card p,.permission-card p,.history-card p,.history-card small,.history-card time,.empty-state,.user-role-row span{margin:0;color:#97afb4}
.user-role-row{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-top:10px;font-size:12px}
.user-actions{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:10px;margin-top:12px}
.user-actions select,.ghost-btn{height:38px;padding:0 12px;border-radius:12px}
.user-actions select{border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8}
.ghost-btn{border:1px solid rgba(164,215,210,.22);background:transparent;color:#d7e8eb;cursor:pointer}
.ghost-btn:disabled,.user-actions select:disabled{opacity:.6;cursor:not-allowed}
.status-tag{padding:4px 8px;border-radius:999px;font-size:12px}
.status-tag.pending{background:rgba(255,200,87,.12);color:#ffe2a4}
.status-tag.completed{background:rgba(125,207,116,.12);color:#d6f2cf}
.compact-scroll{max-height:360px;overflow:auto;padding-right:4px}
.compact-panel{gap:12px}
.history-list{grid-template-columns:repeat(3,minmax(0,1fr))}
.compact-history{max-height:240px;overflow:auto;padding-right:4px}
.mode{color:#ffe2a4}
.history-card p,.history-card small,.history-card time{display:block;margin-top:8px}
.pagination-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 12px;border-radius:14px;background:rgba(8,27,32,.72);color:#98b0b5}
.modal-mask{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(2,10,13,.66);backdrop-filter:blur(8px);z-index:30}
.modal-card{width:min(760px,100%);display:grid;gap:16px;padding:22px;border-radius:24px;background:rgba(9,27,32,.98);border:1px solid rgba(176,224,221,.14);box-shadow:0 24px 60px rgba(0,0,0,.35)}
.modal-log-list{max-height:420px;overflow:auto;grid-template-columns:1fr}
@media (max-width:1100px){
  .summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .top-grid{grid-template-columns:1fr}
  .history-list{grid-template-columns:1fr}
}
@media (max-width:820px){
  .user-actions{grid-template-columns:1fr}
}
@media (max-width:720px){
  .summary-grid{grid-template-columns:1fr}
  .panel-header,.section-head,.detail-header,.user-top,.history-top,.permission-top{flex-direction:column}
}
</style>

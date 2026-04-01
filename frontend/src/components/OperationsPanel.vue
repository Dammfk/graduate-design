<template>
  <section class="operations-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">生产任务与资产</p>
        <h2>生产任务与资产管理</h2>
      </div>
      <span class="summary-badge">待办 {{ summary.pending_tasks || 0 }} 项</span>
    </div>

    <div v-if="feedback.message" class="feedback" :class="feedback.type">
      {{ feedback.message }}
    </div>

    <div class="summary-grid">
      <div><span>生产任务</span><strong>{{ summary.task_count || 0 }}</strong></div>
      <div><span>低库存物资</span><strong>{{ summary.low_stock_items || 0 }}</strong></div>
      <div><span>设备资产</span><strong>{{ summary.asset_count || 0 }}</strong></div>
      <div><span>待保养设备</span><strong>{{ summary.maintenance_due_assets || 0 }}</strong></div>
    </div>

    <div class="form-section">
      <h3>新增生产任务</h3>
      <div class="form-grid">
        <input v-model="newTask.title" placeholder="任务标题，如 下午消毒巡检" />
        <select v-model="newTask.category">
          <option value="feeding">饲喂</option>
          <option value="sanitation">消毒</option>
          <option value="immunization">免疫</option>
          <option value="maintenance">设备保养</option>
        </select>
        <select v-model="newTask.priority">
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select>
        <input v-model="newTask.zone_name" placeholder="区域，如 A区" />
        <select v-model="newTask.archive_id">
          <option :value="null">不关联批次</option>
          <option v-for="archive in archives" :key="archive.id" :value="archive.id">
            {{ archive.batch_number }}
          </option>
        </select>
        <select v-model="newTask.assignee_user_id">
          <option :value="null">未指定负责人</option>
          <option v-for="user in users" :key="user.id" :value="user.id">
            {{ user.username }}
          </option>
        </select>
        <input v-model="newTask.due_at" type="datetime-local" />
        <input v-model="newTask.description" placeholder="任务说明" />
      </div>
      <button class="primary-btn" :disabled="submittingTask" @click="submitTask">
        {{ submittingTask ? '提交中...' : '新增任务' }}
      </button>
    </div>

    <div class="operations-grid">
      <div class="records-box">
        <h3>今日任务</h3>
        <div class="task-list">
          <article v-for="task in tasks" :key="task.id" class="task-card">
            <div class="task-top">
              <strong>{{ task.title }}</strong>
              <span class="status-tag" :class="task.status">{{ statusLabel(task.status) }}</span>
            </div>
            <p>{{ categoryLabel(task.category) }} / {{ priorityLabel(task.priority) }}优先级 / {{ task.zone_name || '未分区' }}</p>
            <p>{{ task.archive_batch_number || '未关联批次' }} / {{ task.assignee_name || '未指定负责人' }}</p>
            <small>截止时间：{{ formatDateTime(task.due_at) }}</small>
            <div class="task-actions">
              <button class="ghost-btn" :disabled="busyTaskId === task.id" @click="updateStatus(task.id, 'in_progress')">
                {{ busyTaskId === task.id ? '提交中...' : '进行中' }}
              </button>
              <button class="primary-btn small" :disabled="busyTaskId === task.id" @click="updateStatus(task.id, 'completed')">
                {{ busyTaskId === task.id ? '提交中...' : '完成' }}
              </button>
            </div>
          </article>
        </div>
      </div>

      <div class="records-box">
        <h3>库存概况</h3>
        <div class="inventory-list">
          <article v-for="item in inventory" :key="item.id" class="inventory-card" :class="{ warning: item.is_low_stock }">
            <div class="task-top">
              <strong>{{ item.item_name }}</strong>
              <span class="status-tag" :class="item.is_low_stock ? 'pending' : 'completed'">
                {{ item.is_low_stock ? '需补货' : '充足' }}
              </span>
            </div>
            <p>{{ item.category }} / {{ item.location || '未登记位置' }}</p>
            <small>库存：{{ item.current_stock }} {{ item.unit }} / 安全库存：{{ item.safety_stock }} {{ item.unit }}</small>
          </article>
        </div>
      </div>

      <div class="records-box">
        <h3>设备资产台账</h3>
        <div class="asset-list">
          <article v-for="asset in assets" :key="asset.id" class="asset-card">
            <div class="task-top">
              <strong>{{ asset.asset_name }}</strong>
              <span class="status-tag" :class="asset.status === 'maintenance_due' ? 'pending' : 'completed'">
                {{ assetStatusLabel(asset.status) }}
              </span>
            </div>
            <p>{{ asset.asset_code }} / {{ asset.zone_name || '未分区' }}</p>
            <small>下次保养：{{ formatDate(asset.next_maintenance_at) }}</small>
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
  tasks: { type: Array, default: () => [] },
  inventory: { type: Array, default: () => [] },
  assets: { type: Array, default: () => [] },
  archives: { type: Array, default: () => [] },
  users: { type: Array, default: () => [] },
  onCreateTask: { type: Function, required: true },
  onUpdateTaskStatus: { type: Function, required: true }
})

const feedback = reactive({ type: '', message: '' })
const newTask = reactive({
  title: '',
  category: 'feeding',
  priority: 'medium',
  zone_name: '',
  archive_id: null,
  assignee_user_id: null,
  due_at: '',
  description: ''
})
const submittingTask = ref(false)
const busyTaskId = ref(null)

function setFeedback(type, message) {
  feedback.type = type
  feedback.message = message
}

function normalizeError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback
}

function statusLabel(status) {
  return { pending: '待处理', in_progress: '进行中', completed: '已完成' }[status] || status
}

function priorityLabel(priority) {
  return { high: '高', medium: '中', low: '低' }[priority] || priority
}

function categoryLabel(category) {
  return { feeding: '饲喂', sanitation: '消毒', immunization: '免疫', maintenance: '保养' }[category] || category
}

function assetStatusLabel(status) {
  return { online: '正常', maintenance_due: '待保养', offline: '离线' }[status] || status
}

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString('zh-CN') : '--'
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}

async function submitTask() {
  if (!newTask.title || !newTask.due_at) {
    setFeedback('error', '请先填写任务标题和截止时间。')
    return
  }

  submittingTask.value = true
  setFeedback('', '')

  try {
    await props.onCreateTask({
      title: newTask.title,
      category: newTask.category,
      priority: newTask.priority,
      zone_name: newTask.zone_name || null,
      archive_id: newTask.archive_id || null,
      assignee_user_id: newTask.assignee_user_id || null,
      due_at: new Date(newTask.due_at).toISOString(),
      description: newTask.description || null
    })
    newTask.title = ''
    newTask.category = 'feeding'
    newTask.priority = 'medium'
    newTask.zone_name = ''
    newTask.archive_id = null
    newTask.assignee_user_id = null
    newTask.due_at = ''
    newTask.description = ''
    setFeedback('success', '生产任务新增成功。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '生产任务新增失败。'))
  } finally {
    submittingTask.value = false
  }
}

async function updateStatus(taskId, status) {
  busyTaskId.value = taskId
  try {
    await props.onUpdateTaskStatus(taskId, status)
    setFeedback('success', '任务状态已更新。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '任务状态更新失败。'))
  } finally {
    busyTaskId.value = null
  }
}
</script>

<style scoped lang="scss">
.operations-panel{display:flex;flex-direction:column;gap:16px}.panel-header{display:flex;justify-content:space-between;gap:12px}.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}h2,h3{margin:0;color:#f3f7fa}.summary-badge{align-self:flex-start;padding:6px 12px;border-radius:999px;background:rgba(125,207,116,.12);color:#d6f2cf}
.feedback{padding:12px 14px;border-radius:14px;font-size:14px}.feedback.success{background:rgba(79,169,143,.18);color:#c8f0e6}.feedback.error{background:rgba(255,107,107,.16);color:#ffd3d3}
.summary-grid,.form-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.summary-grid div,.records-box,.form-section{padding:14px;border-radius:16px;background:rgba(10,33,39,.88)}.summary-grid span{display:block;color:#87a5ac;font-size:12px;margin-bottom:6px}.summary-grid strong{font-size:20px}
.form-section{display:grid;gap:12px}.form-grid input,.form-grid select{height:40px;padding:0 12px;border-radius:12px;border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8}
.operations-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.task-list,.inventory-list,.asset-list{display:grid;gap:10px}
.task-card,.inventory-card,.asset-card{padding:14px;border-radius:14px;background:rgba(7,24,29,.88)}.inventory-card.warning{border:1px solid rgba(255,184,77,.35)}
.task-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.task-card p,.task-card small,.inventory-card p,.inventory-card small,.asset-card p,.asset-card small{margin:0;color:#98b0b5}
.status-tag{padding:4px 8px;border-radius:999px;font-size:12px}.status-tag.pending,.status-tag.in_progress{background:rgba(255,200,87,.12);color:#ffe2a4}.status-tag.completed{background:rgba(125,207,116,.12);color:#d6f2cf}.status-tag.maintenance_due{background:rgba(255,107,107,.18);color:#ffd3d3}
.task-actions{display:flex;gap:10px;margin-top:12px}.primary-btn,.ghost-btn{height:40px;padding:0 16px;border-radius:12px;cursor:pointer}.primary-btn{border:none;background:linear-gradient(135deg,#4fa98f,#2f7f6d);color:#fff}.primary-btn.small{height:34px}.ghost-btn{border:1px solid rgba(164,215,210,.18);background:transparent;color:#eaf3f5}.primary-btn:disabled,.ghost-btn:disabled{opacity:.6;cursor:not-allowed}
@media (max-width:1100px){.summary-grid,.form-grid,.operations-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>

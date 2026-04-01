<template>
  <section class="operations-panel">
    <div v-if="feedback.message" class="feedback" :class="feedback.type">
      {{ feedback.message }}
    </div>

    <div class="summary-grid">
      <div><span>每日任务</span><strong>{{ summary.daily_task_count || 0 }}</strong></div>
      <div><span>今日任务</span><strong>{{ summary.task_count || 0 }}</strong></div>
      <div><span>低库存物资</span><strong>{{ summary.low_stock_items || 0 }}</strong></div>
      <div><span>设备资产</span><strong>{{ summary.asset_count || 0 }}</strong></div>
    </div>

    <div class="operations-grid">
      <section class="records-box">
        <div class="box-head">
          <div>
            <h3>今日任务</h3>
            <p>基于每日任务执行，也支持手动追加和编辑。</p>
          </div>
          <button class="primary-btn small" @click="openTaskModal()">新增今日任务</button>
        </div>

        <div class="selector-list compact-scroll">
          <article
            v-for="task in tasks"
            :key="task.id"
            class="selector-card"
            :class="{ active: selectedTaskId === task.id }"
            @click="selectedTaskId = task.id"
          >
            <div class="task-top">
              <strong>{{ task.title }}</strong>
              <span class="status-tag" :class="task.status">{{ statusLabel(task.status) }}</span>
            </div>
            <p>{{ categoryLabel(task.category) }} / {{ task.zone_name || '未分区' }}</p>
            <small>{{ formatDateTime(task.due_at) }}</small>

            <div v-if="selectedTaskId === task.id" class="inline-detail">
              <div class="meta-pairs">
                <span>{{ priorityLabel(task.priority) }}优先级</span>
                <span>{{ task.archive_batch_number || '未关联批次' }}</span>
                <span>{{ task.assignee_name || '未指定负责人' }}</span>
                <span>{{ statusLabel(task.status) }}</span>
              </div>
              <small>{{ task.description || '无任务说明' }}</small>
              <div class="task-actions">
                <button class="ghost-btn" :disabled="busyTaskId === task.id" @click.stop="openTaskModal(task)">编辑</button>
                <button class="ghost-btn" :disabled="busyTaskId === task.id" @click.stop="updateStatus(task.id, 'in_progress')">
                  {{ busyTaskId === task.id ? '提交中...' : '进行中' }}
                </button>
                <button class="primary-btn small" :disabled="busyTaskId === task.id" @click.stop="updateStatus(task.id, 'completed')">
                  {{ busyTaskId === task.id ? '提交中...' : '完成' }}
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="records-box">
        <div class="box-head">
          <div>
            <h3>每日任务</h3>
            <p>点击任务后，在该条目下方直接查看和操作。</p>
          </div>
          <button class="primary-btn small" @click="openDailyTaskModal()">新增每日任务</button>
        </div>

        <div class="selector-list compact-scroll">
          <article
            v-for="task in dailyTasks"
            :key="`daily-${task.id}`"
            class="selector-card"
            :class="{ active: selectedDailyTaskId === task.id }"
            @click="selectedDailyTaskId = task.id"
          >
            <div class="task-top">
              <strong>{{ task.title }}</strong>
              <span class="status-tag" :class="task.is_active ? 'completed' : 'pending'">
                {{ task.is_active ? '启用中' : '已停用' }}
              </span>
            </div>
            <p>{{ categoryLabel(task.category) }} / {{ task.zone_name || '未分区' }}</p>

            <div v-if="selectedDailyTaskId === task.id" class="inline-detail">
              <div class="meta-pairs">
                <span>{{ priorityLabel(task.priority) }}优先级</span>
                <span>{{ task.archive_batch_number || '未关联批次' }}</span>
                <span>{{ task.assignee_name || '未指定负责人' }}</span>
                <span>{{ task.is_active ? '当前启用' : '当前停用' }}</span>
              </div>
              <small>{{ task.description || '无任务说明' }}</small>
              <div class="task-actions">
                <button class="ghost-btn" @click.stop="openDailyTaskModal(task)">编辑</button>
                <button class="ghost-btn" @click.stop="toggleDailyTask(task)">
                  {{ task.is_active ? '停用' : '启用' }}
                </button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="records-box side-stack">
        <div>
          <h3>库存概况</h3>
          <div class="inventory-list compact-scroll short-scroll">
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

        <div>
          <h3>设备资产台账</h3>
          <div class="asset-list compact-scroll short-scroll">
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
      </section>
    </div>

    <div v-if="showTaskModal" class="modal-mask" @click.self="closeTaskModal">
      <div class="modal-card">
        <div class="box-head">
          <div>
            <h3>{{ editingTaskId ? '编辑今日任务' : '新增今日任务' }}</h3>
            <p>通过弹窗录入和调整今日任务。</p>
          </div>
          <button class="ghost-btn" @click="closeTaskModal">关闭</button>
        </div>
        <div class="form-grid">
          <input v-model="taskForm.title" placeholder="任务标题" />
          <select v-model="taskForm.category">
            <option value="feeding">饲喂</option>
            <option value="sanitation">消毒</option>
            <option value="immunization">免疫</option>
            <option value="maintenance">设备保养</option>
          </select>
          <select v-model="taskForm.priority">
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
          <select v-model="taskForm.status">
            <option value="pending">待处理</option>
            <option value="in_progress">进行中</option>
            <option value="completed">已完成</option>
          </select>
          <input v-model="taskForm.zone_name" placeholder="区域，如 A区" />
          <select v-model="taskForm.archive_id">
            <option :value="null">不关联批次</option>
            <option v-for="archive in archives" :key="archive.id" :value="archive.id">{{ archive.batch_number }}</option>
          </select>
          <select v-model="taskForm.assignee_user_id">
            <option :value="null">未指定负责人</option>
            <option v-for="user in users" :key="user.id" :value="user.id">{{ user.username }}</option>
          </select>
          <input v-model="taskForm.due_at" type="datetime-local" />
          <input v-model="taskForm.description" class="span-2" placeholder="任务说明" />
        </div>
        <button class="primary-btn" :disabled="submittingTask" @click="submitTask">
          {{ submittingTask ? '提交中...' : (editingTaskId ? '保存今日任务' : '新增今日任务') }}
        </button>
      </div>
    </div>

    <div v-if="showDailyTaskModal" class="modal-mask" @click.self="closeDailyTaskModal">
      <div class="modal-card">
        <div class="box-head">
          <div>
            <h3>{{ editingDailyTaskId ? '编辑每日任务' : '新增每日任务' }}</h3>
            <p>通过弹窗录入和调整每日任务。</p>
          </div>
          <button class="ghost-btn" @click="closeDailyTaskModal">关闭</button>
        </div>
        <div class="form-grid">
          <input v-model="dailyTaskForm.title" placeholder="任务标题" />
          <select v-model="dailyTaskForm.category">
            <option value="feeding">饲喂</option>
            <option value="sanitation">消毒</option>
            <option value="immunization">免疫</option>
            <option value="maintenance">设备保养</option>
          </select>
          <select v-model="dailyTaskForm.priority">
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
          <select v-model="dailyTaskForm.is_active">
            <option :value="true">启用</option>
            <option :value="false">停用</option>
          </select>
          <input v-model="dailyTaskForm.zone_name" placeholder="区域，如 A区" />
          <select v-model="dailyTaskForm.archive_id">
            <option :value="null">不关联批次</option>
            <option v-for="archive in archives" :key="archive.id" :value="archive.id">{{ archive.batch_number }}</option>
          </select>
          <select v-model="dailyTaskForm.assignee_user_id">
            <option :value="null">未指定负责人</option>
            <option v-for="user in users" :key="user.id" :value="user.id">{{ user.username }}</option>
          </select>
          <input v-model="dailyTaskForm.description" class="span-2" placeholder="任务说明" />
        </div>
        <button class="primary-btn" :disabled="submittingDailyTask" @click="submitDailyTask">
          {{ submittingDailyTask ? '提交中...' : (editingDailyTaskId ? '保存每日任务' : '新增每日任务') }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  summary: { type: Object, default: () => ({}) },
  dailyTasks: { type: Array, default: () => [] },
  tasks: { type: Array, default: () => [] },
  inventory: { type: Array, default: () => [] },
  assets: { type: Array, default: () => [] },
  archives: { type: Array, default: () => [] },
  users: { type: Array, default: () => [] },
  onCreateTask: { type: Function, required: true },
  onUpdateTask: { type: Function, required: true },
  onCreateDailyTask: { type: Function, required: true },
  onUpdateDailyTask: { type: Function, required: true },
  onUpdateTaskStatus: { type: Function, required: true }
})

const feedback = reactive({ type: '', message: '' })
const busyTaskId = ref(null)
const submittingTask = ref(false)
const submittingDailyTask = ref(false)
const showTaskModal = ref(false)
const showDailyTaskModal = ref(false)
const editingTaskId = ref(null)
const editingDailyTaskId = ref(null)
const selectedTaskId = ref(null)
const selectedDailyTaskId = ref(null)

watch(() => props.tasks, (value) => {
  if (!value.length) {
    selectedTaskId.value = null
    return
  }
  if (!value.some(task => task.id === selectedTaskId.value)) {
    selectedTaskId.value = value[0].id
  }
}, { immediate: true, deep: true })

watch(() => props.dailyTasks, (value) => {
  if (!value.length) {
    selectedDailyTaskId.value = null
    return
  }
  if (!value.some(task => task.id === selectedDailyTaskId.value)) {
    selectedDailyTaskId.value = value[0].id
  }
}, { immediate: true, deep: true })

const taskForm = reactive({
  title: '',
  category: 'feeding',
  priority: 'medium',
  status: 'pending',
  zone_name: '',
  archive_id: null,
  assignee_user_id: null,
  due_at: '',
  description: ''
})

const dailyTaskForm = reactive({
  title: '',
  category: 'feeding',
  priority: 'medium',
  zone_name: '',
  archive_id: null,
  assignee_user_id: null,
  description: '',
  is_active: true
})

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
  if (!value) return '--'
  const normalizedValue = /z$|[+-]\d{2}:\d{2}$/i.test(value) ? value : `${value}Z`
  const date = new Date(normalizedValue)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN')
}

function resetTaskForm() {
  taskForm.title = ''
  taskForm.category = 'feeding'
  taskForm.priority = 'medium'
  taskForm.status = 'pending'
  taskForm.zone_name = ''
  taskForm.archive_id = null
  taskForm.assignee_user_id = null
  taskForm.due_at = ''
  taskForm.description = ''
}

function resetDailyTaskForm() {
  dailyTaskForm.title = ''
  dailyTaskForm.category = 'feeding'
  dailyTaskForm.priority = 'medium'
  dailyTaskForm.zone_name = ''
  dailyTaskForm.archive_id = null
  dailyTaskForm.assignee_user_id = null
  dailyTaskForm.description = ''
  dailyTaskForm.is_active = true
}

function openTaskModal(task = null) {
  editingTaskId.value = task?.id || null
  if (task) {
    taskForm.title = task.title || ''
    taskForm.category = task.category || 'feeding'
    taskForm.priority = task.priority || 'medium'
    taskForm.status = task.status || 'pending'
    taskForm.zone_name = task.zone_name || ''
    taskForm.archive_id = task.archive_id || null
    taskForm.assignee_user_id = task.assignee_user_id || null
    taskForm.due_at = task.due_at ? new Date(task.due_at).toISOString().slice(0, 16) : ''
    taskForm.description = task.description || ''
  } else {
    resetTaskForm()
  }
  showTaskModal.value = true
}

function closeTaskModal() {
  showTaskModal.value = false
  editingTaskId.value = null
  resetTaskForm()
}

function openDailyTaskModal(task = null) {
  editingDailyTaskId.value = task?.id || null
  if (task) {
    dailyTaskForm.title = task.title || ''
    dailyTaskForm.category = task.category || 'feeding'
    dailyTaskForm.priority = task.priority || 'medium'
    dailyTaskForm.zone_name = task.zone_name || ''
    dailyTaskForm.archive_id = task.archive_id || null
    dailyTaskForm.assignee_user_id = task.assignee_user_id || null
    dailyTaskForm.description = task.description || ''
    dailyTaskForm.is_active = task.is_active !== false
  } else {
    resetDailyTaskForm()
  }
  showDailyTaskModal.value = true
}

function closeDailyTaskModal() {
  showDailyTaskModal.value = false
  editingDailyTaskId.value = null
  resetDailyTaskForm()
}

async function submitTask() {
  if (!taskForm.title || !taskForm.due_at) {
    setFeedback('error', '请先填写任务标题和截止时间。')
    return
  }

  submittingTask.value = true
  try {
    const payload = {
      title: taskForm.title,
      category: taskForm.category,
      priority: taskForm.priority,
      status: taskForm.status,
      zone_name: taskForm.zone_name || null,
      archive_id: taskForm.archive_id || null,
      assignee_user_id: taskForm.assignee_user_id || null,
      due_at: new Date(taskForm.due_at).toISOString(),
      description: taskForm.description || null
    }
    if (editingTaskId.value) {
      await props.onUpdateTask(editingTaskId.value, payload)
      selectedTaskId.value = editingTaskId.value
      setFeedback('success', '今日任务已更新。')
    } else {
      const created = await props.onCreateTask(payload)
      selectedTaskId.value = created?.id ?? selectedTaskId.value
      setFeedback('success', '今日任务新增成功。')
    }
    closeTaskModal()
  } catch (error) {
    setFeedback('error', normalizeError(error, '今日任务保存失败。'))
  } finally {
    submittingTask.value = false
  }
}

async function submitDailyTask() {
  if (!dailyTaskForm.title) {
    setFeedback('error', '请先填写每日任务标题。')
    return
  }

  submittingDailyTask.value = true
  try {
    const payload = {
      title: dailyTaskForm.title,
      category: dailyTaskForm.category,
      priority: dailyTaskForm.priority,
      zone_name: dailyTaskForm.zone_name || null,
      archive_id: dailyTaskForm.archive_id || null,
      assignee_user_id: dailyTaskForm.assignee_user_id || null,
      description: dailyTaskForm.description || null,
      is_active: dailyTaskForm.is_active
    }
    if (editingDailyTaskId.value) {
      await props.onUpdateDailyTask(editingDailyTaskId.value, payload)
      selectedDailyTaskId.value = editingDailyTaskId.value
      setFeedback('success', '每日任务已更新。')
    } else {
      const created = await props.onCreateDailyTask(payload)
      selectedDailyTaskId.value = created?.id ?? selectedDailyTaskId.value
      setFeedback('success', '每日任务新增成功。')
    }
    closeDailyTaskModal()
  } catch (error) {
    setFeedback('error', normalizeError(error, '每日任务保存失败。'))
  } finally {
    submittingDailyTask.value = false
  }
}

async function toggleDailyTask(task) {
  try {
    await props.onUpdateDailyTask(task.id, { is_active: !task.is_active })
    selectedDailyTaskId.value = task.id
    setFeedback('success', '每日任务状态已更新。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '每日任务状态更新失败。'))
  }
}

async function updateStatus(taskId, status) {
  busyTaskId.value = taskId
  try {
    await props.onUpdateTaskStatus(taskId, status)
    selectedTaskId.value = taskId
    setFeedback('success', '今日任务状态已更新。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '今日任务状态更新失败。'))
  } finally {
    busyTaskId.value = null
  }
}
</script>

<style scoped lang="scss">
.operations-panel{display:flex;flex-direction:column;gap:14px}
.box-head,.task-top{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
h3{margin:0;color:#f3f7fa}
.box-head p{margin:8px 0 0;color:#8ea9af;font-size:13px;line-height:1.6}
.feedback{padding:12px 14px;border-radius:14px;font-size:14px}.feedback.success{background:rgba(79,169,143,.18);color:#c8f0e6}.feedback.error{background:rgba(255,107,107,.16);color:#ffd3d3}
.summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.summary-grid div,.records-box{padding:14px;border-radius:16px;background:rgba(10,33,39,.88)}
.summary-grid span{display:block;color:#87a5ac;font-size:12px;margin-bottom:6px}.summary-grid strong{font-size:20px}
.operations-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;align-items:start}
.selector-list,.inventory-list,.asset-list{display:grid;gap:10px}
.selector-card,.inventory-card,.asset-card{padding:14px;border-radius:14px;background:rgba(7,24,29,.88)}
.selector-card{border:1px solid transparent;cursor:pointer}
.selector-card.active{border-color:rgba(94,194,170,.4);background:rgba(10,35,41,.96)}
.inventory-card.warning{border:1px solid rgba(255,184,77,.35)}
.selector-card p,.selector-card small,.inventory-card p,.inventory-card small,.asset-card p,.asset-card small,.inline-detail small{margin:0;color:#98b0b5}
.status-tag{padding:4px 8px;border-radius:999px;font-size:12px}.status-tag.pending,.status-tag.in_progress{background:rgba(255,200,87,.12);color:#ffe2a4}.status-tag.completed{background:rgba(125,207,116,.12);color:#d6f2cf}
.inline-detail{display:grid;gap:8px;margin-top:12px;padding-top:12px;border-top:1px solid rgba(164,215,210,.12)}
.meta-pairs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 10px}
.meta-pairs span{padding:8px 10px;border-radius:10px;background:rgba(12,43,49,.72);color:#b8cfd4;font-size:12px}
.task-actions{display:flex;gap:10px;flex-wrap:wrap}
.primary-btn,.ghost-btn{height:40px;padding:0 16px;border-radius:12px;cursor:pointer}.primary-btn{border:none;background:linear-gradient(135deg,#4fa98f,#2f7f6d);color:#fff}.primary-btn.small{height:34px}.ghost-btn{border:1px solid rgba(164,215,210,.18);background:transparent;color:#eaf3f5}.primary-btn:disabled,.ghost-btn:disabled{opacity:.6;cursor:not-allowed}
.compact-scroll{max-height:520px;overflow:auto;padding-right:4px}
.short-scroll{max-height:220px}
.side-stack{display:grid;gap:14px}
.modal-mask{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(2,10,13,.66);backdrop-filter:blur(8px);z-index:30}
.modal-card{width:min(760px,100%);display:grid;gap:16px;padding:22px;border-radius:24px;background:rgba(9,27,32,.98);border:1px solid rgba(176,224,221,.14);box-shadow:0 24px 60px rgba(0,0,0,.35)}
.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.form-grid input,.form-grid select{height:40px;padding:0 12px;border-radius:12px;border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8}.span-2{grid-column:span 2}
@media (max-width:1100px){.summary-grid,.operations-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.side-stack{grid-column:1/-1}}
@media (max-width:780px){.summary-grid,.operations-grid,.form-grid,.meta-pairs{grid-template-columns:1fr}.span-2{grid-column:auto}}
</style>

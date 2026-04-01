<template>
  <section class="operations-panel">
    <div v-if="feedback.message" class="feedback" :class="feedback.type">{{ feedback.message }}</div>

    <div class="summary-grid">
      <div class="summary-card"><span>今日任务</span><strong>{{ summary.task_count || mergedTasks.length }}</strong></div>
      <div class="summary-card"><span>每日任务</span><strong>{{ summary.daily_task_count || dailyTasks.length }}</strong></div>
      <div class="summary-card"><span>低库存物资</span><strong>{{ summary.low_stock_items || 0 }}</strong></div>
      <div class="summary-card"><span>设备台账</span><strong>{{ summary.asset_count || assets.length }}</strong></div>
    </div>

    <div class="operations-grid">
      <section class="records-box">
        <div class="box-head">
          <div>
            <h3>今日任务</h3>
            <p>每日任务会并入今日任务，未完成任务置顶，已完成任务自动下沉。</p>
          </div>
          <button class="primary-btn small" @click="openTaskModal()">新增今日任务</button>
        </div>

        <div class="task-group compact-scroll">
          <div class="subsection-head">
            <span>待执行任务</span>
            <small>{{ activeTasks.length }} 条</small>
          </div>
          <article
            v-for="task in activeTasks"
            :key="task.id"
            class="selector-card"
            :class="{ active: selectedTaskId === task.id, template: task.source === 'daily' }"
            @click="selectedTaskId = task.id"
          >
            <div class="task-top">
              <strong>{{ task.title }}</strong>
              <span class="status-tag" :class="taskStatusClass(task)">{{ taskStatusLabel(task) }}</span>
            </div>
            <p>{{ categoryLabel(task.category) }} / {{ task.zone_name || '未分区' }}</p>
            <small>{{ task.source === 'daily' ? '来自每日任务模板' : `截止时间：${formatDateTime(task.due_at)}` }}</small>

            <div v-if="selectedTaskId === task.id" class="inline-detail">
              <div class="meta-pairs">
                <span>{{ priorityLabel(task.priority) }}优先级</span>
                <span>{{ task.archive_batch_number || '未关联批次' }}</span>
                <span>{{ task.assignee_name || '未指定负责人' }}</span>
                <span>{{ task.source === 'daily' ? '每日模板' : '临时任务' }}</span>
              </div>
              <small>{{ task.description || '暂无任务说明' }}</small>
              <div class="task-actions">
                <template v-if="task.source === 'daily'">
                  <button class="ghost-btn" :disabled="busyTaskId === task.id" @click.stop="updateDailyTaskStatus(task.source_id, 'in_progress')">
                    {{ busyTaskId === task.id ? '提交中...' : '进行中' }}
                  </button>
                  <button class="primary-btn small" :disabled="busyTaskId === task.id" @click.stop="updateDailyTaskStatus(task.source_id, 'completed')">
                    {{ busyTaskId === task.id ? '提交中...' : '完成' }}
                  </button>
                  <button class="ghost-btn" @click.stop="toggleDailyTask(findDailyTask(task.source_id))">
                    {{ findDailyTask(task.source_id)?.is_active ? '停用' : '启用' }}
                  </button>
                </template>
                <template v-else>
                  <button class="ghost-btn" :disabled="busyTaskId === task.id" @click.stop="openTaskModal(task)">编辑</button>
                  <button class="ghost-btn" :disabled="busyTaskId === task.id" @click.stop="updateStatus(task.id, 'in_progress')">
                    {{ busyTaskId === task.id ? '提交中...' : '进行中' }}
                  </button>
                  <button class="primary-btn small" :disabled="busyTaskId === task.id" @click.stop="updateStatus(task.id, 'completed')">
                    {{ busyTaskId === task.id ? '提交中...' : '完成' }}
                  </button>
                  <button class="danger-btn" @click.stop="removeTask(task.id)">删除</button>
                </template>
              </div>
            </div>
          </article>

          <div class="subsection-head completed-head">
            <span>已完成任务</span>
            <small>{{ completedTasks.length }} 条</small>
          </div>
          <article
            v-for="task in completedTasks"
            :key="`completed-${task.id}`"
            class="selector-card completed-card"
            :class="{ active: selectedTaskId === task.id }"
            @click="selectedTaskId = task.id"
          >
            <div class="task-top">
              <strong>{{ task.title }}</strong>
              <span class="status-tag completed">已完成</span>
            </div>
            <p>{{ categoryLabel(task.category) }} / {{ task.zone_name || '未分区' }}</p>
            <small>完成时间：{{ formatDateTime(task.completed_at || task.updated_at) }}</small>

            <div v-if="selectedTaskId === task.id" class="inline-detail">
              <div class="meta-pairs">
                <span>{{ priorityLabel(task.priority) }}优先级</span>
                <span>{{ task.archive_batch_number || '未关联批次' }}</span>
                <span>{{ task.assignee_name || '未指定负责人' }}</span>
                <span>已完成</span>
              </div>
              <small>{{ task.description || '暂无任务说明' }}</small>
              <div class="task-actions">
                <button class="ghost-btn" :disabled="busyTaskId === task.id" @click.stop="openTaskModal(task)">编辑</button>
                <button class="danger-btn" @click.stop="removeTask(task.id)">删除</button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="records-box">
        <div class="box-head">
          <div>
            <h3>每日任务模板</h3>
            <p>这里维护固定模板；启用后的模板会同步出现在左侧今日任务里。</p>
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
                {{ task.is_active ? taskStatusLabel(task) : '已停用' }}
              </span>
            </div>
            <p>{{ categoryLabel(task.category) }} / {{ task.zone_name || '未分区' }}</p>

            <div v-if="selectedDailyTaskId === task.id" class="inline-detail">
              <div class="meta-pairs">
                <span>{{ priorityLabel(task.priority) }}优先级</span>
                <span>{{ task.archive_batch_number || '未关联批次' }}</span>
                <span>{{ task.assignee_name || '未指定负责人' }}</span>
                <span>{{ task.is_active ? taskStatusLabel(task) : '当前停用' }}</span>
              </div>
              <small>{{ task.description || '暂无任务说明' }}</small>
              <div class="task-actions">
                <button class="ghost-btn" @click.stop="openDailyTaskModal(task)">编辑</button>
                <button class="ghost-btn" @click.stop="toggleDailyTask(task)">{{ task.is_active ? '停用' : '启用' }}</button>
                <button class="danger-btn" @click.stop="removeDailyTask(task.id)">删除</button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section class="records-box side-stack">
        <div class="sub-panel">
          <div class="box-head compact-head">
            <div>
              <h3>库存概况</h3>
              <p>可新增库存，选中后在当前条目下编辑。</p>
            </div>
            <button class="primary-btn small" @click="openInventoryModal()">新增库存</button>
          </div>

          <div class="selector-list compact-scroll short-scroll">
            <article
              v-for="item in inventory"
              :key="item.id"
              class="selector-card"
              :class="{ active: selectedInventoryId === item.id, warning: item.is_low_stock }"
              @click="selectedInventoryId = item.id"
            >
              <div class="task-top">
                <strong>{{ item.item_name }}</strong>
                <span class="status-tag" :class="item.is_low_stock ? 'pending' : 'completed'">
                  {{ item.is_low_stock ? '需补货' : '充足' }}
                </span>
              </div>
              <p>{{ item.category }} / {{ item.location || '未登记位置' }}</p>
              <small>库存 {{ item.current_stock }} {{ item.unit }} / 安全库存 {{ item.safety_stock }} {{ item.unit }}</small>

              <div v-if="selectedInventoryId === item.id" class="inline-detail">
                <div class="meta-pairs">
                  <span>供应商：{{ item.supplier || '未登记' }}</span>
                  <span>最近补货：{{ formatDate(item.last_restocked_at) }}</span>
                </div>
                <small>{{ item.notes || '暂无备注' }}</small>
                <div class="task-actions">
                  <button class="ghost-btn" @click.stop="openInventoryModal(item)">编辑库存</button>
                  <button class="danger-btn" @click.stop="removeInventoryItem(item.id)">删除</button>
                </div>
              </div>
            </article>
          </div>
        </div>

        <div class="sub-panel">
          <div class="box-head compact-head">
            <div>
              <h3>设备台账</h3>
              <p>记录设备编号、区域和保养时间，可随时编辑。</p>
            </div>
            <button class="primary-btn small" @click="openAssetModal()">新增台账</button>
          </div>

          <div class="selector-list compact-scroll short-scroll">
            <article
              v-for="asset in assets"
              :key="asset.id"
              class="selector-card"
              :class="{ active: selectedAssetId === asset.id }"
              @click="selectedAssetId = asset.id"
            >
              <div class="task-top">
                <strong>{{ asset.asset_name }}</strong>
                <span class="status-tag" :class="asset.status === 'maintenance_due' ? 'pending' : 'completed'">
                  {{ assetStatusLabel(asset.status) }}
                </span>
              </div>
              <p>{{ asset.asset_code }} / {{ asset.zone_name || '未分区' }}</p>
              <small>下次保养：{{ formatDate(asset.next_maintenance_at) }}</small>

              <div v-if="selectedAssetId === asset.id" class="inline-detail">
                <div class="meta-pairs">
                  <span>设备类型：{{ asset.asset_type }}</span>
                  <span>关联设备：{{ asset.linked_device_id || '未关联' }}</span>
                </div>
                <small>{{ asset.notes || '暂无备注' }}</small>
                <div class="task-actions">
                  <button class="ghost-btn" @click.stop="openAssetModal(asset)">编辑台账</button>
                  <button class="danger-btn" @click.stop="removeAsset(asset.id)">删除</button>
                </div>
              </div>
            </article>
          </div>
        </div>
      </section>
    </div>

    <div v-if="showTaskModal" class="modal-mask" @click.self="closeTaskModal">
      <div class="modal-card">
        <div class="box-head">
          <div><h3>{{ editingTaskId ? '编辑今日任务' : '新增今日任务' }}</h3><p>用于新增或调整当天的临时任务。</p></div>
          <button class="ghost-btn" @click="closeTaskModal">关闭</button>
        </div>
        <div class="form-grid">
          <input v-model="taskForm.title" placeholder="任务标题" />
          <select v-model="taskForm.category"><option value="feeding">饲喂</option><option value="sanitation">消毒</option><option value="immunization">免疫</option><option value="maintenance">设备保养</option></select>
          <select v-model="taskForm.priority"><option value="high">高</option><option value="medium">中</option><option value="low">低</option></select>
          <select v-model="taskForm.status"><option value="pending">待处理</option><option value="in_progress">进行中</option><option value="completed">已完成</option></select>
          <input v-model="taskForm.zone_name" placeholder="区域，例如 A区" />
          <select v-model="taskForm.archive_id"><option :value="null">不关联批次</option><option v-for="archive in archives" :key="archive.id" :value="archive.id">{{ archive.batch_number }}</option></select>
          <select v-model="taskForm.assignee_user_id"><option :value="null">未指定负责人</option><option v-for="user in users" :key="user.id" :value="user.id">{{ user.username }}</option></select>
          <input v-model="taskForm.due_at" type="datetime-local" />
          <input v-model="taskForm.description" class="span-2" placeholder="任务说明" />
        </div>
        <button class="primary-btn" :disabled="submittingTask" @click="submitTask">{{ submittingTask ? '提交中...' : (editingTaskId ? '保存今日任务' : '新增今日任务') }}</button>
      </div>
    </div>

    <div v-if="showDailyTaskModal" class="modal-mask" @click.self="closeDailyTaskModal">
      <div class="modal-card">
        <div class="box-head">
          <div><h3>{{ editingDailyTaskId ? '编辑每日任务' : '新增每日任务' }}</h3><p>每日任务会自动出现在今日任务中。</p></div>
          <button class="ghost-btn" @click="closeDailyTaskModal">关闭</button>
        </div>
        <div class="form-grid">
          <input v-model="dailyTaskForm.title" placeholder="任务标题" />
          <select v-model="dailyTaskForm.category"><option value="feeding">饲喂</option><option value="sanitation">消毒</option><option value="immunization">免疫</option><option value="maintenance">设备保养</option></select>
          <select v-model="dailyTaskForm.priority"><option value="high">高</option><option value="medium">中</option><option value="low">低</option></select>
          <select v-model="dailyTaskForm.is_active"><option :value="true">启用</option><option :value="false">停用</option></select>
          <input v-model="dailyTaskForm.zone_name" placeholder="区域，例如 A区" />
          <select v-model="dailyTaskForm.archive_id"><option :value="null">不关联批次</option><option v-for="archive in archives" :key="archive.id" :value="archive.id">{{ archive.batch_number }}</option></select>
          <select v-model="dailyTaskForm.assignee_user_id"><option :value="null">未指定负责人</option><option v-for="user in users" :key="user.id" :value="user.id">{{ user.username }}</option></select>
          <input v-model="dailyTaskForm.description" class="span-2" placeholder="任务说明" />
        </div>
        <button class="primary-btn" :disabled="submittingDailyTask" @click="submitDailyTask">{{ submittingDailyTask ? '提交中...' : (editingDailyTaskId ? '保存每日任务' : '新增每日任务') }}</button>
      </div>
    </div>

    <div v-if="showInventoryModal" class="modal-mask" @click.self="closeInventoryModal">
      <div class="modal-card">
        <div class="box-head">
          <div><h3>{{ editingInventoryId ? '编辑库存物资' : '新增库存物资' }}</h3><p>维护库存名称、数量、安全库存和补货信息。</p></div>
          <button class="ghost-btn" @click="closeInventoryModal">关闭</button>
        </div>
        <div class="form-grid">
          <input v-model="inventoryForm.item_name" placeholder="物资名称" />
          <input v-model="inventoryForm.category" placeholder="物资分类" />
          <input v-model.number="inventoryForm.current_stock" type="number" min="0" step="0.1" placeholder="当前库存" />
          <input v-model.number="inventoryForm.safety_stock" type="number" min="0" step="0.1" placeholder="安全库存" />
          <input v-model="inventoryForm.unit" placeholder="单位，例如 kg" />
          <input v-model="inventoryForm.location" placeholder="存放位置" />
          <input v-model="inventoryForm.supplier" placeholder="供应商" />
          <input v-model="inventoryForm.last_restocked_at" type="datetime-local" />
          <input v-model="inventoryForm.notes" class="span-2" placeholder="备注" />
        </div>
        <button class="primary-btn" :disabled="submittingInventory" @click="submitInventory">{{ submittingInventory ? '提交中...' : (editingInventoryId ? '保存库存物资' : '新增库存物资') }}</button>
      </div>
    </div>

    <div v-if="showAssetModal" class="modal-mask" @click.self="closeAssetModal">
      <div class="modal-card">
        <div class="box-head">
          <div><h3>{{ editingAssetId ? '编辑设备台账' : '新增设备台账' }}</h3><p>记录设备编号、区域、状态和保养时间。</p></div>
          <button class="ghost-btn" @click="closeAssetModal">关闭</button>
        </div>
        <div class="form-grid">
          <input v-model="assetForm.asset_code" placeholder="资产编号" />
          <input v-model="assetForm.asset_name" placeholder="资产名称" />
          <input v-model="assetForm.asset_type" placeholder="设备类型" />
          <input v-model="assetForm.zone_name" placeholder="所在区域" />
          <select v-model="assetForm.status"><option value="online">正常</option><option value="maintenance_due">待保养</option><option value="offline">离线</option></select>
          <input v-model.number="assetForm.linked_device_id" type="number" min="1" placeholder="关联设备ID" />
          <input v-model="assetForm.installed_at" type="datetime-local" />
          <input v-model="assetForm.last_maintenance_at" type="datetime-local" />
          <input v-model="assetForm.next_maintenance_at" type="datetime-local" />
          <input v-model="assetForm.notes" class="span-2" placeholder="备注" />
        </div>
        <button class="primary-btn" :disabled="submittingAsset" @click="submitAsset">{{ submittingAsset ? '提交中...' : (editingAssetId ? '保存设备台账' : '新增设备台账') }}</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

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
  onDeleteDailyTask: { type: Function, required: true },
  onUpdateTaskStatus: { type: Function, required: true },
  onDeleteTask: { type: Function, required: true },
  onCreateInventoryItem: { type: Function, required: true },
  onUpdateInventoryItem: { type: Function, required: true },
  onDeleteInventoryItem: { type: Function, required: true },
  onCreateEquipmentAsset: { type: Function, required: true },
  onUpdateEquipmentAsset: { type: Function, required: true },
  onDeleteEquipmentAsset: { type: Function, required: true }
})

const feedback = reactive({ type: '', message: '' })
const busyTaskId = ref(null)
const showTaskModal = ref(false)
const showDailyTaskModal = ref(false)
const showInventoryModal = ref(false)
const showAssetModal = ref(false)
const submittingTask = ref(false)
const submittingDailyTask = ref(false)
const submittingInventory = ref(false)
const submittingAsset = ref(false)
const editingTaskId = ref(null)
const editingDailyTaskId = ref(null)
const editingInventoryId = ref(null)
const editingAssetId = ref(null)
const selectedTaskId = ref(null)
const selectedDailyTaskId = ref(null)
const selectedInventoryId = ref(null)
const selectedAssetId = ref(null)
const PRIORITY_WEIGHT = { high: 0, medium: 1, low: 2 }

function sortTaskList(list) {
  return [...list].sort((a, b) => {
    const priorityDiff = (PRIORITY_WEIGHT[a.priority] ?? 9) - (PRIORITY_WEIGHT[b.priority] ?? 9)
    if (priorityDiff !== 0) return priorityDiff

    const dueA = a?.due_at ? new Date(a.due_at).getTime() : Number.MAX_SAFE_INTEGER
    const dueB = b?.due_at ? new Date(b.due_at).getTime() : Number.MAX_SAFE_INTEGER
    if (dueA !== dueB) return dueA - dueB

    const updatedA = a?.updated_at ? new Date(a.updated_at).getTime() : 0
    const updatedB = b?.updated_at ? new Date(b.updated_at).getTime() : 0
    return updatedB - updatedA
  })
}

const mergedTasks = computed(() => sortTaskList(props.tasks || []))
const activeTasks = computed(() => mergedTasks.value.filter(task => task.status !== 'completed' && task.status !== 'disabled'))
const completedTasks = computed(() =>
  [...mergedTasks.value.filter(task => task.status === 'completed')].sort((a, b) => {
    const timeA = a?.completed_at ? new Date(a.completed_at).getTime() : (a?.updated_at ? new Date(a.updated_at).getTime() : 0)
    const timeB = b?.completed_at ? new Date(b.completed_at).getTime() : (b?.updated_at ? new Date(b.updated_at).getTime() : 0)
    return timeB - timeA
  })
)

watch(mergedTasks, (value) => {
  if (!value.length) {
    selectedTaskId.value = null
    return
  }
  if (selectedTaskId.value && !value.some(task => task.id === selectedTaskId.value)) {
    selectedTaskId.value = null
  }
}, { immediate: true, deep: true })

watch(() => props.dailyTasks, (value) => {
  if (!value.length) {
    selectedDailyTaskId.value = null
    return
  }
  if (selectedDailyTaskId.value && !value.some(task => task.id === selectedDailyTaskId.value)) {
    selectedDailyTaskId.value = null
  }
}, { immediate: true, deep: true })

watch(() => props.inventory, (value) => {
  if (!value.length) {
    selectedInventoryId.value = null
    return
  }
  if (selectedInventoryId.value && !value.some(item => item.id === selectedInventoryId.value)) {
    selectedInventoryId.value = null
  }
}, { immediate: true, deep: true })

watch(() => props.assets, (value) => {
  if (!value.length) {
    selectedAssetId.value = null
    return
  }
  if (selectedAssetId.value && !value.some(item => item.id === selectedAssetId.value)) {
    selectedAssetId.value = null
  }
}, { immediate: true, deep: true })

const taskForm = reactive({ title: '', category: 'feeding', priority: 'medium', status: 'pending', zone_name: '', archive_id: null, assignee_user_id: null, due_at: '', description: '' })
const dailyTaskForm = reactive({ title: '', category: 'feeding', priority: 'medium', zone_name: '', archive_id: null, assignee_user_id: null, description: '', is_active: true })
const inventoryForm = reactive({ item_name: '', category: '', unit: 'kg', current_stock: 0, safety_stock: 0, location: '', supplier: '', last_restocked_at: '', notes: '' })
const assetForm = reactive({ asset_code: '', asset_name: '', asset_type: '', zone_name: '', linked_device_id: null, status: 'online', installed_at: '', last_maintenance_at: '', next_maintenance_at: '', notes: '' })

function setFeedback(type, message) { feedback.type = type; feedback.message = message }
function normalizeError(error, fallback) { return error?.response?.data?.detail || error?.message || fallback }
function findDailyTask(id) { return props.dailyTasks.find(task => task.id === id) || null }
function taskStatusLabel(task) { return ({ pending: '待处理', in_progress: '进行中', completed: '已完成', disabled: '已停用' }[task.status] || task.status) }
function taskStatusClass(task) { return task.status === 'disabled' ? 'pending' : (task.status || 'pending') }
function priorityLabel(priority) { return ({ high: '高', medium: '中', low: '低' }[priority] || priority) }
function categoryLabel(category) { return ({ feeding: '饲喂', sanitation: '消毒', immunization: '免疫', maintenance: '设备保养' }[category] || category) }
function assetStatusLabel(status) { return ({ online: '正常', maintenance_due: '待保养', offline: '离线' }[status] || status) }
function normalizeNullable(value) { return value === '' || value === undefined ? null : value }
function formatDate(value) {
  if (!value) return '--'
  const normalizedValue = /z$|[+-]\d{2}:\d{2}$/i.test(value) ? value : `${value}Z`
  const date = new Date(normalizedValue)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('zh-CN')
}
function formatDateTime(value) {
  if (!value) return '--'
  const normalizedValue = /z$|[+-]\d{2}:\d{2}$/i.test(value) ? value : `${value}Z`
  const date = new Date(normalizedValue)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN')
}
function toDatetimeLocal(value) {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}
function resetTaskForm() { Object.assign(taskForm, { title: '', category: 'feeding', priority: 'medium', status: 'pending', zone_name: '', archive_id: null, assignee_user_id: null, due_at: '', description: '' }) }
function resetDailyTaskForm() { Object.assign(dailyTaskForm, { title: '', category: 'feeding', priority: 'medium', zone_name: '', archive_id: null, assignee_user_id: null, description: '', is_active: true }) }
function resetInventoryForm() { Object.assign(inventoryForm, { item_name: '', category: '', unit: 'kg', current_stock: 0, safety_stock: 0, location: '', supplier: '', last_restocked_at: '', notes: '' }) }
function resetAssetForm() { Object.assign(assetForm, { asset_code: '', asset_name: '', asset_type: '', zone_name: '', linked_device_id: null, status: 'online', installed_at: '', last_maintenance_at: '', next_maintenance_at: '', notes: '' }) }

function openTaskModal(task = null) {
  editingTaskId.value = task?.id || null
  if (task) {
    Object.assign(taskForm, { title: task.title || '', category: task.category || 'feeding', priority: task.priority || 'medium', status: task.status || 'pending', zone_name: task.zone_name || '', archive_id: task.archive_id || null, assignee_user_id: task.assignee_user_id || null, due_at: toDatetimeLocal(task.due_at), description: task.description || '' })
  } else resetTaskForm()
  showTaskModal.value = true
}
function closeTaskModal() { showTaskModal.value = false; editingTaskId.value = null; resetTaskForm() }

function openDailyTaskModal(task = null) {
  editingDailyTaskId.value = task?.id || null
  if (task) {
    Object.assign(dailyTaskForm, { title: task.title || '', category: task.category || 'feeding', priority: task.priority || 'medium', zone_name: task.zone_name || '', archive_id: task.archive_id || null, assignee_user_id: task.assignee_user_id || null, description: task.description || '', is_active: task.is_active !== false })
  } else resetDailyTaskForm()
  showDailyTaskModal.value = true
}
function closeDailyTaskModal() { showDailyTaskModal.value = false; editingDailyTaskId.value = null; resetDailyTaskForm() }

function openInventoryModal(item = null) {
  editingInventoryId.value = item?.id || null
  if (item) {
    Object.assign(inventoryForm, { item_name: item.item_name || '', category: item.category || '', unit: item.unit || 'kg', current_stock: item.current_stock ?? 0, safety_stock: item.safety_stock ?? 0, location: item.location || '', supplier: item.supplier || '', last_restocked_at: toDatetimeLocal(item.last_restocked_at), notes: item.notes || '' })
  } else resetInventoryForm()
  showInventoryModal.value = true
}
function closeInventoryModal() { showInventoryModal.value = false; editingInventoryId.value = null; resetInventoryForm() }

function openAssetModal(asset = null) {
  editingAssetId.value = asset?.id || null
  if (asset) {
    Object.assign(assetForm, { asset_code: asset.asset_code || '', asset_name: asset.asset_name || '', asset_type: asset.asset_type || '', zone_name: asset.zone_name || '', linked_device_id: asset.linked_device_id ?? null, status: asset.status || 'online', installed_at: toDatetimeLocal(asset.installed_at), last_maintenance_at: toDatetimeLocal(asset.last_maintenance_at), next_maintenance_at: toDatetimeLocal(asset.next_maintenance_at), notes: asset.notes || '' })
  } else resetAssetForm()
  showAssetModal.value = true
}
function closeAssetModal() { showAssetModal.value = false; editingAssetId.value = null; resetAssetForm() }

async function submitTask() {
  if (!taskForm.title || !taskForm.due_at) return setFeedback('error', '请先填写任务标题和截止时间。')
  submittingTask.value = true
  try {
    const payload = { title: taskForm.title, category: taskForm.category, priority: taskForm.priority, status: taskForm.status, zone_name: normalizeNullable(taskForm.zone_name), archive_id: normalizeNullable(taskForm.archive_id), assignee_user_id: normalizeNullable(taskForm.assignee_user_id), due_at: new Date(taskForm.due_at).toISOString(), description: normalizeNullable(taskForm.description) }
    if (editingTaskId.value) {
      await props.onUpdateTask(editingTaskId.value, payload)
      selectedTaskId.value = editingTaskId.value
      setFeedback('success', '今日任务已更新。')
    } else {
      await props.onCreateTask(payload)
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
  if (!dailyTaskForm.title) return setFeedback('error', '请先填写每日任务标题。')
  submittingDailyTask.value = true
  try {
    const payload = { title: dailyTaskForm.title, category: dailyTaskForm.category, priority: dailyTaskForm.priority, zone_name: normalizeNullable(dailyTaskForm.zone_name), archive_id: normalizeNullable(dailyTaskForm.archive_id), assignee_user_id: normalizeNullable(dailyTaskForm.assignee_user_id), description: normalizeNullable(dailyTaskForm.description), is_active: dailyTaskForm.is_active }
    if (editingDailyTaskId.value) {
      await props.onUpdateDailyTask(editingDailyTaskId.value, payload)
      selectedDailyTaskId.value = editingDailyTaskId.value
      setFeedback('success', '每日任务已更新。')
    } else {
      await props.onCreateDailyTask(payload)
      setFeedback('success', '每日任务新增成功。')
    }
    closeDailyTaskModal()
  } catch (error) {
    setFeedback('error', normalizeError(error, '每日任务保存失败。'))
  } finally {
    submittingDailyTask.value = false
  }
}

async function submitInventory() {
  if (!inventoryForm.item_name || !inventoryForm.category) return setFeedback('error', '请先填写库存名称和分类。')
  submittingInventory.value = true
  try {
    const payload = { item_name: inventoryForm.item_name, category: inventoryForm.category, unit: inventoryForm.unit || 'kg', current_stock: Number(inventoryForm.current_stock || 0), safety_stock: Number(inventoryForm.safety_stock || 0), location: normalizeNullable(inventoryForm.location), supplier: normalizeNullable(inventoryForm.supplier), last_restocked_at: inventoryForm.last_restocked_at ? new Date(inventoryForm.last_restocked_at).toISOString() : null, notes: normalizeNullable(inventoryForm.notes) }
    if (editingInventoryId.value) {
      await props.onUpdateInventoryItem(editingInventoryId.value, payload)
      selectedInventoryId.value = editingInventoryId.value
      setFeedback('success', '库存物资已更新。')
    } else {
      const created = await props.onCreateInventoryItem(payload)
      selectedInventoryId.value = created?.id ?? selectedInventoryId.value
      setFeedback('success', '库存物资新增成功。')
    }
    closeInventoryModal()
  } catch (error) {
    setFeedback('error', normalizeError(error, '库存物资保存失败。'))
  } finally {
    submittingInventory.value = false
  }
}

async function submitAsset() {
  if (!assetForm.asset_code || !assetForm.asset_name || !assetForm.asset_type) return setFeedback('error', '请先填写资产编号、名称和设备类型。')
  submittingAsset.value = true
  try {
    const payload = { asset_code: assetForm.asset_code, asset_name: assetForm.asset_name, asset_type: assetForm.asset_type, zone_name: normalizeNullable(assetForm.zone_name), linked_device_id: normalizeNullable(assetForm.linked_device_id), status: assetForm.status, installed_at: assetForm.installed_at ? new Date(assetForm.installed_at).toISOString() : null, last_maintenance_at: assetForm.last_maintenance_at ? new Date(assetForm.last_maintenance_at).toISOString() : null, next_maintenance_at: assetForm.next_maintenance_at ? new Date(assetForm.next_maintenance_at).toISOString() : null, notes: normalizeNullable(assetForm.notes) }
    if (editingAssetId.value) {
      await props.onUpdateEquipmentAsset(editingAssetId.value, payload)
      selectedAssetId.value = editingAssetId.value
      setFeedback('success', '设备台账已更新。')
    } else {
      const created = await props.onCreateEquipmentAsset(payload)
      selectedAssetId.value = created?.id ?? selectedAssetId.value
      setFeedback('success', '设备台账新增成功。')
    }
    closeAssetModal()
  } catch (error) {
    setFeedback('error', normalizeError(error, '设备台账保存失败。'))
  } finally {
    submittingAsset.value = false
  }
}

async function toggleDailyTask(task) {
  if (!task) return
  try {
    await props.onUpdateDailyTask(task.id, { is_active: !task.is_active })
    selectedDailyTaskId.value = task.id
    setFeedback('success', '每日任务状态已更新。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '每日任务状态更新失败。'))
  }
}

async function updateDailyTaskStatus(taskId, status) {
  const busyId = `daily-${taskId}`
  busyTaskId.value = busyId
  try {
    await props.onUpdateDailyTask(taskId, { status })
    selectedTaskId.value = busyId
    selectedDailyTaskId.value = taskId
    setFeedback('success', '每日任务状态已更新。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '每日任务状态更新失败。'))
  } finally {
    busyTaskId.value = null
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

async function removeTask(taskId) {
  try {
    await props.onDeleteTask(taskId)
    if (selectedTaskId.value === taskId) selectedTaskId.value = null
    setFeedback('success', '今日任务已删除。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '删除今日任务失败。'))
  }
}

async function removeDailyTask(taskId) {
  try {
    await props.onDeleteDailyTask(taskId)
    if (selectedDailyTaskId.value === taskId) selectedDailyTaskId.value = null
    if (selectedTaskId.value === `daily-${taskId}`) selectedTaskId.value = null
    setFeedback('success', '每日任务已删除。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '删除每日任务失败。'))
  }
}

async function removeInventoryItem(itemId) {
  try {
    await props.onDeleteInventoryItem(itemId)
    if (selectedInventoryId.value === itemId) selectedInventoryId.value = null
    setFeedback('success', '库存物资已删除。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '删除库存物资失败。'))
  }
}

async function removeAsset(assetId) {
  try {
    await props.onDeleteEquipmentAsset(assetId)
    if (selectedAssetId.value === assetId) selectedAssetId.value = null
    setFeedback('success', '设备台账已删除。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '删除设备台账失败。'))
  }
}
</script>

<style scoped lang="scss">
.operations-panel { display: flex; flex-direction: column; gap: 14px; }
.feedback { padding: 12px 14px; border-radius: 14px; font-size: 14px; }
.feedback.success { background: rgba(79, 169, 143, 0.18); color: #c8f0e6; }
.feedback.error { background: rgba(255, 107, 107, 0.16); color: #ffd3d3; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.summary-card,.records-box { padding: 14px; border-radius: 16px; background: rgba(10, 33, 39, 0.88); }
.summary-card span { display: block; color: #87a5ac; font-size: 12px; margin-bottom: 6px; }
.summary-card strong { font-size: 20px; color: #f4f8fa; }
.operations-grid { display: grid; grid-template-columns: 1.1fr 1.1fr 0.9fr; gap: 12px; align-items: start; }
.box-head,.task-top { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.compact-head { margin-bottom: 10px; }
h3 { margin: 0; color: #f3f7fa; }
.box-head p { margin: 8px 0 0; color: #8ea9af; font-size: 13px; line-height: 1.6; }
.selector-list { display: grid; gap: 10px; }
.task-group { display: grid; gap: 10px; }
.subsection-head { display: flex; justify-content: space-between; align-items: center; color: #b5cbd1; font-size: 13px; padding: 2px 2px 0; }
.subsection-head small { color: #87a5ac; }
.completed-head { margin-top: 8px; padding-top: 12px; border-top: 1px solid rgba(164, 215, 210, 0.12); }
.selector-card { padding: 14px; border-radius: 14px; background: rgba(7, 24, 29, 0.88); border: 1px solid transparent; cursor: pointer; }
.selector-card.active { border-color: rgba(94, 194, 170, 0.4); background: rgba(10, 35, 41, 0.96); }
.selector-card.template { border-style: dashed; }
.selector-card.warning { border-color: rgba(255, 184, 77, 0.35); }
.completed-card { opacity: 0.92; }
.selector-card p,.selector-card small,.inline-detail small { margin: 0; color: #98b0b5; }
.status-tag { padding: 4px 8px; border-radius: 999px; font-size: 12px; }
.status-tag.pending,.status-tag.in_progress { background: rgba(255, 200, 87, 0.12); color: #ffe2a4; }
.status-tag.completed { background: rgba(125, 207, 116, 0.12); color: #d6f2cf; }
.inline-detail { display: grid; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(164, 215, 210, 0.12); }
.meta-pairs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 10px; }
.meta-pairs span { padding: 8px 10px; border-radius: 10px; background: rgba(12, 43, 49, 0.72); color: #b8cfd4; font-size: 12px; }
.task-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.side-stack,.sub-panel { display: grid; gap: 12px; }
.primary-btn,.ghost-btn,.danger-btn { height: 40px; padding: 0 16px; border-radius: 12px; cursor: pointer; }
.primary-btn { border: none; background: linear-gradient(135deg, #4fa98f, #2f7f6d); color: #fff; }
.primary-btn.small { height: 34px; }
.ghost-btn { border: 1px solid rgba(164, 215, 210, 0.18); background: transparent; color: #eaf3f5; }
.danger-btn { border: 1px solid rgba(255, 128, 128, 0.28); background: rgba(117, 31, 31, 0.24); color: #ffd5d5; }
.primary-btn:disabled,.ghost-btn:disabled,.danger-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.compact-scroll { max-height: 560px; overflow: auto; padding-right: 4px; }
.short-scroll { max-height: 270px; }
.modal-mask { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; padding: 24px; background: rgba(2, 10, 13, 0.66); backdrop-filter: blur(8px); z-index: 30; }
.modal-card { width: min(760px, 100%); display: grid; gap: 16px; padding: 22px; border-radius: 24px; background: rgba(9, 27, 32, 0.98); border: 1px solid rgba(176, 224, 221, 0.14); box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35); }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.form-grid input,.form-grid select { height: 40px; padding: 0 12px; border-radius: 12px; border: 1px solid rgba(164, 215, 210, 0.18); background: rgba(12, 43, 49, 0.94); color: #eff7f8; }
.span-2 { grid-column: span 2; }
@media (max-width: 1180px) { .summary-grid,.operations-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .side-stack { grid-column: 1 / -1; } }
@media (max-width: 780px) { .summary-grid,.operations-grid,.form-grid,.meta-pairs { grid-template-columns: 1fr; } .span-2 { grid-column: auto; } }
</style>

<template>
  <section class="operations-panel">
    <div v-if="feedback.message" class="feedback" :class="feedback.type">{{ feedback.message }}</div>

    <div class="summary-grid">
      <div class="summary-card">
        <span>今日任务</span>
        <strong>{{ summary.task_count || mergedTasks.length }}</strong>
      </div>
      <div class="summary-card">
        <span>每日模板</span>
        <strong>{{ summary.daily_task_count || dailyTasks.length }}</strong>
      </div>
      <div class="summary-card">
        <span>低库存物资</span>
        <strong>{{ summary.low_stock_items || 0 }}</strong>
      </div>
      <div class="summary-card">
        <span>设备台账</span>
        <strong>{{ summary.asset_count || assets.length }}</strong>
      </div>
    </div>

    <div class="operations-grid">
      <section class="records-box task-column">
        <div class="box-head">
          <div>
            <h3>今日任务</h3>
            <p>把待执行和已完成任务分开展示，便于先处理最紧急的事项。</p>
          </div>
          <button class="primary-btn small" @click="openTaskModal()">新增今日任务</button>
        </div>

        <div class="task-filter-row">
          <input v-model.trim="taskKeyword" placeholder="按任务标题、区域、批次关键词筛选" />
          <select v-model="taskScope">
            <option value="all">全部任务</option>
            <option value="active">仅待执行</option>
            <option value="completed">仅已完成</option>
            <option value="high">仅高优先级</option>
          </select>
          <select v-model="taskSortMode">
            <option value="priority">按优先级排序</option>
            <option value="due">按截止时间排序</option>
            <option value="recent">按最近更新时间排序</option>
          </select>
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
            @click="toggleTaskSelection(task.id)"
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
                    {{ findDailyTask(task.source_id)?.is_active ? '停用模板' : '启用模板' }}
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
            @click="toggleTaskSelection(task.id)"
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

      <section class="records-box template-column">
        <div class="box-head">
          <div>
            <h3>每日任务模板</h3>
            <p>启用后的模板会自动出现在左侧今日任务中，适合喂养、消毒和巡检类工作。</p>
          </div>
          <button class="primary-btn small" @click="openDailyTaskModal()">新增每日任务</button>
        </div>

        <div class="selector-list compact-scroll">
          <article
            v-for="task in dailyTasks"
            :key="`daily-${task.id}`"
            class="selector-card"
            :class="{ active: selectedDailyTaskId === task.id }"
            @click="toggleDailyTaskSelection(task.id)"
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
                <span>{{ task.is_active ? '当前启用' : '当前停用' }}</span>
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

      <section class="records-box side-stack side-column">
        <div class="sub-panel">
          <div class="box-head compact-head">
            <div>
              <h3>库存概况</h3>
              <p>库存名称、分类和安全库存会优先展示，便于快速补货。</p>
            </div>
            <button class="primary-btn small" @click="openInventoryModal()">新增库存</button>
          </div>

          <div class="selector-list compact-scroll short-scroll">
            <article
              v-for="item in inventory"
              :key="item.id"
              class="selector-card"
              :class="{ active: selectedInventoryId === item.id, warning: item.is_low_stock }"
              @click="toggleInventorySelection(item.id)"
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
              <p>记录资产编号、区域、下次保养时间和关联设备，便于后续运维。</p>
            </div>
            <button class="primary-btn small" @click="openAssetModal()">新增台账</button>
          </div>

          <div class="selector-list compact-scroll short-scroll">
            <article
              v-for="asset in assets"
              :key="asset.id"
              class="selector-card"
              :class="{ active: selectedAssetId === asset.id }"
              @click="toggleAssetSelection(asset.id)"
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
          <div>
            <h3>{{ editingTaskId ? '编辑今日任务' : '新增今日任务' }}</h3>
            <p>用于补充一次性任务或调整当天安排。</p>
          </div>
          <button class="ghost-btn" @click="closeTaskModal">关闭</button>
        </div>
        <p class="form-note">带 * 的字段为必填项，保存前会先做前端校验。</p>
        <div class="form-grid">
          <div class="field-block">
            <label>任务标题 *</label>
            <input v-model="taskForm.title" :class="{ 'input-invalid': taskErrors.title }" placeholder="例如：补充草料" />
            <small v-if="taskErrors.title" class="field-error">{{ taskErrors.title }}</small>
          </div>
          <div class="field-block">
            <label>任务类型</label>
            <select v-model="taskForm.category">
              <option value="feeding">喂养</option>
              <option value="sanitation">消毒</option>
              <option value="immunization">免疫</option>
              <option value="maintenance">设备保养</option>
            </select>
          </div>
          <div class="field-block">
            <label>优先级</label>
            <select v-model="taskForm.priority">
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>
          <div class="field-block">
            <label>任务状态</label>
            <select v-model="taskForm.status">
              <option value="pending">待处理</option>
              <option value="in_progress">进行中</option>
              <option value="completed">已完成</option>
            </select>
          </div>
          <div class="field-block">
            <label>区域</label>
            <input v-model="taskForm.zone_name" placeholder="例如：A区" />
          </div>
          <div class="field-block">
            <label>关联批次</label>
            <select v-model="taskForm.archive_id">
              <option :value="null">不关联批次</option>
              <option v-for="archive in archives" :key="archive.id" :value="archive.id">{{ archive.batch_number }}</option>
            </select>
          </div>
          <div class="field-block">
            <label>负责人</label>
            <select v-model="taskForm.assignee_user_id">
              <option :value="null">未指定负责人</option>
              <option v-for="user in users" :key="user.id" :value="user.id">{{ user.username }}</option>
            </select>
          </div>
          <div class="field-block">
            <label>截止时间 *</label>
            <input v-model="taskForm.due_at" :class="{ 'input-invalid': taskErrors.due_at }" type="datetime-local" />
            <small v-if="taskErrors.due_at" class="field-error">{{ taskErrors.due_at }}</small>
          </div>
          <div class="field-block span-2">
            <label>任务说明</label>
            <input v-model="taskForm.description" placeholder="补充说明，例如：先处理 A 区后处理 B 区" />
          </div>
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
            <p>启用后会自动同步到今日任务中。</p>
          </div>
          <button class="ghost-btn" @click="closeDailyTaskModal">关闭</button>
        </div>
        <p class="form-note">每日任务模板适合固定频率工作，建议先明确标题和执行范围。</p>
        <div class="form-grid">
          <div class="field-block">
            <label>任务标题 *</label>
            <input v-model="dailyTaskForm.title" :class="{ 'input-invalid': dailyTaskErrors.title }" placeholder="例如：早间巡棚" />
            <small v-if="dailyTaskErrors.title" class="field-error">{{ dailyTaskErrors.title }}</small>
          </div>
          <div class="field-block">
            <label>任务类型</label>
            <select v-model="dailyTaskForm.category">
              <option value="feeding">喂养</option>
              <option value="sanitation">消毒</option>
              <option value="immunization">免疫</option>
              <option value="maintenance">设备保养</option>
            </select>
          </div>
          <div class="field-block">
            <label>优先级</label>
            <select v-model="dailyTaskForm.priority">
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>
          <div class="field-block">
            <label>是否启用</label>
            <select v-model="dailyTaskForm.is_active">
              <option :value="true">启用</option>
              <option :value="false">停用</option>
            </select>
          </div>
          <div class="field-block">
            <label>区域</label>
            <input v-model="dailyTaskForm.zone_name" placeholder="例如：A区" />
          </div>
          <div class="field-block">
            <label>关联批次</label>
            <select v-model="dailyTaskForm.archive_id">
              <option :value="null">不关联批次</option>
              <option v-for="archive in archives" :key="archive.id" :value="archive.id">{{ archive.batch_number }}</option>
            </select>
          </div>
          <div class="field-block">
            <label>负责人</label>
            <select v-model="dailyTaskForm.assignee_user_id">
              <option :value="null">未指定负责人</option>
              <option v-for="user in users" :key="user.id" :value="user.id">{{ user.username }}</option>
            </select>
          </div>
          <div class="field-block span-2">
            <label>任务说明</label>
            <input v-model="dailyTaskForm.description" placeholder="例如：上午 9 点前完成喂料和饮水检查" />
          </div>
        </div>
        <button class="primary-btn" :disabled="submittingDailyTask" @click="submitDailyTask">
          {{ submittingDailyTask ? '提交中...' : (editingDailyTaskId ? '保存每日任务' : '新增每日任务') }}
        </button>
      </div>
    </div>

    <div v-if="showInventoryModal" class="modal-mask" @click.self="closeInventoryModal">
      <div class="modal-card">
        <div class="box-head">
          <div>
            <h3>{{ editingInventoryId ? '编辑库存物资' : '新增库存物资' }}</h3>
            <p>保存前先补齐物资名称和分类，避免库存台账过于零散。</p>
          </div>
          <button class="ghost-btn" @click="closeInventoryModal">关闭</button>
        </div>
        <p class="form-note">低库存提示会根据当前库存和安全库存自动判断。</p>
        <div class="form-grid">
          <div class="field-block">
            <label>物资名称 *</label>
            <input v-model="inventoryForm.item_name" :class="{ 'input-invalid': inventoryErrors.item_name }" placeholder="例如：玉米粒" />
            <small v-if="inventoryErrors.item_name" class="field-error">{{ inventoryErrors.item_name }}</small>
          </div>
          <div class="field-block">
            <label>物资分类 *</label>
            <input v-model="inventoryForm.category" :class="{ 'input-invalid': inventoryErrors.category }" placeholder="例如：饲料 / 药品" />
            <small v-if="inventoryErrors.category" class="field-error">{{ inventoryErrors.category }}</small>
          </div>
          <div class="field-block">
            <label>当前库存</label>
            <input v-model.number="inventoryForm.current_stock" type="number" min="0" step="0.1" placeholder="当前库存" />
          </div>
          <div class="field-block">
            <label>安全库存</label>
            <input v-model.number="inventoryForm.safety_stock" type="number" min="0" step="0.1" placeholder="安全库存" />
          </div>
          <div class="field-block">
            <label>单位</label>
            <input v-model="inventoryForm.unit" placeholder="例如：kg" />
          </div>
          <div class="field-block">
            <label>存放位置</label>
            <input v-model="inventoryForm.location" placeholder="例如：东侧仓库" />
          </div>
          <div class="field-block">
            <label>供应商</label>
            <input v-model="inventoryForm.supplier" placeholder="供应商" />
          </div>
          <div class="field-block">
            <label>最近补货</label>
            <input v-model="inventoryForm.last_restocked_at" type="datetime-local" />
          </div>
          <div class="field-block span-2">
            <label>备注</label>
            <input v-model="inventoryForm.notes" placeholder="例如：本批次需优先使用" />
          </div>
        </div>
        <button class="primary-btn" :disabled="submittingInventory" @click="submitInventory">
          {{ submittingInventory ? '提交中...' : (editingInventoryId ? '保存库存物资' : '新增库存物资') }}
        </button>
      </div>
    </div>

    <div v-if="showAssetModal" class="modal-mask" @click.self="closeAssetModal">
      <div class="modal-card">
        <div class="box-head">
          <div>
            <h3>{{ editingAssetId ? '编辑设备台账' : '新增设备台账' }}</h3>
            <p>台账编号、名称和设备类型为必填项，后续维护提醒会基于这些信息生成。</p>
          </div>
          <button class="ghost-btn" @click="closeAssetModal">关闭</button>
        </div>
        <p class="form-note">删除台账前会再次确认，避免误删维护计划。</p>
        <div class="form-grid">
          <div class="field-block">
            <label>资产编号 *</label>
            <input v-model="assetForm.asset_code" :class="{ 'input-invalid': assetErrors.asset_code }" placeholder="例如：ASSET-001" />
            <small v-if="assetErrors.asset_code" class="field-error">{{ assetErrors.asset_code }}</small>
          </div>
          <div class="field-block">
            <label>资产名称 *</label>
            <input v-model="assetForm.asset_name" :class="{ 'input-invalid': assetErrors.asset_name }" placeholder="例如：A区主风机" />
            <small v-if="assetErrors.asset_name" class="field-error">{{ assetErrors.asset_name }}</small>
          </div>
          <div class="field-block">
            <label>设备类型 *</label>
            <input v-model="assetForm.asset_type" :class="{ 'input-invalid': assetErrors.asset_type }" placeholder="例如：风机 / 水泵" />
            <small v-if="assetErrors.asset_type" class="field-error">{{ assetErrors.asset_type }}</small>
          </div>
          <div class="field-block">
            <label>所在区域</label>
            <input v-model="assetForm.zone_name" placeholder="例如：A区" />
          </div>
          <div class="field-block">
            <label>设备状态</label>
            <select v-model="assetForm.status">
              <option value="online">正常</option>
              <option value="maintenance_due">待保养</option>
              <option value="offline">离线</option>
            </select>
          </div>
          <div class="field-block">
            <label>关联设备 ID</label>
            <input v-model.number="assetForm.linked_device_id" type="number" min="1" placeholder="例如：1" />
          </div>
          <div class="field-block">
            <label>安装时间</label>
            <input v-model="assetForm.installed_at" type="datetime-local" />
          </div>
          <div class="field-block">
            <label>最近保养</label>
            <input v-model="assetForm.last_maintenance_at" type="datetime-local" />
          </div>
          <div class="field-block">
            <label>下次保养</label>
            <input v-model="assetForm.next_maintenance_at" type="datetime-local" />
          </div>
          <div class="field-block span-2">
            <label>备注</label>
            <input v-model="assetForm.notes" placeholder="例如：皮带需在下次保养时一并更换" />
          </div>
        </div>
        <button class="primary-btn" :disabled="submittingAsset" @click="submitAsset">
          {{ submittingAsset ? '提交中...' : (editingAssetId ? '保存设备台账' : '新增设备台账') }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useMonitoringStore } from '../stores/monitoring'

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

const monitoringStore = useMonitoringStore()
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
const taskKeyword = ref('')
const taskScope = ref('all')
const taskSortMode = ref('priority')

const PRIORITY_WEIGHT = { high: 0, medium: 1, low: 2 }

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

const inventoryForm = reactive({
  item_name: '',
  category: '',
  unit: 'kg',
  current_stock: 0,
  safety_stock: 0,
  location: '',
  supplier: '',
  last_restocked_at: '',
  notes: ''
})

const assetForm = reactive({
  asset_code: '',
  asset_name: '',
  asset_type: '',
  zone_name: '',
  linked_device_id: null,
  status: 'online',
  installed_at: '',
  last_maintenance_at: '',
  next_maintenance_at: '',
  notes: ''
})

const taskErrors = reactive({ title: '', due_at: '' })
const dailyTaskErrors = reactive({ title: '' })
const inventoryErrors = reactive({ item_name: '', category: '' })
const assetErrors = reactive({ asset_code: '', asset_name: '', asset_type: '' })

const mergedTasks = computed(() => sortTaskList(props.tasks || []))
const filteredTasks = computed(() => {
  const normalizedKeyword = taskKeyword.value.trim().toLowerCase()
  const scopedTasks = mergedTasks.value.filter((task) => {
    if (taskScope.value === 'active') {
      return task.status !== 'completed' && task.status !== 'disabled'
    }
    if (taskScope.value === 'completed') {
      return task.status === 'completed'
    }
    if (taskScope.value === 'high') {
      return task.priority === 'high'
    }
    return true
  })

  const keywordFiltered = !normalizedKeyword
    ? scopedTasks
    : scopedTasks.filter((task) =>
        [task.title, task.zone_name, task.archive_batch_number, task.description]
          .filter(Boolean)
          .some((item) => String(item).toLowerCase().includes(normalizedKeyword))
      )

  return [...keywordFiltered].sort((a, b) => {
    if (taskSortMode.value === 'recent') {
      return new Date(b.updated_at || b.created_at || 0).getTime() - new Date(a.updated_at || a.created_at || 0).getTime()
    }

    if (taskSortMode.value === 'due') {
      const dueA = a?.due_at ? new Date(a.due_at).getTime() : Number.MAX_SAFE_INTEGER
      const dueB = b?.due_at ? new Date(b.due_at).getTime() : Number.MAX_SAFE_INTEGER
      if (dueA !== dueB) return dueA - dueB
    }

    const priorityDiff = (PRIORITY_WEIGHT[a.priority] ?? 9) - (PRIORITY_WEIGHT[b.priority] ?? 9)
    if (priorityDiff !== 0) return priorityDiff

    return new Date(a.due_at || 0).getTime() - new Date(b.due_at || 0).getTime()
  })
})
const activeTasks = computed(() => filteredTasks.value.filter(task => task.status !== 'completed' && task.status !== 'disabled'))
const completedTasks = computed(() =>
  [...filteredTasks.value.filter(task => task.status === 'completed')].sort((a, b) => {
    const timeA = a?.completed_at ? new Date(a.completed_at).getTime() : (a?.updated_at ? new Date(a.updated_at).getTime() : 0)
    const timeB = b?.completed_at ? new Date(b.completed_at).getTime() : (b?.updated_at ? new Date(b.updated_at).getTime() : 0)
    return timeB - timeA
  })
)

watch(filteredTasks, (value) => syncSelection(value, selectedTaskId), { immediate: true, deep: true })
watch(() => props.dailyTasks, (value) => syncSelection(value, selectedDailyTaskId), { immediate: true, deep: true })
watch(() => props.inventory, (value) => syncSelection(value, selectedInventoryId), { immediate: true, deep: true })
watch(() => props.assets, (value) => syncSelection(value, selectedAssetId), { immediate: true, deep: true })

function syncSelection(list, selectedRef) {
  if (!list?.length) {
    selectedRef.value = null
    return
  }
  if (selectedRef.value && !list.some(item => item.id === selectedRef.value)) {
    selectedRef.value = null
  }
}

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

function setFeedback(type, message) {
  feedback.type = type
  feedback.message = message
  if (!message) return
  monitoringStore.showNotice(type === 'error' ? 'error' : 'success', message, type === 'error' ? '操作失败' : '操作成功')
}

function normalizeError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback
}

function toggleTaskSelection(id) {
  selectedTaskId.value = selectedTaskId.value === id ? null : id
}

function toggleDailyTaskSelection(id) {
  selectedDailyTaskId.value = selectedDailyTaskId.value === id ? null : id
}

function toggleInventorySelection(id) {
  selectedInventoryId.value = selectedInventoryId.value === id ? null : id
}

function toggleAssetSelection(id) {
  selectedAssetId.value = selectedAssetId.value === id ? null : id
}

function findDailyTask(id) {
  return props.dailyTasks.find(task => task.id === id) || null
}

function taskStatusLabel(task) {
  return ({
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    disabled: '已停用'
  })[task.status] || task.status
}

function taskStatusClass(task) {
  return task.status === 'disabled' ? 'pending' : (task.status || 'pending')
}

function priorityLabel(priority) {
  return ({ high: '高', medium: '中', low: '低' })[priority] || priority
}

function categoryLabel(category) {
  return ({
    feeding: '喂养',
    sanitation: '消毒',
    immunization: '免疫',
    maintenance: '设备保养'
  })[category] || category
}

function assetStatusLabel(status) {
  return ({
    online: '正常',
    maintenance_due: '待保养',
    offline: '离线'
  })[status] || status
}

function normalizeNullable(value) {
  return value === '' || value === undefined ? null : value
}

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

function resetValidation(errors) {
  Object.keys(errors).forEach((key) => {
    errors[key] = ''
  })
}

function resetTaskForm() {
  Object.assign(taskForm, {
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
  resetValidation(taskErrors)
}

function resetDailyTaskForm() {
  Object.assign(dailyTaskForm, {
    title: '',
    category: 'feeding',
    priority: 'medium',
    zone_name: '',
    archive_id: null,
    assignee_user_id: null,
    description: '',
    is_active: true
  })
  resetValidation(dailyTaskErrors)
}

function resetInventoryForm() {
  Object.assign(inventoryForm, {
    item_name: '',
    category: '',
    unit: 'kg',
    current_stock: 0,
    safety_stock: 0,
    location: '',
    supplier: '',
    last_restocked_at: '',
    notes: ''
  })
  resetValidation(inventoryErrors)
}

function resetAssetForm() {
  Object.assign(assetForm, {
    asset_code: '',
    asset_name: '',
    asset_type: '',
    zone_name: '',
    linked_device_id: null,
    status: 'online',
    installed_at: '',
    last_maintenance_at: '',
    next_maintenance_at: '',
    notes: ''
  })
  resetValidation(assetErrors)
}

function validateTaskForm() {
  resetValidation(taskErrors)
  if (!taskForm.title.trim()) taskErrors.title = '请填写任务标题'
  if (!taskForm.due_at) taskErrors.due_at = '请设置截止时间'
  return !Object.values(taskErrors).some(Boolean)
}

function validateDailyTaskForm() {
  resetValidation(dailyTaskErrors)
  if (!dailyTaskForm.title.trim()) dailyTaskErrors.title = '请填写每日任务标题'
  return !Object.values(dailyTaskErrors).some(Boolean)
}

function validateInventoryForm() {
  resetValidation(inventoryErrors)
  if (!inventoryForm.item_name.trim()) inventoryErrors.item_name = '请填写物资名称'
  if (!inventoryForm.category.trim()) inventoryErrors.category = '请填写物资分类'
  return !Object.values(inventoryErrors).some(Boolean)
}

function validateAssetForm() {
  resetValidation(assetErrors)
  if (!assetForm.asset_code.trim()) assetErrors.asset_code = '请填写资产编号'
  if (!assetForm.asset_name.trim()) assetErrors.asset_name = '请填写资产名称'
  if (!assetForm.asset_type.trim()) assetErrors.asset_type = '请填写设备类型'
  return !Object.values(assetErrors).some(Boolean)
}

function openTaskModal(task = null) {
  editingTaskId.value = task?.id || null
  if (task) {
    Object.assign(taskForm, {
      title: task.title || '',
      category: task.category || 'feeding',
      priority: task.priority || 'medium',
      status: task.status || 'pending',
      zone_name: task.zone_name || '',
      archive_id: task.archive_id || null,
      assignee_user_id: task.assignee_user_id || null,
      due_at: toDatetimeLocal(task.due_at),
      description: task.description || ''
    })
    resetValidation(taskErrors)
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
    Object.assign(dailyTaskForm, {
      title: task.title || '',
      category: task.category || 'feeding',
      priority: task.priority || 'medium',
      zone_name: task.zone_name || '',
      archive_id: task.archive_id || null,
      assignee_user_id: task.assignee_user_id || null,
      description: task.description || '',
      is_active: task.is_active !== false
    })
    resetValidation(dailyTaskErrors)
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

function openInventoryModal(item = null) {
  editingInventoryId.value = item?.id || null
  if (item) {
    Object.assign(inventoryForm, {
      item_name: item.item_name || '',
      category: item.category || '',
      unit: item.unit || 'kg',
      current_stock: item.current_stock ?? 0,
      safety_stock: item.safety_stock ?? 0,
      location: item.location || '',
      supplier: item.supplier || '',
      last_restocked_at: toDatetimeLocal(item.last_restocked_at),
      notes: item.notes || ''
    })
    resetValidation(inventoryErrors)
  } else {
    resetInventoryForm()
  }
  showInventoryModal.value = true
}

function closeInventoryModal() {
  showInventoryModal.value = false
  editingInventoryId.value = null
  resetInventoryForm()
}

function openAssetModal(asset = null) {
  editingAssetId.value = asset?.id || null
  if (asset) {
    Object.assign(assetForm, {
      asset_code: asset.asset_code || '',
      asset_name: asset.asset_name || '',
      asset_type: asset.asset_type || '',
      zone_name: asset.zone_name || '',
      linked_device_id: asset.linked_device_id ?? null,
      status: asset.status || 'online',
      installed_at: toDatetimeLocal(asset.installed_at),
      last_maintenance_at: toDatetimeLocal(asset.last_maintenance_at),
      next_maintenance_at: toDatetimeLocal(asset.next_maintenance_at),
      notes: asset.notes || ''
    })
    resetValidation(assetErrors)
  } else {
    resetAssetForm()
  }
  showAssetModal.value = true
}

function closeAssetModal() {
  showAssetModal.value = false
  editingAssetId.value = null
  resetAssetForm()
}

async function submitTask() {
  if (!validateTaskForm()) {
    setFeedback('error', '请先补齐今日任务的必填项')
    return
  }
  submittingTask.value = true
  try {
    const payload = {
      title: taskForm.title,
      category: taskForm.category,
      priority: taskForm.priority,
      status: taskForm.status,
      zone_name: normalizeNullable(taskForm.zone_name),
      archive_id: normalizeNullable(taskForm.archive_id),
      assignee_user_id: normalizeNullable(taskForm.assignee_user_id),
      due_at: new Date(taskForm.due_at).toISOString(),
      description: normalizeNullable(taskForm.description)
    }
    if (editingTaskId.value) {
      await props.onUpdateTask(editingTaskId.value, payload)
      selectedTaskId.value = editingTaskId.value
      setFeedback('success', '今日任务已更新')
    } else {
      await props.onCreateTask(payload)
      setFeedback('success', '今日任务新增成功')
    }
    closeTaskModal()
  } catch (error) {
    setFeedback('error', normalizeError(error, '今日任务保存失败'))
  } finally {
    submittingTask.value = false
  }
}

async function submitDailyTask() {
  if (!validateDailyTaskForm()) {
    setFeedback('error', '请先补齐每日任务的必填项')
    return
  }
  submittingDailyTask.value = true
  try {
    const payload = {
      title: dailyTaskForm.title,
      category: dailyTaskForm.category,
      priority: dailyTaskForm.priority,
      zone_name: normalizeNullable(dailyTaskForm.zone_name),
      archive_id: normalizeNullable(dailyTaskForm.archive_id),
      assignee_user_id: normalizeNullable(dailyTaskForm.assignee_user_id),
      description: normalizeNullable(dailyTaskForm.description),
      is_active: dailyTaskForm.is_active
    }
    if (editingDailyTaskId.value) {
      await props.onUpdateDailyTask(editingDailyTaskId.value, payload)
      selectedDailyTaskId.value = editingDailyTaskId.value
      setFeedback('success', '每日任务已更新')
    } else {
      await props.onCreateDailyTask(payload)
      setFeedback('success', '每日任务新增成功')
    }
    closeDailyTaskModal()
  } catch (error) {
    setFeedback('error', normalizeError(error, '每日任务保存失败'))
  } finally {
    submittingDailyTask.value = false
  }
}

async function submitInventory() {
  if (!validateInventoryForm()) {
    setFeedback('error', '请先补齐库存物资的必填项')
    return
  }
  submittingInventory.value = true
  try {
    const payload = {
      item_name: inventoryForm.item_name,
      category: inventoryForm.category,
      unit: inventoryForm.unit || 'kg',
      current_stock: Number(inventoryForm.current_stock || 0),
      safety_stock: Number(inventoryForm.safety_stock || 0),
      location: normalizeNullable(inventoryForm.location),
      supplier: normalizeNullable(inventoryForm.supplier),
      last_restocked_at: inventoryForm.last_restocked_at ? new Date(inventoryForm.last_restocked_at).toISOString() : null,
      notes: normalizeNullable(inventoryForm.notes)
    }
    if (editingInventoryId.value) {
      await props.onUpdateInventoryItem(editingInventoryId.value, payload)
      selectedInventoryId.value = editingInventoryId.value
      setFeedback('success', '库存物资已更新')
    } else {
      const created = await props.onCreateInventoryItem(payload)
      selectedInventoryId.value = created?.id ?? selectedInventoryId.value
      setFeedback('success', '库存物资新增成功')
    }
    closeInventoryModal()
  } catch (error) {
    setFeedback('error', normalizeError(error, '库存物资保存失败'))
  } finally {
    submittingInventory.value = false
  }
}

async function submitAsset() {
  if (!validateAssetForm()) {
    setFeedback('error', '请先补齐设备台账的必填项')
    return
  }
  submittingAsset.value = true
  try {
    const payload = {
      asset_code: assetForm.asset_code,
      asset_name: assetForm.asset_name,
      asset_type: assetForm.asset_type,
      zone_name: normalizeNullable(assetForm.zone_name),
      linked_device_id: normalizeNullable(assetForm.linked_device_id),
      status: assetForm.status,
      installed_at: assetForm.installed_at ? new Date(assetForm.installed_at).toISOString() : null,
      last_maintenance_at: assetForm.last_maintenance_at ? new Date(assetForm.last_maintenance_at).toISOString() : null,
      next_maintenance_at: assetForm.next_maintenance_at ? new Date(assetForm.next_maintenance_at).toISOString() : null,
      notes: normalizeNullable(assetForm.notes)
    }
    if (editingAssetId.value) {
      await props.onUpdateEquipmentAsset(editingAssetId.value, payload)
      selectedAssetId.value = editingAssetId.value
      setFeedback('success', '设备台账已更新')
    } else {
      const created = await props.onCreateEquipmentAsset(payload)
      selectedAssetId.value = created?.id ?? selectedAssetId.value
      setFeedback('success', '设备台账新增成功')
    }
    closeAssetModal()
  } catch (error) {
    setFeedback('error', normalizeError(error, '设备台账保存失败'))
  } finally {
    submittingAsset.value = false
  }
}

async function toggleDailyTask(task) {
  if (!task) return
  try {
    await props.onUpdateDailyTask(task.id, { is_active: !task.is_active })
    selectedDailyTaskId.value = task.id
    setFeedback('success', '每日任务状态已更新')
  } catch (error) {
    setFeedback('error', normalizeError(error, '每日任务状态更新失败'))
  }
}

async function updateDailyTaskStatus(taskId, status) {
  busyTaskId.value = taskId
  try {
    await props.onUpdateDailyTask(taskId, { status })
    selectedDailyTaskId.value = taskId
    setFeedback('success', '每日任务状态已更新')
  } catch (error) {
    setFeedback('error', normalizeError(error, '每日任务状态更新失败'))
  } finally {
    busyTaskId.value = null
  }
}

async function updateStatus(taskId, status) {
  busyTaskId.value = taskId
  try {
    await props.onUpdateTaskStatus(taskId, status)
    selectedTaskId.value = taskId
    setFeedback('success', '今日任务状态已更新')
  } catch (error) {
    setFeedback('error', normalizeError(error, '今日任务状态更新失败'))
  } finally {
    busyTaskId.value = null
  }
}

async function removeTask(taskId) {
  if (!window.confirm('确认删除这条今日任务吗？删除后无法恢复。')) return
  try {
    await props.onDeleteTask(taskId)
    if (selectedTaskId.value === taskId) selectedTaskId.value = null
    setFeedback('success', '今日任务已删除')
  } catch (error) {
    setFeedback('error', normalizeError(error, '删除今日任务失败'))
  }
}

async function removeDailyTask(taskId) {
  if (!window.confirm('确认删除这条每日任务模板吗？它会同时从今日任务同步来源中移除。')) return
  try {
    await props.onDeleteDailyTask(taskId)
    if (selectedDailyTaskId.value === taskId) selectedDailyTaskId.value = null
    setFeedback('success', '每日任务已删除')
  } catch (error) {
    setFeedback('error', normalizeError(error, '删除每日任务失败'))
  }
}

async function removeInventoryItem(itemId) {
  if (!window.confirm('确认删除这条库存物资吗？删除后会影响库存统计。')) return
  try {
    await props.onDeleteInventoryItem(itemId)
    if (selectedInventoryId.value === itemId) selectedInventoryId.value = null
    setFeedback('success', '库存物资已删除')
  } catch (error) {
    setFeedback('error', normalizeError(error, '删除库存物资失败'))
  }
}

async function removeAsset(assetId) {
  if (!window.confirm('确认删除这条设备台账吗？删除后需要重新录入保养计划。')) return
  try {
    await props.onDeleteEquipmentAsset(assetId)
    if (selectedAssetId.value === assetId) selectedAssetId.value = null
    setFeedback('success', '设备台账已删除')
  } catch (error) {
    setFeedback('error', normalizeError(error, '删除设备台账失败'))
  }
}
</script>

<style scoped lang="scss">
.operations-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
.feedback { padding: 12px 14px; border-radius: 14px; font-size: 14px; }
.feedback.success { background: rgba(79, 169, 143, 0.18); color: #c8f0e6; }
.feedback.error { background: rgba(255, 107, 107, 0.16); color: #ffd3d3; }

.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.summary-card,
.records-box {
  padding: 12px;
  border-radius: 16px;
  background: rgba(10, 33, 39, 0.88);
  border: 1px solid rgba(164, 215, 210, 0.08);
  overflow: hidden;
}
.summary-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 64px;
  background:
    linear-gradient(180deg, rgba(12, 37, 43, 0.96), rgba(10, 31, 37, 0.92));
}
.summary-card span {
  display: block;
  color: #8fb1b7;
  font-size: 12px;
  margin-bottom: 0;
  max-width: 72px;
  line-height: 1.45;
}
.summary-card strong {
  font-size: 22px;
  color: #f4f8fa;
  letter-spacing: 0.01em;
}

.operations-grid {
  display: grid;
  grid-template-columns: 1.1fr 1.1fr 0.9fr;
  gap: 12px;
  align-items: start;
  flex: 1;
  min-height: 0;
}
.operations-grid > .records-box {
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.task-column {
  height: 100%;
}
.template-column,
.side-column {
  max-height: 100%;
}
.task-filter-row { display: grid; grid-template-columns: minmax(0, 1.4fr) repeat(2, minmax(170px, 0.8fr)); gap: 10px; margin-bottom: 12px; }
.task-filter-row input,
.task-filter-row select {
  height: 38px;
  padding: 0 12px;
  border-radius: 12px;
  border: 1px solid rgba(164, 215, 210, 0.18);
  background: rgba(12, 43, 49, 0.94);
  color: #eff7f8;
}
.box-head,
.task-top { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.compact-head { margin-bottom: 8px; }
h3 {
  margin: 0;
  color: #f3f7fa;
  font-size: 21px;
  line-height: 1.25;
}
.box-head p { display: none; }
.box-head {
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(164, 215, 210, 0.08);
  margin-bottom: 10px;
}

.selector-list,
.task-group { display: grid; gap: 10px; }
.selector-list,
.task-group,
.sub-panel,
.side-stack,
.compact-scroll { min-height: 0; }
.task-group,
.records-box .selector-list {
  flex: 1;
}
.template-column .selector-list {
  flex: initial;
  max-height: calc(100vh - 350px);
}
.side-column .compact-scroll {
  max-height: calc(50vh - 120px);
}
.subsection-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #b5cbd1;
  font-size: 13px;
  padding: 2px 2px 0;
}
.subsection-head small { color: #87a5ac; }
.completed-head { margin-top: 8px; padding-top: 12px; border-top: 1px solid rgba(164, 215, 210, 0.12); }

.selector-card {
  padding: 12px;
  border-radius: 14px;
  background: rgba(7, 24, 29, 0.88);
  border: 1px solid transparent;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}
.selector-card.active { border-color: rgba(94, 194, 170, 0.4); background: rgba(10, 35, 41, 0.96); }
.selector-card:hover {
  transform: translateY(-1px);
  border-color: rgba(164, 215, 210, 0.18);
}
.selector-card.template { border-style: dashed; }
.selector-card.warning { border-color: rgba(255, 184, 77, 0.35); }
.completed-card { opacity: 0.92; }
.selector-card p,
.selector-card small,
.inline-detail small { margin: 0; color: #98b0b5; line-height: 1.55; }
.selector-card strong {
  font-size: 18px;
  line-height: 1.25;
}

.template-column .selector-card,
.side-column .selector-card {
  padding: 11px 12px;
}

.task-filter-row {
  padding: 10px;
  border-radius: 14px;
  background: rgba(8, 28, 33, 0.72);
  border: 1px solid rgba(164, 215, 210, 0.08);
}

.status-tag { padding: 4px 8px; border-radius: 999px; font-size: 12px; }
.status-tag.pending,
.status-tag.in_progress { background: rgba(255, 200, 87, 0.12); color: #ffe2a4; }
.status-tag.completed { background: rgba(125, 207, 116, 0.12); color: #d6f2cf; }

.inline-detail {
  display: grid;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(164, 215, 210, 0.12);
}
.meta-pairs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 10px; }
.meta-pairs span {
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(14, 44, 52, 0.75);
  color: #d3e4e7;
  font-size: 13px;
}

.task-actions,
.inline-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.side-stack,
.sub-panel { display: grid; gap: 12px; }
.side-stack {
  grid-template-rows: repeat(2, minmax(0, 1fr));
}
.sub-panel {
  grid-template-rows: auto minmax(0, 1fr);
}
.short-scroll { max-height: none; }
.compact-scroll { overflow: auto; padding-right: 4px; }
.compact-scroll::-webkit-scrollbar { width: 8px; }
.compact-scroll::-webkit-scrollbar-thumb {
  background: rgba(94, 194, 170, 0.25);
  border-radius: 999px;
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(4, 14, 18, 0.72);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 2000;
}
.modal-card {
  width: min(860px, 100%);
  max-height: 88vh;
  overflow: auto;
  padding: 20px;
  border-radius: 24px;
  border: 1px solid rgba(164, 215, 210, 0.12);
  background: rgba(6, 22, 27, 0.95);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.38);
}

.form-note {
  margin: 0 0 14px;
  color: #8faab0;
  font-size: 14px;
  line-height: 1.6;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.span-2 { grid-column: span 2; }

.field-block {
  display: grid;
  gap: 6px;
}
.field-block label {
  color: #b7cfd4;
  font-size: 14px;
}
.field-error {
  color: #ffc2c2;
  font-size: 13px;
}

input,
select,
button {
  font: inherit;
}

input,
select {
  width: 100%;
  min-height: 44px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid rgba(164, 215, 210, 0.12);
  background: rgba(11, 38, 44, 0.88);
  color: #f3f7fa;
}

.input-invalid {
  border-color: rgba(255, 133, 127, 0.7);
  box-shadow: 0 0 0 1px rgba(255, 133, 127, 0.2) inset;
}

.ghost-btn,
.primary-btn,
.danger-btn {
  min-height: 40px;
  padding: 0 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.18s ease, opacity 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}
.ghost-btn {
  border: 1px solid rgba(164, 215, 210, 0.22);
  background: transparent;
  color: #d7e8eb;
}
.primary-btn {
  border: none;
  background: linear-gradient(135deg, #4fa98f, #2f7f6d);
  color: #fff;
}
.primary-btn.small,
.ghost-btn.small,
.danger-btn.small { min-height: 36px; }
.danger-btn {
  border: none;
  background: rgba(180, 70, 70, 0.9);
  color: #fff;
}
.ghost-btn:disabled,
.primary-btn:disabled,
.danger-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
.ghost-btn:hover:not(:disabled),
.primary-btn:hover:not(:disabled),
.danger-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

@media (max-width: 1280px) {
  .task-filter-row { grid-template-columns: 1fr; }
  .operations-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .side-stack { grid-column: 1 / -1; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .template-column .selector-list,
  .side-column .compact-scroll {
    max-height: 320px;
  }
}

@media (max-width: 900px) {
  .operations-panel {
    overflow: visible;
  }
  .summary-grid,
  .operations-grid,
  .side-stack,
  .form-grid,
  .meta-pairs {
    grid-template-columns: 1fr;
  }
  .operations-grid {
    flex: initial;
    min-height: auto;
  }
  .task-column {
    height: auto;
  }
  .operations-grid > .records-box,
  .side-stack,
  .sub-panel,
  .selector-list,
  .task-group,
  .compact-scroll {
    min-height: auto;
  }
  .template-column .selector-list,
  .side-column .compact-scroll {
    max-height: none;
  }
  .span-2 { grid-column: span 1; }
  .box-head,
  .task-top {
    flex-direction: column;
  }
  .modal-mask {
    align-items: end;
    padding: 0;
  }
  .modal-card {
    width: 100%;
    max-height: 88vh;
    overflow: auto;
    padding: 20px 18px 26px;
    border-radius: 24px 24px 0 0;
  }
}
</style>

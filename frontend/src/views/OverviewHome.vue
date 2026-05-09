<template>
  <div class="page-grid home-grid">
    <section class="hero">
      <aside class="priority-panel page-panel">
        <div class="section-heading compact-heading">
          <div>
            <p>Immediate Focus</p>
            <h3>需要立即处理</h3>
          </div>
        </div>

        <div v-if="priorityCards.length" class="priority-grid">
          <article
            v-for="card in priorityCards"
            :key="card.key"
            class="priority-card"
            :class="card.tone"
          >
            <div>
              <span>{{ card.label }}</span>
              <strong>{{ card.value }}</strong>
              <small>{{ card.description }}</small>
            </div>
            <button class="ghost-btn compact-btn" @click="navigate(card.path)">立即查看</button>
          </article>
        </div>
        <div v-else class="empty-copy">
          当前没有需要优先处理的高风险事项，系统整体运行平稳。
        </div>
      </aside>
    </section>

    <section class="overview-grid">
      <div class="page-panel">
        <div class="section-heading">
          <div>
            <p>Environment Snapshot</p>
            <h3>环境总览</h3>
          </div>
          <button class="ghost-btn compact-btn" @click="navigate('/monitoring')">查看监测页</button>
        </div>
        <div class="summary-grid">
          <div>
            <span>在线设备</span>
            <strong>{{ monitoringStore.overview.summary.online_count || 0 }}</strong>
          </div>
          <div>
            <span>平均温度</span>
            <strong>{{ formatMetric(monitoringStore.overview.summary.avg_temperature, '°C', 1) }}</strong>
          </div>
          <div>
            <span>平均湿度</span>
            <strong>{{ formatMetric(monitoringStore.overview.summary.avg_humidity, '%', 1) }}</strong>
          </div>
          <div>
            <span>平均氨气</span>
            <strong>{{ formatMetric(monitoringStore.overview.summary.avg_ammonia, 'ppm', 1) }}</strong>
          </div>
        </div>
      </div>

      <div class="page-panel">
        <div class="section-heading">
          <div>
            <p>Recent Alarm</p>
            <h3>最近告警</h3>
          </div>
          <button class="ghost-btn compact-btn" @click="navigate('/alarms')">处理告警</button>
        </div>
        <div v-if="prioritizedAlarms.length" class="list-stack">
          <article v-for="alarm in prioritizedAlarms" :key="alarm.id" class="simple-row">
            <strong>{{ alarm.description || formatAlarmType(alarm.alarm_type) }}</strong>
            <small>{{ formatTime(alarm.alarm_time) }}</small>
          </article>
        </div>
        <p v-else class="empty-copy">当前没有待处理告警。</p>
      </div>

      <div class="page-panel">
        <div class="section-heading">
          <div>
            <p>Recent Command</p>
            <h3>最近控制</h3>
          </div>
          <button class="ghost-btn compact-btn" @click="navigate('/control')">查看控制页</button>
        </div>
        <div v-if="prioritizedCommands.length" class="list-stack">
          <article v-for="command in prioritizedCommands" :key="command.id" class="simple-row">
            <div class="row-copy">
              <strong>{{ command.device_name || command.device_id }} / {{ formatComponent(command.target_component) }}</strong>
              <small>{{ formatCommandStatus(command.status) }}</small>
            </div>
            <small>{{ formatTime(command.executed_at || command.created_at) }}</small>
          </article>
        </div>
        <p v-else class="empty-copy">当前没有新的控制记录。</p>
      </div>

      <div class="page-panel">
        <div class="section-heading">
          <div>
            <p>Recent Task</p>
            <h3>任务与档案</h3>
          </div>
          <button class="ghost-btn compact-btn" @click="navigate('/operations')">查看任务页</button>
        </div>
        <div v-if="prioritizedTasks.length" class="list-stack">
          <article v-for="task in prioritizedTasks" :key="task.id" class="simple-row">
            <div class="row-copy">
              <strong>{{ task.title }}</strong>
              <small>{{ priorityLabel(task.priority) }}优先级 / {{ formatTaskStatus(task.status) }}</small>
            </div>
            <small>{{ formatTime(task.due_at || task.updated_at) }}</small>
          </article>
        </div>
        <p v-else class="empty-copy">当前没有任务数据。</p>
        <div class="archive-inline">
          <div class="section-heading compact-heading inline-heading">
            <div>
              <p>Archive Snapshot</p>
              <h4>档案摘要</h4>
            </div>
            <button class="ghost-btn compact-btn" @click="navigate('/archives')">查看档案页</button>
          </div>
          <div class="summary-grid compact archive-grid">
          <div>
            <span>批次档案</span>
            <strong>{{ monitoringStore.archiveDashboard.summary.archive_count || 0 }}</strong>
          </div>
          <div>
            <span>个体档案</span>
            <strong>{{ monitoringStore.archiveDashboard.summary.individual_archive_count || 0 }}</strong>
          </div>
          <div>
            <span>当前存栏</span>
            <strong>{{ monitoringStore.archiveDashboard.summary.total_quantity || 0 }}</strong>
          </div>
          <div>
            <span>活跃批次</span>
            <strong>{{ monitoringStore.archiveDashboard.summary.active_batches || 0 }}</strong>
          </div>
        </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useMonitoringStore } from '../stores/monitoring'

defineProps({
  navigate: { type: Function, required: true }
})

const monitoringStore = useMonitoringStore()

const alarmTypeMap = {
  temperature_high: '温度过高',
  temperature_low: '温度过低',
  humidity_high: '湿度过高',
  humidity_low: '湿度过低',
  co2_high: '二氧化碳超标',
  ammonia_high: '氨气超标'
}

const alarmLevelMap = {
  critical: '严重',
  warning: '警告',
  info: '提示'
}

const componentMap = {
  fan: '风机',
  cooling_pad: '水帘',
  fill_light: '补光灯'
}

const prioritizedAlarms = computed(() => {
  const weight = { critical: 0, warning: 1, info: 2 }
  return [...monitoringStore.alarms]
    .sort((a, b) => {
      const levelDiff = (weight[a.alarm_level] ?? 9) - (weight[b.alarm_level] ?? 9)
      if (levelDiff !== 0) return levelDiff
      return new Date(b.alarm_time || 0).getTime() - new Date(a.alarm_time || 0).getTime()
    })
    .slice(0, 2)
})

const prioritizedCommands = computed(() => {
  const weight = { failed: 0, pending: 1, sent: 2, success: 3 }
  return [...(monitoringStore.controlDashboard.recent_commands || [])]
    .sort((a, b) => {
      const statusDiff = (weight[a.status] ?? 9) - (weight[b.status] ?? 9)
      if (statusDiff !== 0) return statusDiff
      return new Date(b.executed_at || b.created_at || 0).getTime() - new Date(a.executed_at || a.created_at || 0).getTime()
    })
    .slice(0, 2)
})

const prioritizedTasks = computed(() => {
  const priorityWeight = { high: 0, medium: 1, low: 2 }
  return [...(monitoringStore.operationsDashboard.tasks || [])]
    .sort((a, b) => {
      const statusDiff = String(a.status || '').localeCompare(String(b.status || ''))
      const priorityDiff = (priorityWeight[a.priority] ?? 9) - (priorityWeight[b.priority] ?? 9)
      if (statusDiff !== 0) return statusDiff
      if (priorityDiff !== 0) return priorityDiff
      return new Date(a.due_at || a.updated_at || 0).getTime() - new Date(b.due_at || b.updated_at || 0).getTime()
    })
    .slice(0, 2)
})

const priorityCards = computed(() => {
  const cards = []
  const criticalCount = monitoringStore.alarms.filter(item => item.alarm_level === 'critical').length
  const pendingTasks = monitoringStore.operationsDashboard.summary.pending_tasks || 0
  const unsentCommands = (monitoringStore.controlDashboard.recent_commands || []).filter(item => ['pending', 'sent', 'failed'].includes(item.status)).length
  const lowStockItems = monitoringStore.operationsDashboard.summary.low_stock_items || 0

  if (unsentCommands > 0) {
    cards.push({
      key: 'commands',
      label: '待确认控制',
      value: `${unsentCommands} 条`,
      description: '部分命令仍在平台投递或等待设备 ACK，可先检查控制页。',
      path: '/control',
      tone: 'warning'
    })
  }

  if (pendingTasks > 0) {
    cards.push({
      key: 'tasks',
      label: '待办任务',
      value: `${pendingTasks} 项`,
      description: '今日仍有未完成任务，建议优先处理高优先级事项。',
      path: '/operations',
      tone: 'info'
    })
  }

  if (lowStockItems > 0) {
    cards.push({
      key: 'inventory',
      label: '库存预警',
      value: `${lowStockItems} 项`,
      description: '部分库存已接近安全下限，适合尽快安排补货。',
      path: '/operations',
      tone: 'muted'
    })
  }

  if (criticalCount > 0) {
    cards.push({
      key: 'critical-alarms',
      label: '严重告警',
      value: `${criticalCount} 条`,
      description: '建议优先进入预警页处理高风险环境异常。',
      path: '/alarms',
      tone: 'danger'
    })
  }

  return cards
})

function formatAlarmType(type) {
  return alarmTypeMap[type] || type
}

function formatAlarmLevel(level) {
  return alarmLevelMap[level] || level
}

function formatComponent(component) {
  return componentMap[component] || component || '设备组件'
}

function formatMetric(value, unit, precision = 0) {
  return value === null || value === undefined ? `-- ${unit}` : `${Number(value).toFixed(precision)} ${unit}`
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}

function formatTaskStatus(status) {
  return ({
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成'
  })[status] || status
}

function priorityLabel(priority) {
  return ({
    high: '高',
    medium: '中',
    low: '低'
  })[priority] || priority
}

function formatCommandStatus(status) {
  if (status === 'success') return '已执行'
  if (status === 'sent') return '已送达，等待设备执行'
  if (status === 'failed') return '执行失败'
  return '已保存，等待平台投递'
}
</script>

<style scoped lang="scss">
.hero {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.priority-panel {
  display: grid;
  gap: 14px;
}

.compact-heading {
  margin-bottom: 4px;
}

.priority-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.priority-card {
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(176, 224, 221, 0.12);
  background: rgba(10, 36, 41, 0.82);
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.priority-card span,
.summary-grid span {
  color: var(--text-muted);
  font-size: 13px;
}

.priority-card strong,
.summary-grid strong {
  display: block;
  font-size: 24px;
  margin-top: 6px;
}

.priority-card small {
  display: block;
  margin-top: 8px;
  color: #c5d8d9;
  line-height: 1.45;
  font-size: 13px;
}

.priority-card .ghost-btn.compact-btn {
  height: 40px;
  min-width: 98px;
  padding: 0 16px;
  border: 1px solid rgba(94, 194, 170, 0.18);
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(94, 194, 170, 0.96), rgba(73, 167, 148, 0.92));
  color: #062126;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.01em;
  box-shadow: 0 12px 24px rgba(31, 96, 84, 0.22);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}

.priority-card .ghost-btn.compact-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px rgba(31, 96, 84, 0.28);
  filter: brightness(1.03);
}

.priority-card .ghost-btn.compact-btn:active {
  transform: translateY(0);
  box-shadow: 0 10px 18px rgba(31, 96, 84, 0.24);
}

.section-heading .ghost-btn.compact-btn {
  height: 36px;
  min-width: 92px;
  padding: 0 14px;
  border: 1px solid rgba(147, 202, 197, 0.18);
  border-radius: 999px;
  background: rgba(14, 46, 53, 0.78);
  color: #dff4f1;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.section-heading .ghost-btn.compact-btn:hover {
  background: rgba(21, 64, 72, 0.92);
  border-color: rgba(94, 194, 170, 0.32);
  color: #f4fffd;
  transform: translateY(-1px);
}

.section-heading .ghost-btn.compact-btn:active {
  transform: translateY(0);
}

.priority-card.danger {
  border-color: rgba(255, 133, 127, 0.3);
  background: rgba(61, 24, 28, 0.82);
}

.priority-card.warning {
  border-color: rgba(243, 187, 85, 0.24);
}

.priority-card.info {
  border-color: rgba(94, 194, 170, 0.24);
}

.priority-card.muted {
  border-color: rgba(176, 224, 221, 0.18);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.summary-grid > div,
.simple-row {
  padding: 12px;
  border-radius: 14px;
  background: rgba(12, 40, 46, 0.86);
}

.summary-grid.compact strong {
  font-size: 22px;
}

.list-stack {
  display: grid;
  gap: 10px;
}

.simple-row {
  display: flex;
  justify-content: space-between;
  gap: 14px;
}

.row-copy {
  min-width: 0;
}

.row-copy strong,
.simple-row > strong {
  display: block;
  margin-bottom: 6px;
}

.simple-row small,
.empty-copy {
  color: var(--text-muted);
}

.archive-inline {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(176, 224, 221, 0.1);
}

.inline-heading {
  margin-bottom: 10px;
}

.inline-heading h4 {
  margin: 0;
  font-size: 18px;
}

.archive-grid strong {
  font-size: 20px;
}

@media (max-width: 1300px) {
  .priority-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1100px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .priority-card,
  .simple-row,
  .section-heading {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

<template>
  <div class="page-grid">
    <section class="hero">
      <div class="hero-copy page-panel">
        <p class="hero-kicker">精简首页</p>
        <h3>先看系统状态，再通过左侧导航进入具体模块</h3>
        <p>
          首页只保留环境、告警、任务、档案和系统摘要，帮助你快速判断全局情况。
          模块进入统一使用左侧导航，减少重复入口，让页面结构更清晰。
        </p>
      </div>

      <div class="hero-metrics">
        <article v-for="card in monitoringStore.homeCards" :key="card.title" class="metric-card page-panel">
          <span>{{ card.title }}</span>
          <strong>{{ card.value }}</strong>
          <small>{{ card.subtitle }}</small>
        </article>
      </div>
    </section>

    <section class="overview-grid">
      <div class="page-panel">
        <div class="section-heading">
          <div>
            <p>环境摘要</p>
            <h3>监测总览</h3>
          </div>
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
            <p>预警摘要</p>
            <h3>待处理告警</h3>
          </div>
        </div>
        <div v-if="monitoringStore.alarms.length" class="list-stack">
          <article v-for="alarm in monitoringStore.alarms.slice(0, 3)" :key="alarm.id" class="simple-row">
            <strong>{{ alarm.description || formatAlarmType(alarm.alarm_type) }}</strong>
            <small>{{ formatTime(alarm.alarm_time) }}</small>
          </article>
        </div>
        <p v-else class="empty-copy">当前没有待处理告警。</p>
      </div>

      <div class="page-panel">
        <div class="section-heading">
          <div>
            <p>任务摘要</p>
            <h3>今日任务</h3>
          </div>
        </div>
        <div v-if="monitoringStore.operationsDashboard.tasks.length" class="list-stack">
          <article
            v-for="task in monitoringStore.operationsDashboard.tasks.slice(0, 3)"
            :key="task.id"
            class="simple-row"
          >
            <strong>{{ task.title }}</strong>
            <small>{{ task.zone_name || '未分区' }} / {{ statusMap[task.status] || task.status }}</small>
          </article>
        </div>
        <p v-else class="empty-copy">当前没有任务数据。</p>
      </div>

      <div class="page-panel">
        <div class="section-heading">
          <div>
            <p>档案摘要</p>
            <h3>活跃批次与个体</h3>
          </div>
        </div>
        <div class="summary-grid compact">
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
    </section>
  </div>
</template>

<script setup>
import { useMonitoringStore } from '../stores/monitoring'

defineProps({
  navigate: { type: Function, required: true }
})

const monitoringStore = useMonitoringStore()

const statusMap = {
  pending: '待处理',
  in_progress: '进行中',
  completed: '已完成'
}

const alarmTypeMap = {
  temperature_high: '温度过高',
  temperature_low: '温度过低',
  humidity_high: '湿度过高',
  humidity_low: '湿度过低',
  co2_high: '二氧化碳超标',
  ammonia_high: '氨气超标'
}

function formatAlarmType(type) {
  return alarmTypeMap[type] || type
}

function formatMetric(value, unit, precision = 0) {
  return value === null || value === undefined ? `-- ${unit}` : `${Number(value).toFixed(precision)} ${unit}`
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}
</script>

<style scoped lang="scss">
.hero {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 18px;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 220px;
}

.hero-copy h3 {
  font-size: 34px;
  margin: 0 0 14px;
}

.hero-copy p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.8;
}

.hero-kicker {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

.metric-card span,
.summary-grid span {
  color: var(--text-muted);
  font-size: 13px;
}

.metric-card strong,
.summary-grid strong {
  font-size: 30px;
}

.metric-card small {
  color: #bfd5d9;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.summary-grid > div,
.simple-row {
  padding: 14px;
  border-radius: 16px;
  background: rgba(12, 40, 46, 0.86);
}

.summary-grid.compact strong {
  font-size: 24px;
}

.list-stack {
  display: grid;
  gap: 12px;
}

.simple-row {
  display: flex;
  justify-content: space-between;
  gap: 14px;
}

.simple-row small,
.empty-copy {
  color: var(--text-muted);
}

@media (max-width: 1100px) {
  .hero,
  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>

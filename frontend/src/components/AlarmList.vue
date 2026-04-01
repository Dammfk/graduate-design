<template>
  <section class="alarm-list">
    <div class="list-header">
      <div>
        <p class="eyebrow">预警中心</p>
        <h2>待处理告警</h2>
      </div>
      <span class="alarm-count">{{ alarms.length }}</span>
    </div>

    <div v-if="alarms.length === 0" class="empty-state">
      当前没有待处理告警。
    </div>

    <div v-else class="alarm-items">
      <article
        v-for="alarm in alarms"
        :key="alarm.id"
        class="alarm-item"
        :class="[`level-${alarm.alarm_level}`, { blinking: ammoniaAlert && alarm.alarm_type === 'ammonia_high' }]"
      >
        <div class="alarm-top">
          <span class="alarm-type">{{ formatAlarmType(alarm.alarm_type) }}</span>
          <span class="alarm-level" :class="`level-${alarm.alarm_level}`">
            {{ formatAlarmLevel(alarm.alarm_level) }}
          </span>
        </div>

        <p class="alarm-description">{{ alarm.description || '环境指标触发了预警阈值。' }}</p>

        <dl class="alarm-meta">
          <div>
            <dt>阈值</dt>
            <dd>{{ alarm.threshold_value ?? '--' }}</dd>
          </div>
          <div>
            <dt>实际值</dt>
            <dd>{{ formatNumber(alarm.actual_value) }}</dd>
          </div>
          <div>
            <dt>状态</dt>
            <dd>{{ formatStatus(alarm.status) }}</dd>
          </div>
          <div>
            <dt>时间</dt>
            <dd>{{ formatTime(alarm.alarm_time) }}</dd>
          </div>
        </dl>

        <div class="alarm-actions">
          <button v-if="alarm.status === 'pending'" class="ghost-btn" @click="$emit('acknowledge', alarm.id)">
            确认
          </button>
          <button v-if="alarm.status !== 'resolved'" class="primary-btn" @click="$emit('resolve', alarm.id)">
            解决
          </button>
          <span v-else class="resolved-badge">已解决</span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
defineProps({
  alarms: { type: Array, default: () => [] },
  ammoniaAlert: { type: Boolean, default: false }
})

defineEmits(['acknowledge', 'resolve'])

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

const statusMap = {
  pending: '待处理',
  acknowledged: '已确认',
  resolved: '已解决'
}

function formatAlarmType(type) {
  return alarmTypeMap[type] || type
}

function formatAlarmLevel(level) {
  return alarmLevelMap[level] || level
}

function formatStatus(status) {
  return statusMap[status] || status
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}

function formatNumber(value) {
  if (value === null || value === undefined) return '--'
  return Number(value).toFixed(1)
}
</script>

<style scoped lang="scss">
.alarm-list { display: flex; flex-direction: column; gap: 16px; height: 100%; }
.list-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; }
.eyebrow { margin: 0 0 6px; color: #87a5ac; font-size: 12px; letter-spacing: 0.2em; text-transform: uppercase; }
h2 { margin: 0; color: #f3f7fa; font-size: 24px; }
.alarm-count { min-width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; background: rgba(255, 107, 107, 0.18); color: #ffd7d7; font-weight: 700; }
.empty-state { flex: 1; display: flex; align-items: center; justify-content: center; border-radius: 20px; background: rgba(13, 42, 49, 0.76); color: #94aab1; }
.alarm-items { display: flex; flex-direction: column; gap: 12px; overflow: auto; }
.alarm-item { padding: 16px; border-radius: 18px; border: 1px solid rgba(164, 215, 210, 0.16); background: rgba(10, 33, 39, 0.9); }
.alarm-item.level-critical { border-color: rgba(255, 107, 107, 0.4); }
.alarm-item.level-warning { border-color: rgba(255, 200, 87, 0.35); }
.alarm-item.blinking { animation: pulse 1s infinite; }
.alarm-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.alarm-type { color: #f8fbfc; font-weight: 600; }
.alarm-level { padding: 4px 10px; border-radius: 999px; font-size: 12px; }
.alarm-level.level-critical { background: rgba(255, 107, 107, 0.14); color: #ffb8b8; }
.alarm-level.level-warning { background: rgba(255, 200, 87, 0.14); color: #ffe2a4; }
.alarm-level.level-info { background: rgba(95, 211, 188, 0.14); color: #a4e8d9; }
.alarm-description { margin: 0 0 12px; color: #9fb3b8; line-height: 1.5; }
.alarm-meta { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 16px; margin: 0 0 14px; }
.alarm-meta dt { color: #7f98a0; font-size: 12px; }
.alarm-meta dd { margin: 4px 0 0; color: #eff8f9; }
.alarm-actions { display: flex; gap: 10px; }
.ghost-btn,.primary-btn { flex: 1; height: 38px; border-radius: 12px; cursor: pointer; font-weight: 600; transition: 0.2s ease; }
.ghost-btn { border: 1px solid rgba(164, 215, 210, 0.22); background: transparent; color: #d7e8eb; }
.primary-btn { border: none; background: linear-gradient(135deg, #4fa98f, #2f7f6d); color: white; }
.resolved-badge { color: #9cd8be; font-weight: 600; }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 rgba(255,107,107,0); } 50% { box-shadow: 0 0 0 6px rgba(255,107,107,0.08); } }
</style>

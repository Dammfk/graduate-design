<template>
  <section class="alarm-list">
    <div class="list-header">
      <div>
        <p class="eyebrow">Alarm Center</p>
        <h2>待处理告警</h2>
      </div>
      <span class="alarm-count">{{ alarms.length }}</span>
    </div>

    <div v-if="alarms.length === 0" class="empty-state">
      当前没有待处理告警。
    </div>

    <template v-else>
      <div v-if="actionMessage" class="action-banner" :class="actionMessage.type">
        {{ actionMessage.text }}
      </div>

      <div class="alarm-items">
        <article
          v-for="alarm in pagedAlarms"
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

          <div class="alarm-meta">
            <span>阈值 {{ alarm.threshold_value ?? '--' }}</span>
            <span>实际 {{ formatNumber(alarm.actual_value) }}</span>
            <span>{{ formatStatus(alarm.status) }}</span>
            <span>{{ formatTime(alarm.alarm_time) }}</span>
          </div>

          <div class="alarm-actions">
            <button
              v-if="alarm.status === 'pending'"
              class="ghost-btn"
              :disabled="isBusy(alarm.id)"
              @click="$emit('acknowledge', alarm.id)"
            >
              {{ busyAction === 'acknowledge' && busyAlarmId === alarm.id ? '确认中...' : '确认' }}
            </button>
            <button
              v-if="alarm.status !== 'resolved'"
              class="primary-btn"
              :disabled="isBusy(alarm.id)"
              @click="$emit('resolve', alarm.id)"
            >
              {{ busyAction === 'resolve' && busyAlarmId === alarm.id ? '处理中...' : '解决' }}
            </button>
            <span v-else class="resolved-badge">已解决</span>
          </div>
        </article>
      </div>

      <div class="pagination-bar">
        <button class="ghost-btn" type="button" :disabled="page === 1" @click="page -= 1">上一页</button>
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <button class="ghost-btn" type="button" :disabled="page >= totalPages" @click="page += 1">下一页</button>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  alarms: { type: Array, default: () => [] },
  ammoniaAlert: { type: Boolean, default: false },
  busyAlarmId: { type: Number, default: null },
  busyAction: { type: String, default: '' },
  actionMessage: { type: Object, default: null }
})

defineEmits(['acknowledge', 'resolve'])

const page = ref(1)
const pageSize = 5

const totalPages = computed(() => Math.max(1, Math.ceil(props.alarms.length / pageSize)))
const pagedAlarms = computed(() => {
  const start = (page.value - 1) * pageSize
  return props.alarms.slice(start, start + pageSize)
})

watch(
  () => props.alarms,
  () => {
    if (page.value > totalPages.value) {
      page.value = totalPages.value
    }
  },
  { deep: true }
)

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

function isBusy(alarmId) {
  return props.busyAlarmId === alarmId
}
</script>

<style scoped lang="scss">
.alarm-list{display:flex;flex-direction:column;gap:14px;height:100%}
.list-header{display:flex;align-items:flex-end;justify-content:space-between;gap:12px}
.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}
h2{margin:0;color:#f3f7fa;font-size:22px}
.alarm-count{min-width:34px;height:34px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;background:rgba(255,107,107,.18);color:#ffd7d7;font-weight:700}
.empty-state{flex:1;display:flex;align-items:center;justify-content:center;border-radius:16px;background:rgba(13,42,49,.76);color:#94aab1}
.action-banner{padding:10px 12px;border-radius:12px;border:1px solid rgba(164,215,210,.18);font-size:13px}
.action-banner.success{background:rgba(58,122,104,.18);color:#c8f0e2;border-color:rgba(108,210,178,.28)}
.action-banner.error{background:rgba(108,39,39,.24);color:#ffd5d0;border-color:rgba(255,133,127,.26)}
.alarm-items{display:grid;gap:10px}
.alarm-item{padding:14px;border-radius:16px;border:1px solid rgba(164,215,210,.16);background:rgba(10,33,39,.9)}
.alarm-item.level-critical{border-color:rgba(255,107,107,.4)}
.alarm-item.level-warning{border-color:rgba(255,200,87,.35)}
.alarm-item.blinking{animation:pulse 1s infinite}
.alarm-top{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}
.alarm-type{color:#f8fbfc;font-weight:600}
.alarm-level{padding:4px 10px;border-radius:999px;font-size:12px}
.alarm-level.level-critical{background:rgba(255,107,107,.14);color:#ffb8b8}
.alarm-level.level-warning{background:rgba(255,200,87,.14);color:#ffe2a4}
.alarm-level.level-info{background:rgba(95,211,188,.14);color:#a4e8d9}
.alarm-description{margin:0 0 10px;color:#9fb3b8;line-height:1.5}
.alarm-meta{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.alarm-meta span{padding:6px 10px;border-radius:999px;background:rgba(17,56,63,.9);color:#d7e7ea;font-size:12px}
.alarm-actions{display:flex;gap:8px}
.ghost-btn,.primary-btn{height:36px;padding:0 14px;border-radius:10px;cursor:pointer;font-weight:600;transition:.2s ease}
.ghost-btn{border:1px solid rgba(164,215,210,.22);background:transparent;color:#d7e8eb}
.primary-btn{border:none;background:linear-gradient(135deg,#4fa98f,#2f7f6d);color:#fff}
.ghost-btn:disabled,.primary-btn:disabled{opacity:.6;cursor:not-allowed}
.resolved-badge{color:#9cd8be;font-weight:600}
.pagination-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 12px;border-radius:14px;background:rgba(8,27,32,.72);color:#98b0b5}
@keyframes pulse{0%,100%{box-shadow:0 0 0 rgba(255,107,107,0)}50%{box-shadow:0 0 0 6px rgba(255,107,107,.08)}}
</style>

<template>
  <section class="alarm-list">
    <div class="list-header">
      <div>
        <p class="eyebrow">Alarm Center</p>
        <h2>待处理告警</h2>
      </div>
      <span class="alarm-count">{{ alarms.length }}</span>
    </div>

    <div class="filter-bar">
      <input v-model.trim="keyword" class="filter-input" placeholder="按告警说明、类型、区域关键词筛选" />
      <select v-model="levelFilter" class="filter-select">
        <option value="all">全部等级</option>
        <option value="critical">仅严重</option>
        <option value="warning">仅警告</option>
        <option value="info">仅提示</option>
      </select>
      <select v-model="sortMode" class="filter-select">
        <option value="severity">按严重程度优先</option>
        <option value="latest">按最新时间优先</option>
        <option value="threshold">按偏离阈值优先</option>
      </select>
    </div>

    <div v-if="actionMessage" class="action-banner" :class="actionMessage.type">
      {{ actionMessage.text }}
    </div>

    <div v-if="!alarms.length" class="empty-state">
      <strong>当前没有待处理告警</strong>
      <span>环境指标当前处于正常范围内，系统暂时没有需要你立即处理的异常。</span>
    </div>

    <div v-else-if="!filteredAlarms.length" class="empty-state">
      <strong>当前筛选条件下没有匹配的告警</strong>
      <span>可以清空关键词、放宽等级过滤，或切换排序方式再查看。</span>
    </div>

    <template v-else>
      <div class="alarm-items">
        <article
          v-for="alarm in pagedAlarms"
          :key="alarm.id"
          class="alarm-item"
          :class="[`level-${alarm.alarm_level}`, { blinking: ammoniaAlert && alarm.alarm_type === 'ammonia_high' }]"
        >
          <div class="alarm-top">
            <span class="alarm-type" v-html="highlightText(formatAlarmType(alarm.alarm_type))"></span>
            <span class="alarm-level" :class="`level-${alarm.alarm_level}`">
              {{ formatAlarmLevel(alarm.alarm_level) }}
            </span>
          </div>

          <p class="alarm-description" v-html="highlightText(alarm.description || defaultDescription)"></p>

          <div class="alarm-meta">
            <span>阈值 {{ alarm.threshold_value ?? '--' }}</span>
            <span>实际 {{ formatNumber(alarm.actual_value) }}</span>
            <span>{{ alarm.zone_name || '未标注区域' }}</span>
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
const keyword = ref('')
const levelFilter = ref('all')
const sortMode = ref('severity')
const defaultDescription = '环境指标触发了预警阈值。'

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

const filteredAlarms = computed(() => {
  const normalizedKeyword = keyword.value.trim().toLowerCase()
  const severityWeight = { critical: 0, warning: 1, info: 2 }

  return [...props.alarms]
    .filter((alarm) => {
      const levelMatched = levelFilter.value === 'all' || alarm.alarm_level === levelFilter.value
      if (!levelMatched) return false
      if (!normalizedKeyword) return true

      const haystacks = [
        alarm.description,
        alarm.zone_name,
        alarmTypeMap[alarm.alarm_type] || alarm.alarm_type
      ]
        .filter(Boolean)
        .map((item) => String(item).toLowerCase())

      return haystacks.some((item) => item.includes(normalizedKeyword))
    })
    .sort((a, b) => {
      if (sortMode.value === 'latest') {
        return new Date(b.alarm_time || 0).getTime() - new Date(a.alarm_time || 0).getTime()
      }

      if (sortMode.value === 'threshold') {
        const deltaA = Math.abs(Number(a.actual_value || 0) - Number(a.threshold_value || 0))
        const deltaB = Math.abs(Number(b.actual_value || 0) - Number(b.threshold_value || 0))
        if (deltaB !== deltaA) return deltaB - deltaA
      }

      const levelDiff = (severityWeight[a.alarm_level] ?? 9) - (severityWeight[b.alarm_level] ?? 9)
      if (levelDiff !== 0) return levelDiff
      return new Date(b.alarm_time || 0).getTime() - new Date(a.alarm_time || 0).getTime()
    })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredAlarms.value.length / pageSize)))
const pagedAlarms = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredAlarms.value.slice(start, start + pageSize)
})

watch([() => props.alarms, filteredAlarms], () => {
  if (page.value > totalPages.value) {
    page.value = totalPages.value
  }
}, { deep: true })

watch([keyword, levelFilter, sortMode], () => {
  page.value = 1
})

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
  if (value === null || value === undefined || value === '') return '--'
  return Number(value).toFixed(1)
}

function isBusy(alarmId) {
  return props.busyAlarmId === alarmId
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function highlightText(value) {
  const source = escapeHtml(value || '')
  const normalizedKeyword = keyword.value.trim()
  if (!normalizedKeyword) return source

  const escapedKeyword = normalizedKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const pattern = new RegExp(`(${escapedKeyword})`, 'ig')
  return source.replace(pattern, '<mark>$1</mark>')
}
</script>

<style scoped lang="scss">
.alarm-list { display: flex; flex-direction: column; gap: 14px; height: 100%; min-height: 0; }
.list-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; }
.eyebrow { margin: 0 0 6px; color: #87a5ac; font-size: 12px; letter-spacing: .2em; text-transform: uppercase; }
h2 { margin: 0; color: #f3f7fa; font-size: 22px; }
.alarm-count { min-width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; background: rgba(255, 107, 107, .18); color: #ffd7d7; font-weight: 700; }
.filter-bar { display: grid; grid-template-columns: minmax(0, 1.5fr) repeat(2, minmax(160px, .75fr)); gap: 10px; }
.filter-input, .filter-select {
  height: 40px; padding: 0 12px; border-radius: 12px; border: 1px solid rgba(164, 215, 210, .18);
  background: rgba(12, 43, 49, .94); color: #eff7f8;
}
.empty-state {
  flex: 1; display: grid; place-content: center; gap: 8px; text-align: center; padding: 18px;
  border-radius: 16px; background: rgba(13, 42, 49, .76); color: #94aab1;
}
.empty-state strong { color: #eef7f7; font-size: 18px; }
.empty-state span { line-height: 1.6; }
.action-banner { padding: 10px 12px; border-radius: 12px; border: 1px solid rgba(164, 215, 210, .18); font-size: 13px; }
.action-banner.success { background: rgba(58, 122, 104, .18); color: #c8f0e2; border-color: rgba(108, 210, 178, .28); }
.action-banner.error { background: rgba(108, 39, 39, .24); color: #ffd5d0; border-color: rgba(255, 133, 127, .26); }
.alarm-items { display: grid; gap: 10px; flex: 1; align-content: start; }
.alarm-item { padding: 14px; border-radius: 16px; border: 1px solid rgba(164, 215, 210, .16); background: rgba(10, 33, 39, .9); }
.alarm-item.level-critical { border-color: rgba(255, 107, 107, .4); }
.alarm-item.level-warning { border-color: rgba(255, 200, 87, .35); }
.alarm-item.blinking { animation: pulse 1s infinite; }
.alarm-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 8px; }
.alarm-type { color: #f8fbfc; font-weight: 600; }
.alarm-level { padding: 4px 10px; border-radius: 999px; font-size: 12px; }
.alarm-level.level-critical { background: rgba(255, 107, 107, .14); color: #ffb8b8; }
.alarm-level.level-warning { background: rgba(255, 200, 87, .14); color: #ffe2a4; }
.alarm-level.level-info { background: rgba(95, 211, 188, .14); color: #a4e8d9; }
.alarm-description { margin: 0 0 10px; color: #9fb3b8; line-height: 1.6; }
.alarm-description :deep(mark), .alarm-type :deep(mark) {
  background: rgba(255, 200, 87, .18); color: #fff0bf; padding: 0 3px; border-radius: 4px;
}
.alarm-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.alarm-meta span { padding: 6px 10px; border-radius: 999px; background: rgba(17, 56, 63, .9); color: #d7e7ea; font-size: 12px; }
.alarm-actions { display: flex; gap: 8px; }
.ghost-btn, .primary-btn { height: 36px; padding: 0 14px; border-radius: 10px; cursor: pointer; font-weight: 600; transition: .2s ease; }
.ghost-btn { border: 1px solid rgba(164, 215, 210, .22); background: transparent; color: #d7e8eb; }
.primary-btn { border: none; background: linear-gradient(135deg, #4fa98f, #2f7f6d); color: #fff; }
.ghost-btn:disabled, .primary-btn:disabled { opacity: .6; cursor: not-allowed; }
.resolved-badge { color: #9cd8be; font-weight: 600; }
.pagination-bar {
  display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 12px;
  border-radius: 14px; background: rgba(8, 27, 32, .72); color: #98b0b5; margin-top: auto;
}
@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 rgba(255, 107, 107, 0); } 50% { box-shadow: 0 0 0 6px rgba(255, 107, 107, .08); } }
@media (max-width: 960px) {
  .filter-bar { grid-template-columns: 1fr; }
}
</style>

<template>
  <section class="environment-dashboard">
    <div class="panel-header">
      <div>
        <p class="eyebrow">实时感知</p>
        <h2>环境监测仪表盘</h2>
      </div>
      <div class="timestamp">最后更新：{{ formatTime(data.recordedAt) }}</div>
    </div>

    <div class="gauge-grid">
      <article
        v-for="metric in metrics"
        :key="metric.key"
        class="gauge-card"
        :class="{ alert: metric.key === 'ammonia_concentration' && (data.ammonia_concentration ?? 0) > 20 }"
      >
        <div class="gauge-chart" :ref="el => setChartRef(el, metric.key)"></div>
        <div class="metric-meta">
          <span class="metric-label">{{ metric.label }}</span>
          <strong class="metric-value">{{ formatValue(metric.key, metric.unit, metric.precision) }}</strong>
          <span v-if="metric.key === 'ammonia_concentration' && (data.ammonia_concentration ?? 0) > 20" class="alarm-badge">
            氨气超出阈值
          </span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { onBeforeUnmount, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({
      temperature: null,
      humidity: null,
      co2_concentration: null,
      ammonia_concentration: null,
      recordedAt: null
    })
  }
})

const metrics = [
  { key: 'temperature', label: '温度', unit: '°C', max: 50, precision: 1, color: '#ff8f6b' },
  { key: 'humidity', label: '湿度', unit: '%', max: 100, precision: 1, color: '#5fd3bc' },
  { key: 'co2_concentration', label: '二氧化碳', unit: 'ppm', max: 5000, precision: 0, color: '#7dcf74' },
  { key: 'ammonia_concentration', label: '氨气', unit: 'ppm', max: 100, precision: 1, color: '#ffc857' }
]

const chartElements = new Map()
const chartInstances = new Map()

function setChartRef(element, key) {
  if (element) chartElements.set(key, element)
}

function buildGaugeOption(metric, rawValue) {
  const value = rawValue ?? 0
  const ratio = Math.min(value / metric.max, 1)
  const progressColor = ratio > 0.7 ? '#ff6b6b' : metric.color

  return {
    series: [
      {
        type: 'gauge',
        min: 0,
        max: metric.max,
        progress: {
          show: true,
          width: 16,
          itemStyle: { color: progressColor }
        },
        axisLine: {
          lineStyle: {
            width: 16,
            color: [
              [0.6, 'rgba(255,255,255,0.12)'],
              [0.8, 'rgba(255,200,87,0.25)'],
              [1, 'rgba(255,107,107,0.35)']
            ]
          }
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        anchor: { show: false },
        pointer: {
          show: true,
          itemStyle: { color: '#fff' },
          length: '58%',
          width: 4
        },
        detail: {
          valueAnimation: true,
          fontSize: 18,
          color: '#f3f7fa',
          offsetCenter: [0, '72%']
        },
        title: { show: false },
        data: [{ value }]
      }
    ]
  }
}

function ensureCharts() {
  metrics.forEach(metric => {
    const element = chartElements.get(metric.key)
    if (element && !chartInstances.has(metric.key)) {
      chartInstances.set(metric.key, echarts.init(element))
    }
  })
  updateCharts()
}

function updateCharts() {
  metrics.forEach(metric => {
    const chart = chartInstances.get(metric.key)
    if (!chart) return
    chart.setOption(buildGaugeOption(metric, props.data[metric.key]))
  })
}

function resizeCharts() {
  chartInstances.forEach(chart => chart.resize())
}

function disposeCharts() {
  chartInstances.forEach(chart => chart.dispose())
  chartInstances.clear()
}

function formatValue(key, unit, precision) {
  const value = props.data[key]
  if (value === null || value === undefined) return `-- ${unit}`
  return `${Number(value).toFixed(precision)} ${unit}`
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}

onMounted(() => {
  ensureCharts()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})

watch(() => props.data, updateCharts, { deep: true })
</script>

<style scoped lang="scss">
.environment-dashboard {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #87a5ac;
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

h2 {
  margin: 0;
  color: #f3f7fa;
  font-size: 24px;
}

.timestamp {
  color: #9cb1b8;
  font-size: 13px;
}

.gauge-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.gauge-card {
  padding: 16px;
  border-radius: 20px;
  border: 1px solid rgba(164, 215, 210, 0.16);
  background: linear-gradient(180deg, rgba(11, 39, 47, 0.9), rgba(8, 28, 34, 0.88));
}

.gauge-card.alert {
  border-color: rgba(255, 107, 107, 0.5);
  box-shadow: 0 0 0 1px rgba(255, 107, 107, 0.2), 0 16px 40px rgba(95, 13, 13, 0.28);
}

.gauge-chart {
  width: 100%;
  height: 180px;
}

.metric-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.metric-label {
  color: #8cb1af;
  font-size: 14px;
}

.metric-value {
  color: #f6fffd;
  font-size: 24px;
  font-weight: 700;
}

.alarm-badge {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 107, 107, 0.18);
  color: #ffb3b3;
  font-size: 12px;
}

@media (max-width: 900px) {
  .gauge-grid {
    grid-template-columns: 1fr;
  }

  .panel-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

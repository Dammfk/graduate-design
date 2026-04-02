<template>
  <section class="environment-dashboard">
    <div class="panel-header">
      <div>
        <h2>环境监测仪表盘</h2>
      </div>
      <div class="timestamp">最后更新：{{ formatTime(data.recordedAt) }}</div>
    </div>

    <div class="gauge-grid">
      <article
        v-for="metric in metrics"
        :key="metric.key"
        class="gauge-card"
        :class="statusClass(metric)"
      >
        <div class="gauge-chart" :ref="(el) => setChartRef(el, metric.key)"></div>
        <div class="metric-meta">
          <span class="metric-label">{{ metric.label }}</span>
          <strong class="metric-value">{{ formatValue(metric.key, metric.unit, metric.precision) }}</strong>
          <span class="status-badge" :class="statusClass(metric)">{{ statusText(metric) }}</span>
          <span class="metric-reference">{{ metric.reference }}</span>
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
  {
    key: 'temperature',
    label: '温度',
    unit: '°C',
    max: 50,
    precision: 1,
    reference: '参考值：18-28°C 正常，16-32°C 预警，其余异常',
    thresholds: { normal: [18, 28], warn: [16, 32] }
  },
  {
    key: 'humidity',
    label: '湿度',
    unit: '%',
    max: 100,
    precision: 1,
    reference: '参考值：55-75% 正常，45-85% 预警，其余异常',
    thresholds: { normal: [55, 75], warn: [45, 85] }
  },
  {
    key: 'co2_concentration',
    label: '二氧化碳',
    unit: 'ppm',
    max: 5000,
    precision: 0,
    reference: '参考值：≤1000ppm 正常，≤2000ppm 预警，>2000ppm 异常',
    thresholds: { normal: [0, 1000], warn: [0, 2000] }
  },
  {
    key: 'ammonia_concentration',
    label: '氨气',
    unit: 'ppm',
    max: 100,
    precision: 1,
    reference: '参考值：≤10ppm 正常，≤20ppm 预警，>20ppm 异常',
    thresholds: { normal: [0, 10], warn: [0, 20] }
  }
]

const chartElements = new Map()
const chartInstances = new Map()

function setChartRef(element, key) {
  if (element) chartElements.set(key, element)
}

function getMetricStatus(metric, rawValue) {
  if (rawValue === null || rawValue === undefined) return 'normal'
  const [normalMin, normalMax] = metric.thresholds.normal
  const [warnMin, warnMax] = metric.thresholds.warn
  if (rawValue >= normalMin && rawValue <= normalMax) return 'status-normal'
  if (rawValue >= warnMin && rawValue <= warnMax) return 'status-warn'
  return 'status-danger'
}

function statusColor(status) {
  if (status === 'status-danger') return '#ff6b6b'
  if (status === 'status-warn') return '#ffc857'
  return '#67d5aa'
}

function buildGaugeOption(metric, rawValue) {
  const value = rawValue ?? 0
  const status = getMetricStatus(metric, rawValue)
  const progressColor = statusColor(status)

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
              [0.6, 'rgba(103,213,170,0.18)'],
              [0.8, 'rgba(255,200,87,0.22)'],
              [1, 'rgba(255,107,107,0.26)']
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
          offsetCenter: [0, '72%'],
          formatter: (currentValue) => Number(currentValue).toFixed(metric.precision)
        },
        title: { show: false },
        data: [{ value }]
      }
    ]
  }
}

function ensureCharts() {
  metrics.forEach((metric) => {
    const element = chartElements.get(metric.key)
    if (element && !chartInstances.has(metric.key)) {
      chartInstances.set(metric.key, echarts.init(element))
    }
  })
  updateCharts()
}

function updateCharts() {
  metrics.forEach((metric) => {
    const chart = chartInstances.get(metric.key)
    if (!chart) return
    chart.setOption(buildGaugeOption(metric, props.data[metric.key]))
  })
}

function resizeCharts() {
  chartInstances.forEach((chart) => chart.resize())
}

function disposeCharts() {
  chartInstances.forEach((chart) => chart.dispose())
  chartInstances.clear()
}

function formatValue(key, unit, precision) {
  const value = props.data[key]
  if (value === null || value === undefined) return `-- ${unit}`
  return `${Number(value).toFixed(precision)} ${unit}`
}

function statusClass(metric) {
  return getMetricStatus(metric, props.data[metric.key])
}

function statusText(metric) {
  const status = getMetricStatus(metric, props.data[metric.key])
  if (status === 'status-danger') return '异常'
  if (status === 'status-warn') return '预警'
  return '正常'
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
  gap: 8px;
  height: 100%;
  overflow: auto;
  padding-right: 2px;
}

.panel-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10px;
}

h2 {
  margin: 0;
  color: #f3f7fa;
  font-size: 20px;
}

.timestamp {
  color: #9cb1b8;
  font-size: 11px;
}

.gauge-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.gauge-card {
  padding: 10px;
  border-radius: 14px;
  border: 1px solid rgba(164, 215, 210, 0.16);
  background: linear-gradient(180deg, rgba(11, 39, 47, 0.9), rgba(8, 28, 34, 0.88));
}

.gauge-card.status-normal {
  border-color: rgba(103, 213, 170, 0.28);
}

.gauge-card.status-warn {
  border-color: rgba(255, 200, 87, 0.4);
}

.gauge-card.status-danger {
  border-color: rgba(255, 107, 107, 0.5);
  box-shadow: 0 0 0 1px rgba(255, 107, 107, 0.2), 0 16px 40px rgba(95, 13, 13, 0.28);
}

.gauge-chart {
  width: 100%;
  height: 96px;
}

.metric-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  text-align: center;
}

.metric-label {
  color: #8cb1af;
  font-size: 12px;
}

.metric-value {
  color: #f6fffd;
  font-size: 18px;
  font-weight: 700;
}

.status-badge {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
}

.status-badge.status-normal {
  background: rgba(103, 213, 170, 0.14);
  color: #c8f7e5;
}

.status-badge.status-warn {
  background: rgba(255, 200, 87, 0.16);
  color: #ffe2a4;
}

.status-badge.status-danger {
  background: rgba(255, 107, 107, 0.18);
  color: #ffb3b3;
}

.metric-reference {
  color: #8cb1af;
  font-size: 11px;
  line-height: 1.3;
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

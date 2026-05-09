<template>
  <section class="trend-chart">
    <div class="chart-header">
      <div class="title-block">
        <p class="eyebrow">History Trend</p>
        <h2>{{ title }}</h2>
        <p class="chart-caption">
          {{ compareMode ? '对比模式会把多指标归一化到同一趋势坐标，方便横向比较波动。' : `${currentMetric.label} 默认优先展示最近 ${rangeLabelMap[activeRange]} 的变化。` }}
        </p>
      </div>

      <div class="toolbar">
        <div class="range-tabs">
          <button
            v-for="range in ranges"
            :key="range.value"
            :class="{ active: activeRange === range.value }"
            @click="activeRange = range.value"
          >
            {{ range.label }}
          </button>
        </div>

        <div class="metric-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            :class="{ active: activeTab === tab.value, muted: compareMode }"
            @click="activeTab = tab.value"
          >
            {{ tab.label }}
          </button>
          <button class="compare-toggle" :class="{ active: compareMode }" @click="compareMode = !compareMode">
            {{ compareMode ? '退出对比' : '多指标对比' }}
          </button>
        </div>
      </div>
    </div>

    <div class="stat-row">
      <article v-for="item in statCards" :key="item.label" class="stat-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </div>

    <div v-if="hasData" ref="chartRef" class="chart-container"></div>
    <div v-else class="chart-empty">
      <strong>当前时间范围内还没有可用趋势数据</strong>
      <span>可以等待设备继续上报，或切换到更长的时间范围后再查看。</span>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  TooltipComponent
} from 'echarts/components'
import { init, use } from 'echarts/core'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent, MarkAreaComponent])

const props = defineProps({
  title: { type: String, default: '环境数据趋势' },
  data: { type: Array, default: () => [] }
})

const chartRef = ref(null)
const chart = ref(null)
const activeTab = ref('temperature')
const activeRange = ref('24h')
const compareMode = ref(false)

const tabs = [
  { label: '温度', value: 'temperature', color: '#ff8f6b', unit: '°C' },
  { label: '湿度', value: 'humidity', color: '#54d3c2', unit: '%' },
  { label: 'CO2', value: 'co2_concentration', color: '#8ad86a', unit: 'ppm' },
  { label: '氨气', value: 'ammonia_concentration', color: '#ffc857', unit: 'ppm' }
]

const ranges = [
  { label: '6小时', value: '6h' },
  { label: '24小时', value: '24h' },
  { label: '全部', value: 'all' }
]

const rangeLabelMap = {
  '6h': '6 小时',
  '24h': '24 小时',
  all: '全部历史'
}

const metricThresholds = {
  temperature: { low: 5, high: 30 },
  humidity: { low: 20, high: 90 },
  co2_concentration: { high: 2000 },
  ammonia_concentration: { high: 20 }
}

const currentMetric = computed(() => tabs.find((item) => item.value === activeTab.value) || tabs[0])

const normalizedData = computed(() => {
  return props.data
    .map((item) => ({
      ...item,
      _time: parseTime(item.timestamp || item.recorded_at || item.alarm_time)
    }))
    .filter((item) => item._time)
    .sort((a, b) => a._time - b._time)
})

const filteredData = computed(() => {
  if (activeRange.value === 'all') {
    return normalizedData.value
  }

  if (!normalizedData.value.length) {
    return []
  }

  const lastTime = normalizedData.value[normalizedData.value.length - 1]._time
  const rangeMs = activeRange.value === '6h' ? 6 * 60 * 60 * 1000 : 24 * 60 * 60 * 1000
  return normalizedData.value.filter((item) => lastTime - item._time <= rangeMs)
})

const hasData = computed(() => filteredData.value.some((item) => tabs.some((tab) => item[tab.value] !== null && item[tab.value] !== undefined)))

const currentValues = computed(() => {
  const values = filteredData.value
    .map((item) => Number(item[currentMetric.value.value]))
    .filter((item) => Number.isFinite(item))

  if (!values.length) {
    return null
  }

  const current = values[values.length - 1]
  const max = Math.max(...values)
  const min = Math.min(...values)
  return { current, max, min }
})

const statCards = computed(() => {
  if (compareMode.value) {
    return tabs.map((tab) => {
      const value = latestMetricValue(tab.value)
      return {
        label: `${tab.label}当前值`,
        value: value === null ? '--' : `${formatNumber(value)} ${tab.unit}`
      }
    })
  }

  return [
    { label: '当前值', value: currentValues.value ? `${formatNumber(currentValues.value.current)} ${currentMetric.value.unit}` : '--' },
    { label: '最高值', value: currentValues.value ? `${formatNumber(currentValues.value.max)} ${currentMetric.value.unit}` : '--' },
    { label: '最低值', value: currentValues.value ? `${formatNumber(currentValues.value.min)} ${currentMetric.value.unit}` : '--' }
  ]
})

function parseTime(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date.getTime()
}

function formatAxisTime(timestamp) {
  return new Date(timestamp).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatNumber(value) {
  return Number(value).toFixed(Math.abs(Number(value)) >= 1000 ? 0 : 1)
}

function latestMetricValue(key) {
  for (let index = filteredData.value.length - 1; index >= 0; index -= 1) {
    const value = Number(filteredData.value[index][key])
    if (Number.isFinite(value)) {
      return value
    }
  }
  return null
}

function buildSingleSeries() {
  const metric = currentMetric.value
  const threshold = metricThresholds[metric.value] || {}
  const data = filteredData.value.map((item) => {
    const raw = Number(item[metric.value])
    return Number.isFinite(raw) ? raw : null
  })

  const markAreaData = []
  if (threshold.high !== undefined) {
    markAreaData.push([
      { yAxis: threshold.high, itemStyle: { color: 'rgba(255, 143, 107, 0.08)' } },
      { yAxis: Math.max(...data.filter((value) => value !== null), threshold.high) }
    ])
  }
  if (threshold.low !== undefined) {
    markAreaData.push([
      { yAxis: Math.min(...data.filter((value) => value !== null), threshold.low) },
      { yAxis: threshold.low, itemStyle: { color: 'rgba(95, 211, 188, 0.06)' } }
    ])
  }

  return [
    {
      name: metric.label,
      type: 'line',
      smooth: true,
      showSymbol: false,
      data,
      lineStyle: { color: metric.color, width: 3 },
      itemStyle: { color: metric.color },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: `${metric.color}66` },
            { offset: 1, color: `${metric.color}0a` }
          ]
        }
      },
      markArea: markAreaData.length
        ? {
            silent: true,
            data: markAreaData
          }
        : undefined,
      markPoint: currentValues.value
        ? {
            symbolSize: 48,
            data: [
              {
                coord: [filteredData.value.length - 1, currentValues.value.current],
                value: `当前 ${formatNumber(currentValues.value.current)}`
              }
            ],
            label: {
              color: '#eff7f8',
              formatter: ({ value }) => value
            },
            itemStyle: {
              color: metric.color,
              borderColor: '#eff7f8',
              borderWidth: 1
            }
          }
        : undefined
    }
  ]
}

function normalizeCompareValues(key) {
  const values = filteredData.value
    .map((item) => Number(item[key]))
    .filter((value) => Number.isFinite(value))

  if (!values.length) {
    return filteredData.value.map(() => null)
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  return filteredData.value.map((item) => {
    const raw = Number(item[key])
    return Number.isFinite(raw) ? Number((((raw - min) / range) * 100).toFixed(1)) : null
  })
}

function buildCompareSeries() {
  return tabs.map((tab) => ({
    name: tab.label,
    type: 'line',
    smooth: true,
    showSymbol: false,
    data: normalizeCompareValues(tab.value),
    lineStyle: { color: tab.color, width: 2.5 },
    itemStyle: { color: tab.color }
  }))
}

function updateChart() {
  if (!chart.value) return

  if (!hasData.value) {
    chart.value.clear()
    return
  }

  const xLabels = filteredData.value.map((item) => formatAxisTime(item._time))
  const series = compareMode.value ? buildCompareSeries() : buildSingleSeries()

  chart.value.setOption({
    animationDuration: 450,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(9, 22, 28, 0.94)',
      borderColor: 'rgba(164, 215, 210, 0.25)',
      textStyle: { color: '#eef7f8' },
      formatter(params) {
        const title = `${params[0]?.axisValue || '--'}`
        const rows = params
          .map((point) => {
            if (compareMode.value) {
              return `${point.marker}${point.seriesName}：${point.data ?? '--'}`
            }
            return `${point.marker}${currentMetric.value.label}：${point.data ?? '--'} ${currentMetric.value.unit}`
          })
          .join('<br/>')
        return `${title}<br/>${rows}`
      }
    },
    legend: {
      show: compareMode.value,
      top: 4,
      textStyle: { color: '#9bb0b6' }
    },
    grid: {
      left: 18,
      right: 18,
      top: compareMode.value ? 44 : 28,
      bottom: 18,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xLabels,
      axisLine: { lineStyle: { color: 'rgba(180, 220, 219, 0.25)' } },
      axisLabel: { color: '#9bb0b6' }
    },
    yAxis: {
      type: 'value',
      min: compareMode.value ? 0 : null,
      max: compareMode.value ? 100 : null,
      axisLine: { show: false },
      axisLabel: {
        color: '#9bb0b6',
        formatter: (value) => (compareMode.value ? `${value}%` : value)
      },
      splitLine: { lineStyle: { color: 'rgba(180, 220, 219, 0.12)' } }
    },
    series
  })
}

function resizeChart() {
  chart.value?.resize()
}

onMounted(() => {
  if (!chartRef.value) return
  chart.value = init(chartRef.value)
  updateChart()
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  chart.value?.dispose()
})

watch([filteredData, activeTab, activeRange, compareMode], updateChart, { deep: true })
</script>

<style scoped lang="scss">
.trend-chart {
  display: flex;
  flex-direction: column;
  gap: 14px;
  height: 100%;
}

.chart-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
}

.title-block {
  display: grid;
  gap: 6px;
}

.eyebrow {
  margin: 0;
  color: #87a5ac;
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

h2 {
  margin: 0;
  color: #f3f7fa;
  font-size: 22px;
}

.chart-caption {
  margin: 0;
  color: #8fa8af;
  font-size: 14px;
  line-height: 1.6;
}

.toolbar {
  display: grid;
  gap: 10px;
  justify-items: end;
}

.range-tabs,
.metric-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.range-tabs button,
.metric-tabs button {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(164, 215, 210, 0.18);
  background: rgba(15, 48, 57, 0.6);
  color: #99b2b7;
  cursor: pointer;
  transition: 0.2s ease;
  font-size: 13px;
}

.range-tabs button.active,
.metric-tabs button.active,
.range-tabs button:hover,
.metric-tabs button:hover {
  color: #f4fbfc;
  border-color: rgba(164, 215, 210, 0.45);
  background: rgba(26, 82, 92, 0.72);
}

.metric-tabs button.muted {
  opacity: 0.72;
}

.compare-toggle {
  border-style: dashed !important;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 10px;
}

.stat-card {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(10, 33, 39, 0.82);
  border: 1px solid rgba(164, 215, 210, 0.1);
}

.stat-card span {
  color: #8aa6ad;
  font-size: 13px;
}

.stat-card strong {
  color: #f4f8fa;
  font-size: 18px;
  line-height: 1.2;
}

.chart-container {
  flex: 1;
  min-height: 280px;
}

.chart-empty {
  flex: 1;
  min-height: 280px;
  display: grid;
  place-content: center;
  gap: 8px;
  padding: 18px;
  border-radius: 18px;
  border: 1px dashed rgba(164, 215, 210, 0.16);
  background: rgba(9, 29, 35, 0.74);
  text-align: center;
}

.chart-empty strong {
  color: #eef7f8;
  font-size: 18px;
}

.chart-empty span {
  color: #90a9b0;
  line-height: 1.6;
}

@media (max-width: 1100px) {
  .chart-header {
    flex-direction: column;
  }

  .toolbar {
    width: 100%;
    justify-items: start;
  }

  .range-tabs,
  .metric-tabs {
    justify-content: flex-start;
  }
}

@media (max-width: 720px) {
  .stat-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chart-container,
  .chart-empty {
    min-height: 240px;
  }
}
</style>

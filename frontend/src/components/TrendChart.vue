<template>
  <section class="trend-chart">
    <div class="chart-header">
      <div>
        <p class="eyebrow">历史趋势</p>
        <h2>{{ title }}</h2>
      </div>
      <div class="chart-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          :class="{ active: activeTab === tab.value }"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>
    <div ref="chartRef" class="chart-container"></div>
  </section>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  title: { type: String, default: '环境数据趋势' },
  data: { type: Array, default: () => [] }
})

const chartRef = ref(null)
const chart = ref(null)
const activeTab = ref('temperature')

const tabs = [
  { label: '温度', value: 'temperature', color: '#ff8f6b', unit: '°C' },
  { label: '湿度', value: 'humidity', color: '#54d3c2', unit: '%' },
  { label: 'CO2', value: 'co2_concentration', color: '#8ad86a', unit: 'ppm' },
  { label: '氨气', value: 'ammonia_concentration', color: '#ffc857', unit: 'ppm' }
]

function getCurrentTab() {
  return tabs.find(item => item.value === activeTab.value) || tabs[0]
}

function updateChart() {
  if (!chart.value) return

  const currentTab = getCurrentTab()
  const times = props.data.map(item =>
    new Date(item.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  )
  const values = props.data.map(item => item[currentTab.value] ?? null)

  chart.value.setOption({
    animationDuration: 500,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(9, 22, 28, 0.94)',
      borderColor: 'rgba(164, 215, 210, 0.25)',
      textStyle: { color: '#eef7f8' },
      formatter(params) {
        const point = params[0]
        return `${point.axisValue}<br/>${currentTab.label}：${point.data ?? '--'} ${currentTab.unit}`
      }
    },
    grid: {
      left: 18,
      right: 18,
      top: 30,
      bottom: 18,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLine: { lineStyle: { color: 'rgba(180, 220, 219, 0.25)' } },
      axisLabel: { color: '#9bb0b6' }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#9bb0b6' },
      splitLine: { lineStyle: { color: 'rgba(180, 220, 219, 0.12)' } }
    },
    series: [
      {
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: values,
        lineStyle: { color: currentTab.color, width: 3 },
        itemStyle: { color: currentTab.color },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: `${currentTab.color}66` },
            { offset: 1, color: `${currentTab.color}08` }
          ])
        }
      }
    ]
  })
}

function resizeChart() {
  chart.value?.resize()
}

onMounted(() => {
  if (chartRef.value) {
    chart.value = echarts.init(chartRef.value)
    updateChart()
    window.addEventListener('resize', resizeChart)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  chart.value?.dispose()
})

watch(() => props.data, updateChart, { deep: true })
watch(activeTab, updateChart)
</script>

<style scoped lang="scss">
.trend-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.chart-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
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
  font-size: 22px;
}

.chart-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chart-tabs button {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(164, 215, 210, 0.18);
  background: rgba(15, 48, 57, 0.6);
  color: #99b2b7;
  cursor: pointer;
  transition: 0.2s ease;
  font-size: 13px;
}

.chart-tabs button.active,
.chart-tabs button:hover {
  color: #f4fbfc;
  border-color: rgba(164, 215, 210, 0.45);
  background: rgba(26, 82, 92, 0.72);
}

.chart-container {
  flex: 1;
  min-height: 240px;
}

@media (max-width: 900px) {
  .chart-header {
    flex-direction: column;
  }
}
</style>

<template>
  <div class="page-grid">
    <ModuleContextBar
      :zone-options="monitoringStore.zoneOptions"
      :devices="monitoringStore.currentZoneDevices"
      :selected-zone="monitoringStore.selectedZone"
      :selected-device-id="monitoringStore.selectedDeviceId"
      :selected-hours="monitoringStore.selectedHours"
      :show-device="false"
      show-hours
      @update:zone="handleZoneChange"
      @update:hours="handleHoursChange"
    />

    <section class="monitoring-layout">
      <aside class="page-panel zone-panel">
        <div class="section-heading">
          <div>
            <p>分区概览</p>
            <h3>{{ monitoringStore.currentZone?.zone_name || '未选择区域' }}</h3>
          </div>
        </div>

        <div class="zone-metrics">
          <div>
            <span>在线设备</span>
            <strong>{{ monitoringStore.currentZone?.online_count ?? 0 }}</strong>
          </div>
          <div>
            <span>离线设备</span>
            <strong>{{ monitoringStore.currentZone?.offline_count ?? 0 }}</strong>
          </div>
        </div>

        <div v-if="monitoringStore.currentZoneDevices.length" class="device-list">
          <button
            v-for="device in monitoringStore.currentZoneDevices"
            :key="device.device_id"
            class="device-card"
            :class="{ active: device.device_id === monitoringStore.selectedDeviceId }"
            @click="handleDeviceChange(device.device_id)"
          >
            <div class="device-card-head">
              <strong>{{ device.device_name }}</strong>
              <span class="device-status" :class="{ online: device.is_active !== false }"></span>
            </div>
            <small>{{ device.location || '未标注位置' }}</small>
            <span>{{ device.device_id }}</span>
          </button>
        </div>
        <div v-else class="inline-empty-state">
          <strong>当前区域还没有可展示的设备</strong>
          <span>可以先切换到其他区域，或等待设备完成上报后再查看实时数据。</span>
        </div>
      </aside>

      <div class="page-grid content-stack">
        <section class="page-panel">
          <template v-if="monitoringStore.selectedDeviceId">
            <EnvironmentDashboard :data="monitoringStore.currentMetrics" />
          </template>
          <div v-else class="panel-empty-state">
            <strong>还没有选中设备</strong>
            <span>先从左侧设备列表里选择一台设备，再查看最新环境指标。</span>
          </div>
        </section>

        <section class="page-panel">
          <template v-if="monitoringStore.selectedDeviceId && monitoringStore.historicalData.length">
            <TrendChart :title="`${monitoringStore.currentDevice?.device_name || '当前设备'} 历史趋势`" :data="monitoringStore.historicalData" />
          </template>
          <div v-else class="panel-empty-state">
            <strong>{{ monitoringStore.selectedDeviceId ? '暂时没有历史数据' : '历史趋势暂未就绪' }}</strong>
            <span>
              {{ monitoringStore.selectedDeviceId
                ? '可以等待设备继续上报，或缩短时间范围后再查看趋势。'
                : '先选择一台设备，历史曲线会跟着设备和时间范围一起刷新。' }}
            </span>
          </div>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup>
import EnvironmentDashboard from '../components/EnvironmentDashboard.vue'
import ModuleContextBar from '../components/ModuleContextBar.vue'
import TrendChart from '../components/TrendChart.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()

async function handleZoneChange(zoneName) {
  monitoringStore.selectedZone = zoneName
  const firstDevice = monitoringStore.currentZoneDevices[0]
  monitoringStore.selectedDeviceId = firstDevice ? firstDevice.device_id : ''
  await monitoringStore.loadModule('monitoring')
}

async function handleDeviceChange(deviceId) {
  monitoringStore.selectedDeviceId = deviceId
  await Promise.all([monitoringStore.fetchLatestData(), monitoringStore.fetchHistoricalData()])
}

async function handleHoursChange(hours) {
  monitoringStore.selectedHours = hours
  await monitoringStore.fetchHistoricalData()
}
</script>

<style scoped lang="scss">
.page-grid {
  height: calc(100vh - 190px);
  min-height: calc(100vh - 190px);
  max-height: calc(100vh - 190px);
  grid-template-rows: auto minmax(0, 1fr);
}

.monitoring-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 14px;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.zone-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(10, 33, 39, 0.94), rgba(7, 23, 28, 0.94));
}

.zone-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.section-heading {
  margin-bottom: 12px;
}

.section-heading p {
  margin: 0 0 4px;
  color: var(--text-muted);
  font-size: 13px;
}

.section-heading h3 {
  margin: 0;
  font-size: 20px;
}

.zone-metrics > div,
.device-card {
  padding: 12px;
  border-radius: 14px;
  background: rgba(12, 40, 46, 0.86);
}

.zone-metrics span,
.device-card small,
.device-card span {
  color: var(--text-muted);
}

.zone-metrics strong {
  display: block;
  margin-top: 6px;
  font-size: 20px;
}

.content-stack {
  height: 100%;
  min-height: 0;
  grid-template-rows: minmax(360px, 1.05fr) minmax(0, 1fr);
  overflow: hidden;
}

.content-stack > .page-panel {
  min-height: 0;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(10, 33, 39, 0.94), rgba(7, 23, 28, 0.94));
}

.device-list {
  display: grid;
  gap: 8px;
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-right: 4px;
  grid-auto-rows: 86px;
}

.device-card {
  border: 1px solid transparent;
  text-align: left;
  color: var(--text-main);
  cursor: pointer;
  height: 86px;
  display: grid;
  grid-template-rows: auto auto auto;
  gap: 3px;
  align-content: stretch;
  padding: 10px 12px;
  overflow: hidden;
  line-height: 1.25;
}

.device-card.active {
  border-color: var(--border-strong);
  background: rgba(17, 54, 61, 0.94);
}

.device-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.device-card strong,
.device-card small,
.device-card span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-card strong {
  font-size: 14px;
  line-height: 1.3;
}

.device-card small,
.device-card span {
  font-size: 12px;
  line-height: 1.25;
}

.device-status {
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: 999px;
  background: rgba(255, 128, 128, 0.7);
  box-shadow: 0 0 0 4px rgba(255, 128, 128, 0.08);
}

.device-status.online {
  background: #67d5aa;
  box-shadow: 0 0 0 4px rgba(103, 213, 170, 0.08);
}

.inline-empty-state,
.panel-empty-state {
  display: grid;
  gap: 8px;
  align-content: center;
  justify-items: start;
  min-height: 180px;
  padding: 18px;
  border-radius: 16px;
  border: 1px dashed rgba(164, 215, 210, 0.16);
  background: rgba(9, 29, 35, 0.74);
}

.inline-empty-state strong,
.panel-empty-state strong {
  font-size: 17px;
  color: #eef7f7;
}

.inline-empty-state span,
.panel-empty-state span {
  color: var(--text-muted);
  line-height: 1.6;
}

@media (max-width: 1350px) {
  .page-grid {
    height: auto;
    min-height: auto;
    max-height: none;
  }

  .monitoring-layout {
    grid-template-columns: 1fr;
    height: auto;
    overflow: visible;
  }

  .content-stack {
    height: auto;
    overflow: visible;
  }
}

@media (max-width: 1100px) {
  .page-grid {
    height: auto;
    min-height: auto;
    max-height: none;
  }

  .monitoring-layout {
    grid-template-columns: 1fr;
    height: auto;
    overflow: visible;
  }

  .content-stack {
    height: auto;
    grid-template-rows: auto;
    overflow: visible;
  }
}
</style>

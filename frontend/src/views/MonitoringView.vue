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
        <div class="device-list">
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
      </aside>

      <div class="page-grid">
        <section class="page-panel">
          <EnvironmentDashboard :data="monitoringStore.currentMetrics" />
        </section>
        <section class="page-panel">
          <TrendChart :title="`${monitoringStore.currentDevice?.device_name || '当前设备'} 历史趋势`" :data="monitoringStore.historicalData" />
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
  if (firstDevice) {
    monitoringStore.selectedDeviceId = firstDevice.device_id
  }
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
  background:
    linear-gradient(180deg, rgba(10, 33, 39, 0.94), rgba(7, 23, 28, 0.94));
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

.monitoring-layout > .page-grid {
  height: 100%;
  min-height: 0;
  grid-template-rows: minmax(360px, 1.05fr) minmax(0, 1fr);
  overflow: hidden;
}

.monitoring-layout > .page-grid > .page-panel {
  min-height: 0;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(10, 33, 39, 0.94), rgba(7, 23, 28, 0.94));
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

  .monitoring-layout > .page-grid {
    height: auto;
    grid-template-rows: auto;
    overflow: visible;
  }
}
</style>

<template>
  <div class="page-grid">
    <ModuleContextBar
      :zone-options="monitoringStore.zoneOptions"
      :devices="monitoringStore.currentZoneDevices"
      :selected-zone="monitoringStore.selectedZone"
      :selected-device-id="monitoringStore.selectedDeviceId"
      :selected-hours="monitoringStore.selectedHours"
      show-hours
      @update:zone="handleZoneChange"
      @update:device="handleDeviceChange"
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
            <strong>{{ device.device_name }}</strong>
            <small>{{ device.location }}</small>
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
.monitoring-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 18px;
}

.zone-panel {
  height: fit-content;
}

.zone-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.zone-metrics > div,
.device-card {
  padding: 14px;
  border-radius: 16px;
  background: rgba(12, 40, 46, 0.86);
}

.zone-metrics span,
.device-card small,
.device-card span {
  color: var(--text-muted);
}

.zone-metrics strong {
  display: block;
  margin-top: 8px;
  font-size: 22px;
}

.device-list {
  display: grid;
  gap: 12px;
}

.device-card {
  border: 1px solid transparent;
  text-align: left;
  color: var(--text-main);
  cursor: pointer;
}

.device-card.active {
  border-color: var(--border-strong);
  background: rgba(17, 54, 61, 0.94);
}

@media (max-width: 1100px) {
  .monitoring-layout {
    grid-template-columns: 1fr;
  }
}
</style>

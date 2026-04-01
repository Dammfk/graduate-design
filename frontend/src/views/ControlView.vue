<template>
  <div class="page-grid">
    <ModuleContextBar
      :zone-options="monitoringStore.zoneOptions"
      :devices="monitoringStore.currentZoneDevices"
      :selected-zone="monitoringStore.selectedZone"
      :selected-device-id="monitoringStore.selectedDeviceId"
      @update:zone="handleZoneChange"
      @update:device="handleDeviceChange"
    />

    <section class="control-layout">
      <div class="page-grid">
        <section class="page-panel">
          <ControlPanel :device="monitoringStore.currentControlDevice" @command="handleCommand" />
        </section>
        <section class="page-panel">
          <AutomationRules :rules="monitoringStore.controlDashboard.automation_rules" @toggle="monitoringStore.toggleAutomationRule" />
        </section>
      </div>

      <section class="page-panel">
        <CommandHistory :commands="monitoringStore.controlDashboard.recent_commands" />
      </section>
    </section>
  </div>
</template>

<script setup>
import AutomationRules from '../components/AutomationRules.vue'
import CommandHistory from '../components/CommandHistory.vue'
import ControlPanel from '../components/ControlPanel.vue'
import ModuleContextBar from '../components/ModuleContextBar.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()

async function handleZoneChange(zoneName) {
  monitoringStore.selectedZone = zoneName
  const firstDevice = monitoringStore.currentZoneDevices[0]
  if (firstDevice) {
    monitoringStore.selectedDeviceId = firstDevice.device_id
  }
  await monitoringStore.loadModule('control')
}

async function handleDeviceChange(deviceId) {
  monitoringStore.selectedDeviceId = deviceId
  await monitoringStore.fetchControlDashboard()
}

async function handleCommand(componentKey, commandType, reason) {
  await monitoringStore.executeControlCommand(componentKey, commandType, reason)
}
</script>

<style scoped lang="scss">
.control-layout {
  display: grid;
  gap: 14px;
}

.control-layout > .page-grid {
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 14px;
}

@media (max-width: 1100px) {
  .control-layout > .page-grid {
    grid-template-columns: 1fr;
  }
}
</style>

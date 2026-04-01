<template>
  <div class="page-grid">
    <section class="page-panel">
      <SystemPanel
        :summary="monitoringStore.systemDashboard.summary"
        :users="monitoringStore.systemDashboard.users"
        :role-permissions="monitoringStore.systemDashboard.role_permissions"
        :operation-logs="monitoringStore.systemDashboard.operation_logs"
        :on-update-user="handleUpdateUser"
        :on-view-user-logs="handleViewUserLogs"
      />
    </section>
  </div>
</template>

<script setup>
import SystemPanel from '../components/SystemPanel.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()

async function handleUpdateUser(userId, payload) {
  await monitoringStore.updateUser(userId, payload)
}

async function handleViewUserLogs(userId, limit) {
  return monitoringStore.fetchUserLogs(userId, limit)
}
</script>

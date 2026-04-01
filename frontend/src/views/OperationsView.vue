<template>
  <div class="page-grid">
    <section class="page-panel">
      <OperationsPanel
        :summary="monitoringStore.operationsDashboard.summary"
        :tasks="monitoringStore.operationsDashboard.tasks"
        :inventory="monitoringStore.operationsDashboard.inventory"
        :assets="monitoringStore.operationsDashboard.assets"
        :archives="monitoringStore.archiveDashboard.archives"
        :users="monitoringStore.users"
        :on-create-task="handleCreateTask"
        :on-update-task-status="handleUpdateTaskStatus"
      />
    </section>
  </div>
</template>

<script setup>
import OperationsPanel from '../components/OperationsPanel.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()

async function handleCreateTask(payload) {
  await monitoringStore.createTask(payload)
}

async function handleUpdateTaskStatus(taskId, status) {
  await monitoringStore.updateTaskStatus(taskId, status)
}
</script>

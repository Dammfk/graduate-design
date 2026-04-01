<template>
  <div class="page-grid">
    <section class="page-panel">
      <OperationsPanel
        :summary="monitoringStore.operationsDashboard.summary"
        :daily-tasks="monitoringStore.operationsDashboard.daily_tasks"
        :tasks="monitoringStore.operationsDashboard.tasks"
        :inventory="monitoringStore.operationsDashboard.inventory"
        :assets="monitoringStore.operationsDashboard.assets"
        :archives="monitoringStore.archiveDashboard.archives"
        :users="monitoringStore.users"
        :on-create-task="handleCreateTask"
        :on-update-task="handleUpdateTask"
        :on-create-daily-task="handleCreateDailyTask"
        :on-update-daily-task="handleUpdateDailyTask"
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

async function handleUpdateTask(taskId, payload) {
  await monitoringStore.updateTask(taskId, payload)
}

async function handleCreateDailyTask(payload) {
  await monitoringStore.createDailyTask(payload)
}

async function handleUpdateDailyTask(taskId, payload) {
  await monitoringStore.updateDailyTask(taskId, payload)
}

async function handleUpdateTaskStatus(taskId, status) {
  await monitoringStore.updateTaskStatus(taskId, status)
}
</script>

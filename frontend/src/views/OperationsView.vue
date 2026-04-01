<template>
  <div class="page-grid">
    <section class="page-panel">
      <OperationsPanel
        :summary="monitoringStore.operationsDashboard.summary"
        :daily-tasks="monitoringStore.operationsDashboard.daily_tasks"
        :tasks="monitoringStore.operationsDashboard.today_tasks?.length ? monitoringStore.operationsDashboard.today_tasks : monitoringStore.operationsDashboard.tasks"
        :inventory="monitoringStore.operationsDashboard.inventory"
        :assets="monitoringStore.operationsDashboard.assets"
        :archives="monitoringStore.archiveDashboard.archives"
        :users="monitoringStore.users"
        :on-create-task="handleCreateTask"
        :on-update-task="handleUpdateTask"
        :on-create-daily-task="handleCreateDailyTask"
        :on-update-daily-task="handleUpdateDailyTask"
        :on-update-task-status="handleUpdateTaskStatus"
        :on-delete-task="handleDeleteTask"
        :on-create-inventory-item="handleCreateInventoryItem"
        :on-update-inventory-item="handleUpdateInventoryItem"
        :on-delete-inventory-item="handleDeleteInventoryItem"
        :on-create-equipment-asset="handleCreateEquipmentAsset"
        :on-update-equipment-asset="handleUpdateEquipmentAsset"
        :on-delete-equipment-asset="handleDeleteEquipmentAsset"
        :on-delete-daily-task="handleDeleteDailyTask"
      />
    </section>
  </div>
</template>

<script setup>
import OperationsPanel from '../components/OperationsPanel.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()

async function handleCreateTask(payload) {
  return await monitoringStore.createTask(payload)
}

async function handleUpdateTask(taskId, payload) {
  return await monitoringStore.updateTask(taskId, payload)
}

async function handleCreateDailyTask(payload) {
  return await monitoringStore.createDailyTask(payload)
}

async function handleUpdateDailyTask(taskId, payload) {
  return await monitoringStore.updateDailyTask(taskId, payload)
}

async function handleUpdateTaskStatus(taskId, status) {
  return await monitoringStore.updateTaskStatus(taskId, status)
}

async function handleDeleteTask(taskId) {
  return await monitoringStore.deleteTask(taskId)
}

async function handleCreateInventoryItem(payload) {
  return await monitoringStore.createInventoryItem(payload)
}

async function handleUpdateInventoryItem(itemId, payload) {
  return await monitoringStore.updateInventoryItem(itemId, payload)
}

async function handleDeleteInventoryItem(itemId) {
  return await monitoringStore.deleteInventoryItem(itemId)
}

async function handleCreateEquipmentAsset(payload) {
  return await monitoringStore.createEquipmentAsset(payload)
}

async function handleUpdateEquipmentAsset(assetId, payload) {
  return await monitoringStore.updateEquipmentAsset(assetId, payload)
}

async function handleDeleteEquipmentAsset(assetId) {
  return await monitoringStore.deleteEquipmentAsset(assetId)
}

async function handleDeleteDailyTask(taskId) {
  return await monitoringStore.deleteDailyTask(taskId)
}
</script>

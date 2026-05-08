<template>
  <div class="page-grid">
    <section class="page-panel">
      <ArchivePanel
        :summary="monitoringStore.archiveDashboard.summary"
        :archives="monitoringStore.archiveDashboard.archives"
        :selected-archive-id="monitoringStore.selectedArchiveId"
        :selected-archive="monitoringStore.selectedArchive"
        :on-create-archive="handleCreateArchive"
        :on-update-archive="handleUpdateArchive"
        :on-delete-archive="handleDeleteArchive"
        :on-create-animal="handleCreateAnimal"
        :on-update-animal="handleUpdateAnimal"
        :on-bulk-update-animals="handleBulkUpdateAnimals"
        :on-delete-animal="handleDeleteAnimal"
        @select="monitoringStore.selectedArchiveId = $event"
      />
    </section>
  </div>
</template>

<script setup>
import ArchivePanel from '../components/ArchivePanel.vue'
import { useMonitoringStore } from '../stores/monitoring'

const monitoringStore = useMonitoringStore()

async function handleCreateArchive(payload) {
  await monitoringStore.createArchive(payload)
}

async function handleUpdateArchive(archiveId, payload) {
  await monitoringStore.updateArchive(archiveId, payload)
}

async function handleDeleteArchive(archiveId) {
  await monitoringStore.deleteArchive(archiveId)
}

async function handleCreateAnimal(payload) {
  await monitoringStore.createAnimalProfile(payload)
}

async function handleUpdateAnimal(animalId, payload) {
  await monitoringStore.updateAnimalProfile(animalId, payload)
}

async function handleBulkUpdateAnimals(payload) {
  await monitoringStore.bulkUpdateAnimalProfiles(payload)
}

async function handleDeleteAnimal(animalId) {
  await monitoringStore.deleteAnimalProfile(animalId)
}
</script>

<style scoped>
.page-grid,
.page-panel {
  height: calc(100vh - 160px);
  min-height: calc(100vh - 160px);
  max-height: calc(100vh - 160px);
}

.page-panel {
  overflow: hidden;
}
</style>

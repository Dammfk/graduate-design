import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

export const telemetryAPI = {
  sendTelemetry(data) {
    return api.post('/telemetry/', data)
  },

  getOverview() {
    return api.get('/telemetry/overview')
  },

  getLatest(deviceId) {
    return api.get(`/telemetry/latest/${deviceId}`)
  },

  getHistory(deviceId, hours = 24) {
    return api.get(`/telemetry/history/${deviceId}`, {
      params: { hours }
    })
  },

  getZoneHistory(zoneName, hours = 24) {
    return api.get(`/telemetry/zones/${zoneName}/history`, {
      params: { hours }
    })
  }
}

export const alarmAPI = {
  getPending() {
    return api.get('/alarms/pending')
  },

  getRiskDashboard() {
    return api.get('/alarms/risk-dashboard')
  },

  getSettings() {
    return api.get('/alarms/settings')
  },

  updateSetting(alarmType, data) {
    return api.put(`/alarms/settings/${alarmType}`, data)
  },

  getDeviceAlarms(deviceId, limit = 20) {
    return api.get(`/alarms/device/${deviceId}`, {
      params: { limit }
    })
  },

  acknowledge(alarmId, userId = null) {
    return api.put(`/alarms/${alarmId}/acknowledge`, {
      user_id: userId
    })
  },

  resolve(alarmId) {
    return api.put(`/alarms/${alarmId}/resolve`)
  }
}

export const deviceAPI = {
  list(ownerId = null) {
    return api.get('/devices/', {
      params: { owner_id: ownerId }
    })
  },

  getDetail(deviceId) {
    return api.get(`/devices/${deviceId}`)
  },

  create(data, ownerId) {
    return api.post('/devices/', data, {
      params: { owner_id: ownerId }
    })
  },

  update(deviceId, data) {
    return api.put(`/devices/${deviceId}`, data)
  },

  delete(deviceId) {
    return api.delete(`/devices/${deviceId}`)
  }
}

export const controlAPI = {
  getDashboard() {
    return api.get('/control/dashboard')
  },

  executeCommand(deviceId, data) {
    return api.post(`/control/devices/${deviceId}/commands`, data, {
      timeout: 30000
    })
  },

  updateRule(ruleId, data) {
    return api.put(`/control/rules/${ruleId}`, data)
  }
}

export const archiveAPI = {
  getDashboard() {
    return api.get('/archives/dashboard')
  },

  createArchive(data) {
    return api.post('/archives/', data)
  },

  updateArchive(archiveId, data) {
    return api.put(`/archives/${archiveId}`, data)
  },

  deleteArchive(archiveId) {
    return api.delete(`/archives/${archiveId}`)
  },

  createAnimal(data) {
    return api.post('/archives/animals', data)
  },

  updateAnimal(animalId, data) {
    return api.put(`/archives/animals/${animalId}`, data)
  },

  deleteAnimal(animalId) {
    return api.delete(`/archives/animals/${animalId}`)
  }
}

export const operationsAPI = {
  getDashboard() {
    return api.get('/operations/dashboard')
  },

  createTask(data) {
    return api.post('/operations/tasks', data, {
      timeout: 20000
    })
  },

  updateTaskStatus(taskId, data) {
    return api.put(`/operations/tasks/${taskId}/status`, data, {
      timeout: 20000
    })
  },

  updateTask(taskId, data) {
    return api.put(`/operations/tasks/${taskId}`, data, {
      timeout: 20000
    })
  },

  deleteTask(taskId) {
    return api.delete(`/operations/tasks/${taskId}`, {
      timeout: 20000
    })
  },

  createDailyTask(data) {
    return api.post('/operations/daily-tasks', data, {
      timeout: 20000
    })
  },

  updateDailyTask(taskId, data) {
    return api.put(`/operations/daily-tasks/${taskId}`, data, {
      timeout: 20000
    })
  },

  deleteDailyTask(taskId) {
    return api.delete(`/operations/daily-tasks/${taskId}`, {
      timeout: 20000
    })
  },

  createInventoryItem(data) {
    return api.post('/operations/inventory', data, {
      timeout: 20000
    })
  },

  updateInventoryItem(itemId, data) {
    return api.put(`/operations/inventory/${itemId}`, data, {
      timeout: 20000
    })
  },

  deleteInventoryItem(itemId) {
    return api.delete(`/operations/inventory/${itemId}`, {
      timeout: 20000
    })
  },

  createEquipmentAsset(data) {
    return api.post('/operations/assets', data, {
      timeout: 20000
    })
  },

  updateEquipmentAsset(assetId, data) {
    return api.put(`/operations/assets/${assetId}`, data, {
      timeout: 20000
    })
  },

  deleteEquipmentAsset(assetId) {
    return api.delete(`/operations/assets/${assetId}`, {
      timeout: 20000
    })
  }
}

export const systemAPI = {
  getDashboard() {
    return api.get('/system/dashboard')
  },

  getUserLogs(userId, limit = 20) {
    return api.get(`/system/users/${userId}/logs`, {
      params: { limit }
    })
  },

  updateUser(userId, data) {
    return api.put(`/system/users/${userId}`, data, {
      timeout: 20000
    })
  }
}

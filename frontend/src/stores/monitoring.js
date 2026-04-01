import { computed, reactive, ref } from 'vue'
import { defineStore } from 'pinia'
import { alarmAPI, archiveAPI, controlAPI, operationsAPI, systemAPI, telemetryAPI } from '../api/client'

const CACHE_KEY = 'smart-ranch-dashboard-cache'

function createEmptyLatestData() {
  return {
    temperature: null,
    humidity: null,
    co2_concentration: null,
    ammonia_concentration: null,
    recordedAt: null
  }
}

function normalizeError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback
}

function readCache() {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(CACHE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function writeCache(payload) {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(CACHE_KEY, JSON.stringify(payload))
  } catch {
    // Ignore cache write failures and keep runtime state working.
  }
}

export const useMonitoringStore = defineStore('monitoring', () => {
  const selectedZone = ref('')
  const selectedDeviceId = ref('')
  const selectedHours = ref(24)
  const selectedArchiveId = ref(null)

  const overview = reactive({
    summary: {
      device_count: 0,
      zone_count: 0,
      online_count: 0,
      offline_count: 0,
      avg_temperature: null,
      avg_humidity: null,
      avg_co2: null,
      avg_ammonia: null,
      last_updated_at: null
    },
    zones: [],
    devices: []
  })

  const controlDashboard = reactive({
    devices: [],
    automation_rules: [],
    recent_commands: [],
    components_catalog: []
  })

  const archiveDashboard = reactive({
    summary: {
      archive_count: 0,
      active_batches: 0,
      total_quantity: 0,
      average_weight: null,
      average_feed_consumption: null,
      individual_archive_count: 0
    },
    archives: []
  })

  const riskDashboard = reactive({
    summary: {},
    level_distribution: {},
    type_distribution: {},
    zone_distribution: {},
    archive_risks: [],
    history: []
  })

  const operationsDashboard = reactive({
    summary: {},
    daily_tasks: [],
    tasks: [],
    today_tasks: [],
    inventory: [],
    assets: []
  })

  const systemDashboard = reactive({
    summary: {},
    users: [],
    role_permissions: [],
    operation_logs: []
  })

  const users = ref([])
  const latestData = reactive(createEmptyLatestData())
  const historicalData = ref([])
  const alarms = ref([])
  const loading = ref(false)
  const ammoniaAlert = ref(false)
  const lastRefreshError = ref('')
  const activeModuleKey = ref('home')
  const errorByModule = reactive({
    home: '',
    monitoring: '',
    control: '',
    archives: '',
    alarms: '',
    operations: '',
    system: ''
  })
  const moduleInFlight = reactive({
    home: null,
    monitoring: null,
    control: null,
    archives: null,
    alarms: null,
    operations: null,
    system: null
  })
  const moduleRequestVersion = reactive({
    home: 0,
    monitoring: 0,
    control: 0,
    archives: 0,
    alarms: 0,
    operations: 0,
    system: 0
  })

  function persistCache() {
    writeCache({
      selectedZone: selectedZone.value,
      selectedDeviceId: selectedDeviceId.value,
      selectedHours: selectedHours.value,
      selectedArchiveId: selectedArchiveId.value,
      overview: {
        summary: overview.summary,
        zones: overview.zones,
        devices: overview.devices
      },
      controlDashboard: {
        devices: controlDashboard.devices,
        automation_rules: controlDashboard.automation_rules,
        recent_commands: controlDashboard.recent_commands,
        components_catalog: controlDashboard.components_catalog
      },
      archiveDashboard: {
        summary: archiveDashboard.summary,
        archives: archiveDashboard.archives
      },
      riskDashboard: {
        summary: riskDashboard.summary,
        level_distribution: riskDashboard.level_distribution,
        type_distribution: riskDashboard.type_distribution,
        zone_distribution: riskDashboard.zone_distribution,
        archive_risks: riskDashboard.archive_risks,
        history: riskDashboard.history
      },
      operationsDashboard: {
        summary: operationsDashboard.summary,
        daily_tasks: operationsDashboard.daily_tasks,
        tasks: operationsDashboard.tasks,
        today_tasks: operationsDashboard.today_tasks,
        inventory: operationsDashboard.inventory,
        assets: operationsDashboard.assets
      },
      systemDashboard: {
        summary: systemDashboard.summary,
        users: systemDashboard.users,
        role_permissions: systemDashboard.role_permissions,
        operation_logs: systemDashboard.operation_logs
      },
      latestData: { ...latestData },
      historicalData: historicalData.value,
      alarms: alarms.value,
      users: users.value
    })
  }

  function hydrateFromCache() {
    const cache = readCache()
    if (!cache) return

    selectedZone.value = cache.selectedZone || ''
    selectedDeviceId.value = cache.selectedDeviceId || ''
    selectedHours.value = cache.selectedHours || 24
    selectedArchiveId.value = cache.selectedArchiveId ?? null

    Object.assign(overview, cache.overview || {})
    Object.assign(controlDashboard, cache.controlDashboard || {})
    Object.assign(archiveDashboard, cache.archiveDashboard || {})
    Object.assign(riskDashboard, cache.riskDashboard || {})
    Object.assign(operationsDashboard, cache.operationsDashboard || {})
    Object.assign(systemDashboard, cache.systemDashboard || {})
    Object.assign(latestData, cache.latestData || createEmptyLatestData())
    historicalData.value = cache.historicalData || []
    alarms.value = cache.alarms || []
    users.value = cache.users || []

    syncDefaultSelection()
  }

  const zoneOptions = computed(() => overview.zones)
  const currentZone = computed(() => overview.zones.find(item => item.zone_name === selectedZone.value) || null)
  const currentZoneDevices = computed(() => currentZone.value?.devices || [])
  const currentDevice = computed(() => overview.devices.find(item => item.device_id === selectedDeviceId.value) || null)
  const currentMetrics = computed(() => {
    const source = currentDevice.value?.latest_data
    if (!source) return latestData
    return {
      temperature: source.temperature,
      humidity: source.humidity,
      co2_concentration: source.co2_concentration,
      ammonia_concentration: source.ammonia_concentration,
      recordedAt: source.recorded_at
    }
  })
  const currentControlDevice = computed(() => controlDashboard.devices.find(item => item.device_id === selectedDeviceId.value) || null)
  const selectedArchive = computed(() => archiveDashboard.archives.find(item => item.id === selectedArchiveId.value) || null)

  const homeCards = computed(() => [
    { title: '监测区域', value: overview.summary.zone_count || 0, subtitle: `设备 ${overview.summary.device_count || 0} 台` },
    { title: '待处理告警', value: alarms.value.length, subtitle: `高风险区域 ${riskDashboard.summary.highest_risk_zone || '--'}` },
    { title: '今日任务', value: operationsDashboard.summary.pending_tasks || 0, subtitle: `库存预警 ${operationsDashboard.summary.low_stock_items || 0} 项` },
    { title: '活跃用户', value: systemDashboard.summary.active_users || 0, subtitle: `活跃批次 ${archiveDashboard.summary.active_batches || 0}` }
  ])

  function applyLatestData(data) {
    latestData.temperature = data?.temperature ?? null
    latestData.humidity = data?.humidity ?? null
    latestData.co2_concentration = data?.co2_concentration ?? null
    latestData.ammonia_concentration = data?.ammonia_concentration ?? null
    latestData.recordedAt = data?.recorded_at ?? null
    ammoniaAlert.value = (latestData.ammonia_concentration ?? 0) > 20
  }

  function syncDefaultSelection() {
    if (!selectedZone.value && overview.zones.length > 0) {
      selectedZone.value = overview.zones[0].zone_name
    }

    const devices = currentZoneDevices.value
    if (!devices.some(item => item.device_id === selectedDeviceId.value) && devices.length > 0) {
      selectedDeviceId.value = devices[0].device_id
    }

    if (!selectedArchiveId.value && archiveDashboard.archives.length > 0) {
      selectedArchiveId.value = archiveDashboard.archives[0].id
    }

    if (selectedArchiveId.value && !archiveDashboard.archives.some(item => item.id === selectedArchiveId.value)) {
      selectedArchiveId.value = archiveDashboard.archives[0]?.id ?? null
    }
  }

  function setModuleError(moduleKey, error, fallback) {
    const message = normalizeError(error, fallback)
    errorByModule[moduleKey] = message
    lastRefreshError.value = message
  }

  function clearModuleError(moduleKey) {
    errorByModule[moduleKey] = ''
    if (activeModuleKey.value === moduleKey) {
      lastRefreshError.value = ''
    }
  }

  hydrateFromCache()

  async function fetchOverview() {
    const response = await telemetryAPI.getOverview()
    if (response.data.status === 'success') {
      overview.summary = response.data.data.summary
      overview.zones = response.data.data.zones
      overview.devices = response.data.data.devices
      syncDefaultSelection()
      if (currentDevice.value?.latest_data) applyLatestData(currentDevice.value.latest_data)
      persistCache()
    }
  }

  async function fetchControlDashboard() {
    const response = await controlAPI.getDashboard()
    if (response.data.status === 'success') {
      Object.assign(controlDashboard, response.data.data)
      persistCache()
    }
  }

  async function fetchArchiveDashboard() {
    const response = await archiveAPI.getDashboard()
    if (response.data.status === 'success') {
      archiveDashboard.summary = response.data.data.summary
      archiveDashboard.archives = response.data.data.archives
      syncDefaultSelection()
      persistCache()
    }
  }

  async function fetchRiskDashboard() {
    const response = await alarmAPI.getRiskDashboard()
    if (response.data.status === 'success') {
      Object.assign(riskDashboard, response.data.data)
      persistCache()
    }
  }

  async function fetchOperationsDashboard() {
    const response = await operationsAPI.getDashboard()
    if (response.data.status === 'success') {
      Object.assign(operationsDashboard, response.data.data)
      users.value = response.data.data.users || users.value
      persistCache()
    }
  }

  async function fetchSystemDashboard() {
    const response = await systemAPI.getDashboard()
    if (response.data.status === 'success') {
      Object.assign(systemDashboard, response.data.data)
      users.value = response.data.data.users || users.value
      persistCache()
    }
  }

  async function fetchLatestData(deviceId = selectedDeviceId.value) {
    if (!deviceId) return
    const response = await telemetryAPI.getLatest(deviceId)
    if (response.data.status === 'success') {
      applyLatestData(response.data.data)
      persistCache()
    }
  }

  async function fetchHistoricalData(deviceId = selectedDeviceId.value, hours = selectedHours.value) {
    if (!deviceId) return
    const response = await telemetryAPI.getHistory(deviceId, hours)
    if (response.data.status === 'success') {
      historicalData.value = response.data.data.map(item => ({
        timestamp: new Date(item.timestamp),
        temperature: item.temperature,
        humidity: item.humidity,
        co2_concentration: item.co2_concentration,
        ammonia_concentration: item.ammonia_concentration
      }))
      persistCache()
    }
  }

  async function fetchAlarms() {
    const response = await alarmAPI.getPending()
    if (response.data.status === 'success') {
      alarms.value = response.data.data
      persistCache()
    }
  }

  async function acknowledgeAlarm(alarmId) {
    await alarmAPI.acknowledge(alarmId)
    await Promise.all([fetchAlarms(), fetchRiskDashboard()])
  }

  async function resolveAlarm(alarmId) {
    await alarmAPI.resolve(alarmId)
    await Promise.all([fetchAlarms(), fetchRiskDashboard()])
  }

  async function executeControlCommand(targetComponent, commandType, reason) {
    if (!selectedDeviceId.value) return
    await controlAPI.executeCommand(selectedDeviceId.value, {
      target_component: targetComponent,
      command_type: commandType,
      execution_mode: 'manual',
      reason
    })
    await fetchControlDashboard()
  }

  async function toggleAutomationRule(ruleId, isEnabled) {
    await controlAPI.updateRule(ruleId, { is_enabled: isEnabled })
    await fetchControlDashboard()
  }

  async function createTask(payload) {
    let response
    try {
      response = await operationsAPI.createTask(payload)
    } catch (error) {
      if (String(error?.message || '').includes('timeout')) {
        try {
          await fetchOperationsDashboard()
          const matchedTask = operationsDashboard.tasks.find(task =>
            task.title === payload.title &&
            task.category === payload.category &&
            task.due_at === payload.due_at
          )
          if (matchedTask) {
            return matchedTask
          }
        } catch {
          // Keep original timeout error if verification refresh also fails.
        }
      }
      throw error
    }
    if (response.data.status !== 'success') throw new Error('创建生产任务失败')
    const createdTask = response.data.data
    operationsDashboard.tasks = [createdTask, ...operationsDashboard.tasks]
      .sort((a, b) => {
        const timeA = a?.due_at ? new Date(a.due_at).getTime() : Number.MAX_SAFE_INTEGER
        const timeB = b?.due_at ? new Date(b.due_at).getTime() : Number.MAX_SAFE_INTEGER
        return timeA - timeB
      })
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      task_count: (operationsDashboard.summary.task_count || 0) + 1,
      pending_tasks: (operationsDashboard.summary.pending_tasks || 0) + (createdTask.status === 'completed' ? 0 : 1)
    }
    persistCache()
    fetchOperationsDashboard().catch(error => {
      lastRefreshError.value = normalizeError(error, '任务创建成功，但任务面板刷新失败，请稍后手动刷新查看。')
    })
    return createdTask
  }

  async function updateTask(taskId, payload) {
    let response
    try {
      response = await operationsAPI.updateTask(taskId, payload)
    } catch (error) {
      if (String(error?.message || '').includes('timeout')) {
        try {
          await fetchOperationsDashboard()
          const refreshedTask = operationsDashboard.tasks.find(task => task.id === taskId)
          const matchedStatus = payload.status === undefined || refreshedTask?.status === payload.status
          if (refreshedTask && matchedStatus) {
            return refreshedTask
          }
        } catch {
          // keep original timeout below
        }
      }
      throw error
    }
    if (response.data.status !== 'success') throw new Error('更新今日任务失败')
    const updatedTask = response.data.data
    operationsDashboard.tasks = operationsDashboard.tasks.map(task =>
      task.id === taskId ? { ...task, ...updatedTask } : task
    )
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      pending_tasks: operationsDashboard.tasks.filter(task => task.status !== 'completed').length
    }
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return updatedTask
  }

  async function deleteTask(taskId) {
    if (!Array.isArray(operationsDashboard.today_tasks)) {
      operationsDashboard.today_tasks = []
    }
    const existingTask = operationsDashboard.tasks.find(task => task.id === taskId)
    const existingTodayTask = operationsDashboard.today_tasks.find(task => task.id === taskId)
    const response = await operationsAPI.deleteTask(taskId)
    if (response.data.status !== 'success') throw new Error('删除今日任务失败')
    operationsDashboard.tasks = operationsDashboard.tasks.filter(task => task.id !== taskId)
    operationsDashboard.today_tasks = operationsDashboard.today_tasks.filter(task => task.id !== taskId)
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      task_count: Math.max((operationsDashboard.summary.task_count || 1) - (existingTodayTask ? 1 : 0), 0),
      pending_tasks: Math.max(
        (operationsDashboard.summary.pending_tasks || 0) - (existingTask && existingTask.status !== 'completed' ? 1 : 0),
        0
      )
    }
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return response.data.data
  }

  async function updateTaskStatus(taskId, status) {
    const previousTask = operationsDashboard.tasks.find(task => task.id === taskId)
    if (previousTask) {
      operationsDashboard.tasks = operationsDashboard.tasks.map(task =>
        task.id === taskId
          ? {
              ...task,
              status,
              completed_at: status === 'completed' ? new Date().toISOString() : null
            }
          : task
      )
      operationsDashboard.summary = {
        ...operationsDashboard.summary,
        pending_tasks: operationsDashboard.tasks.filter(task => task.status !== 'completed').length
      }
      persistCache()
    }
    let response
    try {
      response = await operationsAPI.updateTaskStatus(taskId, { status })
    } catch (error) {
      if (String(error?.message || '').includes('timeout')) {
        try {
          await fetchOperationsDashboard()
          const refreshedTask = operationsDashboard.tasks.find(task => task.id === taskId)
          if (refreshedTask?.status === status) {
            return refreshedTask
          }
        } catch {
          // Keep original timeout error if verification refresh also fails.
        }
      }
      if (previousTask) {
        operationsDashboard.tasks = operationsDashboard.tasks.map(task =>
          task.id === taskId ? previousTask : task
        )
        operationsDashboard.summary = {
          ...operationsDashboard.summary,
          pending_tasks: operationsDashboard.tasks.filter(task => task.status !== 'completed').length
        }
        persistCache()
      }
      throw error
    }
    if (response.data.status !== 'success') throw new Error('更新任务状态失败')
    const updatedTask = response.data.data
    operationsDashboard.tasks = operationsDashboard.tasks.map(task =>
      task.id === taskId ? { ...task, ...updatedTask } : task
    )
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      pending_tasks: operationsDashboard.tasks.filter(task => task.status !== 'completed').length
    }
    persistCache()
    fetchOperationsDashboard().catch(error => {
      lastRefreshError.value = normalizeError(error, '任务状态已更新，但任务面板刷新失败，请稍后手动刷新查看。')
    })
    return updatedTask || previousTask
  }

  async function createDailyTask(payload) {
    const response = await operationsAPI.createDailyTask(payload)
    if (response.data.status !== 'success') throw new Error('创建每日任务失败')
    const createdTask = response.data.data
    if (!Array.isArray(operationsDashboard.today_tasks)) {
      operationsDashboard.today_tasks = []
    }
    operationsDashboard.daily_tasks = [createdTask, ...operationsDashboard.daily_tasks]
    if (createdTask.is_active !== false) {
      operationsDashboard.today_tasks = [
        {
          ...createdTask,
          id: `daily-${createdTask.id}`,
          source: 'daily',
          source_id: createdTask.id,
          is_template: true
        },
        ...operationsDashboard.today_tasks.filter(task => task.id !== `daily-${createdTask.id}`)
      ]
    }
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      daily_task_count: (operationsDashboard.summary.daily_task_count || 0) + 1,
      task_count: (operationsDashboard.summary.task_count || 0) + (createdTask.is_active === false ? 0 : 1),
      pending_tasks: (operationsDashboard.summary.pending_tasks || 0) + ((createdTask.is_active !== false && createdTask.status !== 'completed') ? 1 : 0)
    }
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return createdTask
  }

  async function updateDailyTask(taskId, payload) {
    if (!Array.isArray(operationsDashboard.today_tasks)) {
      operationsDashboard.today_tasks = []
    }
    const previousTask = operationsDashboard.daily_tasks.find(task => task.id === taskId)
    if (previousTask) {
      operationsDashboard.daily_tasks = operationsDashboard.daily_tasks.map(task =>
        task.id === taskId ? { ...task, ...payload } : task
      )
      const todayTaskId = `daily-${taskId}`
      if (operationsDashboard.today_tasks.some(task => task.id === todayTaskId)) {
        operationsDashboard.today_tasks = operationsDashboard.today_tasks.map(task =>
          task.id === todayTaskId ? { ...task, ...payload } : task
        )
      }
      persistCache()
    }
    let response
    try {
      response = await operationsAPI.updateDailyTask(taskId, payload)
    } catch (error) {
      if (String(error?.message || '').includes('timeout')) {
        try {
          await fetchOperationsDashboard()
          const refreshedTask = operationsDashboard.daily_tasks.find(task => task.id === taskId)
          const matchedActive = payload.is_active === undefined || refreshedTask?.is_active === payload.is_active
          if (refreshedTask && matchedActive) {
            return refreshedTask
          }
        } catch {
          // keep original timeout below
        }
      }
      if (previousTask) {
        operationsDashboard.daily_tasks = operationsDashboard.daily_tasks.map(task =>
          task.id === taskId ? previousTask : task
        )
        persistCache()
      }
      throw error
    }
    if (response.data.status !== 'success') throw new Error('更新每日任务失败')
    const updatedTask = response.data.data
    operationsDashboard.daily_tasks = operationsDashboard.daily_tasks.map(task =>
      task.id === taskId ? { ...task, ...updatedTask } : task
    )
    const todayTaskId = `daily-${taskId}`
    if (updatedTask.is_active === false) {
      operationsDashboard.today_tasks = operationsDashboard.today_tasks.filter(task => task.id !== todayTaskId)
    } else if (operationsDashboard.today_tasks.some(task => task.id === todayTaskId)) {
      operationsDashboard.today_tasks = operationsDashboard.today_tasks.map(task =>
        task.id === todayTaskId
          ? { ...task, ...updatedTask, id: todayTaskId, source: 'daily', source_id: taskId, is_template: true }
          : task
      )
    } else {
      operationsDashboard.today_tasks = [
        { ...updatedTask, id: todayTaskId, source: 'daily', source_id: taskId, is_template: true },
        ...operationsDashboard.today_tasks
      ]
    }
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return updatedTask
  }

  async function deleteDailyTask(taskId) {
    if (!Array.isArray(operationsDashboard.today_tasks)) {
      operationsDashboard.today_tasks = []
    }
    const existingTask = operationsDashboard.daily_tasks.find(task => task.id === taskId)
    const response = await operationsAPI.deleteDailyTask(taskId)
    if (response.data.status !== 'success') throw new Error('删除每日任务失败')
    operationsDashboard.daily_tasks = operationsDashboard.daily_tasks.filter(task => task.id !== taskId)
    operationsDashboard.today_tasks = operationsDashboard.today_tasks.filter(task => task.id !== `daily-${taskId}`)
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      daily_task_count: Math.max((operationsDashboard.summary.daily_task_count || 1) - 1, 0),
      task_count: Math.max((operationsDashboard.summary.task_count || 0) - (existingTask?.is_active ? 1 : 0), 0),
      pending_tasks: Math.max(
        (operationsDashboard.summary.pending_tasks || 0) - (existingTask?.is_active && existingTask?.status !== 'completed' ? 1 : 0),
        0
      )
    }
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return response.data.data
  }

  async function createInventoryItem(payload) {
    const response = await operationsAPI.createInventoryItem(payload)
    if (response.data.status !== 'success') throw new Error('新增库存物资失败')
    const createdItem = response.data.data
    operationsDashboard.inventory = [createdItem, ...operationsDashboard.inventory].sort((a, b) =>
      `${a.category}-${a.item_name}`.localeCompare(`${b.category}-${b.item_name}`, 'zh-CN')
    )
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      low_stock_items: operationsDashboard.inventory.filter(item => item.is_low_stock).length
    }
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return createdItem
  }

  async function updateInventoryItem(itemId, payload) {
    const response = await operationsAPI.updateInventoryItem(itemId, payload)
    if (response.data.status !== 'success') throw new Error('更新库存物资失败')
    const updatedItem = response.data.data
    operationsDashboard.inventory = operationsDashboard.inventory
      .map(item => (item.id === itemId ? { ...item, ...updatedItem } : item))
      .sort((a, b) => `${a.category}-${a.item_name}`.localeCompare(`${b.category}-${b.item_name}`, 'zh-CN'))
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      low_stock_items: operationsDashboard.inventory.filter(item => item.is_low_stock).length
    }
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return updatedItem
  }

  async function deleteInventoryItem(itemId) {
    const response = await operationsAPI.deleteInventoryItem(itemId)
    if (response.data.status !== 'success') throw new Error('删除库存物资失败')
    operationsDashboard.inventory = operationsDashboard.inventory.filter(item => item.id !== itemId)
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      low_stock_items: operationsDashboard.inventory.filter(item => item.is_low_stock).length
    }
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return response.data.data
  }

  async function createEquipmentAsset(payload) {
    const response = await operationsAPI.createEquipmentAsset(payload)
    if (response.data.status !== 'success') throw new Error('新增设备台账失败')
    const createdAsset = response.data.data
    operationsDashboard.assets = [createdAsset, ...operationsDashboard.assets].sort((a, b) =>
      `${a.zone_name || ''}-${a.asset_name}`.localeCompare(`${b.zone_name || ''}-${b.asset_name}`, 'zh-CN')
    )
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      asset_count: operationsDashboard.assets.length
    }
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return createdAsset
  }

  async function updateEquipmentAsset(assetId, payload) {
    const response = await operationsAPI.updateEquipmentAsset(assetId, payload)
    if (response.data.status !== 'success') throw new Error('更新设备台账失败')
    const updatedAsset = response.data.data
    operationsDashboard.assets = operationsDashboard.assets
      .map(asset => (asset.id === assetId ? { ...asset, ...updatedAsset } : asset))
      .sort((a, b) => `${a.zone_name || ''}-${a.asset_name}`.localeCompare(`${b.zone_name || ''}-${b.asset_name}`, 'zh-CN'))
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return updatedAsset
  }

  async function deleteEquipmentAsset(assetId) {
    const response = await operationsAPI.deleteEquipmentAsset(assetId)
    if (response.data.status !== 'success') throw new Error('删除设备台账失败')
    operationsDashboard.assets = operationsDashboard.assets.filter(asset => asset.id !== assetId)
    operationsDashboard.summary = {
      ...operationsDashboard.summary,
      asset_count: Math.max((operationsDashboard.summary.asset_count || 1) - 1, 0)
    }
    persistCache()
    fetchOperationsDashboard().catch(() => {})
    return response.data.data
  }

  async function updateUser(userId, payload) {
    let response
    try {
      response = await systemAPI.updateUser(userId, payload)
    } catch (error) {
      if (String(error?.message || '').includes('timeout')) {
        try {
          await fetchSystemDashboard()
          const refreshedUser = systemDashboard.users.find(user => user.id === userId)
          const matchedRole = payload.role === undefined || refreshedUser?.role === payload.role
          const matchedActive = payload.is_active === undefined || refreshedUser?.is_active === payload.is_active
          if (refreshedUser && matchedRole && matchedActive) {
            return refreshedUser
          }
        } catch {
          // Keep the original timeout error if the follow-up verification also fails.
        }
      }
      throw error
    }
    if (response.data.status !== 'success') throw new Error('更新用户信息失败')
    const previousUser = systemDashboard.users.find(user => user.id === userId)
    const updatedUser = response.data.data
    systemDashboard.users = systemDashboard.users.map(user =>
      user.id === userId ? { ...user, ...updatedUser } : user
    )
    systemDashboard.summary = {
      ...systemDashboard.summary,
      user_count: systemDashboard.users.length,
      active_users: systemDashboard.users.filter(user => user.is_active).length
    }
    const changes = []
    if (previousUser?.role !== updatedUser.role) {
      changes.push(`role: ${previousUser?.role ?? '--'} -> ${updatedUser.role}`)
    }
    if (previousUser?.is_active !== updatedUser.is_active) {
      changes.push(`is_active: ${previousUser?.is_active ?? '--'} -> ${updatedUser.is_active}`)
    }
    if (changes.length) {
      systemDashboard.operation_logs = [
        {
          id: `local-${Date.now()}-${userId}`,
          user_id: updatedUser.id,
          username: updatedUser.username,
          module_name: 'system',
          action: 'update_user',
          target: updatedUser.username,
          detail: changes.join('; '),
          created_at: new Date().toISOString()
        },
        ...systemDashboard.operation_logs
      ].slice(0, 12)
      systemDashboard.summary = {
        ...systemDashboard.summary,
        log_count: Math.max(systemDashboard.summary.log_count || 0, systemDashboard.operation_logs.length)
      }
      persistCache()
    }
    fetchSystemDashboard().catch(error => {
      lastRefreshError.value = normalizeError(error, '用户信息已更新，但系统面板刷新失败，请稍后手动刷新查看。')
    })
    return response.data.data
  }

  async function fetchUserLogs(userId, limit = 20) {
    const response = await systemAPI.getUserLogs(userId, limit)
    if (response.data.status !== 'success') throw new Error('查询用户操作日志失败')
    return response.data.data
  }

  async function createArchive(payload) {
    const response = await archiveAPI.createArchive(payload)
    if (response.data.status !== 'success') throw new Error('创建批次档案失败')
    const createdArchive = {
      ...response.data.data,
      animals: response.data.data.animals || []
    }
    archiveDashboard.archives = [createdArchive, ...archiveDashboard.archives]
    archiveDashboard.summary = {
      ...archiveDashboard.summary,
      archive_count: (archiveDashboard.summary.archive_count || 0) + 1,
      active_batches: (archiveDashboard.summary.active_batches || 0) + (createdArchive.is_active === false ? 0 : 1),
      total_quantity: (archiveDashboard.summary.total_quantity || 0) + (createdArchive.quantity || 0)
    }
    selectedArchiveId.value = createdArchive.id
    fetchArchiveDashboard().catch(error => {
      lastRefreshError.value = normalizeError(error, '批次档案已新增，但档案面板刷新失败，请稍后手动刷新查看。')
    })
    return response.data.data
  }

  async function updateArchive(archiveId, payload) {
    const response = await archiveAPI.updateArchive(archiveId, payload)
    if (response.data.status !== 'success') throw new Error('更新批次档案失败')
    archiveDashboard.archives = archiveDashboard.archives.map(item =>
      item.id === archiveId
        ? { ...item, ...response.data.data, animals: response.data.data.animals || item.animals || [] }
        : item
    )
    selectedArchiveId.value = archiveId
    fetchArchiveDashboard().catch(error => {
      lastRefreshError.value = normalizeError(error, '批次档案已更新，但档案面板刷新失败，请稍后手动刷新查看。')
    })
    return response.data.data
  }

  async function deleteArchive(archiveId) {
    const response = await archiveAPI.deleteArchive(archiveId)
    if (response.data.status !== 'success') throw new Error('删除批次档案失败')
    const removedArchive = archiveDashboard.archives.find(item => item.id === archiveId)
    archiveDashboard.archives = archiveDashboard.archives.filter(item => item.id !== archiveId)
    archiveDashboard.summary = {
      ...archiveDashboard.summary,
      archive_count: Math.max((archiveDashboard.summary.archive_count || 1) - 1, 0),
      active_batches: Math.max(
        (archiveDashboard.summary.active_batches || 0) - (removedArchive?.is_active === false ? 0 : 1),
        0
      ),
      total_quantity: Math.max((archiveDashboard.summary.total_quantity || 0) - (removedArchive?.quantity || 0), 0)
    }
    if (selectedArchiveId.value === archiveId) {
      selectedArchiveId.value = archiveDashboard.archives[0]?.id ?? null
    }
    fetchArchiveDashboard().catch(error => {
      lastRefreshError.value = normalizeError(error, '批次档案已删除，但档案面板刷新失败，请稍后手动刷新查看。')
    })
    return response.data.data
  }

  async function createAnimalProfile(payload) {
    const response = await archiveAPI.createAnimal(payload)
    if (response.data.status !== 'success') throw new Error('创建个体档案失败')
    const createdAnimal = {
      ...response.data.data,
      history_records: response.data.data.history_records || []
    }
    archiveDashboard.archives = archiveDashboard.archives.map(item => {
      if (item.id !== createdAnimal.archive_id) return item
      return {
        ...item,
        animals: [createdAnimal, ...(item.animals || [])]
      }
    })
    archiveDashboard.summary = {
      ...archiveDashboard.summary,
      individual_archive_count: (archiveDashboard.summary.individual_archive_count || 0) + 1
    }
    selectedArchiveId.value = createdAnimal.archive_id
    fetchArchiveDashboard().catch(error => {
      lastRefreshError.value = normalizeError(error, '个体档案已新增，但档案面板刷新失败，请稍后手动刷新查看。')
    })
    return response.data.data
  }

  async function updateAnimalProfile(animalId, payload) {
    const response = await archiveAPI.updateAnimal(animalId, payload)
    if (response.data.status !== 'success') throw new Error('更新个体档案失败')
    const updatedAnimal = {
      ...response.data.data,
      history_records: response.data.data.history_records || []
    }
    archiveDashboard.archives = archiveDashboard.archives.map(item => ({
      ...item,
      animals: (item.animals || []).map(animal => (animal.id === animalId ? updatedAnimal : animal))
    }))
    selectedArchiveId.value = updatedAnimal.archive_id
    fetchArchiveDashboard().catch(error => {
      lastRefreshError.value = normalizeError(error, '个体档案已更新，但档案面板刷新失败，请稍后手动刷新查看。')
    })
    return response.data.data
  }

  async function deleteAnimalProfile(animalId) {
    const response = await archiveAPI.deleteAnimal(animalId)
    if (response.data.status !== 'success') throw new Error('删除个体档案失败')
    let removed = false
    archiveDashboard.archives = archiveDashboard.archives.map(item => {
      const currentAnimals = item.animals || []
      const nextAnimals = currentAnimals.filter(animal => animal.id !== animalId)
      if (nextAnimals.length !== currentAnimals.length) removed = true
      return { ...item, animals: nextAnimals }
    })
    if (removed) {
      archiveDashboard.summary = {
        ...archiveDashboard.summary,
        individual_archive_count: Math.max((archiveDashboard.summary.individual_archive_count || 1) - 1, 0)
      }
    }
    fetchArchiveDashboard().catch(error => {
      lastRefreshError.value = normalizeError(error, '个体档案已删除，但档案面板刷新失败，请稍后手动刷新查看。')
    })
    return response.data.data
  }

  async function refreshHomeSummary() {
    await Promise.all([
      fetchOverview(),
      fetchAlarms(),
      fetchRiskDashboard(),
      fetchArchiveDashboard(),
      fetchOperationsDashboard(),
      fetchSystemDashboard()
    ])
  }

  async function refreshMonitoringModule() {
    await fetchOverview()
    await Promise.all([fetchLatestData(), fetchHistoricalData()])
  }

  async function refreshControlModule() {
    await Promise.all([fetchOverview(), fetchControlDashboard()])
  }

  async function refreshArchivesModule() {
    await fetchArchiveDashboard()
  }

  async function refreshAlarmsModule() {
    await Promise.all([fetchRiskDashboard(), fetchAlarms()])
  }

  async function refreshOperationsModule() {
    await Promise.all([fetchOperationsDashboard(), fetchArchiveDashboard()])
  }

  async function refreshSystemModule() {
    await fetchSystemDashboard()
  }

  const moduleLoaders = {
    home: refreshHomeSummary,
    monitoring: refreshMonitoringModule,
    control: refreshControlModule,
    archives: refreshArchivesModule,
    alarms: refreshAlarmsModule,
    operations: refreshOperationsModule,
    system: refreshSystemModule
  }

  async function loadModule(moduleKey, options = {}) {
    const loader = moduleLoaders[moduleKey]
    if (!loader) return

    activeModuleKey.value = moduleKey
    const requestVersion = moduleRequestVersion[moduleKey] + 1
    moduleRequestVersion[moduleKey] = requestVersion

    if (options.silent && moduleInFlight[moduleKey]) {
      return moduleInFlight[moduleKey]
    }

    const task = (async () => {
      try {
        if (!options.silent) loading.value = true
        if (!options.silent) {
          clearModuleError(moduleKey)
        }
        await loader()
      } catch (error) {
        if (moduleRequestVersion[moduleKey] === requestVersion && !options.silent) {
          setModuleError(moduleKey, error, '数据加载失败，当前页面已保留上一次成功内容。')
        }
      } finally {
        if (moduleRequestVersion[moduleKey] === requestVersion) {
          moduleInFlight[moduleKey] = null
          if (!options.silent && activeModuleKey.value === moduleKey) {
            loading.value = false
          }
        }
      }
    })()

    moduleInFlight[moduleKey] = task
    return task
  }

  return {
    selectedZone,
    selectedDeviceId,
    selectedHours,
    selectedArchiveId,
    overview,
    controlDashboard,
    archiveDashboard,
    riskDashboard,
    operationsDashboard,
    systemDashboard,
    latestData,
    historicalData,
    alarms,
    loading,
    ammoniaAlert,
    lastRefreshError,
    activeModuleKey,
    errorByModule,
    users,
    zoneOptions,
    currentZone,
    currentZoneDevices,
    currentDevice,
    currentMetrics,
    currentControlDevice,
    selectedArchive,
    homeCards,
    fetchOverview,
    fetchControlDashboard,
    fetchArchiveDashboard,
    fetchRiskDashboard,
    fetchOperationsDashboard,
    fetchSystemDashboard,
    fetchLatestData,
    fetchHistoricalData,
    fetchAlarms,
    acknowledgeAlarm,
    resolveAlarm,
    executeControlCommand,
    toggleAutomationRule,
    createTask,
    updateTaskStatus,
    updateTask,
    deleteTask,
    createDailyTask,
    updateDailyTask,
    deleteDailyTask,
    createInventoryItem,
    updateInventoryItem,
    deleteInventoryItem,
    createEquipmentAsset,
    updateEquipmentAsset,
    deleteEquipmentAsset,
    updateUser,
    fetchUserLogs,
    createArchive,
    updateArchive,
    deleteArchive,
    createAnimalProfile,
    updateAnimalProfile,
    deleteAnimalProfile,
    loadModule
  }
})

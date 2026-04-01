<template>
  <section class="toolbar-card">
    <div class="toolbar-field">
      <label>监测区域</label>
      <select :value="selectedZone" @change="$emit('update:zone', $event.target.value)">
        <option v-for="zone in zoneOptions" :key="zone.zone_name" :value="zone.zone_name">
          {{ zone.zone_name }}（{{ zone.device_count }} 台设备）
        </option>
      </select>
    </div>

    <div class="toolbar-field">
      <label>监测设备</label>
      <select :value="selectedDeviceId" @change="$emit('update:device', $event.target.value)">
        <option v-for="device in devices" :key="device.device_id" :value="device.device_id">
          {{ device.device_name }} / {{ device.device_id }}
        </option>
      </select>
    </div>

    <div v-if="showHours" class="toolbar-field">
      <label>趋势时长</label>
      <select :value="selectedHours" @change="$emit('update:hours', Number($event.target.value))">
        <option :value="6">近 6 小时</option>
        <option :value="12">近 12 小时</option>
        <option :value="24">近 24 小时</option>
        <option :value="48">近 48 小时</option>
      </select>
    </div>
  </section>
</template>

<script setup>
defineProps({
  zoneOptions: { type: Array, default: () => [] },
  devices: { type: Array, default: () => [] },
  selectedZone: { type: String, default: '' },
  selectedDeviceId: { type: String, default: '' },
  selectedHours: { type: Number, default: 24 },
  showHours: { type: Boolean, default: false }
})

defineEmits(['update:zone', 'update:device', 'update:hours'])
</script>

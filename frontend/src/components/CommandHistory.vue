<template>
  <section class="history-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">Command History</p>
        <h2>近期控制记录</h2>
      </div>
      <span class="history-count">{{ commands.length }}</span>
    </div>

    <div v-if="commands.length === 0" class="empty-state">暂无控制记录。</div>

    <template v-else>
      <div class="history-list">
        <article v-for="command in pagedCommands" :key="command.id" class="history-card">
          <div class="history-top">
            <strong>{{ command.device_name || command.device_id }}</strong>
            <div class="status-group">
              <span class="mode">{{ command.execution_mode === 'auto' ? '自动' : '手动' }}</span>
              <span :class="['status-chip', mapStatusTone(command.status)]">
                {{ formatLocalStatus(command.status) }}
              </span>
            </div>
          </div>

          <p class="command-main">{{ formatTarget(command.target_component) }} / {{ formatCommand(command.command_type) }}</p>
          <small>{{ command.reason || '无说明' }}</small>

          <div class="meta-row">
            <span v-if="command.ctwing_command_status" class="platform-chip">
              平台：{{ command.ctwing_command_status }}
            </span>
            <span v-if="command.ctwing_command_id" class="platform-chip">
              ID {{ command.ctwing_command_id }}
            </span>
          </div>

          <time>{{ formatTime(command.executed_at) }}</time>
        </article>
      </div>

      <div class="pagination-bar">
        <button class="ghost-btn" type="button" :disabled="page === 1" @click="page -= 1">上一页</button>
        <span>第 {{ page }} / {{ totalPages }} 页</span>
        <button class="ghost-btn" type="button" :disabled="page >= totalPages" @click="page += 1">下一页</button>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  commands: { type: Array, default: () => [] }
})

const page = ref(1)
const pageSize = 6

const totalPages = computed(() => Math.max(1, Math.ceil(props.commands.length / pageSize)))
const pagedCommands = computed(() => {
  const start = (page.value - 1) * pageSize
  return props.commands.slice(start, start + pageSize)
})

watch(
  () => props.commands,
  () => {
    if (page.value > totalPages.value) {
      page.value = totalPages.value
    }
  },
  { deep: true }
)

const targetLabelMap = {
  fan: '风机',
  cooling_pad: '水帘',
  fill_light: '补光灯'
}

function formatTarget(target) {
  return targetLabelMap[target] || target || '--'
}

function formatCommand(commandType) {
  if (commandType === 'ON') return '开启'
  if (commandType === 'OFF') return '关闭'
  return commandType || '--'
}

function formatLocalStatus(status) {
  if (status === 'sent') return '已送达'
  if (status === 'success') return '已执行'
  if (status === 'failed') return '失败'
  return '已保存'
}

function mapStatusTone(status) {
  if (status === 'failed') return 'failed'
  if (status === 'sent' || status === 'success') return 'success'
  return 'pending'
}

function formatTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}
</script>

<style scoped lang="scss">
.history-panel{display:flex;flex-direction:column;gap:14px}
.panel-header{display:flex;justify-content:space-between;gap:12px}
.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}
h2{margin:0;color:#f3f7fa;font-size:22px}
.history-count{align-self:flex-start;padding:6px 12px;border-radius:999px;background:rgba(95,211,188,.12);color:#bfece3}
.history-list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.history-card,.empty-state{padding:14px;border-radius:16px;background:rgba(10,33,39,.88);border:1px solid rgba(164,215,210,.1)}
.history-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}
.status-group{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.mode{color:#ffe2a4}
.status-chip,.platform-chip{padding:5px 10px;border-radius:999px;font-size:13px}
.status-chip.pending{background:rgba(255,200,87,.12);color:#ffe2a4}
.status-chip.success{background:rgba(95,211,188,.12);color:#bfece3}
.status-chip.failed{background:rgba(255,120,120,.12);color:#ffc2c2}
.platform-chip{background:rgba(17,56,63,.9);color:#d7e7ea}
.command-main{font-size:16px;font-weight:600;color:#f2f7f9}
.history-card p,.history-card small,.history-card time{display:block;margin-top:8px;color:#97afb4}
.meta-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.pagination-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 12px;border-radius:14px;background:rgba(8,27,32,.72);color:#98b0b5}
.ghost-btn{height:36px;padding:0 14px;border-radius:10px;border:1px solid rgba(164,215,210,.22);background:transparent;color:#d7e8eb;cursor:pointer}
.ghost-btn:disabled{opacity:.6;cursor:not-allowed}
@media (max-width:1000px){
  .history-list{grid-template-columns:1fr}
}
</style>

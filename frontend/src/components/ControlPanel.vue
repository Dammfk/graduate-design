<template>
  <section class="control-panel">
    <div class="panel-header">
      <div>
        <p class="eyebrow">Device Control</p>
        <h2>{{ device?.device_name || '设备控制面板' }}</h2>
      </div>
      <span class="zone-badge">{{ device?.zone_name || '未选择区域' }}</span>
    </div>

    <div v-if="!device" class="empty-state">请先选择设备，再查看当前状态和控制信息。</div>

    <template v-else>
      <div v-if="feedbackSummary" :class="['feedback-banner', feedbackSummary.tone]">
        <strong>{{ feedbackSummary.title }}</strong>
        <span>{{ feedbackSummary.message }}</span>
      </div>

      <div class="context-hints">
        <article class="context-hint">
          <span>设备活跃状态</span>
          <strong :class="deviceActivity.tone">{{ deviceActivity.label }}</strong>
          <small>{{ deviceActivity.hint }}</small>
        </article>
        <article class="context-hint">
          <span>平台投递提示</span>
          <strong>{{ deliveryHint.title }}</strong>
          <small>{{ deliveryHint.message }}</small>
        </article>
      </div>

      <div class="control-grid">
        <div class="snapshot-card">
          <h3>环境快照</h3>
          <div class="env-snapshot compact">
            <div>
              <span>温度</span>
              <strong>{{ formatValue(device.latest_environment?.temperature, '°C', 1) }}</strong>
            </div>
            <div>
              <span>湿度</span>
              <strong>{{ formatValue(device.latest_environment?.humidity, '%', 1) }}</strong>
            </div>
            <div>
              <span>CO2</span>
              <strong>{{ formatValue(device.latest_environment?.co2_concentration, 'ppm', 0) }}</strong>
            </div>
            <div>
              <span>氨气</span>
              <strong>{{ formatValue(device.latest_environment?.ammonia_concentration, 'ppm', 1) }}</strong>
            </div>
          </div>
        </div>

        <div class="action-card">
          <div class="section-title">
            <h3>设备组件</h3>
            <small>把设备当前状态和最近命令状态分开看，再结合流程时间线判断命令卡在哪一步。</small>
          </div>

          <div class="component-list">
            <article v-for="component in device.components" :key="component.component_key" class="component-card">
              <div class="component-info">
                <div class="component-heading">
                  <strong>{{ component.component_name }}</strong>
                  <span :class="['component-chip', component.mode === 'auto' ? 'auto' : 'manual']">
                    {{ component.mode === 'auto' ? '自动联动' : '手动优先' }}
                  </span>
                </div>

                <div class="status-stack">
                  <div class="status-row">
                    <span class="status-label">当前设备状态</span>
                    <span :class="['status-pill', component.status === 'ON' ? 'on' : 'off']">
                      {{ component.status === 'ON' ? '运行中' : '已关闭' }}
                    </span>
                  </div>

                  <div class="status-row">
                    <span class="status-label">最近命令状态</span>
                    <span :class="['status-pill', mapStatusTone(component.last_command_status)]">
                      {{ formatRecentCommandStatus(component) }}
                    </span>
                  </div>
                </div>

                <small v-if="feedbackFor(component)" class="command-hint">
                  最近命令：{{ describeFeedback(feedbackFor(component)) }}
                </small>

                <div class="timeline">
                  <div
                    v-for="step in commandTimeline(component)"
                    :key="`${component.component_key}-${step.key}`"
                    class="timeline-step"
                    :class="step.state"
                  >
                    <span class="timeline-dot"></span>
                    <strong>{{ step.label }}</strong>
                  </div>
                </div>
              </div>

              <div class="component-actions">
                <button
                  class="ghost-btn"
                  :disabled="isBusy(component.component_key)"
                  @click="$emit('command', component.component_key, 'OFF', `手动关闭${component.component_name}`)"
                >
                  {{ isBusy(component.component_key) ? '发送中...' : '关闭' }}
                </button>
                <button
                  class="primary-btn"
                  :disabled="isBusy(component.component_key)"
                  @click="$emit('command', component.component_key, 'ON', `手动开启${component.component_name}`)"
                >
                  {{ isBusy(component.component_key) ? '发送中...' : '开启' }}
                </button>
              </div>
            </article>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  device: { type: Object, default: null },
  busyMap: { type: Object, default: () => ({}) },
  lastFeedback: { type: Object, default: null }
})

defineEmits(['command'])

const componentNameMap = {
  fan: '风机',
  cooling_pad: '水帘',
  fill_light: '补光灯'
}

const feedbackSummary = computed(() => {
  if (!props.lastFeedback) return null

  const targetLabel =
    componentNameMap[props.lastFeedback.target_component] ||
    props.lastFeedback.target_component ||
    '设备'

  if (props.lastFeedback.error_message) {
    return {
      tone: 'failed',
      title: `${targetLabel}命令发送失败`,
      message: props.lastFeedback.error_message
    }
  }

  const ctwingStatus = props.lastFeedback.ctwing_command_status
  const status = props.lastFeedback.status
  const commandType = props.lastFeedback.command_type === 'ON' ? '开启' : '关闭'

  if (ctwingStatus) {
    return {
      tone: mapStatusTone(status),
      title: `${targetLabel}${commandType}命令已提交`,
      message: `平台状态：${ctwingStatus}${props.lastFeedback.ctwing_command_id ? ` · 命令 ID ${props.lastFeedback.ctwing_command_id}` : ''}`
    }
  }

  return {
    tone: mapStatusTone(status),
    title: `${targetLabel}${commandType}命令已提交`,
    message: `当前跟踪状态：${formatLocalStatus(status)}`
  }
})

const deviceActivity = computed(() => {
  const recordedAt = props.device?.latest_environment?.recorded_at
  if (!recordedAt) {
    return {
      tone: 'pending',
      label: '暂未确认',
      hint: '还没有拿到最近上报时间，平台下行可能会更慢。'
    }
  }

  const seconds = Math.max(0, Math.round((Date.now() - new Date(recordedAt).getTime()) / 1000))
  if (seconds <= 45) {
    return {
      tone: 'success',
      label: '活跃',
      hint: `最近 ${seconds} 秒内有上报，下行命令通常更容易及时投递。`
    }
  }

  if (seconds <= 180) {
    return {
      tone: 'pending',
      label: '一般',
      hint: `最近一次上报距今约 ${seconds} 秒，命令可能会先停留在“已保存”。`
    }
  }

  return {
    tone: 'failed',
    label: '偏低',
    hint: `最近一次上报距今约 ${seconds} 秒，建议先保持上报开启再下发命令。`
  }
})

const deliveryHint = computed(() => {
  const feedback = props.lastFeedback
  if (!feedback) {
    return {
      title: '等待新命令',
      message: '新命令提交后，会依次经历已提交、已保存、已送达和已执行。'
    }
  }

  if (feedback.error_message) {
    return {
      title: '提交失败',
      message: '这次命令没有成功提交到平台，请根据错误提示重试。'
    }
  }

  if (feedback.status === 'success') {
    return {
      title: '已执行',
      message: '设备 ACK 已回传，当前动作已经被硬件侧确认执行。'
    }
  }

  if (feedback.status === 'sent') {
    return {
      title: '等待 ACK',
      message: '平台侧已经送达，正在等待设备执行并回传 ACK。'
    }
  }

  return {
    title: '平台处理中',
    message: '如果设备活跃度较低，命令可能会先保存，稍后再投递。'
  }
})

function formatValue(value, unit, precision) {
  if (value === null || value === undefined) return `-- ${unit}`
  return `${Number(value).toFixed(precision)} ${unit}`
}

function isBusy(componentKey) {
  return Boolean(props.busyMap?.[componentKey])
}

function feedbackFor(component) {
  if (!props.lastFeedback) return null
  return props.lastFeedback.target_component === component.component_key ? props.lastFeedback : null
}

function mapStatusTone(status) {
  if (status === 'failed') return 'failed'
  if (status === 'sent' || status === 'success') return 'success'
  return 'pending'
}

function formatLocalStatus(status) {
  if (status === 'sent') return '已送达'
  if (status === 'success') return '已执行'
  if (status === 'failed') return '失败'
  return '已保存'
}

function formatRecentCommandStatus(component) {
  const status = component?.last_command_status
  if (!status || status === 'idle') return '暂无新命令'
  if (status === 'pending') return '已保存，等待投递'
  return formatLocalStatus(status)
}

function describeFeedback(feedback) {
  if (!feedback) return ''
  if (feedback.error_message) return `失败 · ${feedback.error_message}`
  if (feedback.ctwing_command_status) return `${feedback.command_type} · ${feedback.ctwing_command_status}`
  return `${feedback.command_type} · ${formatLocalStatus(feedback.status)}`
}

function commandTimeline(component) {
  const feedback = feedbackFor(component)
  const status = feedback?.status || component?.last_command_status || 'idle'
  const ctwingStatus = String(feedback?.ctwing_command_status || '')
  const failed = status === 'failed' || Boolean(feedback?.error_message)
  const submitted = status !== 'idle'
  const saved = submitted
  const delivered = status === 'sent' || status === 'success' || ctwingStatus.includes('送达')
  const executed = status === 'success'

  return [
    { key: 'submitted', label: '已提交', state: submitted ? 'done' : 'idle' },
    { key: 'saved', label: '已保存', state: failed ? 'failed' : saved ? 'done' : 'idle' },
    { key: 'delivered', label: '已送达', state: failed ? 'failed' : delivered ? 'done' : 'idle' },
    { key: 'executed', label: '已执行', state: failed ? 'failed' : executed ? 'done' : 'idle' }
  ]
}
</script>

<style scoped lang="scss">
.control-panel{display:flex;flex-direction:column;gap:14px}
.panel-header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
.eyebrow{margin:0 0 6px;color:#87a5ac;font-size:12px;letter-spacing:.2em;text-transform:uppercase}
h2,h3{margin:0;color:#f3f7fa}
.zone-badge{align-self:flex-start;padding:6px 12px;border-radius:999px;background:rgba(95,211,188,.12);color:#bfece3}
.empty-state{padding:22px;border-radius:16px;background:rgba(10,33,39,.8);color:#95abb0}
.feedback-banner{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px;border-radius:14px;border:1px solid rgba(255,255,255,.08)}
.feedback-banner strong{font-size:16px;color:#f5fbfc}
.feedback-banner span{color:#d0e1e4;font-size:15px}
.feedback-banner.pending{background:rgba(255,200,87,.12);border-color:rgba(255,200,87,.25)}
.feedback-banner.success{background:rgba(95,211,188,.12);border-color:rgba(95,211,188,.24)}
.feedback-banner.failed{background:rgba(255,120,120,.12);border-color:rgba(255,120,120,.24)}
.context-hints{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.context-hint{padding:14px;border-radius:16px;background:rgba(10,33,39,.88);border:1px solid rgba(164,215,210,.1)}
.context-hint span{display:block;color:#87a5ac;font-size:13px;margin-bottom:6px}
.context-hint strong{display:block;font-size:18px;color:#f3f7fa}
.context-hint strong.success{color:#bfece3}
.context-hint strong.pending{color:#ffe2a4}
.context-hint strong.failed{color:#ffc2c2}
.context-hint small{display:block;margin-top:6px;color:#97afb4;line-height:1.5}
.control-grid{display:grid;grid-template-columns:240px minmax(0,1fr);gap:12px}
.snapshot-card,.action-card,.component-card{padding:14px;border-radius:16px;background:rgba(10,33,39,.88);border:1px solid rgba(164,215,210,.1)}
.section-title{display:grid;gap:4px;margin-bottom:10px}
.section-title small{color:#8ea9af;font-size:14px;line-height:1.5}
.env-snapshot{display:grid;gap:10px}
.env-snapshot.compact{grid-template-columns:repeat(2,minmax(0,1fr))}
.env-snapshot span{display:block;color:#87a5ac;font-size:13px;margin-bottom:6px}
.env-snapshot strong{font-size:19px}
.component-list{display:grid;gap:10px}
.component-card{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:14px;align-items:center}
.component-heading{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.component-chip{padding:5px 10px;border-radius:999px;font-size:13px}
.component-chip.auto{background:rgba(255,200,87,.12);color:#ffe2a4}
.component-chip.manual{background:rgba(95,211,188,.12);color:#bfece3}
.status-stack{display:grid;gap:8px;margin-top:10px}
.status-row{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.status-label{color:#97afb4;font-size:14px}
.status-pill{display:inline-flex;align-items:center;justify-content:center;min-height:32px;padding:0 12px;border-radius:999px;font-size:14px}
.status-pill.on,.status-pill.success{background:rgba(95,211,188,.12);color:#bfece3}
.status-pill.off{background:rgba(164,215,210,.08);color:#d1dee1}
.status-pill.pending{background:rgba(255,200,87,.12);color:#ffe2a4}
.status-pill.failed{background:rgba(255,120,120,.12);color:#ffc2c2}
.command-hint{display:block;margin-top:10px;font-size:14px;line-height:1.5;color:#97afb4}
.timeline{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:12px}
.timeline-step{display:grid;justify-items:center;gap:6px;padding:10px 8px;border-radius:12px;background:rgba(12,43,49,.5);border:1px solid rgba(164,215,210,.08)}
.timeline-step strong{font-size:13px;color:#87a5ac}
.timeline-step.done{background:rgba(95,211,188,.1);border-color:rgba(95,211,188,.22)}
.timeline-step.done strong{color:#d7f6ef}
.timeline-step.failed{background:rgba(255,120,120,.1);border-color:rgba(255,120,120,.22)}
.timeline-step.failed strong{color:#ffd3d3}
.timeline-dot{width:10px;height:10px;border-radius:999px;background:rgba(164,215,210,.24)}
.timeline-step.done .timeline-dot{background:#5fd3bc}
.timeline-step.failed .timeline-dot{background:#ff857f}
.component-actions{display:flex;gap:8px}
.ghost-btn,.primary-btn{height:38px;min-width:76px;border-radius:10px;cursor:pointer;font-size:15px}
.ghost-btn{border:1px solid rgba(164,215,210,.22);background:transparent;color:#d7e8eb}
.primary-btn{border:none;background:linear-gradient(135deg,#4fa98f,#2f7f6d);color:#fff}
.ghost-btn:disabled,.primary-btn:disabled{opacity:.65;cursor:not-allowed}
@media (max-width:900px){
  .context-hints{grid-template-columns:1fr}
  .control-grid{grid-template-columns:1fr}
  .component-card{grid-template-columns:1fr}
  .feedback-banner{flex-direction:column;align-items:flex-start}
  .timeline{grid-template-columns:repeat(2,minmax(0,1fr))}
}
</style>

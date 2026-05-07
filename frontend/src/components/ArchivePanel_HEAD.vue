<template>
  <section class="archive-panel">
    <div v-if="feedback.message" class="feedback" :class="feedback.type">
      {{ feedback.message }}
    </div>

    <div class="summary-grid">
      <div><span>批次档案</span><strong>{{ summary.archive_count || 0 }}</strong></div>
      <div><span>活跃批次</span><strong>{{ summary.active_batches || 0 }}</strong></div>
      <div><span>当前存栏</span><strong>{{ summary.total_quantity || 0 }}</strong></div>
      <div><span>个体档案</span><strong>{{ summary.individual_archive_count || 0 }}</strong></div>
    </div>

    <div class="archive-workbench">
      <aside class="workbench-column batch-column">
        <div class="column-header">
          <div>
            <p class="column-label">Batch List</p>
            <h3>批次列表</h3>
          </div>
          <div class="column-actions">
            <span class="column-count">{{ visibleArchives.length }}</span>
            <button class="primary-btn" type="button" @click="showArchiveModal = true">新增批次档案</button>
          </div>
        </div>

        <div class="archive-list">
          <button
            v-for="archive in pagedArchives"
            :key="archive.id"
            class="archive-card"
            :class="{ active: archive.id === selectedArchiveId }"
            @click="emit('select', archive.id)"
          >
            <div class="archive-top">
              <strong>{{ archive.batch_number }}</strong>
              <span class="health-tag" :class="archive.health_status">{{ formatHealth(archive.health_status) }}</span>
            </div>
            <p>{{ archive.species }} / {{ archive.quantity }} 头</p>
            <small>入栏时间：{{ formatDate(archive.check_in_date) }}</small>
          </button>
        </div>
        <div class="pagination-bar">
          <button class="ghost-btn" type="button" :disabled="archivePage === 1" @click="archivePage -= 1">上一页</button>
          <span>第 {{ archivePage }} / {{ totalArchivePages }} 页</span>
          <button class="ghost-btn" type="button" :disabled="archivePage >= totalArchivePages" @click="archivePage += 1">下一页</button>
        </div>
      </aside>

      <section class="workbench-column animal-column">
        <div class="column-header">
          <div>
            <p class="column-label">Animal List</p>
            <h3>个体列表</h3>
          </div>
          <span class="column-count">{{ filteredAnimals.length }}</span>
        </div>

        <div class="search-field animal-search">
          <input v-model.trim="animalKeyword" placeholder="编号查询：输入个体编号或耳标号" />
        </div>

        <div v-if="selectedArchive" class="animal-selector-panel">
          <div v-if="filteredAnimals.length" class="animal-selector-list">
            <button
              v-for="animal in pagedAnimals"
              :key="animal.id"
              class="animal-selector-card"
              :class="{ active: animal.id === selectedAnimalId }"
              @click="selectedAnimalId = animal.id"
            >
              <div class="animal-top">
                <strong>{{ animal.animal_code }}</strong>
                <span class="health-tag" :class="animal.health_status">{{ formatHealth(animal.health_status) }}</span>
              </div>
              <p>{{ animal.species }} / {{ animal.breed || '未录入品种' }}</p>
              <small>耳标：{{ animal.ear_tag || '--' }}</small>
            </button>
          </div>
          <div v-else class="empty-state">
            当前筛选条件下没有找到个体档案。
          </div>

          <div class="pagination-bar">
            <button class="ghost-btn" type="button" :disabled="animalPage === 1" @click="animalPage -= 1">上一页</button>
            <span>第 {{ animalPage }} / {{ totalAnimalPages }} 页</span>
            <button class="ghost-btn" type="button" :disabled="animalPage >= totalAnimalPages" @click="animalPage += 1">下一页</button>
          </div>
        </div>
        <div v-else class="empty-state">
          请先从左侧选择一个批次。
        </div>
      </section>

      <section class="workbench-column detail-column">
        <div v-if="selectedArchive" class="detail-scroll">
          <div class="records-box">
            <div class="detail-header">
              <h3>批次信息</h3>
              <div class="inline-actions">
                <button class="ghost-btn" :disabled="submitting.archiveEdit" @click="submitArchiveEdit">
                  {{ submitting.archiveEdit ? '保存中...' : '保存批次修改' }}
                </button>
                <button class="danger-btn" :disabled="submitting.archiveDelete" @click="removeArchive">
                  {{ submitting.archiveDelete ? '删除中...' : '删除批次档案' }}
                </button>
              </div>
            </div>

            <div class="form-grid">
              <input v-model="archiveForm.batch_number" placeholder="批次编号" />
              <input v-model="archiveForm.species" placeholder="养殖品类" />
              <input v-model.number="archiveForm.quantity" type="number" min="1" placeholder="数量" />
              <select v-model="archiveForm.health_status">
                <option value="good">良好</option>
                <option value="stable">稳定</option>
                <option value="observe">观察</option>
              </select>
              <input v-model.number="archiveForm.average_weight" type="number" min="0" step="0.1" placeholder="平均体重(kg)" />
              <input v-model.number="archiveForm.feed_consumption" type="number" min="0" step="0.1" placeholder="累计饲料(kg)" />
              <input v-model="archiveForm.expected_checkout_date" type="datetime-local" />
              <input v-model="archiveForm.notes" placeholder="批次备注" />
            </div>
          </div>

          <div class="records-box">
            <div class="detail-header">
              <h3>个体详情</h3>
              <div class="inline-actions">
                <button class="primary-btn" type="button" @click="showAnimalModal = true">新增个体档案</button>
              </div>
            </div>

            <div v-if="selectedAnimal" class="animal-editor">
              <div class="animal-meta">
                <strong>{{ selectedAnimal.animal_code }}</strong>
                <span>最后更新时间：{{ formatDateTime(selectedAnimal.updated_at) }}</span>
              </div>

              <div class="animal-form-grid">
                <input v-model="selectedAnimalForm.animal_code" placeholder="个体编号" />
                <input v-model="selectedAnimalForm.species" placeholder="物种" />
                <input v-model="selectedAnimalForm.breed" placeholder="品种" />
                <input v-model="selectedAnimalForm.gender" placeholder="性别" />
                <input v-model="selectedAnimalForm.ear_tag" placeholder="耳标号" />
                <input v-model.number="selectedAnimalForm.weight" type="number" min="0" step="0.1" placeholder="体重(kg)" />
                <input v-model="selectedAnimalForm.check_in_date" type="datetime-local" placeholder="入栏时间" />
                <input v-model="selectedAnimalForm.source" placeholder="来源地" />
                <select v-model="selectedAnimalForm.health_status">
                  <option value="good">良好</option>
                  <option value="stable">稳定</option>
                  <option value="observe">观察</option>
                </select>
                <input v-model="selectedAnimalForm.immunization_note" placeholder="免疫记录" />
                <input v-model="selectedAnimalForm.notes" placeholder="个体备注" />
              </div>

              <div class="inline-actions">
                <button class="ghost-btn" :disabled="busyAnimalId === selectedAnimal.id" @click="submitAnimalEdit">
                  {{ busyAnimalId === selectedAnimal.id ? '保存中...' : '保存个体修改' }}
                </button>
                <button class="ghost-btn" type="button" @click="toggleHistory">
                  {{ historyExpanded ? '收起更新记录' : '查看更新记录' }}
                </button>
                <button class="danger-btn" :disabled="busyAnimalId === selectedAnimal.id" @click="removeAnimal">
                  {{ busyAnimalId === selectedAnimal.id ? '删除中...' : '删除个体档案' }}
                </button>
              </div>

              <div v-if="historyExpanded" class="history-box">
                <h4>耳标 / 体重更新记录</h4>
                <div v-if="selectedAnimal.history_records?.length" class="history-list">
                  <div v-for="record in selectedAnimal.history_records" :key="record.id" class="history-item">
                    <strong>{{ historyFieldLabel(record.field_name) }}</strong>
                    <span>{{ record.old_value || '--' }} -> {{ record.new_value || '--' }}</span>
                    <small>{{ formatDateTime(record.changed_at) }}</small>
                  </div>
                </div>
                <p v-else>暂无耳标号或体重的历史更新记录。</p>
              </div>
            </div>
            <div v-else class="empty-state">
              当前批次下暂无可编辑的个体档案。
            </div>
          </div>
        </div>
        <div v-else class="empty-state detail-empty">
          请先选择批次，右侧将显示批次信息和个体详情。
        </div>
      </section>
    </div>

    <div v-if="showArchiveModal" class="modal-mask" @click.self="showArchiveModal = false">
      <div class="modal-card">
        <div class="detail-header">
          <h3>新增批次档案</h3>
          <button class="ghost-btn" type="button" @click="showArchiveModal = false">取消</button>
        </div>
        <div class="form-grid">
          <input v-model="newArchive.batch_number" placeholder="批次编号，如 BATCH-CATTLE-004" />
          <input v-model="newArchive.species" placeholder="养殖品类，如 肉牛 / 奶牛 / 肉羊" />
          <input v-model.number="newArchive.quantity" type="number" min="1" placeholder="数量" />
          <input v-model="newArchive.check_in_date" type="datetime-local" />
        </div>
        <div class="inline-actions">
          <button class="primary-btn" :disabled="submitting.archive" @click="submitArchive">
            {{ submitting.archive ? '提交中...' : '确认新增' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showAnimalModal" class="modal-mask" @click.self="showAnimalModal = false">
      <div class="modal-card">
        <div class="detail-header">
          <h3>新增个体档案</h3>
          <button class="ghost-btn" type="button" @click="showAnimalModal = false">取消</button>
        </div>
        <div class="form-grid">
          <input v-model="newAnimal.animal_code" placeholder="个体编号，如 CATTLE-010" />
          <input v-model="newAnimal.species" placeholder="物种，如 肉牛 / 肉羊" />
          <input v-model="newAnimal.breed" placeholder="品种" />
          <input v-model="newAnimal.gender" placeholder="性别" />
          <input v-model="newAnimal.ear_tag" placeholder="耳标号" />
          <input v-model.number="newAnimal.weight" type="number" min="0" step="0.1" placeholder="体重(kg)" />
          <input v-model="newAnimal.check_in_date" type="datetime-local" />
          <input v-model="newAnimal.source" placeholder="来源地" />
        </div>
        <div class="inline-actions">
          <button class="primary-btn" :disabled="submitting.animal" @click="submitAnimal">
            {{ submitting.animal ? '提交中...' : '确认新增' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  summary: { type: Object, default: () => ({}) },
  archives: { type: Array, default: () => [] },
  selectedArchiveId: { type: Number, default: null },
  selectedArchive: { type: Object, default: null },
  onCreateArchive: { type: Function, required: true },
  onUpdateArchive: { type: Function, required: true },
  onDeleteArchive: { type: Function, required: true },
  onCreateAnimal: { type: Function, required: true },
  onUpdateAnimal: { type: Function, required: true },
  onDeleteAnimal: { type: Function, required: true }
})

const emit = defineEmits(['select'])

const newArchive = reactive({ batch_number: '', species: '', quantity: 1, check_in_date: '' })
const newAnimal = reactive({ animal_code: '', species: '', breed: '', gender: '', ear_tag: '', weight: null, check_in_date: '', source: '' })
const archiveForm = reactive({
  batch_number: '',
  species: '',
  quantity: 1,
  health_status: 'stable',
  average_weight: null,
  feed_consumption: null,
  expected_checkout_date: '',
  notes: ''
})
const selectedAnimalForm = reactive({
  animal_code: '',
  species: '',
  breed: '',
  gender: '',
  ear_tag: '',
  weight: null,
  check_in_date: '',
  source: '',
  health_status: 'stable',
  immunization_note: '',
  notes: ''
})

const selectedAnimalId = ref(null)
const historyExpanded = ref(false)
const showArchiveModal = ref(false)
const showAnimalModal = ref(false)
const archivePage = ref(1)
const animalKeyword = ref('')
const animalPage = ref(1)
const pageSize = 7
const submitting = reactive({ archive: false, archiveEdit: false, archiveDelete: false, animal: false })
const busyAnimalId = ref(null)
const feedback = reactive({ type: '', message: '' })

const healthMap = { stable: '稳定', good: '良好', observe: '观察' }

const visibleArchives = computed(() => props.archives.filter((archive) => archive.is_active !== false))
const totalArchivePages = computed(() => Math.max(1, Math.ceil(visibleArchives.value.length / pageSize)))
const pagedArchives = computed(() => {
  const start = (archivePage.value - 1) * pageSize
  return visibleArchives.value.slice(start, start + pageSize)
})

const filteredAnimals = computed(() => {
  const normalizedKeyword = animalKeyword.value.trim().toLowerCase()
  const animals = props.selectedArchive?.animals || []

  if (!normalizedKeyword) return animals
  return animals.filter((animal) => {
    const code = (animal.animal_code || '').toLowerCase()
    const earTag = (animal.ear_tag || '').toLowerCase()
    return code.includes(normalizedKeyword) || earTag.includes(normalizedKeyword)
  })
})

const totalAnimalPages = computed(() => Math.max(1, Math.ceil(filteredAnimals.value.length / pageSize)))

const pagedAnimals = computed(() => {
  const start = (animalPage.value - 1) * pageSize
  return filteredAnimals.value.slice(start, start + pageSize)
})

const selectedAnimal = computed(() => {
  return filteredAnimals.value.find((animal) => animal.id === selectedAnimalId.value) || pagedAnimals.value[0] || null
})

watch(
  [visibleArchives, archivePage],
  () => {
    if (archivePage.value > totalArchivePages.value) {
      archivePage.value = totalArchivePages.value
    }
  },
  { immediate: true }
)

watch(
  () => props.selectedArchiveId,
  (archiveId) => {
    if (!archiveId) return
    const index = visibleArchives.value.findIndex((archive) => archive.id === archiveId)
    if (index === -1) return
    archivePage.value = Math.floor(index / pageSize) + 1
  },
  { immediate: true }
)

watch(
  () => props.selectedArchive,
  (archive) => {
    if (!archive) return

    archiveForm.batch_number = archive.batch_number || ''
    archiveForm.species = archive.species || ''
    archiveForm.quantity = archive.quantity || 1
    archiveForm.health_status = archive.health_status || 'stable'
    archiveForm.average_weight = archive.average_weight
    archiveForm.feed_consumption = archive.feed_consumption
    archiveForm.expected_checkout_date = toDatetimeLocal(archive.expected_checkout_date)
    archiveForm.notes = archive.notes || ''
    animalKeyword.value = ''
    animalPage.value = 1

    const animals = archive.animals || []
    if (!animals.some((animal) => animal.id === selectedAnimalId.value)) {
      selectedAnimalId.value = animals[0]?.id ?? null
    }
    historyExpanded.value = false
  },
  { immediate: true }
)

watch([filteredAnimals, animalPage], () => {
  if (animalPage.value > totalAnimalPages.value) {
    animalPage.value = totalAnimalPages.value
  }

  if (!filteredAnimals.value.some((animal) => animal.id === selectedAnimalId.value)) {
    selectedAnimalId.value = pagedAnimals.value[0]?.id ?? filteredAnimals.value[0]?.id ?? null
  }
})

watch(
  selectedAnimal,
  (animal) => {
    if (!animal) return

    selectedAnimalForm.animal_code = animal.animal_code || ''
    selectedAnimalForm.species = animal.species || ''
    selectedAnimalForm.breed = animal.breed || ''
    selectedAnimalForm.gender = animal.gender || ''
    selectedAnimalForm.ear_tag = animal.ear_tag || ''
    selectedAnimalForm.weight = animal.weight
    selectedAnimalForm.check_in_date = toDatetimeLocal(animal.check_in_date)
    selectedAnimalForm.source = animal.source || ''
    selectedAnimalForm.health_status = animal.health_status || 'stable'
    selectedAnimalForm.immunization_note = animal.immunization_note || ''
    selectedAnimalForm.notes = animal.notes || ''
    historyExpanded.value = false
  },
  { immediate: true }
)

function formatHealth(value) {
  return healthMap[value] || value || '未知'
}

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString('zh-CN') : '--'
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}

function setFeedback(type, message) {
  feedback.type = type
  feedback.message = message
}

function normalizeError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback
}

function historyFieldLabel(fieldName) {
  return fieldName === 'ear_tag' ? '耳标号' : fieldName === 'weight' ? '体重' : fieldName
}

function toggleHistory() {
  historyExpanded.value = !historyExpanded.value
}

function toDatetimeLocal(value) {
  if (!value) return ''
  const date = new Date(value)
  const offset = date.getTimezoneOffset()
  const normalized = new Date(date.getTime() - offset * 60000)
  return normalized.toISOString().slice(0, 16)
}

async function submitArchive() {
  if (!newArchive.batch_number || !newArchive.species || !newArchive.check_in_date) {
    setFeedback('error', '请先填写完整的批次编号、养殖品类和入栏时间。')
    return
  }

  submitting.archive = true
  setFeedback('', '')
  try {
    await props.onCreateArchive({
      batch_number: newArchive.batch_number,
      species: newArchive.species,
      quantity: Number(newArchive.quantity || 1),
      check_in_date: new Date(newArchive.check_in_date).toISOString()
    })
    newArchive.batch_number = ''
    newArchive.species = ''
    newArchive.quantity = 1
    newArchive.check_in_date = ''
    showArchiveModal.value = false
    setFeedback('success', '批次档案新增成功。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '批次档案新增失败。'))
  } finally {
    submitting.archive = false
  }
}

async function submitArchiveEdit() {
  if (!props.selectedArchiveId) return

  submitting.archiveEdit = true
  setFeedback('', '')
  try {
    await props.onUpdateArchive(props.selectedArchiveId, {
      batch_number: archiveForm.batch_number,
      species: archiveForm.species,
      quantity: Number(archiveForm.quantity || 1),
      health_status: archiveForm.health_status,
      average_weight: archiveForm.average_weight === '' ? null : archiveForm.average_weight,
      feed_consumption: archiveForm.feed_consumption === '' ? null : archiveForm.feed_consumption,
      expected_checkout_date: archiveForm.expected_checkout_date ? new Date(archiveForm.expected_checkout_date).toISOString() : null,
      notes: archiveForm.notes || null
    })
    setFeedback('success', '批次档案已更新。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '批次档案更新失败。'))
  } finally {
    submitting.archiveEdit = false
  }
}

async function removeArchive() {
  if (!props.selectedArchiveId) return

  submitting.archiveDelete = true
  setFeedback('', '')
  try {
    await props.onDeleteArchive(props.selectedArchiveId)
    selectedAnimalId.value = null
    historyExpanded.value = false
    setFeedback('success', '批次档案已删除。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '批次档案删除失败。'))
  } finally {
    submitting.archiveDelete = false
  }
}

async function submitAnimal() {
  if (!props.selectedArchiveId) {
    setFeedback('error', '请先选择一个批次，再新增个体档案。')
    return
  }
  if (!newAnimal.animal_code || !newAnimal.species || !newAnimal.check_in_date) {
    setFeedback('error', '请先填写完整的个体编号、物种和入栏时间。')
    return
  }

  submitting.animal = true
  setFeedback('', '')
  try {
    await props.onCreateAnimal({
      archive_id: props.selectedArchiveId,
      animal_code: newAnimal.animal_code,
      species: newAnimal.species,
      breed: newAnimal.breed || null,
      gender: newAnimal.gender || null,
      ear_tag: newAnimal.ear_tag || null,
      weight: newAnimal.weight !== '' ? newAnimal.weight : null,
      check_in_date: new Date(newAnimal.check_in_date).toISOString(),
      source: newAnimal.source || null
    })
    newAnimal.animal_code = ''
    newAnimal.species = ''
    newAnimal.breed = ''
    newAnimal.gender = ''
    newAnimal.ear_tag = ''
    newAnimal.weight = null
    newAnimal.check_in_date = ''
    newAnimal.source = ''
    showAnimalModal.value = false
    animalPage.value = 1
    setFeedback('success', '个体档案新增成功。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '个体档案新增失败。'))
  } finally {
    submitting.animal = false
  }
}

async function submitAnimalEdit() {
  if (!selectedAnimal.value) return

  busyAnimalId.value = selectedAnimal.value.id
  setFeedback('', '')
  try {
    await props.onUpdateAnimal(selectedAnimal.value.id, {
      animal_code: selectedAnimalForm.animal_code,
      species: selectedAnimalForm.species,
      breed: selectedAnimalForm.breed || null,
      gender: selectedAnimalForm.gender || null,
      ear_tag: selectedAnimalForm.ear_tag || null,
      weight: selectedAnimalForm.weight === '' ? null : selectedAnimalForm.weight,
      check_in_date: selectedAnimalForm.check_in_date ? new Date(selectedAnimalForm.check_in_date).toISOString() : null,
      source: selectedAnimalForm.source || null,
      health_status: selectedAnimalForm.health_status,
      immunization_note: selectedAnimalForm.immunization_note || null,
      notes: selectedAnimalForm.notes || null
    })
    setFeedback('success', '个体档案已更新。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '个体档案更新失败。'))
  } finally {
    busyAnimalId.value = null
  }
}

async function removeAnimal() {
  if (!selectedAnimal.value) return

  busyAnimalId.value = selectedAnimal.value.id
  setFeedback('', '')
  try {
    await props.onDeleteAnimal(selectedAnimal.value.id)
    historyExpanded.value = false
    setFeedback('success', '个体档案已删除。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '个体档案删除失败。'))
  } finally {
    busyAnimalId.value = null
  }
}
</script>

<style scoped lang="scss">
.archive-panel{display:flex;flex-direction:column;gap:10px;height:100%;min-height:0;overflow:hidden}
.detail-header,.inline-actions,.archive-top,.animal-top,.animal-meta{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
h2,h3,h4{margin:0;color:#f3f7fa}
.feedback{padding:10px 12px;border-radius:12px;font-size:13px;flex:none}
.feedback.success{background:rgba(79,169,143,.18);color:#c8f0e6}
.feedback.error{background:rgba(255,107,107,.16);color:#ffd3d3}
.summary-grid,.form-grid,.animal-form-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.summary-grid{flex:none}
.summary-grid div,.records-box,.archive-card,.animal-selector-card,.history-item{padding:14px;border-radius:16px;background:rgba(10,33,39,.88)}
.summary-grid div{padding:10px 12px;border-radius:14px}
.summary-grid span{display:block;color:#87a5ac;font-size:11px;margin-bottom:4px}
.summary-grid strong{font-size:18px;line-height:1}
.search-field{display:grid;gap:8px}
.search-field label{font-size:13px;color:#87a5ac}
.form-grid input,.form-grid select,.animal-form-grid input,.animal-form-grid select,.search-field input{height:40px;padding:0 12px;border-radius:12px;border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8}
.archive-workbench{display:grid;grid-template-columns:320px 360px minmax(0,1fr);gap:10px;align-items:stretch;flex:1;min-height:0;height:auto}
.workbench-column{min-width:0;height:100%;display:flex;flex-direction:column;gap:10px;padding:14px;border-radius:20px;background:linear-gradient(180deg,rgba(8,27,32,.96),rgba(4,16,21,.96));border:1px solid rgba(164,215,210,.12);box-shadow:inset 0 1px 0 rgba(200,255,245,.03),0 18px 40px rgba(0,0,0,.22)}
.column-header{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.column-actions{display:flex;align-items:center;justify-content:flex-end;gap:10px;flex-wrap:wrap}
.column-label{margin:0 0 4px;color:#7ea7ae;font-size:10px;letter-spacing:.18em;text-transform:uppercase}
.column-count{min-width:34px;height:34px;display:inline-flex;align-items:center;justify-content:center;padding:0 10px;border-radius:999px;background:rgba(125,207,116,.12);color:#d6f2cf;font-weight:600}
.batch-column,.animal-column,.detail-column{overflow:hidden}
.archive-list,.animal-selector-panel{flex:1;min-height:0}
.archive-list,.animal-selector-list,.history-list,.detail-scroll{display:grid;gap:10px;align-content:start}
.archive-list{overflow:auto;padding-right:4px}
.archive-card,.animal-selector-card{
  text-align:left;
  border:1px solid rgba(164,215,210,.12);
  cursor:pointer;
  color:#eff7f8;
  font:inherit;
  line-height:1.35;
  appearance:none;
  -webkit-appearance:none;
}
.archive-card{height:110px;display:grid;grid-template-rows:auto 1fr auto;align-content:stretch;gap:6px}
.archive-card.active,.animal-selector-card.active{border-color:rgba(125,207,116,.35);background:rgba(16,52,58,.94)}
.archive-card.inactive{opacity:.6}
.archive-card p,.archive-card small,.animal-selector-card p,.animal-selector-card small,.animal-meta span,.history-item span,.history-item small{margin:0;color:#98b0b5}
.archive-card strong,.archive-card p,.archive-card small,.animal-selector-card strong,.animal-selector-card p,.animal-selector-card small{
  display:block;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
  line-height:1.35;
}
.health-tag{padding:4px 8px;border-radius:999px;font-size:12px}
.health-tag.good,.health-tag.stable{background:rgba(125,207,116,.12);color:#d6f2cf}
.health-tag.observe{background:rgba(255,200,87,.12);color:#ffe2a4}
.animal-search{flex:none}
.animal-selector-panel{display:flex;flex-direction:column;gap:10px}
.animal-selector-list{flex:1;min-height:0;grid-auto-rows:110px;overflow:auto;padding-right:4px}
.animal-selector-card{height:110px;display:grid;grid-template-rows:auto 1fr auto;align-content:stretch;gap:6px}
.animal-editor{display:grid;gap:10px;padding:12px;border-radius:16px;background:rgba(8,27,32,.72);min-width:0}
.animal-form-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.pagination-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:8px 10px;border-radius:12px;background:rgba(8,27,32,.72);color:#98b0b5;flex:none;font-size:13px}
.history-box{margin-top:2px;padding:10px;border-radius:14px;background:rgba(8,27,32,.72)}
.detail-scroll{height:100%;overflow:auto;padding-right:4px;align-content:start}
.records-box{overflow:hidden}
.records-box .detail-header{align-items:center}
.history-list{max-height:220px;overflow:auto;padding-right:4px}
.inline-actions{flex-wrap:wrap}
.empty-state{flex:1;display:flex;align-items:center;justify-content:center;padding:18px;border-radius:16px;border:1px dashed rgba(164,215,210,.18);background:rgba(8,27,32,.58);color:#8ea9af;text-align:center}
.detail-empty{height:100%}
.modal-mask{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(2,10,13,.66);backdrop-filter:blur(8px);z-index:30}
.modal-card{width:min(760px,100%);display:grid;gap:16px;padding:22px;border-radius:24px;background:rgba(9,27,32,.98);border:1px solid rgba(176,224,221,.14);box-shadow:0 24px 60px rgba(0,0,0,.35)}
.primary-btn,.ghost-btn,.danger-btn{height:36px;padding:0 14px;border-radius:12px;cursor:pointer}
.primary-btn{border:none;background:linear-gradient(135deg,#4fa98f,#2f7f6d);color:#fff}
.ghost-btn{border:1px solid rgba(164,215,210,.18);background:transparent;color:#eaf3f5}
.danger-btn{border:none;background:linear-gradient(135deg,#b45454,#8d2e2e);color:#fff}
.primary-btn:disabled,.ghost-btn:disabled,.danger-btn:disabled{opacity:.6;cursor:not-allowed}
@media (max-width:1200px){
  .summary-grid,.form-grid,.animal-form-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .archive-workbench{grid-template-columns:1fr;height:auto;min-height:auto}
  .workbench-column{min-height:420px}
}
@media (max-width:720px){
  .summary-grid,.form-grid,.animal-form-grid{grid-template-columns:1fr}
}
</style>

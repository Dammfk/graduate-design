<template>
  <section class="archive-panel">
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

        <div class="filter-row">
          <input v-model.trim="batchKeyword" placeholder="批次编号 / 品类关键词" />
          <select v-model="batchSort">
            <option value="recent">按入栏时间排序</option>
            <option value="quantity">按数量排序</option>
            <option value="name">按批次编号排序</option>
          </select>
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

        <div class="filter-row animal-search">
          <input v-model.trim="animalKeyword" placeholder="编号查询：输入个体编号或耳标号" />
          <select v-model="animalSort">
            <option value="recent">按最近更新排序</option>
            <option value="code">按个体编号排序</option>
            <option value="health">按健康状态排序</option>
          </select>
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
          <div class="context-strip">
            <article class="context-card">
              <span>当前批次</span>
              <strong>{{ selectedArchive.batch_number }}</strong>
              <small>{{ selectedArchive.species }} / {{ selectedArchive.quantity }} 头</small>
            </article>
            <article class="context-card">
              <span>当前个体</span>
              <strong>{{ selectedAnimal?.animal_code || '未选择个体' }}</strong>
              <small>{{ selectedAnimal?.ear_tag ? `耳标 ${selectedAnimal.ear_tag}` : '请先在中间列表选择个体' }}</small>
            </article>
            <article class="context-card">
              <span>当前批量作用范围</span>
              <strong>{{ filteredAnimals.length }} 个个体</strong>
              <small>{{ animalKeyword ? '基于当前筛选结果生效' : '默认作用于当前批次全部个体' }}</small>
            </article>
          </div>

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
              <input v-model="archiveForm.batch_number" :class="{ 'input-invalid': archiveErrors.batch_number }" placeholder="批次编号" />
              <input v-model="archiveForm.species" :class="{ 'input-invalid': archiveErrors.species }" placeholder="养殖品类" />
              <input v-model.number="archiveForm.quantity" :class="{ 'input-invalid': archiveErrors.quantity }" type="number" min="1" placeholder="数量" />
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
                <button
                  class="ghost-btn"
                  type="button"
                  :disabled="!filteredAnimals.length"
                  @click="openBulkModal"
                >
                  批量登记
                </button>
                <button class="primary-btn" type="button" @click="showAnimalModal = true">新增个体档案</button>
              </div>
            </div>

            <div v-if="selectedAnimal" class="animal-editor">
              <div class="animal-meta">
                <strong>{{ selectedAnimal.animal_code }}</strong>
                <span>最后更新时间：{{ formatDateTime(selectedAnimal.updated_at) }}</span>
              </div>

              <div class="animal-form-grid">
                <input v-model="selectedAnimalForm.animal_code" :class="{ 'input-invalid': animalFormErrors.animal_code }" placeholder="个体编号" />
                <input v-model="selectedAnimalForm.species" :class="{ 'input-invalid': animalFormErrors.species }" placeholder="物种" />
                <input v-model="selectedAnimalForm.breed" placeholder="品种" />
                <input v-model="selectedAnimalForm.gender" placeholder="性别" />
                <input v-model="selectedAnimalForm.ear_tag" placeholder="耳标号" />
                <input v-model.number="selectedAnimalForm.weight" type="number" min="0" step="0.1" placeholder="体重(kg)" />
                <input v-model="selectedAnimalForm.check_in_date" :class="{ 'input-invalid': animalFormErrors.check_in_date }" type="datetime-local" placeholder="入栏时间" />
                <input v-model="selectedAnimalForm.source" placeholder="来源地" />
                <select v-model="selectedAnimalForm.health_status">
                  <option value="good">良好</option>
                  <option value="stable">稳定</option>
                  <option value="observe">观察</option>
                </select>
                <input v-model="selectedAnimalForm.notes" placeholder="个体备注" />
              </div>

              <div v-if="firstAnimalFormError" class="field-error-banner">{{ firstAnimalFormError }}</div>

              <div class="record-section">
                <div class="record-section-header">
                  <strong>已有接种记录</strong>
                  <div class="record-section-actions">
                    <span>{{ immunizationEntries.length }} 条</span>
                    <button class="ghost-btn compact-btn" type="button" @click="openImmunizationModal">
                      新增接种记录
                    </button>
                  </div>
                </div>
                <div v-if="immunizationEntries.length" class="record-entry-list">
                  <div v-for="(entry, index) in immunizationEntries" :key="`${selectedAnimal.id}-immunization-${index}`" class="record-entry-card">
                    {{ entry }}
                  </div>
                </div>
                <p v-else class="record-empty">暂无接种记录。</p>
              </div>

              <div class="inline-actions">
                <button class="ghost-btn" :disabled="busyAnimalId === selectedAnimal.id" @click="submitAnimalEdit">
                  {{ busyAnimalId === selectedAnimal.id ? '保存中...' : '保存基础档案' }}
                </button>
                <button class="ghost-btn" type="button" @click="openHistoryModal">
                  查看更新记录
                </button>
                <button class="danger-btn" :disabled="busyAnimalId === selectedAnimal.id" @click="removeAnimal">
                  {{ busyAnimalId === selectedAnimal.id ? '删除中...' : '删除个体档案' }}
                </button>
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
        <p class="form-note">带 <strong>*</strong> 的字段为必填项。</p>
        <div class="form-grid">
          <div class="field-block">
            <label>批次编号 *</label>
            <input v-model="newArchive.batch_number" :class="{ 'input-invalid': archiveCreateErrors.batch_number }" placeholder="如 BATCH-CATTLE-004" />
            <small v-if="archiveCreateErrors.batch_number" class="field-error">{{ archiveCreateErrors.batch_number }}</small>
          </div>
          <div class="field-block">
            <label>养殖品类 *</label>
            <input v-model="newArchive.species" :class="{ 'input-invalid': archiveCreateErrors.species }" placeholder="如 肉牛 / 奶牛 / 肉羊" />
            <small v-if="archiveCreateErrors.species" class="field-error">{{ archiveCreateErrors.species }}</small>
          </div>
          <div class="field-block">
            <label>数量 *</label>
            <input v-model.number="newArchive.quantity" :class="{ 'input-invalid': archiveCreateErrors.quantity }" type="number" min="1" placeholder="数量" />
            <small v-if="archiveCreateErrors.quantity" class="field-error">{{ archiveCreateErrors.quantity }}</small>
          </div>
          <div class="field-block">
            <label>入栏时间 *</label>
            <input v-model="newArchive.check_in_date" :class="{ 'input-invalid': archiveCreateErrors.check_in_date }" type="datetime-local" />
            <small v-if="archiveCreateErrors.check_in_date" class="field-error">{{ archiveCreateErrors.check_in_date }}</small>
          </div>
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
        <p class="form-note">基础档案保存的是个体静态信息，接种记录请在详情页右侧单独追加。</p>
        <div class="form-grid">
          <div class="field-block">
            <label>个体编号 *</label>
            <input v-model="newAnimal.animal_code" :class="{ 'input-invalid': animalCreateErrors.animal_code }" placeholder="如 CATTLE-010" />
            <small v-if="animalCreateErrors.animal_code" class="field-error">{{ animalCreateErrors.animal_code }}</small>
          </div>
          <div class="field-block">
            <label>物种 *</label>
            <input v-model="newAnimal.species" :class="{ 'input-invalid': animalCreateErrors.species }" placeholder="如 肉牛 / 肉羊" />
            <small v-if="animalCreateErrors.species" class="field-error">{{ animalCreateErrors.species }}</small>
          </div>
          <div class="field-block">
            <label>品种</label>
            <input v-model="newAnimal.breed" placeholder="品种" />
          </div>
          <div class="field-block">
            <label>性别</label>
            <input v-model="newAnimal.gender" placeholder="性别" />
          </div>
          <div class="field-block">
            <label>耳标号</label>
            <input v-model="newAnimal.ear_tag" placeholder="耳标号" />
          </div>
          <div class="field-block">
            <label>体重</label>
            <input v-model.number="newAnimal.weight" type="number" min="0" step="0.1" placeholder="体重(kg)" />
          </div>
          <div class="field-block">
            <label>入栏时间 *</label>
            <input v-model="newAnimal.check_in_date" :class="{ 'input-invalid': animalCreateErrors.check_in_date }" type="datetime-local" />
            <small v-if="animalCreateErrors.check_in_date" class="field-error">{{ animalCreateErrors.check_in_date }}</small>
          </div>
          <div class="field-block">
            <label>来源地</label>
            <input v-model="newAnimal.source" placeholder="来源地" />
          </div>
        </div>
        <div class="inline-actions">
          <button class="primary-btn" :disabled="submitting.animal" @click="submitAnimal">
            {{ submitting.animal ? '提交中...' : '确认新增' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showBulkModal" class="modal-mask" @click.self="closeBulkModal">
      <div class="modal-card">
        <div class="detail-header">
          <div>
            <h3>批量登记</h3>
            <p class="modal-tip">当前批次 {{ selectedArchive?.batch_number || '--' }}，先勾选本次实际执行该操作的编号，再统一登记。</p>
          </div>
          <button class="ghost-btn" type="button" @click="closeBulkModal">取消</button>
        </div>
        <div class="bulk-targets">
          <div class="record-section-header">
            <strong>作用对象</strong>
            <div class="record-section-actions">
              <span>已选 {{ selectedBulkAnimalIds.length }} / {{ bulkSelectableAnimals.length }}</span>
              <button class="ghost-btn compact-btn" type="button" @click="selectAllBulkAnimals">全选</button>
              <button class="ghost-btn compact-btn" type="button" @click="clearBulkAnimalSelection">清空</button>
            </div>
          </div>
          <div class="bulk-filter-row">
            <select v-model="bulkHealthFilter">
              <option value="">按健康状态筛选：全部</option>
              <option value="good">仅良好</option>
              <option value="stable">仅稳定</option>
              <option value="observe">仅观察</option>
            </select>
            <input v-model.trim="bulkEarTagKeyword" placeholder="按耳标快速筛选" />
          </div>
          <div class="bulk-target-list">
            <label v-for="animal in bulkSelectableAnimals" :key="`bulk-${animal.id}`" class="bulk-target-item">
              <input v-model="selectedBulkAnimalIds" type="checkbox" :value="animal.id" />
              <span class="bulk-target-code">{{ animal.animal_code }}</span>
              <small>{{ animal.ear_tag || '未录入耳标' }}</small>
            </label>
          </div>
        </div>
        <div class="form-grid bulk-form-grid">
          <input v-model="bulkAnimalForm.action_date" type="date" />
          <select v-model="bulkAnimalForm.health_status">
            <option value="">健康状态：不修改</option>
            <option value="good">健康状态：良好</option>
            <option value="stable">健康状态：稳定</option>
            <option value="observe">健康状态：观察</option>
          </select>
          <textarea
            v-model="bulkAnimalForm.immunization_note"
            class="bulk-textarea compact-textarea"
            placeholder="批量免疫记录，例如：口蹄疫疫苗第1针"
          />
          <textarea
            v-model="bulkAnimalForm.notes"
            class="bulk-textarea compact-textarea"
            placeholder="批量备注，例如：今日统一驱虫或复查"
          />
        </div>
        <div class="inline-actions">
          <button class="primary-btn" :disabled="submitting.bulkAnimal" @click="submitBulkAnimalUpdate">
            {{ submitting.bulkAnimal ? '提交中...' : '确认批量登记' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showImmunizationModal" class="modal-mask" @click.self="closeImmunizationModal">
      <div class="modal-card">
        <div class="detail-header">
          <div>
            <h3>新增接种记录</h3>
            <p class="modal-tip">当前个体 {{ selectedAnimal?.animal_code || '--' }}，仅追加本次接种内容，不会覆盖已有记录。</p>
          </div>
          <button class="ghost-btn" type="button" @click="closeImmunizationModal">取消</button>
        </div>
        <textarea
          v-model="selectedAnimalForm.immunization_note"
          class="bulk-textarea"
          placeholder="例如：口蹄疫疫苗第一针"
        />
        <div class="inline-actions">
          <button class="primary-btn" :disabled="busyAnimalId === selectedAnimal?.id" @click="submitAnimalEdit">
            {{ busyAnimalId === selectedAnimal?.id ? '保存中...' : '确认追加记录' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showHistoryModal" class="modal-mask" @click.self="closeHistoryModal">
      <div class="modal-card history-modal-card">
        <div class="detail-header">
          <div>
            <h3>个体更新记录</h3>
            <p class="modal-tip">{{ selectedAnimal?.animal_code || '--' }} 的历史变更记录</p>
          </div>
          <button class="ghost-btn" type="button" @click="closeHistoryModal">关闭</button>
        </div>
        <div class="history-filter-row">
          <button
            v-for="item in historyFilterOptions"
            :key="item.value"
            class="ghost-btn compact-btn"
            :class="{ active: historyFieldFilter === item.value }"
            type="button"
            @click="historyFieldFilter = item.value"
          >
            {{ item.label }}
          </button>
        </div>
        <div v-if="displayHistoryRecords.length" class="history-list history-list-modal">
          <div v-for="record in displayHistoryRecords" :key="record.id" class="history-item">
            <strong class="history-field">{{ historyFieldLabel(record.field_name) }}</strong>
            <div class="history-change" :class="{ compact: isAppendOnlyHistory(record.field_name) }">
              <template v-if="isAppendOnlyHistory(record.field_name)">
                <span class="history-change-label">新增记录</span>
                <span class="history-change-value">{{ latestAppendOnlyEntry(record.old_value, record.new_value) }}</span>
              </template>
              <template v-else>
                <span>{{ formatHistoryValue(record.field_name, record.old_value) }}</span>
                <span class="history-arrow">→</span>
                <span>{{ formatHistoryValue(record.field_name, record.new_value) }}</span>
              </template>
            </div>
            <small class="history-time">{{ formatDateTime(record.changed_at) }}</small>
          </div>
        </div>
        <p v-else class="record-empty">暂无个体历史更新记录。</p>
      </div>
    </div>

  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useMonitoringStore } from '../stores/monitoring'

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
  onDeleteAnimal: { type: Function, required: true },
  onBulkUpdateAnimals: { type: Function, required: true }
})

const emit = defineEmits(['select'])
const monitoringStore = useMonitoringStore()

const newArchive = reactive({ batch_number: '', species: '', quantity: 1, check_in_date: '' })
const newAnimal = reactive({ animal_code: '', species: '', breed: '', gender: '', ear_tag: '', weight: null, check_in_date: '', source: '' })
const bulkAnimalForm = reactive({ action_date: '', health_status: '', immunization_note: '', notes: '' })
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
const selectedBulkAnimalIds = ref([])
const showArchiveModal = ref(false)
const showAnimalModal = ref(false)
const showImmunizationModal = ref(false)
const showBulkModal = ref(false)
const showHistoryModal = ref(false)
const archivePage = ref(1)
const batchKeyword = ref('')
const batchSort = ref('recent')
const animalKeyword = ref('')
const animalSort = ref('recent')
const animalPage = ref(1)
const bulkHealthFilter = ref('')
const bulkEarTagKeyword = ref('')
const historyFieldFilter = ref('all')
const pageSize = 7
const submitting = reactive({ archive: false, archiveEdit: false, archiveDelete: false, animal: false, bulkAnimal: false })
const busyAnimalId = ref(null)
const archiveCreateErrors = reactive({ batch_number: '', species: '', quantity: '', check_in_date: '' })
const archiveErrors = reactive({ batch_number: '', species: '', quantity: '' })
const animalCreateErrors = reactive({ animal_code: '', species: '', check_in_date: '' })
const animalFormErrors = reactive({ animal_code: '', species: '', check_in_date: '' })

const healthMap = { stable: '稳定', good: '良好', observe: '观察' }

const visibleArchives = computed(() => {
  const normalizedKeyword = batchKeyword.value.trim().toLowerCase()
  const sorted = props.archives
    .filter((archive) => archive.is_active !== false)
    .filter((archive) => {
      if (!normalizedKeyword) return true
      return [archive.batch_number, archive.species, archive.notes]
        .filter(Boolean)
        .some((item) => String(item).toLowerCase().includes(normalizedKeyword))
    })
    .sort((left, right) => {
      if (batchSort.value === 'quantity') {
        return Number(right.quantity || 0) - Number(left.quantity || 0)
      }
      if (batchSort.value === 'name') {
        return String(left.batch_number || '').localeCompare(String(right.batch_number || ''))
      }
      return new Date(right.check_in_date || 0).getTime() - new Date(left.check_in_date || 0).getTime()
    })

  return sorted
})
const totalArchivePages = computed(() => Math.max(1, Math.ceil(visibleArchives.value.length / pageSize)))
const pagedArchives = computed(() => {
  const start = (archivePage.value - 1) * pageSize
  return visibleArchives.value.slice(start, start + pageSize)
})

const filteredAnimals = computed(() => {
  const normalizedKeyword = animalKeyword.value.trim().toLowerCase()
  const animals = props.selectedArchive?.animals || []

  const filtered = !normalizedKeyword
    ? animals
    : animals.filter((animal) => {
        const code = (animal.animal_code || '').toLowerCase()
        const earTag = (animal.ear_tag || '').toLowerCase()
        return code.includes(normalizedKeyword) || earTag.includes(normalizedKeyword)
      })

  return [...filtered].sort((left, right) => {
    if (animalSort.value === 'code') {
      return String(left.animal_code || '').localeCompare(String(right.animal_code || ''))
    }
    if (animalSort.value === 'health') {
      return healthWeight(left.health_status) - healthWeight(right.health_status)
    }
    return new Date(right.updated_at || right.created_at || 0).getTime() - new Date(left.updated_at || left.created_at || 0).getTime()
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

const immunizationEntries = computed(() => {
  return splitAppendOnlyEntries(selectedAnimal.value?.immunization_note).reverse()
})

const bulkSelectableAnimals = computed(() => {
  const health = bulkHealthFilter.value
  const earTagKeyword = bulkEarTagKeyword.value.trim().toLowerCase()
  return filteredAnimals.value.filter((animal) => {
    const healthMatched = !health || animal.health_status === health
    const earTagMatched = !earTagKeyword || String(animal.ear_tag || '').toLowerCase().includes(earTagKeyword)
    return healthMatched && earTagMatched
  })
})

const historyFilterOptions = [
  { value: 'all', label: '全部' },
  { value: 'basic', label: '基础档案' },
  { value: 'immunization_note', label: '接种记录' },
  { value: 'notes', label: '备注' },
  { value: 'time', label: '时间字段' }
]

const displayHistoryRecords = computed(() => {
  const records = selectedAnimal.value?.history_records || []
  const seen = new Set()

  return records.filter((record) => {
    if (!matchesHistoryFilter(record.field_name)) {
      return false
    }
    const signature = `${record.field_name}::${record.old_value || ''}::${record.new_value || ''}`
    if (seen.has(signature)) {
      return false
    }
    seen.add(signature)
    return true
  })
})

const firstAnimalFormError = computed(() => {
  return animalFormErrors.animal_code || animalFormErrors.species || animalFormErrors.check_in_date || ''
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
  (archive, previousArchive) => {
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
    if (archive.id !== previousArchive?.id) {
      showHistoryModal.value = false
    }
  },
  { immediate: true }
)

watch([batchKeyword, batchSort], () => {
  archivePage.value = 1
})

watch([filteredAnimals, animalPage], () => {
  if (animalPage.value > totalAnimalPages.value) {
    animalPage.value = totalAnimalPages.value
  }

  if (!filteredAnimals.value.some((animal) => animal.id === selectedAnimalId.value)) {
    selectedAnimalId.value = pagedAnimals.value[0]?.id ?? filteredAnimals.value[0]?.id ?? null
  }
})

watch([animalKeyword, animalSort], () => {
  animalPage.value = 1
})

watch(
  selectedAnimal,
  (animal, previousAnimal) => {
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
    selectedAnimalForm.notes = animal.notes || ''
    if (animal.id !== previousAnimal?.id) {
      selectedAnimalForm.immunization_note = ''
      showImmunizationModal.value = false
      showBulkModal.value = false
      showHistoryModal.value = false
      clearAnimalFormErrors()
    }
  },
  { immediate: true }
)

function formatHealth(value) {
  return healthMap[value] || value || '未知'
}

function healthWeight(value) {
  return { observe: 0, stable: 1, good: 2 }[value] ?? 9
}

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString('zh-CN') : '--'
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '--'
}

function setFeedback(type, message) {
  if (!message) return
  const tone = type === 'error' ? 'error' : type === 'success' ? 'success' : 'info'
  const title = type === 'error' ? '操作失败' : type === 'success' ? '操作成功' : '提示'
  monitoringStore.showNotice(tone, message, title)
}

function normalizeError(error, fallback) {
  return error?.response?.data?.detail || error?.message || fallback
}

function historyFieldLabel(fieldName) {
  const labels = {
    animal_code: '个体编号',
    species: '品类',
    breed: '品种',
    gender: '性别',
    birth_date: '出生日期',
    check_in_date: '入栏日期',
    weight: '体重',
    health_status: '健康状态',
    ear_tag: '耳标号',
    source: '来源',
    immunization_note: '免疫记录',
    notes: '备注',
    is_active: '启用状态'
  }
  return labels[fieldName] || fieldName
}

function isAppendOnlyHistory(fieldName) {
  return fieldName === 'immunization_note' || fieldName === 'notes'
}

function extractAppendedHistory(oldValue, newValue) {
  const oldText = oldValue ? String(oldValue).trim() : ''
  const newText = newValue ? String(newValue).trim() : ''
  if (!newText) return '--'
  if (!oldText) return newText
  if (newText.startsWith(oldText)) {
    const appended = newText.slice(oldText.length).trim()
    return normalizeAppendOnlyText(appended || newText)
  }
  return normalizeAppendOnlyText(newText)
}

function normalizeAppendOnlyText(value) {
  return String(value)
    .replace(/(?<!^)(?=\d{4}-\d{2}-\d{2}(?:[：:\s]|$))/g, '\n')
    .trim()
}

function splitAppendOnlyEntries(value) {
  const normalized = normalizeAppendOnlyText(value || '')
  if (!normalized) return []
  return normalized
    .split('\n')
    .map(item => item.trim())
    .filter(Boolean)
}

function latestAppendOnlyEntry(oldValue, newValue) {
  const normalized = extractAppendedHistory(oldValue, newValue)
  const entries = splitAppendOnlyEntries(normalized)

  return entries.at(-1) || normalized || '--'
}

function formatHistoryValue(fieldName, value) {
  if (value === null || value === undefined || value === '') {
    return '--'
  }

  if (fieldName === 'weight') {
    const numericValue = Number(value)
    return Number.isFinite(numericValue) ? `${numericValue} kg` : String(value)
  }

  if (fieldName === 'is_active') {
    if (value === true || value === 'True' || value === 'true' || value === '1') return '启用'
    if (value === false || value === 'False' || value === 'false' || value === '0') return '停用'
  }

  if (fieldName === 'health_status') {
    return formatHealth(value)
  }

  if (fieldName === 'immunization_note' || fieldName === 'notes') {
    return normalizeAppendOnlyText(value)
  }

  if (fieldName === 'birth_date' || fieldName === 'check_in_date') {
    const parsedDate = new Date(value)
    return Number.isNaN(parsedDate.getTime()) ? String(value) : formatDateTime(parsedDate)
  }

  return String(value)
}

function openHistoryModal() {
  showHistoryModal.value = true
}

function closeHistoryModal() {
  showHistoryModal.value = false
}

function openImmunizationModal() {
  selectedAnimalForm.immunization_note = ''
  showImmunizationModal.value = true
}

function closeImmunizationModal() {
  showImmunizationModal.value = false
  selectedAnimalForm.immunization_note = ''
}

function resetBulkForm() {
  bulkAnimalForm.action_date = new Date().toISOString().slice(0, 10)
  bulkAnimalForm.health_status = ''
  bulkAnimalForm.immunization_note = ''
  bulkAnimalForm.notes = ''
  selectedBulkAnimalIds.value = []
  bulkHealthFilter.value = ''
  bulkEarTagKeyword.value = ''
}

function selectAllBulkAnimals() {
  selectedBulkAnimalIds.value = bulkSelectableAnimals.value.map(item => item.id)
}

function clearBulkAnimalSelection() {
  selectedBulkAnimalIds.value = []
}

function openBulkModal() {
  if (!filteredAnimals.value.length) {
    setFeedback('error', '当前筛选结果中没有可批量处理的个体。')
    return
  }
  resetBulkForm()
  selectAllBulkAnimals()
  showBulkModal.value = true
}

function closeBulkModal() {
  showBulkModal.value = false
  resetBulkForm()
}

function toDatetimeLocal(value) {
  if (!value) return ''
  const date = new Date(value)
  const offset = date.getTimezoneOffset()
  const normalized = new Date(date.getTime() - offset * 60000)
  return normalized.toISOString().slice(0, 16)
}

function resetValidation(errors) {
  Object.keys(errors).forEach((key) => {
    errors[key] = ''
  })
}

function clearAnimalFormErrors() {
  resetValidation(animalFormErrors)
}

function validateArchiveCreate() {
  resetValidation(archiveCreateErrors)
  if (!newArchive.batch_number.trim()) archiveCreateErrors.batch_number = '请填写批次编号'
  if (!newArchive.species.trim()) archiveCreateErrors.species = '请填写养殖品类'
  if (!newArchive.quantity || Number(newArchive.quantity) < 1) archiveCreateErrors.quantity = '数量至少为 1'
  if (!newArchive.check_in_date) archiveCreateErrors.check_in_date = '请选择入栏时间'
  return !Object.values(archiveCreateErrors).some(Boolean)
}

function validateArchiveEdit() {
  resetValidation(archiveErrors)
  if (!archiveForm.batch_number.trim()) archiveErrors.batch_number = '批次编号不能为空'
  if (!archiveForm.species.trim()) archiveErrors.species = '养殖品类不能为空'
  if (!archiveForm.quantity || Number(archiveForm.quantity) < 1) archiveErrors.quantity = '数量至少为 1'
  return !Object.values(archiveErrors).some(Boolean)
}

function validateAnimalCreate() {
  resetValidation(animalCreateErrors)
  if (!newAnimal.animal_code.trim()) animalCreateErrors.animal_code = '请填写个体编号'
  if (!newAnimal.species.trim()) animalCreateErrors.species = '请填写物种'
  if (!newAnimal.check_in_date) animalCreateErrors.check_in_date = '请选择入栏时间'
  return !Object.values(animalCreateErrors).some(Boolean)
}

function validateAnimalEdit() {
  resetValidation(animalFormErrors)
  if (!selectedAnimalForm.animal_code.trim()) animalFormErrors.animal_code = '个体编号不能为空'
  if (!selectedAnimalForm.species.trim()) animalFormErrors.species = '物种不能为空'
  if (!selectedAnimalForm.check_in_date) animalFormErrors.check_in_date = '请保留或重新选择入栏时间'
  return !Object.values(animalFormErrors).some(Boolean)
}

function matchesHistoryFilter(fieldName) {
  if (historyFieldFilter.value === 'all') return true
  if (historyFieldFilter.value === 'immunization_note') return fieldName === 'immunization_note'
  if (historyFieldFilter.value === 'notes') return fieldName === 'notes'
  if (historyFieldFilter.value === 'time') return fieldName === 'check_in_date' || fieldName === 'birth_date'
  if (historyFieldFilter.value === 'basic') {
    return !['immunization_note', 'notes', 'check_in_date', 'birth_date'].includes(fieldName)
  }
  return true
}

async function submitArchive() {
  if (!validateArchiveCreate()) {
    setFeedback('error', '请先补全批次档案里的必填项。')
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
  if (!validateArchiveEdit()) {
    setFeedback('error', '请先修正批次信息中的必填项。')
    return
  }

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
  if (!window.confirm(`确认删除批次 ${props.selectedArchive?.batch_number || ''} 吗？这会同时隐藏该批次下的个体档案。`)) {
    return
  }

  submitting.archiveDelete = true
  setFeedback('', '')
  try {
    await props.onDeleteArchive(props.selectedArchiveId)
    selectedAnimalId.value = null
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
  if (!validateAnimalCreate()) {
    setFeedback('error', '请先补全个体档案里的必填项。')
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
  if (!validateAnimalEdit()) {
    setFeedback('error', '基础档案还有未完成的必填项，请先修正。')
    return
  }

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
    if (selectedAnimalForm.immunization_note?.trim()) {
      closeImmunizationModal()
    }
    setFeedback('success', '个体档案已更新。')
  } catch (error) {
    setFeedback('error', normalizeError(error, '个体档案更新失败。'))
  } finally {
    busyAnimalId.value = null
  }
}

async function submitBulkAnimalUpdate() {
  if (!props.selectedArchiveId) {
    setFeedback('error', '请先选择批次后再进行批量管理。')
    return
  }
  if (!filteredAnimals.value.length) {
    setFeedback('error', '当前筛选结果中没有可批量处理的个体。')
    return
  }
  if (!selectedBulkAnimalIds.value.length) {
    setFeedback('error', '请先勾选本次实际执行该操作的个体编号。')
    return
  }
  if (!bulkAnimalForm.health_status && !bulkAnimalForm.immunization_note.trim() && !bulkAnimalForm.notes.trim()) {
    setFeedback('error', '请至少填写一项批量更新内容。')
    return
  }

  submitting.bulkAnimal = true
  setFeedback('', '')
  try {
    const selectedCount = selectedBulkAnimalIds.value.length
    const result = await props.onBulkUpdateAnimals({
      archive_id: props.selectedArchiveId,
      animal_ids: selectedBulkAnimalIds.value,
      action_date: bulkAnimalForm.action_date ? new Date(`${bulkAnimalForm.action_date}T00:00:00`).toISOString() : null,
      health_status: bulkAnimalForm.health_status || null,
      immunization_note: bulkAnimalForm.immunization_note.trim() || null,
      notes: bulkAnimalForm.notes.trim() || null
    })
    closeBulkModal()
    setFeedback('success', `已批量更新 ${result.updated_count || selectedCount} 个个体档案。`)
  } catch (error) {
    setFeedback('error', normalizeError(error, '批量更新个体档案失败。'))
  } finally {
    submitting.bulkAnimal = false
  }
}

async function removeAnimal() {
  if (!selectedAnimal.value) return
  if (!window.confirm(`确认删除个体 ${selectedAnimal.value.animal_code} 吗？删除后历史记录也不会再显示。`)) {
    return
  }

  busyAnimalId.value = selectedAnimal.value.id
  setFeedback('', '')
  try {
    await props.onDeleteAnimal(selectedAnimal.value.id)
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
.summary-grid,.form-grid,.animal-form-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.summary-grid{flex:none}
.form-note{margin:0;color:#8ea9af;font-size:14px;line-height:1.6}
.field-block{display:grid;gap:6px}
.field-block label{color:#a7c0c5;font-size:13px}
.field-error{color:#ffc7c7;font-size:12px;line-height:1.4}
.field-error-banner{padding:10px 12px;border-radius:12px;background:rgba(255,120,120,.1);color:#ffd3d3;font-size:13px}
.input-invalid{border-color:rgba(255,120,120,.38)!important;box-shadow:0 0 0 1px rgba(255,120,120,.12)}
.summary-grid div,.records-box,.archive-card,.animal-selector-card,.history-item{padding:14px;border-radius:16px;background:rgba(10,33,39,.88)}
.summary-grid div{padding:10px 12px;border-radius:14px}
.summary-grid span{display:block;color:#87a5ac;font-size:11px;margin-bottom:4px}
.summary-grid strong{font-size:18px;line-height:1}
.context-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
.context-card{padding:12px 14px;border-radius:16px;background:rgba(8,27,32,.72);border:1px solid rgba(164,215,210,.12)}
.context-card span{display:block;color:#87a5ac;font-size:13px;margin-bottom:6px}
.context-card strong{display:block;font-size:18px;line-height:1.35;color:#f1f7f8}
.context-card small{display:block;margin-top:4px;color:#98b0b5;font-size:14px;line-height:1.5}
.search-field{display:grid;gap:8px}
.search-field label{font-size:13px;color:#87a5ac}
.filter-row{display:grid;grid-template-columns:minmax(0,1fr) 180px;gap:10px}
.form-grid input,.form-grid select,.animal-form-grid input,.animal-form-grid select,.search-field input{height:40px;padding:0 12px;border-radius:12px;border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8}
.filter-row input,.filter-row select{height:40px;padding:0 12px;border-radius:12px;border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8}
.archive-workbench{display:grid;grid-template-columns:minmax(280px,320px) minmax(320px,360px) minmax(420px,1fr);gap:10px;align-items:stretch;flex:1;min-height:0;height:auto}
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
.detail-scroll{height:100%;overflow:auto;padding-right:4px;align-content:start}
.records-box{overflow:hidden}
.records-box .detail-header{align-items:center}
.record-section{display:grid;gap:10px;padding:14px 16px;border-radius:16px;background:rgba(8,27,32,.72)}
.record-section-header{display:flex;align-items:center;justify-content:space-between;gap:12px}
.record-section-header strong{font-size:17px;line-height:1.35;color:#f1f7f8}
.record-section-header span{font-size:14px;line-height:1.4;color:#8fb0b8}
.record-section-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.record-entry-list{display:grid;gap:10px}
.record-entry-card{padding:12px 14px;border-radius:14px;border:1px solid rgba(164,215,210,.12);background:rgba(10,33,39,.88);font-size:16px;line-height:1.7;color:#d7e5e8;word-break:break-word}
.record-empty{margin:0;font-size:15px;line-height:1.6;color:#8ea9af}
.immunization-editor{display:grid;gap:8px;margin-top:12px}
.bulk-inline-editor{display:grid;gap:12px;margin-top:12px}
.compact-btn{height:32px;padding:0 12px;border-radius:10px;font-size:13px}
.compact-textarea{min-height:88px}
.record-tip{color:#8ea9af;font-size:13px;line-height:1.5}
.history-list{max-height:260px;overflow:auto;padding-right:4px;gap:14px}
.history-list-modal{max-height:min(62vh,680px);padding-right:8px}
.history-modal-card{width:min(860px,100%)}
.history-filter-row{display:flex;gap:8px;flex-wrap:wrap}
.history-item{display:grid;gap:10px;padding:18px 20px;border:1px solid rgba(164,215,210,.12)}
.history-field{font-size:18px;line-height:1.35;color:#f1f7f8;font-weight:700}
.history-change{font-size:17px;line-height:1.75;color:#d3e1e4;word-break:break-word;display:flex;align-items:flex-start;gap:8px;flex-wrap:wrap}
.history-change.compact{display:grid;gap:6px}
.history-change-label{font-size:14px;line-height:1.3;color:#8fb0b8;letter-spacing:.08em;text-transform:uppercase}
.history-change-value{font-size:17px;line-height:1.7;color:#dce8ea;white-space:pre-wrap}
.history-arrow{display:inline-block;margin:0 8px;color:#9ac8bf;font-weight:700}
.history-time{font-size:15px;line-height:1.5;color:#8fb0b8}
.inline-actions{flex-wrap:wrap}
.empty-state{flex:1;display:flex;align-items:center;justify-content:center;padding:18px;border-radius:16px;border:1px dashed rgba(164,215,210,.18);background:rgba(8,27,32,.58);color:#8ea9af;text-align:center}
.detail-empty{height:100%}
.modal-mask{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(2,10,13,.66);backdrop-filter:blur(8px);z-index:30}
.modal-card{width:min(760px,100%);display:grid;gap:16px;padding:22px;border-radius:24px;background:rgba(9,27,32,.98);border:1px solid rgba(176,224,221,.14);box-shadow:0 24px 60px rgba(0,0,0,.35)}
.modal-tip{margin:8px 0 0;color:#90afb5;font-size:14px;line-height:1.5}
.bulk-form-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.bulk-targets{display:grid;gap:10px;padding:14px 16px;border-radius:16px;background:rgba(8,27,32,.72)}
.bulk-filter-row{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.bulk-filter-row input,.bulk-filter-row select{height:40px;padding:0 12px;border-radius:12px;border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8}
.bulk-target-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;max-height:220px;overflow:auto;padding-right:4px}
.bulk-target-item{display:grid;grid-template-columns:auto minmax(0,1fr);align-items:center;gap:10px;padding:10px 12px;border-radius:12px;border:1px solid rgba(164,215,210,.12);background:rgba(10,33,39,.88);cursor:pointer}
.bulk-target-item input{width:16px;height:16px;margin:0}
.bulk-target-code{font-size:15px;color:#eef7f7;line-height:1.4}
.bulk-target-item small{grid-column:2;color:#8ea9af;font-size:13px;line-height:1.4}
.bulk-textarea{min-height:110px;padding:12px;border-radius:12px;border:1px solid rgba(164,215,210,.18);background:rgba(12,43,49,.94);color:#eff7f8;resize:vertical}
.primary-btn,.ghost-btn,.danger-btn{height:36px;padding:0 14px;border-radius:12px;cursor:pointer}
.primary-btn{border:none;background:linear-gradient(135deg,#4fa98f,#2f7f6d);color:#fff}
.ghost-btn{border:1px solid rgba(164,215,210,.18);background:transparent;color:#eaf3f5}
.ghost-btn.active{border-color:rgba(95,211,188,.32);background:rgba(95,211,188,.1)}
.danger-btn{border:none;background:linear-gradient(135deg,#b45454,#8d2e2e);color:#fff}
.primary-btn:disabled,.ghost-btn:disabled,.danger-btn:disabled{opacity:.6;cursor:not-allowed}
@media (max-width:1500px){
  .archive-workbench{grid-template-columns:minmax(260px,320px) minmax(320px,1fr)}
  .detail-column{grid-column:1 / -1}
}
@media (max-width:1200px){
  .summary-grid,.form-grid,.animal-form-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .context-strip{grid-template-columns:1fr}
  .archive-workbench{grid-template-columns:1fr;height:auto;min-height:auto}
  .workbench-column{min-height:420px}
  .filter-row,
  .bulk-filter-row{grid-template-columns:1fr}
}
@media (max-width:720px){
  .summary-grid,.form-grid,.animal-form-grid{grid-template-columns:1fr}
  .bulk-target-list{grid-template-columns:1fr}
}
@media (max-width:900px){
  .modal-mask{align-items:end;padding:0}
  .modal-card,
  .history-modal-card{
    width:100%;
    max-height:88vh;
    overflow:auto;
    border-radius:24px 24px 0 0;
    padding:20px 18px 26px;
  }
}
</style>

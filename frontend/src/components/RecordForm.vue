<script setup>
import { computed } from 'vue'

import FormField from './FormField.vue'
import { blankRow, isEditable, isRequired, isShown, ruleValues } from '../forms'

// The fields of a record form, in the DocType's sections. `values` is edited in place.
const props = defineProps({
  form: { type: Object, required: true },
  values: { type: Object, required: true },
  currency: { type: String, default: null },
})

const rules = computed(() => ruleValues(props.form, props.values))
const sections = computed(() =>
  props.form.layout
    .filter((section) => isShown(section, rules.value))
    .map((section) => ({ ...section, fields: section.fields.filter((field) => isShown(field, rules.value)) }))
    .filter((section) => section.fields.length),
)
const shownColumns = (field) => (field.columns ?? []).filter((column) => column.fieldtype !== 'Table')
const rowRules = (row) => ({ ...rules.value, ...row })
const addRow = (field) => props.values[field.fieldname].push(blankRow(field))
const removeRow = (field, index) => props.values[field.fieldname].splice(index, 1)
</script>

<template>
  <div class="rf">
    <section v-for="(section, index) in sections" :key="index" class="bj-section">
      <h2 v-if="section.label">{{ section.label }}</h2>
      <div class="page__card bj-card rf__grid">
        <template v-for="field in section.fields" :key="field.fieldname">
          <div v-if="field.fieldtype === 'Table'" class="rf__table">
            <p class="rf__table-title">{{ field.label }}</p>
            <p v-if="!values[field.fieldname]?.length" class="bj-muted">No rows.</p>
            <div v-else class="bj-table-wrap">
              <table class="bj-table bj-table--stack">
                <thead>
                  <tr>
                    <th scope="col">No.</th>
                    <th v-for="column in shownColumns(field)" :key="column.fieldname" scope="col">{{ column.label }}</th>
                    <th v-if="field.editable" scope="col"><span class="rf__sr">Remove</span></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rowIndex) in values[field.fieldname]" :key="row.name || rowIndex">
                    <td data-label="No.">{{ rowIndex + 1 }}</td>
                    <td v-for="column in shownColumns(field)" :key="column.fieldname" :data-label="column.label">
                      <FormField
                        v-if="isShown(column, rowRules(row))"
                        v-model="row[column.fieldname]"
                        :field="column"
                        :values="rowRules(row)"
                        :editable="isEditable(column, rowRules(row))"
                        :required="isRequired(column, rowRules(row))"
                        :currency="currency"
                        :label="`${column.label}, row ${rowIndex + 1}`"
                        compact
                      />
                      <span v-else class="bj-muted">—</span>
                    </td>
                    <td v-if="field.editable">
                      <button type="button" class="bj-btn bj-btn--icon" :aria-label="`Remove ${field.label} row ${rowIndex + 1}`" @click="removeRow(field, rowIndex)">
                        <span class="lucide-trash-2" aria-hidden="true" />
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <button v-if="field.editable" type="button" class="bj-btn rf__add" @click="addRow(field)">
              <span class="lucide-plus" aria-hidden="true" />Add {{ field.label.toLowerCase() }} row
            </button>
          </div>
          <FormField
            v-else
            v-model="values[field.fieldname]"
            :field="field"
            :values="rules"
            :editable="isEditable(field, rules)"
            :required="isRequired(field, rules)"
            :currency="currency"
            :doctype="form.doctype"
            :docname="form.name"
          />
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.rf__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px 20px;
}
.rf__table {
  grid-column: 1 / -1;
}
.rf__table-title {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--bj-muted);
}
.rf__add {
  margin-top: 12px;
}
.rf__sr {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
</style>

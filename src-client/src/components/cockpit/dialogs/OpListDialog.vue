<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" maximized transition-show="slide-up" transition-hide="slide-down">
    <q-card>
      <q-bar class="vemag-bg-primary text-white">
        <q-icon name="list" />
        <div class="text-h6 q-ml-sm">Ordens de Produção Liberadas (SAP)</div>
        <q-space />
        <q-btn dense flat icon="close" v-close-popup />
      </q-bar>

      <q-card-section class="q-pa-none">
        <q-table :rows="rows" :columns="columns" row-key="op_number" :loading="loading" flat bordered separator="cell">
          <template v-slot:body="props">
            <q-tr @click="$emit('select-op', props.row)" class="cursor-pointer hover-bg-grey-3">
              <q-td key="op_number" :props="props">
                <div class="text-weight-bold text-subtitle1">{{ props.row.op_number }}</div>
                <div class="text-caption text-grey-7" v-if="props.row.custom_ref">Ref: {{ props.row.custom_ref }}</div>
              </q-td>
              <q-td key="part_name" :props="props">
                <div class="text-weight-medium">{{ props.row.part_name }}</div>
                <div class="text-caption text-blue-grey">{{ props.row.item_code }}</div>
              </q-td>
              <q-td key="planned_qty" :props="props" class="text-center text-weight-bold">
                {{ props.row.planned_qty }} {{ props.row.uom }}
              </q-td>
              <q-td key="action" :props="props" class="text-center">
                <q-btn round color="secondary" icon="arrow_forward" size="sm" />
              </q-td>
            </q-tr>
          </template>
          <template v-slot:no-data>
            <div class="full-width row flex-center q-pa-md text-grey">
              <q-icon name="warning" size="sm" class="q-mr-sm" /> Nenhuma O.P. liberada encontrada no SAP.
            </div>
          </template>
        </q-table>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
defineProps<{ modelValue: boolean; rows: any[]; loading: boolean; columns: any[] }>();
defineEmits(['update:modelValue', 'select-op']);
</script>

<style scoped>
.vemag-bg-primary { background-color: #008C7A !important; }
.hover-bg-grey-3:hover { background-color: #eeeeee; }
</style>
<template>
  <q-dialog :model-value="modelValue" @update:model-value="val => emit('update:modelValue', val)">
    <q-card style="width: 900px; max-width: 90vw;" v-if="part">
      <q-card-section class="row items-center bg-grey-2">
        <div class="text-h6">Kardex: {{ part.name }}</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section>
        <q-table
          :rows="displayedHistory"
          :columns="historyColumns"
          row-key="id"
          :loading="partStore.isHistoryLoading"
          no-data-label="Nenhuma movimentação registrada."
          flat bordered dense
          separator="cell"
          :hide-bottom="isDemo && partStore.selectedPartHistory.length > demoLimit"
        >
          <template v-slot:body-cell-transaction_type="props">
             <q-td :props="props">
                <q-badge 
                    :color="getTransactionColor(props.value)" 
                    text-color="white"
                    :label="props.value"
                />
             </q-td>
          </template>

          <template v-slot:body-cell-item_code="props">
            <q-td :props="props">
              <span v-if="props.value" class="text-mono text-grey-8">#{{ props.value }}</span>
              <span v-else class="text-grey-5">-</span>
            </q-td>
          </template>
        </q-table>

        <div v-if="isDemo && partStore.selectedPartHistory.length > demoLimit" class="q-pa-md text-center bg-grey-1 rounded-borders q-mt-md">
          <div class="text-weight-bold text-grey-8 q-mb-xs">
            <q-icon name="lock" /> Histórico Completo Bloqueado
          </div>
          <div class="text-caption q-mb-sm">
            O plano Demo exibe apenas as últimas {{ demoLimit }} movimentações.
          </div>
          <q-btn 
            outline 
            color="primary" 
            label="Ver Planos PRO" 
            size="sm" 
            @click="showUpgradeInfo"
          />
        </div>

      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useQuasar } from 'quasar';
import { usePartStore } from 'stores/part-store';
import { useAuthStore } from 'stores/auth-store'; 
import type { Part } from 'src/models/part-models';
import type { QTableProps } from 'quasar';
import { format } from 'date-fns';

defineProps<{ modelValue: boolean, part: Part | null }>();
const emit = defineEmits(['update:modelValue']);

const $q = useQuasar();
const partStore = usePartStore();
const authStore = useAuthStore();

const isDemo = computed(() => authStore.user?.role === 'cliente_demo');
const demoLimit = 5;

const displayedHistory = computed(() => {
  if (!isDemo.value) return partStore.selectedPartHistory;
  return partStore.selectedPartHistory.slice(0, demoLimit);
});

function showUpgradeInfo() {
  $q.dialog({
    title: 'Auditoria Profissional',
    message: 'Tenha rastreabilidade total de cada peça com o plano PRO.',
    ok: { label: 'Entendido', color: 'primary' }
  });
}

function getTransactionColor(type: string) {
    if (type.includes('Entrada') || type.includes('Compra')) return 'positive';
    if (type.includes('Saída') || type.includes('Consumo')) return 'negative';
    return 'primary';
}

const historyColumns: QTableProps['columns'] = [
  { 
    name: 'timestamp', 
    label: 'Data/Hora', 
    field: 'timestamp', 
    sortable: true, 
    align: 'left', 
    format: (val) => format(new Date(val), 'dd/MM/yyyy HH:mm'),
    style: 'width: 140px'
  },
  { 
    name: 'transaction_type', 
    label: 'Movimento', 
    field: 'transaction_type', 
    sortable: true, 
    align: 'center',
    style: 'width: 120px'
  },
  { 
    name: 'item_code', 
    label: 'ID Serial', 
    field: (row) => row.item?.item_identifier, 
    align: 'center',
    style: 'width: 100px'
  }, 
  { 
    name: 'user', 
    label: 'Responsável', 
    field: (row) => row.user?.full_name || 'Sistema', 
    align: 'left' 
  },
  { 
    name: 'notes', 
    label: 'Justificativa / OS', 
    field: 'notes', 
    align: 'left', 
    style: 'white-space: pre-wrap; min-width: 200px;' 
  },
];
</script>
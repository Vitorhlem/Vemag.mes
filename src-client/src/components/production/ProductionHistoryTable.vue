<template>
  <div class="column full-height q-pa-sm">
    <q-card flat bordered class="bg-white q-mb-md">
      <q-card-section class="row items-center q-gutter-sm wrap">
        
        <q-select 
          outlined dense 
          v-model="filterType" 
          :options="typeOptions" 
          label="Filtrar por Tipo" 
          style="min-width: 220px" 
          clearable
          emit-value map-options
          bg-color="white"
          @update:model-value="resetAndFetch"
        >
          <template v-slot:prepend><q-icon name="filter_list" /></template>
        </q-select>

        <q-input 
          outlined dense 
          v-model="searchText" 
          debounce="300" 
          placeholder="Buscar operador ou motivo..." 
          bg-color="white"
          class="col-grow"
        >
          <template v-slot:prepend><q-icon name="search" /></template>
        </q-input>

        <q-separator vertical class="q-mx-sm mobile-hide" inset />

        <q-btn 
          outline color="secondary" 
          icon="file_download" 
          label="Exportar CSV" 
          @click="exportTable" 
          :disable="rows.length === 0"
        />
        
        <q-btn 
          flat round 
          :icon="isDense ? 'density_medium' : 'density_small'" 
          :color="isDense ? 'primary' : 'grey-7'" 
          @click="isDense = !isDense" 
        >
          <q-tooltip>Alternar Densidade</q-tooltip>
        </q-btn>

        <q-btn flat round icon="refresh" color="primary" @click="resetAndFetch" :loading="loading">
           <q-tooltip>Recarregar Dados</q-tooltip>
        </q-btn>
      </q-card-section>
    </q-card>

    <q-table
      class="my-sticky-header-table shadow-1"
      :rows="filteredRows"
      :columns="columns"
      row-key="id"
      :loading="loading"
      flat bordered
      :dense="isDense"
      v-model:pagination="pagination"
      @request="onRequest"
      binary-state-sort
      no-data-label="Nenhum registro encontrado para os filtros atuais."
    >
      <template v-slot:header="props">
        <q-tr :props="props">
          <q-th v-for="col in props.cols" :key="col.name" :props="props" class="text-primary text-weight-bold">
            {{ col.label }}
          </q-th>
        </q-tr>
      </template>

      <template v-slot:body-cell-timestamp="props">
        <q-td :props="props">
          <div class="row items-center no-wrap">
             <q-icon name="event" color="grey-6" size="xs" class="q-mr-xs" />
             <span class="font-monospace text-grey-9">{{ props.value }}</span>
          </div>
        </q-td>
      </template>

      <template v-slot:body-cell-event_type="props">
        <q-td :props="props">
          <q-chip 
            dense 
            outline 
            :color="getTypeColor(props.value)" 
            :icon="getTypeIcon(props.value)"
            class="text-weight-bold"
          >
            {{ formatEventType(props.value) }}
          </q-chip>
        </q-td>
      </template>

      <template v-slot:body-cell-operator_name="props">
        <q-td :props="props">
          
          <div v-if="props.row.operator_id" class="row items-center no-wrap">
             <q-avatar size="24px" class="q-mr-sm vemag-bg-primary text-white" style="font-size: 10px">
                {{ props.value ? props.value.charAt(0).toUpperCase() : 'U' }}
             </q-avatar>
             
             <div class="column">
                <router-link 
                  :to="`/users/${props.row.operator_id}/stats`"
                  class="text-primary text-weight-bold hover-underline"
                  style="text-decoration: none; cursor: pointer;"
                >
                  {{ props.value }}
                </router-link>
                
                <div class="text-caption text-grey-6" style="font-size: 0.7em; line-height: 1;">
                  {{ props.row.operator_badge || 'Crachá N/A' }}
                </div>
             </div>
          </div>

          <div v-else class="row items-center no-wrap">
             <q-avatar size="24px" color="grey-3" text-color="grey-7" icon="smart_toy" class="q-mr-sm"/>
             <span class="text-grey-8 font-italic">{{ props.value || 'Sistema' }}</span>
          </div>

        </q-td>
      </template>

      <template v-slot:body-cell-status="props">
        <q-td :props="props">
          <div v-if="props.row.event_type === 'STATUS_CHANGE' || props.row.new_status">
             <span class="text-weight-bold" :class="getStatusTextColor(props.row.new_status)">
                {{ props.row.new_status }}
             </span>
             <div v-if="props.row.reason" class="text-caption text-grey-8 bg-grey-2 q-px-sm rounded-borders inline-block q-ml-sm">
                Motivo: {{ props.row.reason }}
             </div>
          </div>
          <div v-else-if="props.row.event_type === 'COUNT'">
             Registrado produção.
          </div>
          <div v-else-if="props.row.event_type === 'ANDON_OPEN'">
             <span class="text-negative text-weight-bold">Chamado Aberto</span>
             <span v-if="props.row.details"> - {{ props.row.details }}</span>
          </div>
          <div v-else>
             {{ props.row.details || '-' }}
          </div>
        </q-td>
      </template>

    </q-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useProductionStore, type ProductionLog } from 'stores/production-store';
import { format } from 'date-fns';
import { exportFile, useQuasar, type QTableColumn } from 'quasar';

const props = defineProps<{ machineId: number }>();
const store = useProductionStore();
const $q = useQuasar();

const loading = ref(false);
const rows = ref<ProductionLog[]>([]);
const filterType = ref<string | null>(null);
const searchText = ref('');
const isDense = ref(false);

const pagination = ref({
  sortBy: 'timestamp',
  descending: true,
  page: 1,
  rowsPerPage: 15,
  rowsNumber: 9999 
});

const typeOptions = [
  { label: 'Mudança de Status', value: 'STATUS_CHANGE' },
  { label: 'Produção (Apontamento)', value: 'COUNT' },
  { label: 'Alertas (Andon)', value: 'ANDON_OPEN' },
  { label: 'Acesso (Login/Logout)', value: 'LOGIN' }
];

const columns: QTableColumn[] = [
  { name: 'timestamp', label: 'Data/Hora', field: 'timestamp', format: (val: string) => format(new Date(val), 'dd/MM/yyyy HH:mm:ss'), align: 'left', sortable: true },
  { name: 'event_type', label: 'Evento', field: 'event_type', align: 'left', sortable: true },
  { name: 'operator_name', label: 'Operador', field: 'operator_name', align: 'left', sortable: true },
  { name: 'operator', label: 'Operador', align: 'left', field: 'operator_name', sortable: true },
  { name: 'status', label: 'Detalhes & Status', field: 'new_status', align: 'left' },
  { name: 'details', label: 'Observações', field: 'details', align: 'left' }
];

const filteredRows = computed(() => {
   if (!searchText.value) return rows.value;
   const lower = searchText.value.toLowerCase();
   return rows.value.filter(r => 
      JSON.stringify(r).toLowerCase().includes(lower)
   );
});

function formatEventType(type: string) {
   const map: Record<string, string> = { 
      'STATUS_CHANGE': 'Status', 
      'LOGIN': 'Acesso', 
      'LOGOUT': 'Saída', 
      'COUNT': 'Produção', 
      'ANDON_OPEN': 'Andon' 
   };
   return map[type] || type;
}

function getTypeColor(type: string) {
   if (type === 'ANDON_OPEN') return 'purple';
   if (type === 'STATUS_CHANGE') return 'blue-grey';
   if (type === 'COUNT') return 'positive';
   if (type === 'LOGIN' || type === 'LOGOUT') return 'teal';
   return 'primary';
}

function getTypeIcon(type: string) {
   if (type === 'ANDON_OPEN') return 'campaign';
   if (type === 'STATUS_CHANGE') return 'sync_alt';
   if (type === 'COUNT') return 'add_circle';
   if (type === 'LOGIN') return 'login';
   return 'info';
}

function getStatusTextColor(status?: string) {
   if (!status) return 'text-dark';
   if (status === 'RUNNING' || status === 'IN_USE') return 'text-positive';
   if (status === 'STOPPED' || status === 'MAINTENANCE') return 'text-negative';
   if (status === 'SETUP') return 'text-orange-9';
   return 'text-dark';
}

async function onRequest(reqProps: { pagination: { page: number; rowsPerPage: number } }) {
  const { page, rowsPerPage } = reqProps.pagination;
  loading.value = true;
  const skip = (page - 1) * rowsPerPage;
  
  try {
    const data = await store.fetchMachineHistory(props.machineId || 1, {
      skip: skip,
      limit: rowsPerPage,
      event_type: filterType.value || undefined
    });
    
    rows.value = data;
    
    pagination.value.page = page;
    pagination.value.rowsPerPage = rowsPerPage;
    if (data.length < rowsPerPage) {
       pagination.value.rowsNumber = skip + data.length;
    } else {
       pagination.value.rowsNumber = skip + data.length + 1; 
    }
  } catch (error) {
     console.error(error);
     $q.notify({ type: 'negative', message: 'Erro ao carregar histórico.' });
  } finally {
    loading.value = false;
  }
}

function resetAndFetch() {
  pagination.value.page = 1;
  void onRequest({ pagination: pagination.value });
}

// CORREÇÃO: Tipagem e lógica segura de conversão para string
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function wrapCsvValue(val: unknown, formatFn?: (v: any, r?: any) => any) {
  // Passamos 'val' direto. O segundo argumento do formatFn (row) vai como undefined pois no CSV tratamos celula a celula
  let formatted = formatFn !== undefined ? formatFn(val, undefined) : val;
  
  if (formatted === undefined || formatted === null) {
    formatted = '';
  }
  
  const safeStr = String(formatted);
  const result = safeStr.split('"').join('""');
  return `"${result}"`;
}

function exportTable() {
  if (rows.value.length === 0) return;

  // 1. Gera o cabeçalho
  const header = columns.map(col => wrapCsvValue(col.label)).join(',');

  // 2. Gera as linhas de dados
  const body = rows.value.map(row => {
    return columns.map(col => {
      // Type assertion para acessar dinamicamente
      const rowData = row as Record<string, unknown>;
      
      // Acessa valor do campo
      const fieldVal = typeof col.field === 'function' 
        ? col.field(row) 
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-type-assertion
        : rowData[col.field as string];
      
      // CORREÇÃO: Agora o TypeScript aceita col.format porque as assinaturas batem
      return wrapCsvValue(fieldVal, col.format);
    }).join(',');
  }).join('\r\n');

  // 3. Junta tudo
  const content = `${header}\r\n${body}`;

  const status = exportFile(
    `historico_producao_maq_${props.machineId}_${format(new Date(), 'yyyyMMdd')}.csv`,
    '\ufeff' + content,
    'text/csv'
  );

  if (status !== true) {
    $q.notify({ message: 'Navegador bloqueou o download...', color: 'negative', icon: 'warning' });
  }
}

onMounted(() => {
  resetAndFetch();
});
</script>

<style scoped>
.font-monospace {
   font-family: 'Consolas', 'Monaco', monospace;
   font-size: 0.9em;
}
.my-sticky-header-table {
  max-height: calc(100vh - 180px); 
}
.hover-underline:hover {
  text-decoration: underline !important;
}
</style>
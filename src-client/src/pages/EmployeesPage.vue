<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<template>
  <q-page class="bg-grey-1 column no-wrap" style="height: 100vh; overflow: hidden;">
    
    <div class="bg-white q-py-sm q-px-md border-bottom-light row items-center justify-between shadow-1" style="height: 60px; z-index: 10;">
      <div class="row items-center q-gutter-x-md">
        <div class="bg-primary text-white rounded-borders q-pa-xs"><q-icon name="analytics" size="sm" /></div>
        <div>
          <div class="text-subtitle1 text-weight-bold lh-small">Workforce Intelligence</div>
          <div class="text-caption text-grey-7 lh-small">Análise de Performance Operacional</div>
        </div>
      </div>

      <div class="row items-center q-gutter-x-sm">
        <q-input dense outlined v-model="dateRangeDisplay" readonly class="cursor-pointer bg-grey-1" style="min-width: 240px">
          <template v-slot:prepend><q-icon name="date_range" color="primary" /></template>
          <q-popup-proxy cover transition-show="scale" transition-hide="scale">
            <q-date v-model="dateRange" range mask="YYYY-MM-DD">
              <div class="row items-center justify-end">
                <q-btn v-close-popup label="Filtrar" color="primary" flat @click="loadList" />
              </div>
            </q-date>
          </q-popup-proxy>
        </q-input>

        <q-btn icon="refresh" flat round color="primary" @click="loadList" :loading="loadingList">
           <q-tooltip>Atualizar Dados</q-tooltip>
        </q-btn>
      </div>
    </div>

    <q-splitter v-model="splitterModel" class="col-grow">

      <template v-slot:before>
        <div class="column full-height bg-white">
          <div class="q-pa-sm border-bottom-light bg-grey-1">
            <q-input dense outlined v-model="search" placeholder="Buscar por nome..." clearable bg-color="white">
              <template v-slot:prepend><q-icon name="person_search" /></template>
            </q-input>
          </div>
          
          <q-scroll-area class="col">
            <q-list separator>
              <q-item 
                v-for="emp in filteredEmployees" :key="emp.employee_name" 
                clickable v-ripple 
                :active="selectedEmpSummary?.employee_name === emp.employee_name"
                active-class="bg-blue-1 text-primary border-left-active"
                class="q-py-md transition-hover"
                @click="selectEmployee(emp)"
              >
                <q-item-section avatar>
                  <q-avatar size="42px" font-size="16px" :color="getEfficiencyColorBg(emp.efficiency)" :text-color="getEfficiencyColorText(emp.efficiency)">
                    {{ getInitials(emp.employee_name) }}
                  </q-avatar>
                </q-item-section>
                
                <q-item-section>
                  <div class="text-weight-bold text-body2">{{ emp.employee_name }}</div>
                  <div class="row items-center no-wrap q-gutter-x-xs text-caption text-grey-7">
                    <q-icon name="timer" size="xs" />
                    <span>{{ emp.total_hours }}h registradas</span>
                  </div>
                </q-item-section>

                <q-item-section side>
                  <div class="column items-end">
                    <div class="text-weight-bolder text-subtitle2" :class="getEfficiencyColorText(emp.efficiency)">{{ emp.efficiency }}%</div>
                  </div>
                </q-item-section>
              </q-item>
              
              <div v-if="filteredEmployees.length === 0 && !loadingList" class="text-center q-pa-lg text-grey">
                 Nenhum colaborador encontrado neste período.
              </div>
            </q-list>
          </q-scroll-area>
        </div>
      </template>

      <template v-slot:after>
        <div v-if="loadingDetail" class="flex flex-center full-height">
           <q-spinner-dots size="4em" color="primary" />
        </div>

        <div v-else-if="detailData" class="full-height column bg-grey-1 scroll">
          
          <div class="bg-white q-pa-md shadow-1 q-mb-md">
            <div class="row items-center justify-between">
              <div>
                <div class="text-h4 text-weight-bolder text-dark">{{ selectedEmpSummary?.employee_name }}</div>
                <div class="text-caption text-grey-8">Relatório Consolidado • {{ dateRangeDisplay }}</div>
              </div>
              
              <div class="row q-gutter-md">
                 <q-card flat bordered class="bg-green-1">
                    <q-card-section class="q-py-xs text-center">
                       <div class="text-h6 text-positive">{{ detailData.productive_hours }}h</div>
                       <div class="text-caption text-uppercase text-positive">Produtivas</div>
                    </q-card-section>
                 </q-card>
                 <q-card flat bordered class="bg-red-1">
                    <q-card-section class="q-py-xs text-center">
                       <div class="text-h6 text-negative">{{ detailData.unproductive_hours }}h</div>
                       <div class="text-caption text-uppercase text-negative">Paradas</div>
                    </q-card-section>
                 </q-card>
                 <q-card flat bordered class="bg-grey-1">
                    <q-card-section class="q-py-xs text-center">
                       <div class="text-h6 text-dark">{{ detailData.total_hours }}h</div>
                       <div class="text-caption text-uppercase text-dark">Totais</div>
                    </q-card-section>
                 </q-card>
              </div>
            </div>
            
            <q-separator class="q-my-md" />
            
            <div>
               <div class="row justify-between text-caption q-mb-xs">
                  <span>Eficiência Global do Período</span>
                  <span class="text-weight-bold">{{ detailData.efficiency }}%</span>
               </div>
               <q-linear-progress :value="detailData.efficiency / 100" size="10px" rounded :color="getEfficiencyColor(detailData.efficiency)" class="bg-grey-3" />
            </div>
          </div>

          <div class="q-px-md q-pb-md col-grow column q-gutter-y-md">
            
            <div class="row q-col-gutter-md">
              <div class="col-12 col-md-4">
                <q-card class="full-height shadow-1 column">
                  <q-card-section class="bg-white border-bottom-light">
                    <div class="text-subtitle1 text-weight-bold row items-center">
                       <q-icon name="warning" class="q-mr-sm text-orange" /> 
                       Top Motivos de Parada
                    </div>
                  </q-card-section>
                  <q-card-section class="col scroll">
                    <div v-if="detailData.top_reasons.length > 0">
                       <q-list separator>
                          <q-item v-for="(reason, idx) in detailData.top_reasons" :key="idx" class="q-px-none">
                             <q-item-section>
                                <q-item-label class="text-weight-bold">{{ reason.label }}</q-item-label>
                             </q-item-section>
                             <q-item-section side>
                                <q-badge color="grey-3" text-color="dark">{{ reason.count }} ocorrências</q-badge>
                             </q-item-section>
                          </q-item>
                       </q-list>
                    </div>
                    <div v-else class="flex flex-center full-height text-grey column text-center q-pa-md">
                       <q-icon name="thumb_up" size="2em" class="q-mb-sm text-positive" />
                       <div>Nenhuma parada registrada.<br>Operação 100% fluida ou sem dados.</div>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <div class="col-12 col-md-8">
                <q-card class="full-height shadow-1 column">
                   <q-card-section class="bg-white border-bottom-light row items-center justify-between">
                      <div class="text-subtitle1 text-weight-bold row items-center">
                         <q-icon name="history" class="q-mr-sm text-primary" /> 
                         Histórico de Sessões de Trabalho
                      </div>
                      <q-chip dense color="blue-1" text-color="primary">{{ detailData.sessions.length }} Sessões</q-chip>
                   </q-card-section>
                   
                   <q-card-section class="q-pa-none col">
                      <q-table
                         :rows="detailData.sessions"
                         :columns="sessionColumns"
                         row-key="id"
                         flat
                         :pagination="{ rowsPerPage: 0 }"
                         hide-bottom
                         class="sticky-header-table full-height"
                         no-data-label="Nenhuma sessão de trabalho encontrada."
                      >
                         <template v-slot:body-cell-status="props">
                            <q-td :props="props">
                               <q-chip v-if="!props.row.end_time" color="green-1" text-color="green-9" dense icon="sync" label="Em Andamento" />
                               <q-chip v-else color="grey-2" text-color="grey-8" dense icon="check" label="Finalizada" />
                            </q-td>
                         </template>
                         
                         <template v-slot:body-cell-efficiency="props">
                            <q-td :props="props" style="width: 150px">
                               <div class="row items-center no-wrap">
                                  <span class="q-mr-xs text-caption text-weight-bold">{{ props.value }}%</span>
                                  <q-linear-progress :value="props.value / 100" rounded size="6px" :color="getEfficiencyColor(props.value)" class="col" />
                               </div>
                            </q-td>
                         </template>
                      </q-table>
                   </q-card-section>
                </q-card>
              </div>
            </div>

          </div>
        </div>

        <div v-else class="flex flex-center full-height bg-grey-1 text-grey-5">
           <div class="text-center">
              <q-icon name="engineering" size="6rem" color="grey-4" />
              <div class="text-h5 text-grey-6 q-mt-md">Selecione um Colaborador</div>
              <div>Use a lista à esquerda para analisar a produtividade detalhada.</div>
           </div>
        </div>
      </template>

    </q-splitter>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { api } from 'boot/axios';
import { useQuasar, date, type QTableColumn } from 'quasar';

const $q = useQuasar();
const splitterModel = ref(28); 
const loadingList = ref(false);
const loadingDetail = ref(false);
const search = ref('');

// Data padrão: Últimos 30 dias
const today = new Date();
const thirtyDaysAgo = date.subtractFromDate(today, { days: 30 });
const dateRange = ref({ 
  from: date.formatDate(thirtyDaysAgo, 'YYYY-MM-DD'), 
  to: date.formatDate(today, 'YYYY-MM-DD') 
});

interface EmployeeSummary {
  employee_name: string;
  total_hours: number;
  efficiency: number;
}

// Interface auxiliar para garantir tipagem no fallback de busca
interface EmployeeWithId extends EmployeeSummary {
    user_id?: number;
    id?: number;
}

interface EmployeeDetail {
  total_hours: number;
  productive_hours: number;
  unproductive_hours: number;
  efficiency: number;
  top_reasons: { label: string; count: number }[];
  sessions: {
     id: number;
     machine_name: string;
     order_code: string;
     start_time: string;
     end_time: string | null;
     duration: string;
     efficiency: number;
  }[];
}

const employeesList = ref<EmployeeSummary[]>([]);
const selectedEmpSummary = ref<EmployeeSummary | null>(null);
const detailData = ref<EmployeeDetail | null>(null);

const dateRangeDisplay = computed(() => {
   if (typeof dateRange.value === 'string') return dateRange.value;
   return `${date.formatDate(dateRange.value.from, 'DD/MM/YYYY')} até ${date.formatDate(dateRange.value.to, 'DD/MM/YYYY')}`;
});

const filteredEmployees = computed(() => {
   if (!search.value) return employeesList.value;
   const lower = search.value.toLowerCase();
   return employeesList.value.filter(e => e.employee_name.toLowerCase().includes(lower));
});

const sessionColumns: QTableColumn[] = [
   { name: 'status', label: 'Status', field: 'end_time', align: 'left' },
   { name: 'start_time', label: 'Início', field: 'start_time', format: val => date.formatDate(val, 'DD/MM HH:mm'), align: 'left', sortable: true },
   { name: 'machine_name', label: 'Máquina', field: 'machine_name', align: 'left' },
   { name: 'order_code', label: 'Ordem Prod.', field: 'order_code', align: 'left' },
   { name: 'duration', label: 'Duração', field: 'duration', align: 'right' },
   { name: 'efficiency', label: 'Eficiência', field: 'efficiency', align: 'right', sortable: true },
];

async function loadList() {
  loadingList.value = true;
  try {
    // Corrigido: const
    const start = typeof dateRange.value === 'string' ? dateRange.value : dateRange.value.from;
    const end = typeof dateRange.value === 'string' ? dateRange.value : dateRange.value.to;

    const { data } = await api.get<EmployeeSummary[]>('/production/stats/employees', {
       params: { start_date: start, end_date: end }
    });
    employeesList.value = data;
    
    if (selectedEmpSummary.value) {
       await selectEmployee(selectedEmpSummary.value);
    }
  } catch (error) {
    console.error(error);
    $q.notify({ type: 'negative', message: 'Erro ao carregar lista.' });
  } finally {
    loadingList.value = false;
  }
}

async function selectEmployee(emp: EmployeeSummary) {
   selectedEmpSummary.value = emp;
   loadingDetail.value = true;
   detailData.value = null; 
   
   try {
      // Corrigido: const e prefer-const
      const start = typeof dateRange.value === 'string' ? dateRange.value : dateRange.value.from;
      const end = typeof dateRange.value === 'string' ? dateRange.value : dateRange.value.to;
      
      const empWithId = emp as EmployeeWithId;
      const uid = empWithId.user_id || empWithId.id; 
      
      if (uid) {
         const { data } = await api.get(`/production/stats/employee/${uid}/details`, {
            params: { start_date: start, end_date: end }
         });
         detailData.value = data;
      } else {
         // eslint-disable-next-line @typescript-eslint/no-explicit-any
         const allUsers = (await api.get<any[]>('/users/')).data;
         // Corrigido: Tipagem no find
         const found = allUsers.find((u: { full_name: string; email: string; id: number }) => 
            u.full_name === emp.employee_name || u.email === emp.employee_name
         );
         if (found) {
            const { data } = await api.get(`/production/stats/employee/${found.id}/details`, {
                params: { start_date: start, end_date: end }
            });
            detailData.value = data;
         }
      }

   } catch (error) {
      console.error(error);
      $q.notify({ type: 'negative', message: 'Erro ao carregar detalhes.' });
   } finally {
      loadingDetail.value = false;
   }
}

// ... helpers (mantidos) ...
function getInitials(name: string) {
   if (!name) return '?';
   return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
}

function getEfficiencyColorText(val: number) {
   if(val >= 85) return 'text-positive';
   if(val >= 70) return 'text-warning';
   return 'text-negative';
}

function getEfficiencyColorBg(val: number) {
   if(val >= 85) return 'green-1';
   if(val >= 70) return 'orange-1';
   if(val === 0) return 'grey-2';
   return 'red-1';
}

function getEfficiencyColor(val: number) {
   if(val >= 85) return 'positive';
   if(val >= 70) return 'warning';
   return 'negative';
}

onMounted(loadList);
</script>

<style scoped>
.lh-small { line-height: 1.2; }
.border-bottom-light { border-bottom: 1px solid #e0e0e0; }
.border-left-active { border-left: 4px solid var(--q-primary); }
.transition-hover { transition: background-color 0.2s; }
.sticky-header-table { height: 100%; }
.sticky-header-table :deep(thead tr:first-child th) {
  background-color: #fff;
  position: sticky;
  top: 0;
  z-index: 1;
}
</style>
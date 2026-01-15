<template>
  <q-page class="bg-surface column no-wrap page-container" style="height: 100vh; overflow: hidden;">
    
    <div class="header-bar q-px-md q-py-sm row items-center justify-between shadow-1 bg-white z-top">
      <div class="row items-center q-gutter-x-md">
        <div class="icon-box bg-primary text-white shadow-2">
          <q-icon name="engineering" size="24px" />
        </div>
        <div>
          <div class="text-subtitle1 text-weight-bold text-primary-dark leading-tight">Gestão de Mão de Obra</div>
          <div class="text-caption text-grey-7 leading-tight">Análise de Eficiência Operacional</div>
        </div>
      </div>

      <div class="row items-center q-gutter-x-sm">
        <q-btn outline no-caps class="date-selector bg-grey-1 text-grey-9" :ripple="false">
          <div class="row items-center no-wrap">
            <q-icon name="event" color="primary" size="xs" class="q-mr-sm" />
            <span class="text-weight-medium text-body2">{{ dateRangeDisplay }}</span>
          </div>
          <q-popup-proxy cover transition-show="scale" transition-hide="scale">
            <q-date v-model="dateRange" range mask="YYYY-MM-DD" color="primary">
              <div class="row items-center justify-end q-pa-sm">
                <q-btn v-close-popup label="Aplicar Filtro" color="primary" unelevated @click="loadList" />
              </div>
            </q-date>
          </q-popup-proxy>
        </q-btn>

        <q-separator vertical inset class="q-mx-sm" />

        <q-btn flat round icon="refresh" color="grey-7" @click="loadList" :loading="loadingList">
           <q-tooltip>Atualizar Lista</q-tooltip>
        </q-btn>
      </div>
    </div>

    <q-splitter v-model="splitterModel" class="col-grow" :limits="[20, 40]" separator-class="bg-grey-3" separator-style="width: 1px">

      <template v-slot:before>
        <div class="column full-height bg-white">
          <div class="q-pa-md border-bottom-light bg-grey-1">
            <q-input 
              dense 
              outlined 
              v-model="search" 
              placeholder="Buscar operador..." 
              class="search-input bg-white"
            >
              <template v-slot:prepend><q-icon name="search" color="grey-5" /></template>
              <template v-slot:append v-if="search">
                <q-icon name="close" @click="search = ''" class="cursor-pointer" />
              </template>
            </q-input>
          </div>
          
          <q-scroll-area class="col">
            <q-list separator class="q-py-xs">
              <q-item 
                v-for="emp in filteredEmployees" :key="emp.employee_name" 
                clickable v-ripple 
                :active="selectedEmpSummary?.employee_name === emp.employee_name"
                active-class="active-employee-item"
                class="employee-item q-py-md q-px-md"
                @click="selectEmployee(emp)"
              >
                <q-item-section avatar>
                  <div class="relative-position">
                    <q-avatar size="44px" font-size="16px" :class="getAvatarClass(emp.efficiency)" class="shadow-1">
                      {{ getInitials(emp.employee_name) }}
                    </q-avatar>
                    <q-badge v-if="emp.efficiency >= 85" floating rounded color="positive" class="status-dot border-white" />
                  </div>
                </q-item-section>
                
                <q-item-section>
                  <div class="text-weight-bold text-body2 text-primary-dark">{{ emp.employee_name }}</div>
                  <div class="row items-center no-wrap q-gutter-x-xs text-caption text-grey-6">
                    <q-icon name="history" size="xs" />
                    <span>{{ emp.total_hours }}h totais</span>
                  </div>
                </q-item-section>

                <q-item-section side>
                  <div class="column items-end">
                    <div class="text-weight-bolder text-subtitle1" :class="getEfficiencyColorText(emp.efficiency)">
                      {{ emp.efficiency }}%
                    </div>
                    <div class="text-caption text-grey-5" style="font-size: 10px;">OEE</div>
                  </div>
                </q-item-section>
              </q-item>
              
              <div v-if="filteredEmployees.length === 0 && !loadingList" class="column items-center justify-center q-pa-xl text-grey-5 full-height">
                 <q-icon name="person_off" size="40px" class="q-mb-sm opacity-50" />
                 <div class="text-center">Nenhum operador encontrado.</div>
              </div>
            </q-list>
          </q-scroll-area>
        </div>
      </template>

      <template v-slot:after>
        <div v-if="loadingDetail" class="flex flex-center full-height bg-surface">
           <q-spinner-dots size="4em" color="primary" />
        </div>

        <div v-else-if="!detailData" class="flex flex-center full-height bg-surface text-grey-6 column">
           <div class="bg-white q-pa-xl rounded-borders shadow-1 text-center">
              <q-icon name="assignment_ind" size="64px" color="grey-4" class="q-mb-md" />
              <div class="text-h6 text-weight-regular text-primary-dark">Selecione um Colaborador</div>
              <div class="text-caption q-mt-xs">Clique na lista à esquerda para ver os indicadores de performance.</div>
           </div>
        </div>

        <div v-else class="full-height column bg-surface scroll p-container">
          
          <div class="q-pa-lg">
            <div class="row items-center justify-between q-mb-lg">
              <div>
                <div class="text-h4 text-weight-bolder text-primary-dark q-mb-xs">{{ selectedEmpSummary?.employee_name }}</div>
                <div class="row items-center text-grey-7">
                  <q-icon name="date_range" size="xs" class="q-mr-xs" />
                  <span class="text-caption">Período: <b>{{ dateRangeDisplay }}</b></span>
                </div>
              </div>
              <q-chip outline color="primary" icon="verified" label="Operador Ativo" class="bg-white" />
            </div>
            
            <div class="row q-col-gutter-md">
               <div class="col-12 col-sm-4">
                 <q-card flat class="kpi-card bg-white border-light">
                    <q-card-section class="row items-center no-wrap">
                       <div class="col">
                          <div class="text-caption text-uppercase text-grey-6 text-weight-bold">Horas Totais</div>
                          <div class="text-h4 text-primary-dark q-mt-xs">{{ detailData.total_hours }}<span class="text-h6 text-grey-5">h</span></div>
                       </div>
                       <q-avatar color="blue-1" text-color="primary" icon="schedule" size="lg" />
                    </q-card-section>
                 </q-card>
               </div>
               <div class="col-12 col-sm-4">
                 <q-card flat class="kpi-card bg-white border-light">
                    <q-card-section class="row items-center no-wrap">
                       <div class="col">
                          <div class="text-caption text-uppercase text-positive text-weight-bold">Produtivas</div>
                          <div class="text-h4 text-positive q-mt-xs">{{ detailData.productive_hours }}<span class="text-h6 text-green-2">h</span></div>
                       </div>
                       <q-avatar color="green-1" text-color="positive" icon="precision_manufacturing" size="lg" />
                    </q-card-section>
                 </q-card>
               </div>
               <div class="col-12 col-sm-4">
                 <q-card flat class="kpi-card bg-white border-light">
                    <q-card-section class="row items-center no-wrap">
                       <div class="col">
                          <div class="text-caption text-uppercase text-negative text-weight-bold">Paradas</div>
                          <div class="text-h4 text-negative q-mt-xs">{{ detailData.unproductive_hours }}<span class="text-h6 text-red-2">h</span></div>
                       </div>
                       <q-avatar color="red-1" text-color="negative" icon="warning" size="lg" />
                    </q-card-section>
                 </q-card>
               </div>
            </div>
            
            <q-card flat class="q-mt-md bg-white border-light">
              <q-card-section>
                 <div class="row justify-between items-end q-mb-xs">
                    <div class="row items-center">
                       <span class="text-subtitle1 text-weight-bold text-primary-dark q-mr-sm">Eficiência Global</span>
                       <q-badge :color="getEfficiencyColor(detailData.efficiency)" outline class="text-weight-bold">{{ detailData.efficiency }}%</q-badge>
                    </div>
                    <div class="text-caption text-grey-6">Meta: <b>85%</b></div>
                 </div>
                 <q-linear-progress 
                    :value="detailData.efficiency / 100" 
                    size="12px" 
                    rounded 
                    :color="getEfficiencyColor(detailData.efficiency)" 
                    class="bg-grey-2 q-mt-sm" 
                    stripe 
                 />
              </q-card-section>
            </q-card>
          </div>

          <div class="q-px-lg q-pb-lg col-grow">
            <div class="row q-col-gutter-md full-height">
              
              <div class="col-12 col-md-4 column">
                <q-card flat class="col bg-white border-light column">
                  <q-card-section class="border-bottom row items-center q-py-sm bg-grey-1">
                     <q-icon name="analytics" color="orange-8" size="xs" class="q-mr-sm" /> 
                     <div class="text-subtitle2 text-weight-bold text-primary-dark">Principais Paradas</div>
                  </q-card-section>
                  
                  <q-card-section class="col scroll q-pa-none">
                    <div v-if="detailData.top_reasons.length > 0">
                       <q-list separator>
                          <q-item v-for="(reason, idx) in detailData.top_reasons" :key="idx" class="q-py-md">
                             <q-item-section avatar>
                                <q-avatar size="sm" color="grey-3" text-color="grey-8" class="text-weight-bold shadow-1">{{ idx + 1 }}</q-avatar>
                             </q-item-section>
                             <q-item-section>
                                <q-item-label class="text-weight-medium text-grey-9">{{ reason.label }}</q-item-label>
                             </q-item-section>
                             <q-item-section side>
                                <q-badge color="grey-2" text-color="dark" class="shadow-1">{{ reason.count }}x</q-badge>
                             </q-item-section>
                          </q-item>
                       </q-list>
                    </div>
                    <div v-else class="flex flex-center full-height text-grey column text-center q-pa-md">
                       <q-icon name="thumb_up_alt" size="2em" class="q-mb-sm text-positive" />
                       <div class="text-caption">Operação sem paradas registradas.</div>
                    </div>
                  </q-card-section>
                </q-card>
              </div>

              <div class="col-12 col-md-8 column">
                <q-card flat class="col bg-white border-light column">
                   <q-card-section class="border-bottom row items-center justify-between q-py-sm bg-grey-1">
                      <div class="text-subtitle2 text-weight-bold text-primary-dark row items-center">
                         <q-icon name="history" class="q-mr-sm text-primary" /> Histórico de Sessões
                      </div>
                      <q-badge color="primary" text-color="white" :label="`${detailData.sessions.length} Reg.`" />
                   </q-card-section>
                   
                   <q-card-section class="col q-pa-none">
                      <q-table
                         :rows="detailData.sessions"
                         :columns="sessionColumns"
                         row-key="id"
                         flat
                         :pagination="{ rowsPerPage: 0 }"
                         hide-bottom
                         class="sticky-header-table full-height no-border"
                         no-data-label="Nenhuma sessão encontrada."
                      >
                         <template v-slot:header="props">
                            <q-tr :props="props" class="bg-grey-1 text-grey-7 text-uppercase text-weight-bold" style="font-size: 0.75rem;">
                               <q-th v-for="col in props.cols" :key="col.name" :props="props">{{ col.label }}</q-th>
                            </q-tr>
                         </template>

                         <template v-slot:body-cell-status="props">
                            <q-td :props="props">
                               <q-badge v-if="!props.row.end_time" color="green-1" text-color="green-9" class="q-py-xs q-px-sm border-green">
                                  <q-icon name="sync" size="10px" class="q-mr-xs spin-icon" /> EM ANDAMENTO
                               </q-badge>
                               <q-badge v-else color="grey-2" text-color="grey-7" class="q-py-xs q-px-sm border-grey">
                                  FINALIZADA
                               </q-badge>
                            </q-td>
                         </template>
                         
                         <template v-slot:body-cell-efficiency="props">
                            <q-td :props="props" style="width: 140px">
                               <div class="row items-center no-wrap">
                                  <span class="q-mr-sm text-caption text-weight-bold" :class="getEfficiencyColorText(props.value)">{{ props.value }}%</span>
                                  <q-linear-progress :value="props.value / 100" rounded size="6px" :color="getEfficiencyColor(props.value)" class="col bg-grey-2" />
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
      </template>

    </q-splitter>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { api } from 'boot/axios';
import { useQuasar, date, type QTableColumn } from 'quasar';

const $q = useQuasar();
const splitterModel = ref(25); // Lista lateral um pouco mais estreita
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
   return `${date.formatDate(dateRange.value.from, 'DD/MM')} a ${date.formatDate(dateRange.value.to, 'DD/MM')}`;
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
   { name: 'order_code', label: 'O.P.', field: 'order_code', align: 'left' },
   { name: 'duration', label: 'Duração', field: 'duration', align: 'right' },
   { name: 'efficiency', label: 'Efic.', field: 'efficiency', align: 'right', sortable: true },
];

async function loadList() {
  loadingList.value = true;
  try {
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
         // Fallback de Segurança
         // eslint-disable-next-line @typescript-eslint/no-explicit-any
         const allUsers = (await api.get<any[]>('/users/')).data;
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

function getInitials(name: string) {
   if (!name) return '?';
   return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
}

function getEfficiencyColorText(val: number) {
   if(val >= 85) return 'text-positive';
   if(val >= 70) return 'text-warning';
   return 'text-negative';
}


function getEfficiencyColor(val: number) {
   if(val >= 85) return 'positive';
   if(val >= 70) return 'warning';
   return 'negative';
}

function getAvatarClass(val: number) {
    if(val >= 85) return 'bg-green-1 text-green-9';
    if(val >= 70) return 'bg-orange-1 text-orange-9';
    if(val === 0) return 'bg-grey-3 text-grey-8';
    return 'bg-red-1 text-red-9';
}

onMounted(loadList);
</script>

<style lang="scss" scoped>
/* VARIAVEIS DE TEMA INDUSTRIAL */
.bg-surface { background-color: #f8fafc; }
.text-primary-dark { color: #1e293b; }
.leading-tight { line-height: 1.2; }
.border-light { border: 1px solid #e2e8f0; }
.border-bottom { border-bottom: 1px solid #e2e8f0; }
.border-green { border: 1px solid #bbf7d0; }
.border-grey { border: 1px solid #e2e8f0; }
.border-white { border: 2px solid white; }

.header-bar {
  border-bottom: 1px solid #e2e8f0;
}

.icon-box {
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 8px;
}

/* LISTA DE FUNCIONÁRIOS */
.employee-item {
  border-bottom: 1px solid transparent;
  margin: 0 8px 4px 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #f1f5f9;
  }
}

.active-employee-item {
  background-color: #eff6ff !important;
  border: 1px solid #bfdbfe;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  
  .text-primary-dark { color: var(--q-primary); }
}

.status-dot {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 10px;
  height: 10px;
  padding: 0;
  transform: translate(-10%, -10%);
}

/* CARDS E DETALHES */
.kpi-card {
  border-radius: 12px;
  transition: transform 0.2s, box-shadow 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  }
}

.sticky-header-table {
  height: 100%;
  
  :deep(thead tr:first-child th) {
    background-color: inherit;
    position: sticky;
    top: 0;
    z-index: 1;
  }
}

/* ANIMAÇÕES */
@keyframes spin { 100% { transform: rotate(360deg); } }
.spin-icon { animation: spin 2s linear infinite; }

/* DARK MODE OVERRIDES */
.body--dark {
  .bg-surface { background-color: #0f172a; }
  .bg-white { background-color: #1e293b !important; color: #f8fafc; }
  .text-primary-dark { color: #f8fafc; }
  .border-light, .border-bottom, .header-bar { border-color: #334155; }
  .bg-grey-1 { background-color: #334155 !important; }
  .date-selector { background-color: #1e293b !important; color: white !important; border: 1px solid #475569; }
  .search-input :deep(.q-field__control) { background-color: #1e293b !important; }
  .employee-item:hover { background-color: #334155; }
  .active-employee-item { background-color: rgba(var(--q-primary), 0.2) !important; border-color: var(--q-primary); }
}
</style>
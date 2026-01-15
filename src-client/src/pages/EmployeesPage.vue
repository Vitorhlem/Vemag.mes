<template>
  <q-page class="q-pa-md bg-grey-1">
    
    <div class="row items-center justify-between q-mb-md">
      <div>
        <div class="text-h4 text-weight-bold text-blue-grey-9">Painel de Performance (MES)</div>
        <div class="text-subtitle1 text-grey-7">Análise detalhada de produtividade e paradas</div>
      </div>
      
      <div class="row q-gutter-md">
        <q-input outlined dense v-model="filterDate" mask="date" :rules="['date']" label="Data de Análise" bg-color="white" style="width: 150px">
          <template v-slot:append>
            <q-icon name="event" class="cursor-pointer">
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="filterDate" @update:model-value="refreshData">
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Fechar" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>

        <q-btn-dropdown push color="teal-8" icon="file_download" label="Exportar Dados">
           <q-list>
              <q-item clickable v-close-popup @click="exportToCsv">
                 <q-item-section avatar><q-icon name="table_view" color="green" /></q-item-section>
                 <q-item-section>
                    <q-item-label>Excel / CSV</q-item-label>
                    <q-item-label caption>Dados da aba atual</q-item-label>
                 </q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="printReport">
                 <q-item-section avatar><q-icon name="print" color="grey-8" /></q-item-section>
                 <q-item-section>Imprimir PDF</q-item-section>
              </q-item>
           </q-list>
        </q-btn-dropdown>

        <q-btn push color="primary" icon="refresh" @click="refreshData" :loading="mesStore.isLoading">
            <q-tooltip>Atualizar Dados</q-tooltip>
        </q-btn>
      </div>
    </div>

    <q-card class="q-mb-md shadow-1">
        <q-tabs
          v-model="activeTab"
          align="left"
          class="text-grey-7"
          active-color="primary"
          indicator-color="primary"
          narrow-indicator
        >
          <q-tab name="machine" icon="precision_manufacturing" label="Visão Máquina" />
          <q-tab name="employee" icon="badge" label="Visão Operadores" />
        </q-tabs>
    </q-card>

    <q-tab-panels v-model="activeTab" animated class="bg-transparent q-pa-none">
        
        <q-tab-panel name="machine" class="q-pa-none">
            
            <div class="row q-mb-md">
                <q-select 
                    outlined dense 
                    v-model="selectedMachine" 
                    :options="machineOptions"
                    option-label="label"
                    option-value="value"
                    emit-value map-options
                    label="Selecionar Equipamento"
                    bg-color="white"
                    class="col-12 col-md-4"
                    @update:model-value="refreshData"
                />
            </div>

            <div class="row q-col-gutter-md q-mb-lg">
                <div class="col-12 col-md-3">
                    <q-card class="full-height shadow-2 relative-position overflow-hidden">
                    <div class="absolute-full bg-blue-grey-9 opacity-10"></div>
                    <q-card-section class="column items-center justify-center text-center q-py-lg">
                        <div class="text-h6 text-grey-8 text-uppercase">OEE Global</div>
                        <div class="text-h2 text-weight-bolder text-blue-grey-10 q-my-sm">
                            {{ mesStore.oeeData?.oee_percentage || 0 }}<span class="text-h5">%</span>
                        </div>
                        <q-badge :color="getOeeColor(mesStore.oeeData?.oee_percentage)" class="q-py-xs q-px-md text-caption">
                            {{ getOeeLabel(mesStore.oeeData?.oee_percentage) }}
                        </q-badge>
                    </q-card-section>
                    </q-card>
                </div>

                <div class="col-12 col-md-3">
                    <q-card class="full-height shadow-1">
                    <q-card-section>
                        <div class="row items-center no-wrap">
                            <q-icon name="timer" color="primary" size="lg" class="q-mr-md bg-blue-1 q-pa-sm rounded-borders" />
                            <div>
                                <div class="text-caption text-grey-6 text-uppercase text-weight-bold">Disponibilidade</div>
                                <div class="text-h4 text-weight-bold text-primary">{{ mesStore.oeeData?.availability || 0 }}%</div>
                            </div>
                        </div>
                        <q-separator class="q-my-md" />
                        <div class="row justify-between text-caption text-grey-8">
                            <span>Tempo Produzindo:</span>
                            <span class="text-weight-bold">{{ Math.round(mesStore.oeeData?.metrics.producing_min || 0) }} min</span>
                        </div>
                        <div class="row justify-between text-caption text-grey-8">
                            <span>Paradas Planejadas:</span>
                            <span class="text-weight-bold">{{ Math.round(mesStore.oeeData?.metrics.planned_stop_min || 0) }} min</span>
                        </div>
                    </q-card-section>
                    </q-card>
                </div>

                <div class="col-12 col-md-3">
                    <q-card class="full-height shadow-1">
                    <q-card-section>
                        <div class="row items-center no-wrap">
                            <q-icon name="speed" color="orange-8" size="lg" class="q-mr-md bg-orange-1 q-pa-sm rounded-borders" />
                            <div>
                                <div class="text-caption text-grey-6 text-uppercase text-weight-bold">Performance</div>
                                <div class="text-h4 text-weight-bold text-orange-9">{{ mesStore.oeeData?.performance || 0 }}%</div>
                            </div>
                        </div>
                        <q-separator class="q-my-md" />
                        <div class="text-caption text-grey-6">
                            Comparativo entre Ciclo Padrão vs Realizado.
                            <br><em>(Requer cadastro de tempos de ciclo)</em>
                        </div>
                    </q-card-section>
                    </q-card>
                </div>

                <div class="col-12 col-md-3">
                    <q-card class="full-height shadow-1">
                    <q-card-section>
                        <div class="row items-center no-wrap">
                            <q-icon name="verified" color="positive" size="lg" class="q-mr-md bg-green-1 q-pa-sm rounded-borders" />
                            <div>
                                <div class="text-caption text-grey-6 text-uppercase text-weight-bold">Qualidade</div>
                                <div class="text-h4 text-weight-bold text-positive">{{ mesStore.oeeData?.quality || 0 }}%</div>
                            </div>
                        </div>
                        <q-separator class="q-my-md" />
                        <div class="text-caption text-grey-6">
                            Peças Boas vs Total Produzido (incluindo Refugos).
                        </div>
                    </q-card-section>
                    </q-card>
                </div>
            </div>

            <q-card class="q-mb-lg shadow-2">
                <q-card-section class="row items-center justify-between">
                    <div class="text-h6 text-weight-bold">Linha do Tempo (Gantt Chart)</div>
                    <div class="row q-gutter-x-md text-caption">
                        <div class="row items-center"><div class="q-mr-xs" style="width:12px;height:12px;background:#21BA45;"></div> Operação</div>
                        <div class="row items-center"><div class="q-mr-xs" style="width:12px;height:12px;background:#F2C037;"></div> Setup/Manut.</div>
                        <div class="row items-center"><div class="q-mr-xs" style="width:12px;height:12px;background:#C10015;"></div> Parada</div>
                    </div>
                </q-card-section>
                
                <q-card-section class="q-pt-none overflow-auto">
                    <div class="gantt-container rounded-borders relative-position bg-grey-3" style="height: 60px; display: flex; width: 100%;">
                        <div 
                            v-for="(block, idx) in mesStore.timeline" 
                            :key="idx"
                            :class="`bg-${block.color} relative-position hover-highlight`"
                            :style="{ width: getBlockWidth(block.duration_min) + '%', minWidth: '2px' }"
                        >
                            <q-tooltip anchor="top middle" self="bottom middle">
                                <div class="text-bold">{{ block.status }}</div>
                                <div>{{ formatTime(block.start) }} - {{ formatTime(block.end) }}</div>
                                <div>Duração: {{ block.duration_min }} min</div>
                                <div v-if="block.reason" class="text-yellow-2">{{ block.reason }}</div>
                            </q-tooltip>
                        </div>
                    </div>
                    <div class="row justify-between text-caption text-grey-6 q-mt-xs font-monospace">
                        <span>00:00</span><span>04:00</span><span>08:00</span><span>12:00</span><span>16:00</span><span>20:00</span><span>23:59</span>
                    </div>
                </q-card-section>
            </q-card>

            <q-card class="shadow-1">
                <q-card-section>
                    <div class="text-h6 text-weight-bold q-mb-md">Histórico de Eventos Detalhado</div>
                    
                    <q-table
                        :rows="mesStore.rawLogs"
                        :columns="columns"
                        row-key="id"
                        flat bordered
                        :pagination="{ rowsPerPage: 15 }"
                    >
                        <template v-slot:body-cell-new_status="props">
                            <q-td :props="props">
                                <q-badge :color="getStatusColor(props.value)" :label="props.value" />
                            </q-td>
                        </template>
                        <template v-slot:body-cell-timestamp="props">
                            <q-td :props="props">
                                {{ new Date(props.value).toLocaleString('pt-BR') }}
                            </q-td>
                        </template>
                    </q-table>
                </q-card-section>
            </q-card>
        </q-tab-panel>

        <q-tab-panel name="employee" class="q-pa-none">
            
            <div class="row q-col-gutter-md q-mb-lg">
                <div class="col-12 col-md-4">
                    <q-card class="bg-teal-9 text-white shadow-3">
                        <q-card-section class="row items-center">
                            <q-icon name="groups" size="50px" class="q-mr-md opacity-50" />
                            <div>
                                <div class="text-h4 text-weight-bold">{{ mesStore.employeeStats.length }}</div>
                                <div class="text-subtitle2 opacity-80">Operadores Ativos</div>
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
                <div class="col-12 col-md-4">
                    <q-card class="bg-blue-grey-9 text-white shadow-3">
                        <q-card-section class="row items-center">
                            <q-icon name="schedule" size="50px" class="q-mr-md opacity-50" />
                            <div>
                                <div class="text-h4 text-weight-bold">{{ totalHoursFormatted }}h</div>
                                <div class="text-subtitle2 opacity-80">Horas Totais Apontadas</div>
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
                <div class="col-12 col-md-4">
                    <q-card class="bg-orange-9 text-white shadow-3">
                        <q-card-section class="row items-center">
                            <q-icon name="trending_up" size="50px" class="q-mr-md opacity-50" />
                            <div>
                                <div class="text-h4 text-weight-bold">{{ avgEfficiency }}%</div>
                                <div class="text-subtitle2 opacity-80">Eficiência Média da Equipe</div>
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
            </div>

            <q-card class="shadow-2">
                <q-card-section>
                    <div class="text-h6 text-weight-bold text-blue-grey-9 q-mb-md row items-center">
                        <q-icon name="leaderboard" class="q-mr-sm" /> Ranking de Produtividade
                    </div>
                    
                    <q-table
                        :rows="mesStore.employeeStats"
                        :columns="employeeColumns"
                        row-key="id"
                        flat bordered
                        :pagination="{ rowsPerPage: 20 }"
                        separator="cell"
                        @row-click="onOperatorClick" 
                        class="cursor-pointer hover-effect-table"
                    >
                        <template v-slot:body-cell-employee_name="props">
                            <q-td :props="props" class="row items-center no-wrap">
                                <q-avatar color="primary" text-color="white" size="32px" class="q-mr-sm">
                                    {{ props.value.charAt(0).toUpperCase() }}
                                </q-avatar>
                                <div class="text-weight-bold">{{ props.value }}</div>
                            </q-td>
                        </template>

                        <template v-slot:body-cell-efficiency="props">
                            <q-td :props="props" style="width: 250px;">
                                <div class="row items-center">
                                    <div class="col-grow q-mr-sm">
                                        <q-linear-progress 
                                            :value="props.value / 100" 
                                            :color="getEfficiencyColor(props.value)" 
                                            size="8px" 
                                            rounded 
                                            track-color="grey-3"
                                        />
                                    </div>
                                    <div class="text-weight-bold">{{ props.value }}%</div>
                                </div>
                            </q-td>
                        </template>

                        <template v-slot:body-cell-top_reasons="props">
                            <q-td :props="props">
                                <div v-if="props.value && props.value.length > 0" class="row q-gutter-xs">
                                    <q-badge 
                                        v-for="(reason, idx) in props.value" 
                                        :key="idx"
                                        color="red-1" 
                                        text-color="red-9"
                                        class="q-pa-xs"
                                    >
                                        {{ reason.label }} ({{ reason.count }})
                                    </q-badge>
                                </div>
                                <span v-else class="text-grey-5 italic">Sem paradas registradas</span>
                            </q-td>
                        </template>
                    </q-table>
                </q-card-section>
            </q-card>
        </q-tab-panel>

    </q-tab-panels>

  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { date, exportFile, useQuasar } from 'quasar';
import type { QTableColumn } from 'quasar';
import { useMesStore } from 'stores/mes-store'; // CORREÇÃO: Import QTableColumn
import type { EmployeeStat } from 'stores/mes-store'; // CORREÇÃO: Import EmployeeStat
import { useProductionStore } from 'stores/production-store';
import { useRouter } from 'vue-router'; // Importação essencial para redirecionamento

const $q = useQuasar();
const router = useRouter(); // Instância do router
const mesStore = useMesStore();
const productionStore = useProductionStore();

const activeTab = ref('machine'); // Aba padrão
const filterDate = ref(date.formatDate(new Date(), 'YYYY-MM-DD'));
const selectedMachine = ref<number | null>(null);

// Carrega lista de máquinas
const machineOptions = computed(() => 
    productionStore.machinesList.map(m => ({ label: `${m.brand} ${m.model}`, value: m.id }))
);

// --- COLUNAS DA TABELA MÁQUINA ---
const columns: QTableColumn[] = [
  { name: 'timestamp', label: 'Data/Hora', field: 'timestamp', align: 'left', sortable: true },
  { name: 'event_type', label: 'Tipo Evento', field: 'event_type', align: 'left', sortable: true },
  { name: 'new_status', label: 'Status', field: 'new_status', align: 'center', sortable: true },
  { name: 'reason', label: 'Motivo', field: 'reason', align: 'left', sortable: true },
  { name: 'operator_name', label: 'Operador', field: 'operator_name', align: 'left', sortable: true },
  { name: 'details', label: 'Detalhes', field: 'details', align: 'left', sortable: true }
];

// CORREÇÃO: Tipagem QTableColumn
const employeeColumns: QTableColumn[] = [
    { name: 'employee_name', label: 'Colaborador', field: 'employee_name', align: 'left', sortable: true },
    { name: 'total_hours', label: 'Horas Totais', field: 'total_hours', align: 'center', sortable: true },
    { name: 'productive_hours', label: 'Hrs Produtivas', field: 'productive_hours', align: 'center', sortable: true, classes: 'text-bold text-positive' },
    { name: 'unproductive_hours', label: 'Hrs Paradas', field: 'unproductive_hours', align: 'center', sortable: true, classes: 'text-negative' },
    { name: 'efficiency', label: 'Eficiência Geral', field: 'efficiency', align: 'left', sortable: true },
    { name: 'top_reasons', label: 'Principais Ofensores (Paradas)', field: 'top_reasons', align: 'left' },
];

// --- COMPUTEDS ---
const totalHoursFormatted = computed(() => {
    const total = mesStore.employeeStats.reduce((acc, curr) => acc + curr.total_hours, 0);
    return total.toFixed(1);
});

const avgEfficiency = computed(() => {
    if (mesStore.employeeStats.length === 0) return 0;
    const total = mesStore.employeeStats.reduce((acc, curr) => acc + curr.efficiency, 0);
    return Math.round(total / mesStore.employeeStats.length);
});

// --- FUNÇÃO DE CLIQUE NO OPERADOR (NOVA) ---
function onOperatorClick(evt: Event, row: EmployeeStat) {
    void router.push(`/users/${row.id}/stats`);
}

// --- FUNÇÕES DE COR E FORMATO ---
function getStatusColor(status: string) {
    const s = String(status).toUpperCase();
    if (s === 'RUNNING' || s === 'EM OPERAÇÃO') return 'positive';
    if (s === 'STOPPED' || s === 'PARADA') return 'negative';
    if (s === 'SETUP' || s === 'MANUTENÇÃO') return 'warning';
    return 'grey';
}

function getEfficiencyColor(val: number) {
    if (val >= 90) return 'positive';
    if (val >= 75) return 'primary';
    if (val >= 50) return 'warning';
    return 'negative';
}

function getOeeColor(val?: number) {
    if (!val) return 'grey';
    if (val >= 85) return 'positive';
    if (val >= 65) return 'warning';
    return 'negative';
}

function getOeeLabel(val?: number) {
    if (!val) return 'N/A';
    if (val >= 85) return 'World Class';
    if (val >= 65) return 'Aceitável';
    return 'Crítico';
}

function getBlockWidth(minutes: number) {
    return (minutes / 1440) * 100;
}

function formatTime(isoStr: string) {
    return new Date(isoStr).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

// --- LÓGICA DE DADOS ---
async function refreshData() {
    await mesStore.fetchEmployeeStats(filterDate.value, filterDate.value);
    if (selectedMachine.value) {
        await mesStore.fetchMachineOEE(selectedMachine.value, filterDate.value, filterDate.value);
        await mesStore.fetchDailyTimeline(selectedMachine.value, filterDate.value);
    }
}

// --- RELATÓRIOS ---
function exportToCsv() {
    let content = '';
    let filename = '';

    if (activeTab.value === 'machine') {
        if (!selectedMachine.value) {
            $q.notify({ type: 'warning', message: 'Selecione uma máquina primeiro.' });
            return;
        }
        filename = `Historico_Maquina_${filterDate.value}.csv`;
        content = 'Data/Hora;Status;Motivo;Operador;Detalhes\n';
        
        mesStore.rawLogs.forEach(row => {
            const cleanReason = (row.reason || '').replace(/;/g, ',');
            const cleanDetails = (row.details || '').replace(/;/g, ',');
            content += `${new Date(row.timestamp).toLocaleString()};${row.new_status};${cleanReason};${row.operator_name || ''};${cleanDetails}\n`;
        });
    } else {
        filename = `Ranking_Operadores_${filterDate.value}.csv`;
        content = 'Colaborador;Horas Totais;Horas Produtivas;Horas Paradas;Eficiencia\n';
        
        mesStore.employeeStats.forEach(row => {
            content += `${row.employee_name};${row.total_hours};${row.productive_hours};${row.unproductive_hours};${row.efficiency}%\n`;
        });
    }

    const status = exportFile(filename, content, 'text/csv');
    if (status === true) {
        $q.notify({ type: 'positive', message: 'Download iniciado!' });
    } else {
        $q.notify({ type: 'negative', message: 'Erro ao baixar arquivo' });
    }
}

function printReport() {
    window.print();
}

onMounted(async () => {
    await productionStore.fetchAvailableMachines();
    // CORREÇÃO: Verificação segura de array
    if (machineOptions.value && machineOptions.value.length > 0 && machineOptions.value[0]) {
        selectedMachine.value = machineOptions.value[0].value;
        await refreshData(); // CORREÇÃO: await na promise
    }
});
</script>

<style scoped>
.hover-highlight:hover {
    filter: brightness(1.1);
    cursor: pointer;
    z-index: 10;
    transform: scaleY(1.1);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.font-monospace { font-family: monospace; }
.opacity-10 { opacity: 0.1; }
.opacity-50 { opacity: 0.5; }
.opacity-80 { opacity: 0.8; }

.hover-effect-table tbody tr:hover {
    background-color: #f5f5f5; /* Efeito visual ao passar o mouse */
    transition: background-color 0.2s;
}

/* Ajustes para Impressão */
@media print {
    .q-page { background: white !important; }
    .q-btn, .q-header, .q-drawer, .q-tabs { display: none !important; }
    .q-card { box-shadow: none !important; border: 1px solid #ccc !important; break-inside: avoid; }
    
    /* Força cores na impressão */
    .bg-positive { background-color: #21BA45 !important; -webkit-print-color-adjust: exact; }
    .bg-negative { background-color: #C10015 !important; -webkit-print-color-adjust: exact; }
    .bg-warning { background-color: #F2C037 !important; -webkit-print-color-adjust: exact; }
    .text-positive { color: #21BA45 !important; }
    .bg-blue-grey-9 { background-color: #37474F !important; color: white !important; -webkit-print-color-adjust: exact; }
}
</style>
<template>
  <q-page class="q-pa-md bg-glass-layout">
    
    <div class="row items-center justify-between q-mb-md">
      <div>
        <div class="text-h4 text-weight-bold text-gradient-trucar">Painel de Performance (MES)</div>
        <div class="text-subtitle1 text-teal-9 opacity-80">Análise detalhada de produtividade e paradas</div>
      </div>
      
      <div class="row q-gutter-md items-center"> 
  
        <q-input 
          outlined 
          dense 
          v-model="filterDate" 
          mask="date" 
          :rules="['date']" 
          label="Data de Análise" 
          class="glass-input" 
          style="width: 150px"
          hide-bottom-space  
        >
          <template v-slot:append>
            <q-icon name="event" class="cursor-pointer text-primary">
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="filterDate" color="teal-9" @update:model-value="refreshData">
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Fechar" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>

        <q-btn-dropdown push color="teal-8" icon="file_download" label="Exportar Dados" class="shadow-green text-white">
           <q-list class="glass-menu">
              <q-item clickable v-close-popup @click="exportToCsv">
                 <q-item-section avatar><q-icon name="table_view" color="teal-9" /></q-item-section>
                 <q-item-section>
                    <q-item-label>Excel / CSV</q-item-label>
                    <q-item-label caption class="text-grey-7">Dados da aba atual</q-item-label>
                 </q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="printReport">
                 <q-item-section avatar><q-icon name="print" class="text-grey-8" /></q-item-section>
                 <q-item-section>Imprimir PDF</q-item-section>
              </q-item>
           </q-list>
        </q-btn-dropdown>

        <q-btn push color="primary" icon="refresh" @click="refreshData" :loading="isLoading" class="shadow-green">
            <q-tooltip>Atualizar Dados</q-tooltip>
        </q-btn>
      </div>
    </div>

    <q-card class="q-mb-md glass-card shadow-sm">
        <q-tabs
          v-model="activeTab"
          align="left"
          class="text-teal-8 tab-text-color"
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
                    class="col-12 col-md-4 glass-input"
                    @update:model-value="refreshData"
                />
            </div>

            <div v-if="!selectedMachine" class="flex flex-center q-pa-xl text-teal-9 opacity-50">
                Selecione uma máquina para carregar os dados.
            </div>

            <div v-else>
                <div class="row q-col-gutter-md q-mb-md">
                    <div class="col-12 col-md">
                        <q-card class="full-height glass-card border-left-green shadow-sm">
                            <q-card-section>
                                <div class="text-caption text-uppercase text-weight-bold text-teal-9 opacity-80">Produção humana</div>
                                <div class="text-h4 text-weight-bolder q-mt-sm text-teal-10">{{ machineStats?.formatted_running_operator || '00:00:00' }}</div>
                                <div class="text-caption text-grey-8">Tempo efetivo logado.</div>
                            </q-card-section>
                        </q-card>
                    </div>
                    <div class="col-12 col-md">
                        <q-card class="full-height glass-card border-left-blue shadow-sm">
                            <q-card-section>
                                <div class="text-caption text-uppercase text-weight-bold text-blue-9 opacity-80">Produção Autônoma</div>
                                <div class="text-h4 text-weight-bolder q-mt-sm text-blue-10">{{ machineStats?.formatted_running_autonomous || '00:00:00' }}</div>
                                <div class="text-caption text-grey-8">Sem operador (Troca turno).</div>
                            </q-card-section>
                        </q-card>
                    </div>
                    
                    <div class="col-12 col-md">
                        <q-card class="full-height glass-card border-left-purple shadow-sm">
                            <q-card-section>
                                <div class="text-caption text-uppercase text-weight-bold text-purple-9 opacity-80">Setup (OPP)</div>
                                <div class="text-h4 text-weight-bolder q-mt-sm text-purple-10">{{ machineStats?.formatted_setup || '00:00:00' }}</div>
                                <div class="text-caption text-grey-8">Tempo de ajuste. (Ordem De Parada Produtiva)</div>
                            </q-card-section>
                        </q-card>
                    </div>
                    <div class="col-12 col-md">
    <q-card class="full-height glass-card border-left-black shadow-sm">
        <q-card-section>
            <div class="text-caption text-uppercase text-weight-bold text-black opacity-80">Micro-paradas</div>
            <div class="text-h4 text-weight-bolder q-mt-sm text-black">{{ machineStats?.formatted_micro_stop || '00:00:00' }}</div>
            <div class="text-caption text-grey-8">Paradas - 5 min.</div>
        </q-card-section>
    </q-card>
</div>
                    <div class="col-12 col-md">
                        <q-card class="full-height glass-card border-left-orange shadow-sm">
                            <q-card-section>
                                <div class="text-caption text-uppercase text-weight-bold text-orange-9 opacity-80">Pausa (OPI)</div>
                                <div class="text-h4 text-weight-bolder q-mt-sm text-orange-10">{{ machineStats?.formatted_pause || '00:00:00' }}</div>
                                <div class="text-caption text-grey-8">Logado mas parado. (Ordem De Parada Improdutiva)</div>
                            </q-card-section>
                        </q-card>
                    </div>
                    
                    <div class="col-12 col-md">
                        <q-card class="full-height glass-card border-left-red shadow-sm">
                            <q-card-section>
                                <div class="text-caption text-uppercase text-weight-bold text-red-9 opacity-80">Manutenção / Quebra (OPM)</div>
                                <div class="text-h4 text-weight-bolder q-mt-sm text-red-10">{{ machineStats?.formatted_maintenance || '00:00:00' }}</div>
                                <div class="text-caption text-grey-8">Tempo indisponível. (Ordem De Parada Manutenção)</div>
                            </q-card-section>
                        </q-card>
                    </div>
                </div>

                <q-card class="q-pa-md q-mb-lg glass-card shadow-sm">
                    <div class="text-subtitle2 text-weight-bold text-teal-10 q-mb-sm">Distribuição do Tempo (24h)</div>
                    <div class="row no-wrap rounded-borders overflow-hidden" style="height: 30px; border: 1px solid rgba(128,128,128,0.2)">
                       <div class="bg-green text-white flex flex-center text-caption" :style="{flex: machineStats?.total_running_operator_seconds || 0}">
                          <q-tooltip>Prod. Humana: {{ machineStats?.formatted_running_operator }}</q-tooltip>
                          {{ machineStats?.total_running_operator_seconds ? 'Op.' : '' }}
                       </div>
                       <div class="bg-blue text-white flex flex-center text-caption" :style="{flex: machineStats?.total_running_autonomous_seconds || 0}">
                          <q-tooltip>Autônoma: {{ machineStats?.formatted_running_autonomous }}</q-tooltip>
                          {{ machineStats?.total_running_autonomous_seconds ? 'Auto' : '' }}
                       </div>
                       
                       <div class="bg-purple text-white flex flex-center text-caption" :style="{flex: machineStats?.total_setup_seconds || 0}">
                          <q-tooltip>Setup: {{ machineStats?.formatted_setup }}</q-tooltip>
                          {{ machineStats?.total_setup_seconds ? 'Setup' : '' }}
                       </div>

                       <div class="bg-orange text-white flex flex-center text-caption" :style="{flex: machineStats?.total_pause_seconds || 0}">
                          <q-tooltip>Pausa: {{ machineStats?.formatted_pause }}</q-tooltip>
                          {{ machineStats?.total_pause_seconds ? 'Pausa' : '' }}
                       </div>

                       <div class="bg-red text-white flex flex-center text-caption" :style="{flex: machineStats?.total_maintenance_seconds || 0}">
                          <q-tooltip>Manutenção: {{ machineStats?.formatted_maintenance }}</q-tooltip>
                          {{ machineStats?.total_maintenance_seconds ? 'Manut.' : '' }}
                       </div>
                       <div class="bg-grey-3 text-grey-8 flex flex-center text-caption gantt-idle" :style="{flex: machineStats?.total_idle_seconds || 1}">
                          Ocioso
                       </div>
                    </div>
                </q-card>

                <div class="row q-col-gutter-md q-mb-lg">
                    <div class="col-12 col-md-3">
                        <q-card class="full-height glass-card shadow-green relative-position overflow-hidden">
                        <div class="absolute-full bg-teal-gradient-faded opacity-20"></div>
                        <q-card-section class="column items-center justify-center text-center q-py-lg">
    <div class="text-h6 text-teal-9 text-uppercase">Disponibilidade</div>
    <div class="text-h2 text-weight-bolder text-teal-10 q-my-sm">
        {{ mesStore.oeeData?.oee_percentage ?? 0 }}<span class="text-h5">%</span>
    </div>
    <q-badge 
        :color="getOeeColor(mesStore.oeeData?.oee_percentage)" 
        class="q-py-xs q-px-md text-caption text-weight-bold"
    >
        {{ getOeeLabel(mesStore.oeeData?.oee_percentage) }}
    </q-badge>
</q-card-section>
                        </q-card>
                    </div>

                    <div class="col-12 col-md-3">
                        <q-card class="full-height glass-card shadow-sm">
                        <q-card-section>
                            <div class="row items-center no-wrap">
                                <q-icon name="timer" color="primary" size="lg" class="bg-teal-1 q-pa-sm rounded-borders" />
                                <div class="q-ml-md">
                                    <div class="text-caption text-teal-8 text-uppercase text-weight-bold">Disponibilidade</div>
                                    <div class="text-h4 text-weight-bold text-teal-10">{{ mesStore.oeeData?.availability || 0 }}%</div>
                                </div>
                            </div>
                            <q-separator class="q-my-md opacity-10" />
                            <div class="row justify-between text-caption text-grey-8">
                                <span>Tempo Produzindo:</span>
                                <span class="text-weight-bold text-teal-9">{{ Math.round(mesStore.oeeData?.metrics.producing_min || 0) }} min</span>
                            </div>
                            <div class="row justify-between text-caption text-grey-8">
                                <span>Paradas Planejadas:</span>
                                <span class="text-weight-bold">{{ Math.round(mesStore.oeeData?.metrics.planned_stop_min || 0) }} min</span>
                            </div>
                        </q-card-section>
                        </q-card>
                    </div>

                    <div class="col-12 col-md-3">
                        <q-card class="full-height glass-card shadow-sm">
                        <q-card-section>
                            <div class="row items-center no-wrap">
                                <q-icon name="speed" color="orange-8" size="lg" class="bg-orange-1 q-pa-sm rounded-borders" />
                                <div class="q-ml-md">
                                    <div class="text-caption text-orange-9 text-uppercase text-weight-bold">-----------------</div>
                                </div>
                            </div>
                            <q-separator class="q-my-md opacity-10" />
                            <div class="text-caption text-grey-6 italic"><em></em></div>
                        </q-card-section>
                        </q-card>
                    </div>

                    <div class="col-12 col-md-3">
                        <q-card class="full-height glass-card shadow-sm">
                        <q-card-section>
                            <div class="row items-center no-wrap">
                                <q-icon name="verified" color="positive" size="lg" class="bg-green-1 q-pa-sm rounded-borders" />
                                <div class="q-ml-md">
                                    <div class="text-caption text-teal-9 text-uppercase text-weight-bold">-----------------</div>
                                </div>
                            </div>
                            <q-separator class="q-my-md opacity-10" />
                            <div class="text-caption text-grey-6 italic"></div>
                        </q-card-section>
                        </q-card>
                    </div>
                </div>

                <q-card class="q-mb-lg glass-card shadow-sm overflow-hidden">
                    <q-card-section class="row items-center justify-between border-bottom-light">
                        <div class="text-h6 text-weight-bold text-teal-10">Linha do Tempo (Gantt Chart)</div>
                        <div class="row q-gutter-x-md text-caption text-grey-8">
                            <div class="row items-center"><div class="q-mr-xs legend-dot bg-green"></div> Operação</div>
                            <div class="row items-center"><div class="q-mr-xs legend-dot bg-purple"></div> Setup</div>
                            <div class="row items-center"><div class="q-mr-xs legend-dot bg-orange"></div> Pausa/Ocioso</div>
                            <div class="row items-center"><div class="q-mr-xs legend-dot bg-red"></div> Manutenção</div>
                            <div class="row items-center"><div class="q-mr-xs legend-dot bg-black"></div> Micro-parada</div>
<div class="row items-center"><div class="q-mr-xs legend-dot bg-brown-8"></div> Sem Motivo</div>
<div class="row items-center q-mr-md"> <div class="box-legend q-mr-sm" style="background-color: #2196F3"></div><span class="text-caption">Troca de Turno (Autônomo)</span></div>
</div>                    
</q-card-section>
                    
                    <q-card-section class="q-pt-none overflow-auto">
                        <div class="gantt-container rounded-borders relative-position bg-grey-3 q-mt-md" style="height: 60px; display: flex; width: 100%;">
                            <div 
                                v-for="(block, idx) in mesStore.timeline" 
                                :key="idx"
                                :class="`bg-${getGanttColor(block)} relative-position hover-highlight`"
                                :style="{ width: getBlockWidth(block.duration_min) + '%', minWidth: '2px' }"
                            >
                                <q-tooltip anchor="top middle" self="bottom middle">
                                    <div class="text-bold">{{ translateStatus(block.status) }}</div>
                                    <div>{{ formatTime(block.start) }} - {{ formatTime(block.end) }}</div>
                                    <div>Duração: {{ block.duration_min }} min</div>
                                    <div v-if="block.reason" class="text-yellow-2">{{ block.reason }}</div>
                                </q-tooltip>
                            </div>
                        </div>
                        <div class="row justify-between text-caption text-teal-8 q-mt-xs font-monospace opacity-70">
                            <span>00:00</span><span>04:00</span><span>08:00</span><span>12:00</span><span>16:00</span><span>20:00</span><span>23:59</span>
                        </div>
                    </q-card-section>
                </q-card>

                <q-card class="glass-card shadow-sm overflow-hidden">
    <q-card-section>
        <div class="text-h6 text-weight-bold text-teal-10 q-mb-md">Histórico de Eventos Detalhado</div>
        <q-table
            :rows="mesStore.rawLogs"
            :columns="columns"
            row-key="id"
            flat bordered
            class="glass-table"
            :pagination="{ rowsPerPage: 15 }"
        >
            <template v-slot:body-cell-event_type="props">
                <q-td :props="props">
                    <div class="text-weight-medium text-teal-9">{{ translateEventType(props.value) }}</div>
                </q-td>
            </template>

            <template v-slot:body-cell-new_status="props">
                <q-td :props="props">
                    <q-badge :color="getStatusColor(props.value)" :label="translateStatus(props.value)" class="glass-badge-status" />
                </q-td>
            </template>

            <template v-slot:body-cell-operator_name="props">
                <q-td :props="props">
                    
                    <div v-if="props.row.operator_id" 
                         class="text-primary text-weight-bold cursor-pointer hover-teal row items-center no-wrap"
                         @click.stop="$router.push(`/users/${props.row.operator_id}/stats`)"
                    >
                        <q-avatar size="24px" class="q-mr-sm bg-teal-1 text-teal-9" style="font-size: 10px">
                            {{ props.value ? props.value.charAt(0).toUpperCase() : 'U' }}
                        </q-avatar>
                        <span>{{ props.value }}</span>
                        <q-tooltip content-class="bg-teal-9">Ver Perfil</q-tooltip>
                    </div>

                    <div v-else class="text-grey-6 text-italic row items-center no-wrap">
                        <q-icon name="smart_toy" size="xs" class="q-mr-xs" />
                        <span>{{ props.value || 'Sistema / Automático' }}</span>
                    </div>

                </q-td>
            </template>

            <template v-slot:body-cell-timestamp="props">
                <q-td :props="props" class="text-grey-8">
                    {{ new Date(props.value).toLocaleString('pt-BR') }}
                </q-td>
            </template>
            
            <template v-slot:body-cell-details="props">
                <q-td :props="props" class="text-grey-8">
                    {{ props.value }}
                </q-td>
            </template>
            
            <template v-slot:body-cell-reason="props">
                <q-td :props="props" class="text-grey-8">
                    {{ props.value }}
                </q-td>
            </template>
        </q-table>
    </q-card-section>
</q-card>
            </div>
        </q-tab-panel>

        <q-tab-panel name="employee" class="q-pa-none">
            <div class="row q-col-gutter-md q-mb-lg">
                <div class="col-12 col-md-4">
                    <q-card class="bg-teal-9 text-white shadow-green">
                        <q-card-section class="row items-center">
                            <q-icon name="groups" size="50px" class="q-mr-md opacity-40" />
                            <div>
                                <div class="text-h4 text-weight-bold">{{ mesStore.employeeStats.length }}</div>
                                <div class="text-subtitle2 opacity-80">Operadores Ativos</div>
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
                <div class="col-12 col-md-4">
                    <q-card class="bg-teal-10 text-white shadow-sm">
                        <q-card-section class="row items-center">
                            <q-icon name="schedule" size="50px" class="q-mr-md opacity-40" />
                            <div>
                                <div class="text-h4 text-weight-bold">{{ totalHoursFormatted }}h</div>
                                <div class="text-subtitle2 opacity-80">Horas Totais Apontadas</div>
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
                <div class="col-12 col-md-4">
                    <q-card class="bg-orange-9 text-white shadow-sm">
                        <q-card-section class="row items-center">
                            <q-icon name="trending_up" size="50px" class="q-mr-md opacity-40" />
                            <div>
                                <div class="text-h4 text-weight-bold">{{ avgEfficiency }}%</div>
                                <div class="text-subtitle2 opacity-80">Eficiência Média da Equipe</div>
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
            </div>

            <q-card class="glass-card shadow-sm">
                <q-card-section>
                    <div class="text-h6 text-weight-bold text-teal-10 q-mb-md row items-center">
                        <q-icon name="leaderboard" class="q-mr-sm" /> Ranking de Produtividade
                    </div>
                    
                    <q-table
                        :rows="mesStore.employeeStats"
                        :columns="employeeColumns"
                        row-key="id"
                        flat bordered
                        class="glass-table cursor-pointer hover-effect-table"
                        :pagination="{ rowsPerPage: 20 }"
                        separator="cell"
                        @row-click="onOperatorClick"
                    >
                        <template v-slot:body-cell-employee_name="props">
                            <q-td :props="props" class="row items-center no-wrap">
                                <q-avatar color="primary" text-color="white" size="32px" class="q-mr-sm shadow-1">
                                    {{ props.value.charAt(0).toUpperCase() }}
                                </q-avatar>
                                <div class="text-weight-bold text-teal-10">{{ props.value }}</div>
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
                                            class="glass-progress"
                                        />
                                    </div>
                                    <div class="text-weight-bold text-teal-10">{{ props.value }}%</div>
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
                                        text-color="negative"
                                        class="q-pa-xs border-red-soft"
                                    >
                                        {{ reason.label }} ({{ reason.count }})
                                    </q-badge>
                                </div>
                                <span v-else class="text-teal-5 italic">Sem paradas registradas</span>
                            </q-td>
                        </template>
                        
                        <template v-slot:body-cell-total_hours="props">
                            <q-td :props="props" class="text-grey-8">{{ props.value }}</q-td>
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
import { date, exportFile, useQuasar, setCssVar } from 'quasar';
import type { QTableColumn } from 'quasar';
import { useMesStore } from 'stores/mes-store';
import type { EmployeeStat } from 'stores/mes-store';
import { useProductionStore } from 'stores/production-store';
import { ProductionService, type MachineStats } from 'src/services/production-service';
import { useRouter } from 'vue-router';

const $q = useQuasar();
const router = useRouter();
const mesStore = useMesStore();
const productionStore = useProductionStore();

const activeTab = ref('machine'); 
const filterDate = ref(date.formatDate(new Date(), 'YYYY-MM-DD'));
const selectedMachine = ref<number | null>(null);
const isLoading = ref(false);
const machineStats = ref<MachineStats | null>(null);

const machineOptions = computed(() => 
    productionStore.machinesList.map(m => ({ label: `${m.brand} ${m.model}`, value: m.id }))
);

const columns: QTableColumn[] = [
  { name: 'timestamp', label: 'Data/Hora', field: 'timestamp', align: 'left', sortable: true },
  { name: 'event_type', label: 'Tipo Evento', field: 'event_type', align: 'left', sortable: true },
  { name: 'new_status', label: 'Status', field: 'new_status', align: 'center', sortable: true },
  { name: 'reason', label: 'Motivo', field: 'reason', align: 'left', sortable: true },
  { name: 'operator_name', label: 'Operador', field: 'operator_name', align: 'left', sortable: true },
  { name: 'details', label: 'Detalhes', field: 'details', align: 'left', sortable: true }
];

const employeeColumns: QTableColumn[] = [
    { name: 'employee_name', label: 'Colaborador', field: 'employee_name', align: 'left', sortable: true },
    { name: 'total_hours', label: 'Horas Totais', field: 'total_hours', align: 'center', sortable: true },
    { name: 'productive_hours', label: 'Hrs Produtivas', field: 'productive_hours', align: 'center', sortable: true, classes: 'text-bold text-teal-9' },
    { name: 'unproductive_hours', label: 'Hrs Paradas', field: 'unproductive_hours', align: 'center', sortable: true, classes: 'text-negative' },
    { name: 'efficiency', label: 'Eficiência Geral', field: 'efficiency', align: 'left', sortable: true },
    { name: 'top_reasons', label: 'Principais Ofensores (Paradas)', field: 'top_reasons', align: 'left' },
];

const totalHoursFormatted = computed(() => {
    const total = mesStore.employeeStats.reduce((acc, curr) => acc + curr.total_hours, 0);
    return total.toFixed(1);
});

const avgEfficiency = computed(() => {
    if (mesStore.employeeStats.length === 0) return 0;
    const total = mesStore.employeeStats.reduce((acc, curr) => acc + curr.efficiency, 0);
    return Math.round(total / mesStore.employeeStats.length);
});

function onOperatorClick(_evt: Event, row: EmployeeStat) {
    void router.push(`/users/${row.id}/stats`);
}

function translateEventType(type: string): string {
    const map: Record<string, string> = {
        'LOGIN': 'Entrada (Login)',
        'LOGOUT': 'Saída (Logout)',
        'STATUS_CHANGE': 'Mudança de Status',
        'STEP_START': 'Início de Etapa',
        'STEP_PAUSE': 'Pausa de Etapa',
        'STEP_COMPLETE': 'Conclusão de Etapa',
        'COUNT': 'Apontamento Qtd',
        'MAINTENANCE_REQ': 'Solicitação Manut.',
        'AUTONOMOUS': 'Autonôma',
        'RUNNING': 'Em Operação',
    };
    return map[type] || type;
}


// eslint-disable-next-line @typescript-eslint/no-explicit-any
function translateStatus(status: string, block?: any): string {
    const s = String(status || '').toUpperCase();
    const cat = String(block?.category || '').toUpperCase();
    const duration = block?.duration_min || 0;

    // 1. Regra de Micro-parada (Menos de 5 minutos e não ser Produção)
    const isProducing = s.includes('RUNNING') || s.includes('PRODUCING') || s.includes('OPERAÇÃO');
    if (cat === 'MICRO_STOP' || (duration > 0 && duration < 5 && !isProducing)) {
        return 'MICRO-PARADA';
    }
    
    if (isProducing) return 'EM OPERAÇÃO';
    if (s.includes('PAUSED') || s.includes('STOPPED') || s.includes('PARADA')) return 'PAUSADA';
    if (s.includes('MAINTENANCE') || s.includes('MANUTENÇÃO')) return 'MANUTENÇÃO';
    if (s.includes('IDLE') || s.includes('DISPONÍVEL')) return 'DISPONÍVEL';
    if (s.includes('SETUP')) return 'EM SETUP';
    
    return status;
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getGanttColor(block: any) {
    // Adicionamos .trim() em tudo para evitar que um espaço em branco quebre a lógica
    const s = String(block.status || '').toUpperCase().trim();
    const cat = String(block.category || '').toUpperCase().trim();
    const duration = block.duration_min || 0;
    const reason = String(block.reason || '').toUpperCase().trim(); 

    // 0. PRIORIDADE MÁXIMA: SEM MOTIVO (MARROM)
    // Cobre "SEM MOTIVO", "STATUS: PARADA" (que é o padrão do backend) ou quando vier totalmente vazio.
    if (
        reason === 'SEM MOTIVO' || 
        reason === 'STATUS: PARADA' || 
        ((s.includes('PAUSED') || s.includes('PARADA') || s === '0') && !reason)
    ) {
        return 'brown'; // Deixamos apenas 'brown' para o Quasar reconhecer a classe nativa bg-brown
    }

    // 1. REGRA DE MICRO-PARADA (PRETO)
    const isProducing = s.includes('RUNNING') || s.includes('PRODUCING') || s.includes('OPERAÇÃO') || s === '1';
    
    if (cat === 'MICRO_STOP' || (duration > 0 && duration < 5 && !isProducing)) {
        return 'black';
    }

    // 2. Outras cores normais
    if (s === 'AUTONOMOUS') return 'blue';
    if (s.includes('MAINTENANCE') || s.includes('MANUTENÇÃO')) return 'red';
    if (s.includes('SETUP') || s.includes('PREPARAÇÃO')) return 'purple';
    if (isProducing) return 'green';
    if (s.includes('PAUSED') || s.includes('STOPPED') || s.includes('PARADA') || s === '0') return 'orange';
    
    return 'grey';
}

function getStatusColor(status: string) {
    const s = String(status).toUpperCase();
    
    // Se o backend já mandou como MICRO_STOP
    if (s === 'MICRO_STOP') return 'black';
    
    if (s.includes('RUNNING') || s.includes('OPERAÇÃO') || s.includes('EM USO')) return 'positive';
    if (s.includes('STOPPED') || s.includes('PAUSA')) return 'orange';
    if (s.includes('MAINTENANCE') || s.includes('MANUTENÇÃO')) return 'negative';
    if (s.includes('IDLE') || s.includes('DISPONÍVEL')) return 'grey-7';
    if (s.includes('SETUP')) return 'purple';
    return 'grey';
}

function getEfficiencyColor(val: number) {
    if (val >= 90) return 'positive';
    if (val >= 75) return 'teal-9';
    if (val >= 50) return 'warning';
    return 'negative';
}

function getOeeLabel(val?: number) {
    if (val === undefined || val === null) return 'N/A';
    if (val >= 85) return 'Excelente';
    if (val >= 65) return 'Aceitável';
    return 'Crítico';
}

function getOeeColor(val?: number) {
    if (val === undefined || val === null) return 'grey-7';
    if (val >= 85) return 'positive'; 
    if (val >= 65) return 'warning'; 
    return 'red-10';                  
}

function getBlockWidth(minutes: number) {
    return (minutes / 1440) * 100;
}

function formatTime(isoStr: string) {
    return new Date(isoStr).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

async function refreshData() {
    isLoading.value = true;
    try {
        await mesStore.fetchEmployeeStats(filterDate.value, filterDate.value);
        if (selectedMachine.value) {
            await mesStore.fetchDailyTimeline(selectedMachine.value, filterDate.value);
            await mesStore.fetchMachineOEE(selectedMachine.value, filterDate.value, filterDate.value);
            machineStats.value = await ProductionService.getMachineStats(selectedMachine.value, filterDate.value);
        }
    } catch (e) {
        console.error(e);
        $q.notify({ type: 'negative', message: 'Erro ao atualizar dados.' });
    } finally {
        isLoading.value = false;
    }
}

function exportToCsv() {
    let content = '';
    let filename = '';

    if (activeTab.value === 'machine') {
        if (!selectedMachine.value) {
            $q.notify({ type: 'warning', message: 'Selecione uma máquina primeiro.' });
            return;
        }
        filename = `Historico_Maquina_${filterDate.value}.csv`;
        content = 'Data/Hora;Evento;Status;Motivo;Operador;Detalhes\n';
        
        mesStore.rawLogs.forEach(row => {
            const cleanReason = (row.reason || '').replace(/;/g, ',');
            const cleanDetails = (row.details || '').replace(/;/g, ',');
            content += `${new Date(row.timestamp).toLocaleString()};${translateEventType(row.event_type)};${translateStatus(row.new_status || '')};${cleanReason};${row.operator_name || ''};${cleanDetails}\n`;
        });
    } else {
        filename = `Ranking_Operadores_${filterDate.value}.csv`;
        content = 'Colaborador;Horas Totais;Horas Produtivas;Horas Paradas;Eficiencia\n';
        mesStore.employeeStats.forEach(row => {
            content += `${row.employee_name};${row.total_hours};${row.productive_hours};${row.unproductive_hours};${row.efficiency}%\n`;
        });
    }

    const status = exportFile(filename, content, 'text/csv');
    if (status !== true) {
        $q.notify({ type: 'negative', message: 'Erro ao baixar arquivo' });
    }
}

function printReport() {
    const routeData = router.resolve({
        path: '/print/mes-report',
        query: { 
            date: filterDate.value, 
            machineId: selectedMachine.value,
            type: activeTab.value 
        }
    });
    window.open(routeData.href, '_blank');
}

onMounted(async () => {
    setCssVar('primary', '#128c7e');
    await productionStore.fetchAvailableMachines();
    if (machineOptions.value && machineOptions.value.length > 0 && machineOptions.value[0]) {
        selectedMachine.value = machineOptions.value[0].value;
        void refreshData();
    }
});
</script>

<style scoped lang="scss">
/* Estilização Trucar MES - Identidade Trucar com lógica original preservada */
.bg-glass-layout {
  background-color: #f0f4f4;
  min-height: 100vh;
  transition: background-color 0.3s;
}

.text-black { color: #000000 !important; }
.text-gradient-trucar {
  background: linear-gradient(to right, #128c7e, #70c0b0);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Glassmorphism Classes */
.glass-card {
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid rgba(18, 140, 126, 0.1);
  border-radius: 12px;
}

.glass-input {
  background: rgba(255, 255, 255, 0.5) !important;
  backdrop-filter: blur(8px);
  border-radius: 4px;
}

.glass-menu {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(10px);
}

.glass-badge {
  background: rgba(18, 140, 126, 0.1) !important;
  color: #128c7e !important;
  border: 1px solid rgba(18, 140, 126, 0.2);
}

.glass-badge-status {
  backdrop-filter: blur(4px);
  border: 1px solid rgba(0,0,0,0.05);
}

.glass-table {
  background: transparent !important;
  :deep(.q-table__card) { background: transparent; }
  :deep(thead tr) { background: rgba(18, 140, 126, 0.05); }
}

/* Bordas Coloridas Originais (Preservadas) */
.border-left-green { border-left: 5px solid #4caf50; }
.border-left-blue { border-left: 5px solid #2196f3; }
.border-left-orange { border-left: 5px solid #ff9800; }
.border-left-red { border-left: 5px solid #f44336; }
.border-left-purple { border-left: 5px solid #9C27B0; }
.border-left-black { border-left: 5px solid #000000; }

.legend-dot { width: 12px; height: 12px; border-radius: 2px; }

.hover-highlight:hover {
  filter: brightness(1.1);
  transform: scaleY(1.05);
  cursor: pointer;
  z-index: 10;
  box-shadow: 0 4px 12px rgba(18, 140, 126, 0.2);
}

.shadow-green { box-shadow: 0 4px 14px 0 rgba(18, 140, 126, 0.2); }
.border-bottom-light { border-bottom: 1px solid rgba(18, 140, 126, 0.1); }
.bg-teal-gradient-faded { background: linear-gradient(135deg, rgba(112, 192, 176, 0.2) 0%, transparent 100%); }

.hover-teal:hover { text-decoration: underline; color: #128c7e; }
.font-monospace { font-family: 'JetBrains Mono', monospace; }

.animate-fade { animation: fadeIn 0.8s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.shadow-red {
  box-shadow: 0 0 12px rgba(211, 47, 47, 0.7); 
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.animate-pulse {
  animation: pulse-red 2s infinite;
}

@keyframes pulse-red {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.8; }
  100% { transform: scale(1); opacity: 1; }
}

/* =========================================
   DARK MODE OVERRIDES (DARK FOREST THEME)
   ========================================= */
.body--dark {
  .bg-glass-layout { 
    background-color: #05100e !important; 
  }

  .glass-card {
    background: rgba(5, 20, 18, 0.7) !important;
    border-color: rgba(18, 140, 126, 0.2);
    color: #e0f2f1;
  }

  .glass-input {
    background: rgba(18, 140, 126, 0.1) !important;
    :deep(.q-field__native), :deep(.q-field__label) {
        color: #b2dfdb !important;
    }
  }

  .glass-menu {
    background: rgba(5, 20, 18, 0.95) !important;
    border: 1px solid rgba(18, 140, 126, 0.3);
  }

  .text-teal-9 { color: #80cbc4 !important; } /* Light teal */
  .text-teal-10 { color: #ffffff !important; } /* White */
  .text-grey-8, .text-grey-7, .text-grey-6 { color: #b0bec5 !important; } /* Light grey */
  .opacity-80 { opacity: 0.9; }

  /* Gantt Chart Container */
  .gantt-container.bg-grey-3 {
    background-color: rgba(255, 255, 255, 0.1) !important;
  }
  .gantt-idle {
    background-color: rgba(255, 255, 255, 0.05) !important;
    color: #90a4ae !important;
  }

  /* Table Stripes/Head */
  .glass-table {
    :deep(thead tr) { background: rgba(18, 140, 126, 0.2); }
    :deep(tbody tr:hover) { background: rgba(18, 140, 126, 0.15) !important; }
  }

  .tab-text-color {
    color: #80cbc4 !important;
  }
}
</style>
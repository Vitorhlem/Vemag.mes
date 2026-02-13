<template>
  <div class="print-doc q-pa-md">
    
    <header class="report-header q-mb-xl">
        <div class="row justify-between items-end">
            <div class="col-auto">
                <div class="row items-center q-mb-sm">
                    <q-icon name="precision_manufacturing" size="32px" class="text-primary q-mr-sm" />
                    <div class="text-h5 text-weight-900 text-uppercase tracking-wide text-primary">TruMachine</div>
                </div>
                <div class="text-caption text-grey-6 text-uppercase tracking-widest">Relatório de Inteligência Industrial</div>
            </div>
            <div class="col-auto text-right">
                <div class="report-meta">
                    <div class="meta-item">
                        <span class="label">Referência</span>
                        <span class="value">{{ formattedDate }}</span>
                    </div>
                    <div class="meta-item">
                        <span class="label">Unidade</span>
                        <span class="value">Fabrica 01 - Matriz</span>
                    </div>
                    <div class="meta-item">
                        <span class="label">Emissão</span>
                        <span class="value">{{ new Date().toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit'}) }}</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="header-line"></div>
    </header>

    <div v-if="isLoading" class="absolute-center text-center">
      <q-spinner-dots size="4em" color="primary" />
      <div class="text-grey-5 q-mt-sm text-caption">Consolidando dados...</div>
    </div>

    <main v-else class="report-body">
      
      <div v-if="reportType === 'machine'">
        
        <div class="row items-center q-mb-lg">
            <div class="col">
                <h1 class="text-h4 text-weight-bold q-my-none text-blue-grey-10">{{ machineName }}</h1>
                <div class="text-subtitle2 text-grey-6">Análise de Performance Diária</div>
            </div>
            <div class="col-auto">
                <div class="status-pill" :class="getGlobalStatusClass(machineStats)">
                    <q-icon name="circle" size="8px" class="q-mr-xs" /> Status Final
                </div>
            </div>
        </div>

        <div class="kpi-stripe q-mb-xl">
           <div class="kpi-item">
              <div class="icon-box bg-green-1 text-green-9"><q-icon name="settings_power" size="20px"/></div>
              <div>
                  <div class="label">Produção</div>
                  <div class="value">{{ machineStats?.formatted_running_operator || '00:00' }}</div>
                  <div class="sub">Tempo Efetivo</div>
              </div>
           </div>
           
           <div class="separator-v"></div>

           <div class="kpi-item">
              <div class="icon-box bg-purple-1 text-purple-9"><q-icon name="build_circle" size="20px"/></div>
              <div>
                  <div class="label">Setup</div>
                  <div class="value">{{ machineStats?.formatted_setup || '00:00' }}</div>
                  <div class="sub">Tempo de Ajuste</div>
              </div>
           </div>

           <div class="separator-v"></div>

           <div class="kpi-item">
              <div class="icon-box bg-orange-1 text-orange-9"><q-icon name="timer_off" size="20px"/></div>
              <div>
                  <div class="label">Paradas (Perda)</div>
                  <div class="value">{{ machineStats?.formatted_pause || '00:00' }}</div>
                  <div class="sub">Micro Paradas</div>
              </div>
           </div>

           <div class="separator-v"></div>

           <div class="kpi-item">
              <div class="icon-box bg-red-1 text-red-9"><q-icon name="warning" size="20px"/></div>
              <div>
                  <div class="label">Manutenção</div>
                  <div class="value">{{ machineStats?.formatted_maintenance || '00:00' }}</div>
                  <div class="sub">Indisponibilidade</div>
              </div>
           </div>
        </div>

        <div class="row q-col-gutter-xl q-mb-xl">
            <div class="col-4">
                <div class="oee-display">
                    <div class="oee-circle-bg">
                        <q-circular-progress
                            show-value
                            font-size="28px"
                            :value="mesStore.oeeData?.oee_percentage || 0"
                            size="140px"
                            :thickness="0.15"
                            color="primary"
                            track-color="grey-2"
                            class="text-blue-grey-10 text-weight-bold"
                        >
                            {{ mesStore.oeeData?.oee_percentage || 0 }}%
                        </q-circular-progress>
                    </div>
                    <div class="text-center q-mt-md">
                        <div class="text-h6 text-weight-bold">Disponibilidade</div>
                        <div class="text-caption text-grey-6">Overall Equipment Effectiveness</div>
                    </div>
                </div>
            </div>

            <div class="col-8 column justify-center">
                <div class="metric-row q-mb-md">
                    <div class="row justify-between q-mb-xs">
                        <span class="text-weight-bold text-grey-8"><q-icon name="check_circle" class="q-mr-sm text-grey-5"/>Disponibilidade</span>
                        <span class="text-weight-bold">{{ mesStore.oeeData?.availability || 0 }}%</span>
                    </div>
                    <q-linear-progress :value="(mesStore.oeeData?.availability || 0)/100" color="primary" rounded size="8px" class="bg-grey-2"/>
                </div>

                <div class="metric-row q-mb-md">
                    <div class="row justify-between q-mb-xs">
                        <span class="text-weight-bold text-grey-8"><q-icon name="speed" class="q-mr-sm text-grey-5"/>Performance</span>
                        <span class="text-weight-bold">{{ mesStore.oeeData?.performance || 0 }}%</span>
                    </div>
                    <q-linear-progress :value="(mesStore.oeeData?.performance || 0)/100" color="orange" rounded size="8px" class="bg-grey-2"/>
                </div>

                <div class="metric-row">
                    <div class="row justify-between q-mb-xs">
                        <span class="text-weight-bold text-grey-8"><q-icon name="verified" class="q-mr-sm text-grey-5"/>Qualidade</span>
                        <span class="text-weight-bold">{{ mesStore.oeeData?.quality || 0 }}%</span>
                    </div>
                    <q-linear-progress :value="(mesStore.oeeData?.quality || 0)/100" color="positive" rounded size="8px" class="bg-grey-2"/>
                </div>
            </div>
        </div>

        <div class="section-container q-mb-xl">
            <div class="section-header row justify-between items-end q-mb-md">
                <div class="text-subtitle1 text-weight-bold text-uppercase tracking-wide text-grey-8">Linha do Tempo (Turno 24h)</div>
                <div class="legend row q-gutter-md text-caption text-grey-6">
                    <div class="row items-center"><div class="dot bg-green"></div> Operação</div>
                    <div class="row items-center"><div class="dot bg-purple"></div> Setup</div>
                    <div class="row items-center"><div class="dot bg-orange"></div> Pausa</div>
                    <div class="row items-center"><div class="dot bg-red"></div> Manutenção</div>
                </div>
            </div>
            
            <div class="gantt-track rounded-borders overflow-hidden">
                <div 
                    v-for="(block, idx) in mesStore.timeline" 
                    :key="idx"
                    class="gantt-bar"
                    :class="`bg-${getGanttColor(block)}`"
                    :style="{ width: getBlockWidth(block.duration_min) + '%' }"
                ></div>
            </div>
            <div class="row justify-between text-caption text-grey-5 q-mt-xs font-mono">
                <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>23:59</span>
            </div>
        </div>

        <div class="row q-col-gutter-xl">
            <div class="col-7">
                <div class="text-subtitle1 text-weight-bold text-uppercase tracking-wide text-grey-8 q-mb-md">
                    Top 5 Ofensores (Paradas)
                </div>
                <table class="clean-table full-width">
                    <thead>
                        <tr>
                            <th class="text-left">Motivo da Parada</th>
                            <th class="text-right">Freq.</th>
                            <th class="text-right">Impacto</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="(stop, idx) in topStoppages" :key="idx">
                            <td>
                                <div class="row items-center">
                                    <div class="rank-circle">{{ idx + 1 }}</div>
                                    <span class="text-weight-medium text-grey-9">{{ stop.reason }}</span>
                                </div>
                            </td>
                            <td class="text-right text-grey-7">{{ stop.count }}x</td>
                            <td class="text-right">
                                <span class="text-weight-bold text-red-9">{{ stop.duration }} min</span>
                            </td>
                        </tr>
                        <tr v-if="topStoppages.length === 0">
                            <td colspan="3" class="text-center text-grey-5 q-py-lg italic">
                                Sem registros de paradas no período.
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="col-5">
                <div class="text-subtitle1 text-weight-bold text-uppercase tracking-wide text-grey-8 q-mb-md">
                    Últimos Eventos
                </div>
                <div class="events-list">
                    <div v-for="log in limitedLogs" :key="log.id" class="event-row row items-center no-wrap">
                        <div class="col-auto q-mr-md text-caption font-mono text-grey-6">
                            {{ new Date(log.timestamp).toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit'}) }}
                        </div>
                        <div class="col">
                            <div class="text-weight-medium text-grey-9 text-body2">{{ translateEventType(log.event_type) }}</div>
                            <div class="text-caption text-grey-5 ellipsis">{{ log.operator_name || 'Sistema' }}</div>
                        </div>
                        <div class="col-auto">
                            <div class="status-dot" :class="getStatusDotClass(log.new_status)"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

      </div>

      <div v-else>
         <div class="row items-center justify-between q-mb-xl">
            <div>
                <h1 class="text-h4 text-weight-bold q-my-none text-blue-grey-10">Ranking de Operadores</h1>
                <div class="text-subtitle2 text-grey-6">Produtividade Individual e Eficiência</div>
            </div>
         </div>
         
         <table class="clean-table large-table full-width">
            <thead>
               <tr>
                  <th class="text-left pl-lg">Colaborador</th>
                  <th class="text-center">Hrs Totais</th>
                  <th class="text-center">Hrs Produtivas</th>
                  <th class="text-center">Hrs Paradas</th>
                  <th class="text-center">Eficiência</th>
               </tr>
            </thead>
            <tbody>
               <tr v-for="(row, idx) in mesStore.employeeStats" :key="row.id">
                  <td class="pl-lg">
                      <div class="row items-center">
                          <q-avatar size="32px" color="grey-3" text-color="grey-8" class="q-mr-md text-weight-bold">
                              {{ row.employee_name.charAt(0) }}
                          </q-avatar>
                          <div>
                              <div class="text-weight-bold text-grey-9">{{ row.employee_name }}</div>
                              <div class="text-caption text-grey-5" v-if="idx < 3">
                                <q-icon name="star" color="orange" size="12px"/> Top Performer
                              </div>
                          </div>
                      </div>
                  </td>
                  <td class="text-center text-grey-8">{{ row.total_hours.toFixed(1) }}h</td>
                  <td class="text-center text-green-9 text-weight-bold">{{ row.productive_hours.toFixed(1) }}h</td>
                  <td class="text-center text-red-9">{{ row.unproductive_hours.toFixed(1) }}h</td>
                  <td class="text-center">
                     <div class="efficiency-gauge">
                         <div class="bar-bg">
                             <div class="bar-fill" :style="{ width: row.efficiency + '%', backgroundColor: getEfficiencyColor(row.efficiency) }"></div>
                         </div>
                         <span class="value">{{ row.efficiency }}%</span>
                     </div>
                  </td>
               </tr>
            </tbody>
         </table>
      </div>

    </main>

    <footer class="report-footer">
        <div class="row justify-between items-center text-grey-5 text-caption">
            <div>TruMachine Analytics &copy; {{ new Date().getFullYear() }}</div>
            <div>Página 1 de 1</div>
        </div>
    </footer>

  </div>
</template>

<script setup lang="ts">
/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useMesStore } from 'stores/mes-store';
import { ProductionService, type MachineStats } from 'src/services/production-service';
import { useProductionStore } from 'stores/production-store';

const route = useRoute();
const mesStore = useMesStore();
const productionStore = useProductionStore();

const isLoading = ref(true);
const machineStats = ref<MachineStats | null>(null);

const filterDate = computed(() => route.query.date as string);
const selectedMachine = computed(() => Number(route.query.machineId));
const reportType = computed(() => route.query.type as string || 'machine'); 
const machineName = ref('');

const formattedDate = computed(() => {
   if(!filterDate.value) return '';
   return new Date(filterDate.value + 'T00:00:00').toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' });
});

// Lógica Pareto (Top Ofensores)
const topStoppages = computed(() => {
    const reasonMap: Record<string, { count: number, duration: number }> = {};
    
    // Tenta pegar da timeline para ter duração real
    mesStore.timeline.forEach(block => {
        if (block.reason) {
             const cleanReason = block.reason.split(',')[0].split('-')[0].trim();
             if (!reasonMap[cleanReason]) reasonMap[cleanReason] = { count: 0, duration: 0 };
             reasonMap[cleanReason].duration += Math.round(block.duration_min);
             // Incrementa contagem se for um bloco novo (aproximação)
             reasonMap[cleanReason].count++;
        }
    });

    // Se timeline vazia, tenta raw logs (fallback)
    if (Object.keys(reasonMap).length === 0) {
        mesStore.rawLogs.forEach(log => {
            if (log.reason && log.new_status && (log.new_status.includes('STOPPED') || log.new_status.includes('PAUSE') || log.new_status.includes('MAINTENANCE'))) {
                const cleanReason = log.reason.split(',')[0].trim();
                if (!reasonMap[cleanReason]) reasonMap[cleanReason] = { count: 0, duration: 0 };
                reasonMap[cleanReason].count++;
                // Estimativa arbitrária de 5 min se não tiver dados
                reasonMap[cleanReason].duration += 5; 
            }
        });
    }

    return Object.entries(reasonMap)
        .map(([reason, stats]) => ({ reason, ...stats }))
        .sort((a, b) => b.duration - a.duration)
        .slice(0, 5); 
});

const limitedLogs = computed(() => {
    return [...mesStore.rawLogs]
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, 5);
});

// Helpers Visuais
function getGlobalStatusClass(stats: any) {
    if (!stats) return 'bg-grey-3 text-grey-8';
    // Lógica simples de exemplo
    return 'bg-green-1 text-green-9 border-green';
}

function getGanttColor(block: any) {
    const s = String(block.status || '').toUpperCase();
    const r = String(block.reason || '').toUpperCase();
    if (s.includes('SETUP') || r.includes('SETUP')) return 'purple';
    if (s.includes('RUNNING') || s.includes('PRODUCING')) return 'green';
    if (s.includes('MAINTENANCE')) return 'red';
    if (s.includes('PAUSED') || s.includes('STOPPED')) return 'orange';
    return 'grey';
}

function getBlockWidth(minutes: number) {
    return (minutes / 1440) * 100;
}

function getStatusDotClass(status: string) {
    const s = String(status || '').toUpperCase();
    if (s.includes('RUNNING')) return 'bg-green';
    if (s.includes('MAINTENANCE')) return 'bg-red';
    if (s.includes('STOPPED') || s.includes('PAUSE')) return 'bg-orange';
    return 'bg-grey';
}

function getEfficiencyColor(val: number) {
    if (val >= 90) return '#21BA45';
    if (val >= 75) return '#2196F3';
    if (val >= 50) return '#F2C037';
    return '#C10015';
}

function translateEventType(type: string): string {
    const map: Record<string, string> = { 'LOGIN': 'Login Operador', 'LOGOUT': 'Saída Operador', 'STATUS_CHANGE': 'Mudança de Estado', 'MAINTENANCE_REQ': 'Chamado Manutenção' };
    return map[type] || type;
}

onMounted(async () => {
   try {
      await productionStore.fetchAvailableMachines();
      
      if (reportType.value === 'machine' && selectedMachine.value) {
         const machine = productionStore.machinesList.find(m => m.id === selectedMachine.value);
         machineName.value = machine ? `${machine.brand} ${machine.model}` : 'Equipamento';
         
         // Fetch em paralelo para performance
         await Promise.all([
             mesStore.fetchDailyTimeline(selectedMachine.value, filterDate.value),
             mesStore.fetchMachineOEE(selectedMachine.value, filterDate.value, filterDate.value),
             mesStore.fetchEmployeeStats(filterDate.value, filterDate.value) // para logs se necessario
         ]);
         
         machineStats.value = await ProductionService.getMachineStats(selectedMachine.value, filterDate.value);
      } else {
         await mesStore.fetchEmployeeStats(filterDate.value, filterDate.value);
      }

   } catch (error) {
      console.error(error);
   } finally {
      isLoading.value = false;
      setTimeout(() => {
         window.print();
      }, 800);
   }
});
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');

.print-doc {
    font-family: 'Inter', sans-serif;
    color: #1f2937;
    background: white;
    max-width: 210mm; /* A4 width */
    margin: 0 auto;
    min-height: 297mm;
    position: relative;
}

/* HEADER */
.report-header { position: relative; }
.header-line { height: 4px; width: 100%; background: linear-gradient(90deg, #1976D2 0%, #0D47A1 100%); margin-top: 15px; border-radius: 2px; }
.tracking-wide { letter-spacing: 0.5px; }
.tracking-widest { letter-spacing: 2px; }
.text-weight-900 { font-weight: 900; }

.report-meta { display: flex; gap: 20px; }
.meta-item { display: flex; flex-direction: column; }
.meta-item .label { font-size: 9px; text-transform: uppercase; color: #9ca3af; font-weight: 600; }
.meta-item .value { font-size: 11px; font-weight: 600; color: #374151; }

/* KPI STRIPE (Executive Summary) */
.kpi-stripe {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); /* Soft shadow for screen, subtle for print */
}
.kpi-item { display: flex; align-items: center; gap: 15px; flex: 1; justify-content: center; }
.icon-box { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.separator-v { width: 1px; height: 40px; background: #f3f4f6; }

.kpi-item .label { font-size: 10px; text-transform: uppercase; font-weight: 700; color: #6b7280; letter-spacing: 0.5px; }
.kpi-item .value { font-size: 18px; font-weight: 800; color: #111827; line-height: 1.2; }
.kpi-item .sub { font-size: 9px; color: #9ca3af; }

/* OEE SECTION */
.oee-display { display: flex; flex-direction: column; align-items: center; }
.oee-circle-bg { position: relative; padding: 10px; border-radius: 50%; background: #f9fafb; border: 1px solid #f3f4f6; }

/* GANTT */
.gantt-track { height: 24px; width: 100%; background: #f3f4f6; display: flex; border-radius: 6px; }
.gantt-bar { height: 100%; }
.legend .dot { width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
.font-mono { font-family: 'Courier New', Courier, monospace; }

/* TABLES */
.clean-table { border-collapse: collapse; width: 100%; }
.clean-table th { 
    text-transform: uppercase; 
    font-size: 10px; 
    color: #9ca3af; 
    font-weight: 700; 
    letter-spacing: 0.5px; 
    padding-bottom: 10px; 
    border-bottom: 2px solid #f3f4f6; 
}
.clean-table td { padding: 12px 0; border-bottom: 1px solid #f9fafb; vertical-align: middle; font-size: 12px; }
.clean-table.large-table td { padding: 16px 0; font-size: 13px; }
.pl-lg { padding-left: 15px !important; }

.rank-circle { 
    width: 20px; height: 20px; background: #f3f4f6; color: #6b7280; 
    border-radius: 50%; font-size: 10px; font-weight: bold; 
    display: flex; align-items: center; justify-content: center; margin-right: 10px; 
}

/* EVENTS LIST */
.events-list { display: flex; flex-direction: column; gap: 10px; }
.event-row { padding: 8px; background: #fcfcfc; border-radius: 6px; border: 1px solid #f3f4f6; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }

/* OPERATOR RANKING */
.efficiency-gauge { display: flex; align-items: center; gap: 10px; width: 100%; justify-content: center; }
.bar-bg { width: 80px; height: 6px; background: #f3f4f6; border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 3px; }
.efficiency-gauge .value { font-weight: bold; font-size: 12px; width: 35px; text-align: right; }

/* STATUS PILL */
.status-pill { 
    font-size: 10px; font-weight: bold; text-transform: uppercase; 
    padding: 4px 10px; border-radius: 20px; display: flex; align-items: center; 
    border: 1px solid transparent; 
}
.border-green { border-color: #bbf7d0; background: #f0fdf4; color: #166534; }

/* FOOTER */
.report-footer { 
    position: absolute; bottom: 0; left: 0; right: 0; padding: 20px; 
    border-top: 1px solid #f3f4f6; 
}

/* PRINT OVERRIDES */
@media print {
    @page { size: A4; margin: 0; }
    .print-doc { 
        width: 100%; max-width: none; margin: 0; padding: 10mm; 
        box-shadow: none; border: none; 
    }
    
    /* Ensure backgrounds print */
    .bg-green-1 { background-color: #dcfce7 !important; }
    .bg-purple-1 { background-color: #f3e8ff !important; }
    .bg-orange-1 { background-color: #ffedd5 !important; }
    .bg-red-1 { background-color: #fee2e2 !important; }
    
    .bg-green { background-color: #21BA45 !important; }
    .bg-purple { background-color: #9C27B0 !important; }
    .bg-orange { background-color: #F2C037 !important; }
    .bg-red { background-color: #C10015 !important; }
    
    .text-grey-6 { color: #4b5563 !important; } /* Darken greys for readability */
    
    /* Hide scrollbars/browser elements handled by window.print() usually, 
       but ensure no overflow */
    body { overflow: hidden; }
}
</style>s
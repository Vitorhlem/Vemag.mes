<template>
  <q-page class="dashboard-bg q-pa-md q-pa-lg-xl">
    
    <div class="row items-center justify-between q-mb-xl animate-fade-down">
      <div class="col-12 col-md-auto">
        <div class="row items-center q-gutter-x-sm">
          <q-icon name="factory" size="2em" class="text-primary opacity-80" />
          <div>
            <div class="text-caption text-uppercase text-teal-9 text-weight-bold letter-spacing-2">
              Visão Geral da Planta
            </div>
            <h1 class="text-h4 text-weight-900 q-my-none text-gradient">
              Painel de Controle
            </h1>
          </div>
        </div>
        <div class="text-subtitle1 text-grey-7 q-mt-sm flex items-center">
          <span>Bem-vindo de volta, <strong>{{ authStore.user?.full_name?.split(' ')[0] }}</strong>.</span>
          <q-badge color="teal-1" text-color="teal-9" class="q-ml-md q-px-sm glass-badge">
            <span class="dot-indicator bg-teal-5 q-mr-xs"></span> Sistema Online
          </q-badge>
        </div>
      </div>

      <div class="col-12 col-md-auto q-mt-md q-md-mt-none">
        <div class="row q-gutter-sm">
           <q-btn 
             flat
             color="teal-10" 
             icon="refresh" 
             label="Atualizar Dados" 
             class="btn-hover-effect glass-btn text-teal-9"
             @click="() => refreshData()" 
             :loading="dashboardStore.isLoading || vehicleStore.isLoading"
           />
           <q-btn-dropdown 
             color="primary" 
             icon="add" 
             label="Ações Rápidas" 
             unelevated 
             class="shadow-4 btn-rounded q-px-lg shadow-green"
             content-class="glass-menu shadow-10"
             dropdown-icon="expand_more"
           >
            <q-list class="q-py-md" style="min-width: 240px">
              <div class="text-caption q-px-md q-mb-sm text-teal-9 text-uppercase text-weight-bold">Cadastro</div>
              
              <q-item clickable v-close-popup @click="() => router.push('/vehicles')" class="item-hover">
                <q-item-section avatar><div class="icon-box bg-teal-1 text-teal-9"><q-icon name="precision_manufacturing" size="20px"/></div></q-item-section>
                <q-item-section>
                   <q-item-label class="text-weight-bold text-teal-10">Nova Máquina</q-item-label>
                   <q-item-label caption class="text-grey-7">Cadastrar ativo</q-item-label>
                </q-item-section>
              </q-item>
              
              <q-separator spaced class="q-mx-md opacity-10" />
              <div class="text-caption q-px-md q-mb-sm text-teal-9 text-uppercase text-weight-bold">Operação</div>

              <q-item clickable v-close-popup @click="() => router.push('/factory/kiosk')" class="item-hover">
                <q-item-section avatar><div class="icon-box bg-cyan-1 text-cyan-9"><q-icon name="monitor" size="20px"/></div></q-item-section>
                <q-item-section>
                   <q-item-label class="text-weight-bold text-teal-10">Modo Kiosk</q-item-label>
                   <q-item-label caption class="text-grey-7">Tela do operador</q-item-label>
                </q-item-section>
              </q-item>
              
              <q-item clickable v-close-popup @click="scheduleMaintenanceGeneral" class="item-hover">
                <q-item-section avatar><div class="icon-box bg-orange-1 text-orange-9"><q-icon name="build_circle" size="20px"/></div></q-item-section>
                <q-item-section>
                   <q-item-label class="text-weight-bold text-teal-10">Solicitar Manutenção</q-item-label>
                   <q-item-label caption class="text-grey-7">Abrir chamado</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>
      </div>
    </div>

    <div v-if="dashboardStore.isLoading && !realTimeStats" class="row q-col-gutter-md animate-pulse">
       <div class="col-12 col-md-3" v-for="n in 4" :key="n">
         <q-card flat class="rounded-xl glass-card q-pa-md">
             <div class="row items-center no-wrap">
                <q-skeleton type="circle" size="50px" class="bg-teal-1" />
                <div class="col q-pl-md">
                    <q-skeleton type="text" width="60%" />
                    <q-skeleton type="rect" height="30px" width="40%" class="q-mt-sm" />
                </div>
             </div>
         </q-card>
       </div>
    </div>

    <div v-else class="fade-in-up">
      
      <div class="row q-col-gutter-md q-mb-xl">
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Ativos Totais" 
            :value="realTimeStats.total" 
            icon="domain" 
            color="teal-9" 
            to="/vehicles" 
            :loading="dashboardStore.isLoading"
            class="full-height glass-card shadow-card hover-scale" 
          />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Em Produção" 
            :value="realTimeStats.running" 
            icon="settings_suggest" 
            color="positive" 
            to="/vehicles?status=Em uso" 
            :loading="dashboardStore.isLoading"
            class="full-height glass-card shadow-card hover-scale" 
          />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg">
          <StatCard 
            label="Em Pausa" 
            :value="realTimeStats.paused" 
            icon="pause_circle" 
            color="orange-9" 
            to="/vehicles?status=Parada" 
            :loading="dashboardStore.isLoading"
            class="full-height glass-card shadow-card hover-scale" 
          />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Disponível" 
            :value="realTimeStats.idle" 
            icon="hourglass_empty" 
            color="warning" 
            to="/vehicles?status=Disponível" 
            :loading="dashboardStore.isLoading"
            class="full-height glass-card shadow-card hover-scale" 
          />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Em Manutenção" 
            :value="realTimeStats.stopped" 
            icon="build" 
            color="negative" 
            to="/maintenance" 
            :loading="dashboardStore.isLoading"
            class="full-height glass-card shadow-card hover-scale" 
          />
        </div>
      </div>

      <div class="text-h6 text-weight-bold text-teal-10 q-mb-md flex items-center">
        <q-icon name="insights" class="q-mr-sm text-teal-6" /> Indicadores de Performance
      </div>
      
      <div class="row q-col-gutter-md q-mb-xl">
         
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Disponibilidade" 
             :value="83.7"
             unit="%" 
             icon="bolt" 
             color="cyan-8" 
             class="metric-clean glass-card"
             :formatter="(v: number) => v.toFixed(1)" 
           />
         </div>
         
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Taxa de Utilização" 
             :value="realTimeStats.utilizationRate" 
             unit="%" 
             icon="pie_chart" 
             color="teal" 
             class="metric-clean glass-card"
             :formatter="(v: number) => `${v.toFixed(1)}%`" 
           />
         </div>
      </div>

      <div class="row q-col-gutter-lg">
        
        <div class="col-12 col-lg-8 column q-gutter-y-lg">
          
          <div class="dashboard-card glass-card shadow-1 q-pa-none overflow-hidden">
             <div class="card-header q-pa-md border-bottom-light row justify-between items-center">
                <div>
                   <div class="text-h6 text-weight-bold text-teal-10">Custos Industriais</div>
                   <div class="text-caption text-grey-6">Análise de gastos por categoria</div>
                </div>
                <q-btn round flat icon="more_horiz" color="teal-7" />
             </div>
             <div class="q-pa-md">
                <ApexChart 
                  v-if="(costAnalysisChart.series[0]?.data.length || 0) > 0" 
                  type="bar" 
                  height="350" 
                  :options="costAnalysisChart.options" 
                  :series="costAnalysisChart.series" 
                />
                <div v-else class="empty-state-box">
                   <div class="bg-teal-1 q-pa-lg rounded-circle q-mb-md">
                      <q-icon name="bar_chart" size="3em" color="teal-3" />
                   </div>
                   <div class="text-teal-9 text-weight-medium">Sem dados financeiros</div>
                   <q-btn outline color="primary" label="Lançar Custos" to="/costs" class="q-mt-md rounded-borders" />
                </div>
             </div>
          </div>

          <div class="dashboard-card glass-card shadow-1 q-pa-none overflow-hidden">
             <div class="card-header q-pa-md border-bottom-light row justify-between items-center bg-teal-gradient-faded">
                 <div class="row items-center">
                    <div class="icon-box-sm bg-teal-1 text-teal-9 q-mr-md"><q-icon name="calendar_month" /></div>
                    <div>
                       <div class="text-subtitle1 text-weight-bold text-teal-10">Agenda de Manutenção</div>
                       <div class="text-caption text-grey-6">Próximas intervenções programadas</div>
                    </div>
                 </div>
                 <q-btn flat dense no-caps color="primary" label="Ver todas" to="/maintenance" icon-right="arrow_forward" />
             </div>
             
             <q-list class="q-py-sm">
                 <q-item v-for="item in mergedMaintenanceList" :key="item.id" class="q-py-md q-px-lg transition-bg hover:bg-teal-5-faded">
                   <q-item-section avatar>
                      <q-avatar 
                        :color="item.is_overdue ? 'red-1' : 'teal-1'" 
                        :text-color="item.is_overdue ? 'negative' : 'primary'" 
                        font-size="24px"
                        class="shadow-1"
                      >
                        <q-icon :name="item.is_overdue ? 'warning' : 'schedule'" />
                      </q-avatar>
                   </q-item-section>
                   
                   <q-item-section>
                     <q-item-label class="text-weight-bold text-body1 text-teal-10">{{ item.info }}</q-item-label>
                     <q-item-label caption class="q-mt-xs">
                         <span v-if="item.is_overdue" class="text-negative flex items-center">
                            <q-icon name="error" size="xs" class="q-mr-xs"/> Atrasada há {{ item.overdue_diff }}h
                         </span>
                         <span v-else class="text-grey-7 flex items-center">
                            <q-icon name="event" size="xs" class="q-mr-xs"/> Vence em: 
                            <span class="text-primary q-ml-xs text-weight-medium bg-teal-1 q-px-xs rounded-borders">{{ item.due_label }}</span>
                         </span>
                     </q-item-label>
                   </q-item-section>
                   
                   <q-item-section side>
                      <q-btn 
                        :color="item.is_overdue ? 'negative' : 'teal-1'" 
                        :text-color="item.is_overdue ? 'white' : 'teal-10'"
                        unelevated 
                        dense 
                        class="q-px-md rounded-borders"
                        :icon="item.is_overdue ? 'priority_high' : 'add'"
                        :label="item.is_overdue ? 'Urgente' : 'Abrir OS'" 
                        @click="scheduleMaintenance(item.id)" 
                      />
                   </q-item-section>
                 </q-item>

                 <div v-if="!mergedMaintenanceList.length" class="empty-state-list full-width">
                    <q-icon name="check_circle" size="4em" class="text-teal-5 q-mb-md" />
                    <div class="text-teal-9 text-weight-medium">Tudo em dia!</div>
                    <div class="text-grey-6">Nenhuma manutenção próxima programada.</div>
                </div>
             </q-list>
          </div>
        </div>

        <div class="col-12 col-lg-4 column q-gutter-y-lg">
          
          <div class="dashboard-card glass-card shadow-1 overflow-hidden">
             <div class="q-pa-md border-bottom-light">
                <div class="text-subtitle1 text-weight-bold text-teal-10">Taxa de utilização</div>
             </div>
             <div class="q-pa-md flex flex-center relative-position" style="min-height: 260px">
                <ApexChart 
                    v-if="fleetStatusChart.series.some((v: number) => v > 0)" 
                    type="donut" 
                    height="280" 
                    :options="fleetStatusChart.options" 
                    :series="fleetStatusChart.series" 
                />
                <div v-else class="text-center text-teal-5 absolute-center column flex-center">
                   <q-icon name="pie_chart" size="4em" color="teal-1" />
                   <div class="text-caption q-mt-sm">Sem dados de status</div>
                </div>
             </div>
          </div>

          <div class="dashboard-card glass-card shadow-1 overflow-hidden border-top-critical">
             <div class="card-header q-pa-md row justify-between items-center alert-header-bg">
                <div class="row items-center text-negative">
                   <div class="pulse-icon bg-red-1 q-mr-md flex flex-center" style="width: 32px; height: 32px; border-radius: 50%">
                      <q-icon name="notifications_active" size="18px"/>
                   </div>
                   <div class="text-subtitle1 text-weight-bold">Alertas Andon</div>
                </div>
                <q-badge color="red-1" text-color="negative" :label="processedAlerts.length" rounded class="glass-badge" />
             </div>
             
             <q-scroll-area style="height: 400px;" :thumb-style="{ width: '6px', borderRadius: '3px', backgroundColor: 'rgba(18, 140, 126, 0.2)' }">
               <q-list separator>
                 <q-item v-for="alert in processedAlerts" :key="alert.id" class="q-py-md q-px-md hover:bg-red-1-faded transition-bg cursor-pointer">
                   <q-item-section top avatar>
                      <div class="relative-position">
                        <q-avatar icon="warning" color="negative" text-color="white" size="md" font-size="20px" class="shadow-2" />
                        <span class="absolute-bottom-right bg-white rounded-circle border-1 border-red" style="width: 10px; height: 10px; bottom: 0; right: -2px;"></span>
                      </div>
                   </q-item-section>
                   
                   <q-item-section>
                     <q-item-label class="text-weight-bold text-grey-9 alert-title">{{ alert.title }}</q-item-label>
                     <q-item-label caption class="text-grey-7 text-caption-2 q-mt-xs" :lines="2">{{ alert.subtitle }}</q-item-label>
                   </q-item-section>
                   
                   <q-item-section side top>
                      <span class="text-xs text-grey-5 font-medium">Hoje</span>
                   </q-item-section>
                 </q-item>

                 <div v-if="processedAlerts.length === 0" class="column flex-center full-height q-pa-xl text-center">
                     <div class="bg-teal-1 q-pa-lg rounded-circle q-mb-md">
                        <q-icon name="verified" size="3em" color="teal-5" />
                     </div>
                     <div class="text-teal-9 text-weight-medium">Sem chamados abertos</div>
                     <div class="text-grey-6 text-caption">Sua operação está rodando suavemente.</div>
                 </div>
               </q-list>
             </q-scroll-area>
          </div>

        </div>
      </div>
    </div>
    
    <CreateRequestDialog 
      v-model="showCreateMaintenanceDialog"
      :pre-selected-vehicle-id="selectedVehicleIdForMaintenance"
      :maintenance-type="createDialogType"
      @request-created="refreshData"
    />
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { setCssVar, useQuasar } from 'quasar'; // Adicionado useQuasar
import { useDashboardStore } from 'stores/dashboard-store';
import { useAuthStore } from 'stores/auth-store';
import { useVehicleStore } from 'stores/vehicle-store'; 
import ApexChart from 'vue3-apexcharts';
import StatCard from 'components/StatCard.vue';
import MetricCard from 'components/MetricCard.vue'; 
import CreateRequestDialog from 'components/maintenance/CreateRequestDialog.vue';

interface ICostItem {
    cost_type: string;
    total_amount: number;
}

interface UpcomingMaintenance {
    vehicle_id: number;
    vehicle_info: string;
    due_date?: string;
    due_km?: number;
}

interface UnifiedMaintenanceItem {
    id: number;
    info: string;
    due_label: string;
    is_overdue: boolean;
    overdue_diff: string | number;
}

const dashboardStore = useDashboardStore();
const authStore = useAuthStore();
const vehicleStore = useVehicleStore(); 
const router = useRouter();
const $q = useQuasar(); // Para detectar modo escuro nos gráficos

const showCreateMaintenanceDialog = ref(false); 
const selectedVehicleIdForMaintenance = ref<number | null>(null);
const createDialogType = ref<'PREVENTIVA' | 'CORRETIVA'>('CORRETIVA');

const managerData = computed(() => dashboardStore.managerDashboard);
const upcomingMaintenances = computed(() => managerData.value?.upcoming_maintenances as UpcomingMaintenance[] || []);
const recentAlerts = computed(() => managerData.value?.recent_alerts || []);
const processedAlerts = computed(() => recentAlerts.value);

// --- CORES REATIVAS PARA GRÁFICOS (DARK MODE) ---
const chartTextColor = computed(() => $q.dark.isActive ? '#cbd5e1' : '#64748b');
const chartGridColor = computed(() => $q.dark.isActive ? 'rgba(112, 192, 176, 0.1)' : 'rgba(18, 140, 126, 0.1)');

const realTimeStats = computed(() => {
  const allMachines = vehicleStore.vehicles;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getStatus = (m: any) => String(m.status || '').toUpperCase().trim();
  const total = allMachines.length;
  
  const running = allMachines.filter(m => ['EM USO', 'IN_USE', 'RUNNING', 'EM OPERAÇÃO', 'PRODUCING'].includes(getStatus(m))).length;
  const stopped = allMachines.filter(m => ['EM MANUTENÇÃO', 'MAINTENANCE', 'SETUP', 'QUEBRADA'].includes(getStatus(m))).length;
  const paused = allMachines.filter(m => ['PARADA', 'STOPPED', 'PAUSED', 'EM PAUSA'].includes(getStatus(m))).length;
  const idle = allMachines.filter(m => ['DISPONÍVEL', 'DISPONIVEL', 'AVAILABLE', 'IDLE', 'LIVRE'].includes(getStatus(m))).length;

  return { total, running, stopped, paused, idle, utilizationRate: total > 0 ? (running / total) * 100 : 0 };
});

const overdueVehicles = computed(() => {
   return vehicleStore.vehicles.filter(v => {
      if (v.next_maintenance_km && v.current_engine_hours) {
          return v.current_engine_hours >= v.next_maintenance_km;
      }
      return false;
   });
});

const mergedMaintenanceList = computed(() => {
    const list: UnifiedMaintenanceItem[] = [];
    const addedIds = new Set<number>();

    overdueVehicles.value.forEach(v => {
        const diff = (v.current_engine_hours || 0) - (v.next_maintenance_km || 0);
        list.push({
            id: v.id,
            info: `${v.brand} ${v.model}`,
            due_label: `${v.next_maintenance_km} h`,
            is_overdue: true,
            overdue_diff: diff.toFixed(0)
        });
        addedIds.add(v.id);
    });

    upcomingMaintenances.value.forEach(m => {
        if (!addedIds.has(m.vehicle_id)) {
            list.push({
                id: m.vehicle_id,
                info: m.vehicle_info,
                due_label: m.due_date ? new Date(m.due_date).toLocaleDateString() : `${m.due_km} h`,
                is_overdue: false,
                overdue_diff: 0
            });
        }
    });

    return list;
});

const variableCostTotal = computed(() => {
  const costs: ICostItem[] = managerData.value?.costs_by_category || [];
  const items = costs.filter(c => ['energia', 'insumos', 'manutenção', 'peças'].some(term => c.cost_type.toLowerCase().includes(term)));
  return items.reduce((acc, curr) => acc + curr.total_amount, 0);
});

// --- GRÁFICOS COM TEMA ---
const costAnalysisChart = computed(() => {
  const data: ICostItem[] = managerData.value?.costs_by_category || [];
  const categories = data.map(item => item.cost_type);
  const series = [{ name: 'Custo (R$)', data: data.map(item => item.total_amount) }];
  
  return { 
      series, 
      options: { 
          chart: { type: 'bar', toolbar: { show: false }, fontFamily: 'Inter, sans-serif', background: 'transparent' }, 
          plotOptions: { bar: { borderRadius: 6, columnWidth: '50%', distributed: false } },
          theme: { mode: $q.dark.isActive ? 'dark' : 'light' },
          xaxis: { 
            categories,
            labels: { style: { colors: chartTextColor.value, fontSize: '12px' } },
            axisBorder: { show: false },
            axisTicks: { show: false }
          },
          yaxis: {
            labels: { style: { colors: chartTextColor.value }, formatter: (val: number) => `R$ ${val}` }
          },
          colors: ['#128c7e'], 
          grid: { borderColor: chartGridColor.value, strokeDashArray: 4 },
          dataLabels: { enabled: false },
          tooltip: { theme: $q.dark.isActive ? 'dark' : 'light' }
      } 
  };
});

const fleetStatusChart = computed(() => {
    const s = realTimeStats.value;
    const series = [s.idle, s.running, s.stopped];
    return {
        series,
        options: {
            labels: ['Aguardando', 'Produzindo', 'Manutenção'],
            colors: ['#fbbf24', '#128c7e', '#ef4444'], 
            chart: { type: 'donut', fontFamily: 'Inter, sans-serif', background: 'transparent' },
            theme: { mode: $q.dark.isActive ? 'dark' : 'light' },
            legend: { position: 'bottom', labels: { colors: chartTextColor.value } },
            dataLabels: { enabled: false },
            plotOptions: { donut: { size: '75%', labels: { show: true, total: { show: true, label: 'Total', color: $q.dark.isActive ? '#ffffff' : '#128c7e' } } } },
            stroke: { show: true, width: 2, colors: [$q.dark.isActive ? '#1e1e1e' : '#fff'] }
        }
    };
});

async function refreshData() {
    await Promise.all([
        dashboardStore.fetchManagerDashboard('last_30_days'),
        vehicleStore.fetchAllVehicles({ page: 1, rowsPerPage: 100 })
    ]);
}

function scheduleMaintenance(vehicleId: number) {
  selectedVehicleIdForMaintenance.value = vehicleId;
  createDialogType.value = 'PREVENTIVA';
  showCreateMaintenanceDialog.value = true;
}

function scheduleMaintenanceGeneral() {
  selectedVehicleIdForMaintenance.value = null;
  createDialogType.value = 'CORRETIVA';
  showCreateMaintenanceDialog.value = true;
}

onMounted(() => {
    setCssVar('primary', '#128c7e');
    if (authStore.isManager) {
        void refreshData();
    }
});
</script>

<style scoped lang="scss">
// Variáveis Trucar
$trucar-green: #128c7e;
$trucar-mint: #70c0b0;
$shadow-green: 0 4px 14px 0 rgba(18, 140, 126, 0.39);

.dashboard-bg { 
  background-color: #f0f4f4; // Fundo padrão claro
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

/* --- Glassmorphism --- */
.glass-card {
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid rgba(18, 140, 126, 0.1);
  transition: background-color 0.3s, border-color 0.3s;
}

.glass-badge {
  background: rgba(18, 140, 126, 0.1) !important;
  backdrop-filter: blur(4px);
}

.glass-btn {
  background: rgba(18, 140, 126, 0.05);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(18, 140, 126, 0.1);
}

.glass-menu {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(10px);
}

/* --- Tipografia --- */
.text-weight-900 { font-weight: 900; }
.text-gradient {
  background: linear-gradient(to right, $trucar-green, $trucar-mint);
  -webkit-background-clip: text;
  background-clip: text; /* Correção para compatibilidade */
  -webkit-text-fill-color: transparent;
}
.letter-spacing-2 { letter-spacing: 2px; }

/* --- Cartões e Sombras --- */
.dashboard-card { 
  border-radius: 16px; 
}
.shadow-card {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.shadow-green { box-shadow: $shadow-green; }

/* --- Bordas e Separadores --- */
.border-bottom-light { border-bottom: 1px solid rgba(18, 140, 126, 0.1); }
.border-top-critical { border-top: 4px solid var(--q-negative); }

/* --- Efeitos de Hover --- */
.hover-scale { 
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  &:hover { 
    transform: translateY(-4px); 
    box-shadow: 0 10px 25px -5px rgba(18, 140, 126, 0.2);
    border-color: $trucar-green;
  } 
}
.btn-hover-effect:hover { background: rgba(18, 140, 126, 0.1); color: $trucar-green; }
.item-hover:hover { 
  background-color: rgba(112, 192, 176, 0.1); 
  .text-weight-bold { color: $trucar-green; } 
}

/* --- Elementos Decorativos --- */
.icon-box {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
}
.icon-box-sm {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}
.dot-indicator {
  width: 8px; height: 8px; border-radius: 50%; display: inline-block;
}
.rounded-xl { border-radius: 16px; }
.rounded-circle { border-radius: 50%; }
.btn-rounded { border-radius: 8px; }

/* --- Backgrounds Específicos --- */
.bg-teal-gradient-faded {
  background: linear-gradient(90deg, rgba(112, 192, 176, 0.1) 0%, transparent 100%);
}
.hover\:bg-teal-5-faded:hover { background-color: rgba(112, 192, 176, 0.1); }
.hover\:bg-red-1-faded:hover { background-color: rgba(239, 68, 68, 0.05); }

/* --- Animations --- */
.fade-in-up { animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.animate-pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
.animate-fade-down { animation: fadeDown 0.8s ease-out forwards; }

@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }

.empty-state-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 20px;
  min-height: 250px;
  width: 100%;
}
.empty-state-list .q-icon {
  margin-left: auto;
  margin-right: auto;
  display: block;
}

.empty-state-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    height: 100%;
    min-height: 300px;
}

/* =========================================
   DARK MODE OVERRIDES (DARK FOREST)
   ========================================= */
.body--dark {
  // Fundo Floresta Negra
  .dashboard-bg { 
    background-color: #05100e !important; 
  }

  // Cards Escuros Translúcidos
  .glass-card {
    background: rgba(5, 20, 18, 0.7) !important;
    border-color: rgba(18, 140, 126, 0.2);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
  }
  
  .glass-menu {
    background: rgba(10, 25, 23, 0.95) !important;
    border: 1px solid rgba(18, 140, 126, 0.3);
  }

  .alert-header-bg {
    background: rgba(255, 255, 255, 0.05) !important;
  }

  // Textos
  .text-teal-9 { color: #80cbc4 !important; }  // Teal claro
  .text-teal-10 { color: #e0f2f1 !important; } // Quase branco
  .text-grey-7 { color: #94a3b8 !important; }  // Cinza médio
  .text-grey-6 { color: #64748b !important; }
  .text-grey-9 { color: #e2e8f0 !important; } // Títulos de alerta

  // Ícones e Box
  .icon-box, .icon-box-sm {
    background-color: rgba(18, 140, 126, 0.15) !important;
    .q-icon { color: #4db6ac !important; }
  }
  // Cores específicas dos boxes de ação rápida
  .bg-cyan-1 { background-color: rgba(34, 211, 238, 0.1) !important; }
  .text-cyan-9 { color: #22d3ee !important; }
  .bg-orange-1 { background-color: rgba(251, 146, 60, 0.1) !important; }
  .text-orange-9 { color: #fb923c !important; }

  // Hover em Listas
  .item-hover:hover {
    background-color: rgba(18, 140, 126, 0.15);
  }
  .hover\:bg-teal-5-faded:hover {
     background-color: rgba(18, 140, 126, 0.15) !important;
  }
  .hover\:bg-red-1-faded:hover {
     background-color: rgba(239, 68, 68, 0.1) !important;
  }

  // Badges e Elementos de UI
  .glass-badge {
    background: rgba(18, 140, 126, 0.2) !important;
    color: #80cbc4 !important;
  }
  .bg-teal-1 { background-color: rgba(18, 140, 126, 0.15) !important; }
  
  // Separadores
  .border-bottom-light { border-bottom-color: rgba(255, 255, 255, 0.05); }
}
</style>
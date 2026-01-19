<template>
  <q-page class="dashboard-bg q-pa-md q-pa-lg-xl">
    
    <div class="row items-center justify-between q-mb-xl animate-fade-down">
      <div class="col-12 col-md-auto">
        <div class="row items-center q-gutter-x-sm">
          <q-icon name="factory" size="2em" class="text-primary opacity-80" />
          <div>
            <div class="text-caption text-uppercase text-grey-6 text-weight-bold letter-spacing-2">
              Visão Geral da Planta
            </div>
            <h1 class="text-h4 text-weight-900 q-my-none text-gradient">
              Painel de Controle
            </h1>
          </div>
        </div>
        <div class="text-subtitle1 text-grey-7 q-mt-sm flex items-center">
          <span>Bem-vindo de volta, <strong>{{ authStore.user?.full_name?.split(' ')[0] }}</strong>.</span>
          <q-badge color="green-1" text-color="green-9" class="q-ml-md q-px-sm">
            <span class="dot-indicator bg-green-5 q-mr-xs"></span> Sistema Online
          </q-badge>
        </div>
      </div>

      <div class="col-12 col-md-auto q-mt-md q-md-mt-none">
        <div class="row q-gutter-sm">
           <q-btn 
             flat
             color="grey-8" 
             icon="refresh" 
             label="Atualizar Dados" 
             class="btn-hover-effect"
             @click="() => refreshData()" 
             :loading="dashboardStore.isLoading || vehicleStore.isLoading"
           />
           <q-btn-dropdown 
             color="primary" 
             icon="add" 
             label="Ações Rápidas" 
             unelevated 
             class="shadow-4 btn-rounded q-px-lg"
             content-class="rounded-borders shadow-10"
             dropdown-icon="expand_more"
           >
            <q-list class="q-py-md" style="min-width: 240px">
              <div class="text-caption q-px-md q-mb-sm text-grey-6 text-uppercase text-weight-bold">Cadastro</div>
              
              <q-item clickable v-close-popup @click="() => router.push('/vehicles')" class="item-hover">
                <q-item-section avatar><div class="icon-box bg-blue-1 text-blue-9"><q-icon name="precision_manufacturing" size="20px"/></div></q-item-section>
                <q-item-section>
                   <q-item-label class="text-weight-bold">Nova Máquina</q-item-label>
                   <q-item-label caption>Cadastrar ativo</q-item-label>
                </q-item-section>
              </q-item>
              
              <q-separator spaced class="q-mx-md" />
              <div class="text-caption q-px-md q-mb-sm text-grey-6 text-uppercase text-weight-bold">Operação</div>

              <q-item clickable v-close-popup @click="() => router.push('/factory/kiosk')" class="item-hover">
                <q-item-section avatar><div class="icon-box bg-teal-1 text-teal-9"><q-icon name="monitor" size="20px"/></div></q-item-section>
                <q-item-section>
                   <q-item-label class="text-weight-bold">Modo Kiosk</q-item-label>
                   <q-item-label caption>Tela do operador</q-item-label>
                </q-item-section>
              </q-item>
              
              <q-item clickable v-close-popup @click="scheduleMaintenanceGeneral" class="item-hover">
                <q-item-section avatar><div class="icon-box bg-red-1 text-red-9"><q-icon name="build_circle" size="20px"/></div></q-item-section>
                <q-item-section>
                   <q-item-label class="text-weight-bold">Solicitar Manutenção</q-item-label>
                   <q-item-label caption>Abrir chamado</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>
      </div>
    </div>

    <div v-if="dashboardStore.isLoading && !realTimeStats" class="row q-col-gutter-md animate-pulse">
       <div class="col-12 col-md-3" v-for="n in 4" :key="n">
         <q-card flat class="rounded-xl bg-white q-pa-md">
             <div class="row items-center no-wrap">
                <q-skeleton type="circle" size="50px" />
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
            color="primary" 
            to="/vehicles" 
            :loading="dashboardStore.isLoading"
            class="full-height shadow-card hover-scale" 
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
            class="full-height shadow-card hover-scale" 
          />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Disponível / Parado" 
            :value="realTimeStats.idle" 
            icon="hourglass_empty" 
            color="warning" 
            to="/vehicles?status=Disponível" 
            :loading="dashboardStore.isLoading"
            class="full-height shadow-card hover-scale" 
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
            class="full-height shadow-card hover-scale" 
          />
        </div>
      </div>

      <div class="text-h6 text-weight-bold text-grey-9 q-mb-md flex items-center">
        <q-icon name="insights" class="q-mr-sm text-grey-6" /> Indicadores de Performance
      </div>
      <div class="row q-col-gutter-md q-mb-xl">
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Custo Hora Máquina" 
             :value="efficiencyKpis?.cost_per_km ?? 0" 
             unit="R$/h" 
             icon="attach_money" 
             color="deep-purple" 
             class="metric-clean"
             tooltip="Média dos últimos 30 dias"
           />
         </div>
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Eficiência Global (OEE)" 
             :value="efficiencyKpis?.fleet_avg_efficiency ?? 0" 
             unit="%" 
             icon="bolt" 
             color="blue-8" 
             class="metric-clean"
             :formatter="(v: number) => v.toFixed(1)" 
           />
         </div>
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Custo Variável (Mês)" 
             :value="variableCostTotal" 
             unit="R$" 
             icon="account_balance_wallet" 
             color="orange-9" 
             class="metric-clean"
             :formatter="(v: number) => `R$ ${v.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`" 
           />
         </div>
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Taxa de Utilização" 
             :value="realTimeStats.utilizationRate" 
             unit="%" 
             icon="pie_chart" 
             color="teal" 
             class="metric-clean"
             :formatter="(v: number) => `${v.toFixed(1)}%`" 
           />
         </div>
      </div>

      <div class="row q-col-gutter-lg">
        
        <div class="col-12 col-lg-8 column q-gutter-y-lg">
          
          <div class="dashboard-card shadow-1 q-pa-none overflow-hidden">
             <div class="card-header q-pa-md border-bottom-light row justify-between items-center">
                <div>
                   <div class="text-h6 text-weight-bold text-grey-9">Custos Industriais</div>
                   <div class="text-caption text-grey-6">Análise de gastos por categoria</div>
                </div>
                <q-btn round flat icon="more_horiz" color="grey-7" />
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
                   <div class="bg-grey-2 q-pa-lg rounded-circle q-mb-md">
                      <q-icon name="bar_chart" size="3em" color="grey-5" />
                   </div>
                   <div class="text-grey-7 text-weight-medium">Sem dados financeiros</div>
                   <q-btn outline color="primary" label="Lançar Custos" to="/costs" class="q-mt-md rounded-borders" />
                </div>
             </div>
          </div>

          <div class="dashboard-card shadow-1 q-pa-none overflow-hidden">
             <div class="card-header q-pa-md border-bottom-light row justify-between items-center bg-grey-1-light">
                 <div class="row items-center">
                    <div class="icon-box-sm bg-blue-1 text-blue-9 q-mr-md"><q-icon name="calendar_month" /></div>
                    <div>
                       <div class="text-subtitle1 text-weight-bold text-grey-9">Agenda de Manutenção</div>
                       <div class="text-caption text-grey-6">Próximas intervenções programadas</div>
                    </div>
                 </div>
                 <q-btn flat dense no-caps color="primary" label="Ver todas" to="/maintenance" icon-right="arrow_forward" />
             </div>
             
             <q-list class="q-py-sm">
                 <q-item v-for="item in mergedMaintenanceList" :key="item.id" class="q-py-md q-px-lg transition-bg hover:bg-grey-1">
                   <q-item-section avatar>
                      <q-avatar 
                        :color="item.is_overdue ? 'red-1' : 'blue-1'" 
                        :text-color="item.is_overdue ? 'negative' : 'primary'" 
                        font-size="24px"
                        class="shadow-1"
                      >
                        <q-icon :name="item.is_overdue ? 'warning' : 'schedule'" />
                      </q-avatar>
                   </q-item-section>
                   
                   <q-item-section>
                     <q-item-label class="text-weight-bold text-body1 text-grey-9">{{ item.info }}</q-item-label>
                     <q-item-label caption class="q-mt-xs">
                         <span v-if="item.is_overdue" class="text-negative flex items-center">
                            <q-icon name="error" size="xs" class="q-mr-xs"/> Atrasada há {{ item.overdue_diff }}h
                         </span>
                         <span v-else class="text-grey-7 flex items-center">
                            <q-icon name="event" size="xs" class="q-mr-xs"/> Vence em: 
                            <span class="text-primary q-ml-xs text-weight-medium bg-blue-1 q-px-xs rounded-borders">{{ item.due_label }}</span>
                         </span>
                     </q-item-label>
                   </q-item-section>
                   
                   <q-item-section side>
                      <q-btn 
                        :color="item.is_overdue ? 'negative' : 'grey-3'" 
                        :text-color="item.is_overdue ? 'white' : 'grey-9'"
                        unelevated 
                        dense 
                        class="q-px-md rounded-borders"
                        :icon="item.is_overdue ? 'priority_high' : 'add'"
                        :label="item.is_overdue ? 'Urgente' : 'Abrir OS'" 
                        @click="scheduleMaintenance(item.id)" 
                      />
                   </q-item-section>
                 </q-item>

                 <div v-if="!mergedMaintenanceList.length" class="empty-state-list">
                     <q-icon name="task_alt" size="3em" class="text-green-5 q-mb-sm" />
                     <div class="text-grey-8">Tudo em dia! Nenhuma manutenção próxima.</div>
                 </div>
             </q-list>
          </div>
        </div>

        <div class="col-12 col-lg-4 column q-gutter-y-lg">
          
          <div class="dashboard-card shadow-1 overflow-hidden">
             <div class="q-pa-md border-bottom-light">
                <div class="text-subtitle1 text-weight-bold">Status da Frota</div>
             </div>
             <div class="q-pa-md flex flex-center relative-position" style="min-height: 260px">
                <ApexChart 
                    v-if="fleetStatusChart.series.some((v: number) => v > 0)" 
                    type="donut" 
                    height="280" 
                    :options="fleetStatusChart.options" 
                    :series="fleetStatusChart.series" 
                />
                <div v-else class="text-center text-grey-5 absolute-center column flex-center">
                   <q-icon name="pie_chart" size="4em" color="grey-3" />
                   <div class="text-caption q-mt-sm">Sem dados de status</div>
                </div>
             </div>
          </div>

          <div class="dashboard-card shadow-1 overflow-hidden border-top-critical">
             <div class="card-header q-pa-md row justify-between items-center bg-white">
                <div class="row items-center text-negative">
                   <div class="pulse-icon bg-red-1 q-mr-md flex flex-center" style="width: 32px; height: 32px; border-radius: 50%">
                      <q-icon name="notifications_active" size="18px"/>
                   </div>
                   <div class="text-subtitle1 text-weight-bold">Alertas Andon</div>
                </div>
                <q-badge color="red-1" text-color="negative" :label="processedAlerts.length" rounded />
             </div>
             
             <q-scroll-area style="height: 400px;" :thumb-style="{ width: '6px', borderRadius: '3px', backgroundColor: '#e2e8f0' }">
               <q-list separator>
                 <q-item v-for="alert in processedAlerts" :key="alert.id" class="q-py-md q-px-md hover:bg-red-1 transition-bg cursor-pointer">
                   <q-item-section top avatar>
                      <div class="relative-position">
                        <q-avatar icon="warning" color="negative" text-color="white" size="md" font-size="20px" class="shadow-2" />
                        <span class="absolute-bottom-right bg-white rounded-circle border-1 border-red" style="width: 10px; height: 10px; bottom: 0; right: -2px;"></span>
                      </div>
                   </q-item-section>
                   
                   <q-item-section>
                     <q-item-label class="text-weight-bold text-grey-9">{{ alert.title }}</q-item-label>
                     <q-item-label caption class="text-grey-7 text-caption-2 q-mt-xs" :lines="2">{{ alert.subtitle }}</q-item-label>
                   </q-item-section>
                   
                   <q-item-section side top>
                      <span class="text-xs text-grey-5 font-medium">Hoje</span>
                   </q-item-section>
                 </q-item>

                 <div v-if="processedAlerts.length === 0" class="column flex-center full-height q-pa-xl text-center">
                     <div class="bg-green-1 q-pa-lg rounded-circle q-mb-md">
                        <q-icon name="verified" size="3em" color="positive" />
                     </div>
                     <div class="text-grey-9 text-weight-medium">Sem chamados abertos</div>
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
import { colors } from 'quasar';
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

const showCreateMaintenanceDialog = ref(false); 
const selectedVehicleIdForMaintenance = ref<number | null>(null);
const createDialogType = ref<'PREVENTIVA' | 'CORRETIVA'>('CORRETIVA');

const managerData = computed(() => dashboardStore.managerDashboard);
const efficiencyKpis = computed(() => managerData.value?.efficiency_kpis);
const upcomingMaintenances = computed(() => managerData.value?.upcoming_maintenances as UpcomingMaintenance[] || []);
const recentAlerts = computed(() => managerData.value?.recent_alerts || []);

const processedAlerts = computed(() => recentAlerts.value);

const realTimeStats = computed(() => {
  const allMachines = vehicleStore.vehicles;
  const running = allMachines.filter(m => ['Em uso', 'IN_USE', 'RUNNING'].includes(String(m.status))).length;
  const stopped = allMachines.filter(m => ['Em manutenção', 'MAINTENANCE', 'SETUP'].includes(String(m.status))).length;
  const idle = allMachines.filter(m => ['Disponível', 'AVAILABLE', 'IDLE', 'STOPPED'].includes(String(m.status))).length;
  const total = allMachines.length;

  return { total, running, stopped, idle, utilizationRate: total > 0 ? (running / total) * 100 : 0 };
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

const costAnalysisChart = computed(() => {
  const data: ICostItem[] = managerData.value?.costs_by_category || [];
  const categories = data.map(item => item.cost_type);
  const series = [{ name: 'Custo (R$)', data: data.map(item => item.total_amount) }];
  return { 
      series, 
      options: { 
          chart: { type: 'bar', toolbar: { show: false }, fontFamily: 'Inter, sans-serif' }, 
          plotOptions: { bar: { borderRadius: 6, columnWidth: '50%', distributed: false } },
          xaxis: { 
            categories,
            labels: { style: { colors: '#64748b', fontSize: '12px' } },
            axisBorder: { show: false },
            axisTicks: { show: false }
          },
          yaxis: {
            labels: { style: { colors: '#64748b' }, formatter: (val: number) => `R$ ${val}` }
          },
          colors: [colors.getPaletteColor('primary')],
          grid: { borderColor: '#f1f5f9', strokeDashArray: 4 },
          dataLabels: { enabled: false },
          tooltip: { theme: 'light' }
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
            colors: ['#fbbf24', '#22c55e', '#ef4444'], 
            chart: { type: 'donut', fontFamily: 'Inter, sans-serif' },
            legend: { position: 'bottom', labels: { colors: '#475569' } },
            dataLabels: { enabled: false },
            plotOptions: { donut: { size: '75%', labels: { show: true, total: { show: true, label: 'Total', color: '#64748b' } } } },
            stroke: { show: true, width: 2, colors: ['#fff'] }
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
    if (authStore.isManager) {
        void refreshData();
    }
});
</script>

<style scoped lang="scss">
// Variáveis e Utilitários
$shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
$shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
$shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);

.dashboard-bg { 
  background-color: #f1f5f9; // Slate-100
  min-height: 100vh;
}

// Tipografia
.text-weight-900 { font-weight: 900; }
.text-gradient {
  background: linear-gradient(to right, var(--q-primary), darken(#1976D2, 15%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.letter-spacing-2 { letter-spacing: 2px; }

// Cartões
.dashboard-card { 
  border-radius: 16px; 
  background: white;
  border: 1px solid white;
}
.shadow-card {
  box-shadow: $shadow-sm;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: white;
}

// Bordas e Separadores
.border-bottom-light { border-bottom: 1px solid #f1f5f9; }
.border-top-critical { border-top: 4px solid var(--q-negative); }

// Efeitos de Hover
.hover-scale { 
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  &:hover { 
    transform: translateY(-4px); 
    box-shadow: $shadow-lg;
    border-color: var(--q-primary);
  } 
}
.btn-hover-effect:hover { background: rgba(0,0,0,0.03); color: var(--q-primary); }
.item-hover:hover { background-color: #f8fafc; .text-weight-bold { color: var(--q-primary); } }

// Elementos Decorativos
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

// Empty States
.empty-state-box {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 350px; text-align: center;
}
.empty-state-list {
  padding: 40px; text-align: center; display: flex; flex-direction: column; align-items: center;
}

// Animações
.fade-in-up { animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.animate-pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
.animate-fade-down { animation: fadeDown 0.8s ease-out forwards; }

@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
</style>
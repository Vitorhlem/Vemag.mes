<template>
  <q-page class="dashboard-bg q-pa-md q-pa-lg-xl">
    
    <div class="row items-center justify-between q-mb-lg animate-fade-down">
      <div class="col-12 col-md-auto">
        <div class="text-caption text-uppercase text-grey-7 text-weight-bold letter-spacing-1">
          Visão Geral da Planta
        </div>
        <h1 class="text-h4 text-weight-bolder q-my-none text-primary">
          Painel de Controle
        </h1>
        <div class="text-subtitle2 text-grey-6 q-mt-xs">
          Bem-vindo, {{ authStore.user?.full_name?.split(' ')[0] }}. Monitoramento em tempo real.
        </div>
      </div>

      <div class="col-12 col-md-auto q-mt-md q-md-mt-none">
        <div class="row q-gutter-sm">
           <q-btn 
             outline 
             color="primary" 
             icon="refresh" 
             label="Atualizar" 
             @click="() => refreshData()" 
             :loading="dashboardStore.isLoading || vehicleStore.isLoading"
           />
           <q-btn-dropdown 
             color="primary" 
             icon="add" 
             label="Ações Rápidas" 
             unelevated 
             class="shadow-2"
             content-class="rounded-borders"
           >
            <q-list dense style="min-width: 220px">
              <q-item clickable v-close-popup @click="() => router.push('/vehicles')">
                <q-item-section avatar><q-icon name="precision_manufacturing" color="primary"/></q-item-section>
                <q-item-section>
                   <q-item-label>Cadastrar Máquina</q-item-label>
                   <q-item-label caption>Novo ativo industrial</q-item-label>
                </q-item-section>
              </q-item>
              
              <q-item clickable v-close-popup @click="() => router.push('/machine-kiosk')">
                <q-item-section avatar><q-icon name="monitor" color="secondary"/></q-item-section>
                <q-item-section>
                   <q-item-label>Ir para Kiosk</q-item-label>
                   <q-item-label caption>Tela do Operador</q-item-label>
                </q-item-section>
              </q-item>
              
              <q-separator inset class="q-my-xs" />
              
              <q-item clickable v-close-popup @click="scheduleMaintenanceGeneral">
                <q-item-section avatar><q-icon name="build_circle" color="negative"/></q-item-section>
                <q-item-section>
                   <q-item-label>Solicitar Manutenção</q-item-label>
                   <q-item-label caption>Ordem de Serviço</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>
      </div>
    </div>

    <div v-if="dashboardStore.isLoading && !realTimeStats" class="row q-col-gutter-md">
       <div class="col-12 col-md-3" v-for="n in 4" :key="n">
          <q-card flat bordered class="rounded-borders">
             <q-card-section><q-skeleton type="rect" height="80px" /></q-card-section>
          </q-card>
       </div>
    </div>

    <div v-else class="fade-in">
      
      <div class="row q-col-gutter-md q-mb-lg">
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Máquinas Totais" 
            :value="realTimeStats.total" 
            icon="domain" 
            color="primary" 
            :loading="dashboardStore.isLoading"
            to="/vehicles" 
            class="full-height shadow-1 hover-lift" 
          />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Em Produção" 
            :value="realTimeStats.running" 
            icon="settings_suggest" 
            color="positive" 
            :loading="dashboardStore.isLoading"
            to="/vehicles?status=Em uso" 
            class="full-height shadow-1 hover-lift" 
          />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Parada / Disponível" 
            :value="realTimeStats.idle" 
            icon="hourglass_empty" 
            color="warning" 
            :loading="dashboardStore.isLoading"
            to="/vehicles?status=Disponível" 
            class="full-height shadow-1 hover-lift" 
          />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Em Manutenção / Setup" 
            :value="realTimeStats.stopped" 
            icon="build" 
            color="negative" 
            :loading="dashboardStore.isLoading"
            to="/maintenance" 
            class="full-height shadow-1 hover-lift" 
          />
        </div>
      </div>

      <div class="row q-col-gutter-md q-mb-lg">
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Custo Hora Máquina" 
             :value="efficiencyKpis?.cost_per_km ?? 0" 
             unit="R$/h" 
             icon="attach_money" 
             color="deep-purple" 
             tooltip="Custo médio calculado base nos últimos 30 dias"
           />
         </div>
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Eficiência Global" 
             :value="efficiencyKpis?.fleet_avg_efficiency ?? 0" 
             unit="%" 
             icon="bolt" 
             color="blue-8" 
             tooltip="Performance média vs meta"
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
             :formatter="(v: number) => `R$ ${v.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`" 
           />
         </div>
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Disponibilidade (OEE)" 
             :value="realTimeStats.utilizationRate" 
             unit="%" 
             icon="pie_chart" 
             color="teal" 
             :formatter="(v: number) => `${v.toFixed(1)}%`" 
           />
         </div>
      </div>

      <div class="row q-col-gutter-lg">
        <div class="col-12 col-lg-8 column q-gutter-y-lg">
          <div>
            <PremiumWidget title="Análise de Custos Industriais" icon="analytics" description="Gastos por categoria">
              <ApexChart 
                v-if="(costAnalysisChart.series[0]?.data.length || 0) > 0" 
                type="bar" 
                height="320" 
                :options="costAnalysisChart.options" 
                :series="costAnalysisChart.series" 
              />
              <div v-else class="text-center text-grey q-pa-xl column flex-center" style="height: 320px">
                 <q-icon name="bar_chart" size="4em" color="grey-3" />
                 <div class="q-mt-sm">Ainda sem dados de custos lançados.</div>
                 <q-btn flat color="primary" label="Lançar Custos" to="/vehicle-costs" size="sm" />
              </div>
            </PremiumWidget>
          </div>

          <div>
            <q-card class="dashboard-card shadow-1">
              <q-card-section class="row items-center justify-between border-bottom-light">
                 <div class="text-h6 flex items-center">
                    <q-icon name="calendar_month" class="q-mr-sm text-primary"/> 
                    Próximas Preventivas
                 </div>
                 <q-btn flat dense color="primary" label="Ver Plano Completo" to="/maintenance" size="sm" />
              </q-card-section>
              
              <q-list separator>
                  <q-item v-for="item in mergedMaintenanceList" :key="item.id" class="q-py-md hover-bg" :class="{'bg-red-1': item.is_overdue}">
                    <q-item-section avatar>
                       <q-avatar :color="item.is_overdue ? 'negative' : 'grey-2'" :text-color="item.is_overdue ? 'white' : 'primary'" :icon="item.is_overdue ? 'warning' : 'engineering'" />
                    </q-item-section>
                    <q-item-section>
                      <q-item-label class="text-weight-bold text-subtitle1">{{ item.info }}</q-item-label>
                      <q-item-label caption>
                          <q-badge v-if="item.is_overdue" color="negative" label="VENCIDA" class="q-mr-xs" />
                          <span v-else class="text-grey-7">Vence em: </span>
                          <span class="text-weight-medium" :class="item.is_overdue ? 'text-negative' : 'text-grey-9'">
                             {{ item.is_overdue ? `Passou do limite há ${item.overdue_diff}h` : item.due_label }}
                          </span>
                      </q-item-label>
                    </q-item-section>
                    <q-item-section side>
                       <q-btn :outline="!item.is_overdue" :unelevated="item.is_overdue" dense size="sm" :color="item.is_overdue ? 'negative' : 'primary'" :label="item.is_overdue ? 'Abrir Urgente' : 'Abrir OS'" @click="scheduleMaintenance(item.id)" />
                    </q-item-section>
                  </q-item>
                  <q-item v-if="!mergedMaintenanceList.length" class="q-pa-lg">
                      <q-item-section class="text-center text-grey-6">
                         <q-icon name="check_circle_outline" size="3em" class="q-mb-sm text-positive" />
                         <div>Nenhuma manutenção preventiva próxima.</div>
                      </q-item-section>
                  </q-item>
              </q-list>
            </q-card>
         </div>
        </div>

        <div class="col-12 col-lg-4 column q-gutter-y-lg">
          <div>
            <PremiumWidget title="Disponibilidade Real" icon="donut_large" description="Ativos x Parados">
              <div class="flex flex-center relative-position" style="min-height: 280px">
                <ApexChart 
                    v-if="fleetStatusChart.series.some((v: number) => v > 0)" 
                    type="donut" 
                    height="260" 
                    :options="fleetStatusChart.options" 
                    :series="fleetStatusChart.series" 
                />
                <div v-else class="text-center text-grey-5 absolute-center">
                   <q-icon name="data_usage" size="3em" />
                   <div class="text-caption">Sem dados de status</div>
                </div>
              </div>
            </PremiumWidget>
          </div>

          <div>
              <q-card class="dashboard-card shadow-1 bg-red-1">
              <q-card-section class="row items-center justify-between border-bottom-light-red">
                <div class="text-h6 flex items-center text-negative">
                  <q-icon name="warning" class="q-mr-sm"/> 
                  Alertas Críticos
                </div>
              </q-card-section>
              <q-scroll-area style="height: 350px;">
                <q-list separator>
                  <q-item v-for="alert in processedAlerts" :key="alert.id" class="q-py-md bg-white">
                    <q-item-section avatar><q-avatar icon="priority_high" color="negative" text-color="white" size="md" font-size="20px" /></q-item-section>
                    <q-item-section>
                      <q-item-label class="text-weight-bold">{{ alert.title }}</q-item-label>
                      <q-item-label caption class="text-grey-8">{{ alert.subtitle }}</q-item-label>
                    </q-item-section>
                    <q-item-section side top><q-badge color="grey-3" text-color="grey-8" label="Hoje" /></q-item-section>
                  </q-item>
                  <div v-if="processedAlerts.length === 0" class="text-center q-pa-md text-grey-7 column flex-center full-height">
                      <q-icon name="verified_user" size="3em" color="positive" class="q-mb-xs" />
                      <div>Nenhum chamado Andon aberto.</div>
                  </div>
                </q-list>
              </q-scroll-area>
            </q-card>
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
import PremiumWidget from 'components/PremiumWidget.vue';
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

// --- CORREÇÃO: LÓGICA DE STATUS NO DASHBOARD ---
const realTimeStats = computed(() => {
  const allMachines = vehicleStore.vehicles;
  
  // Mapeia tanto os valores do Backend ("Em uso") quanto os do Código ("IN_USE", "RUNNING")
  // para garantir a contagem correta.
  
  const running = allMachines.filter(m => 
    ['Em uso', 'IN_USE', 'RUNNING'].includes(String(m.status))
  ).length;

  const stopped = allMachines.filter(m => 
    ['Em manutenção', 'MAINTENANCE', 'SETUP'].includes(String(m.status))
  ).length;

  const idle = allMachines.filter(m => 
    ['Disponível', 'AVAILABLE', 'IDLE', 'STOPPED'].includes(String(m.status))
  ).length;

  const total = allMachines.length;

  return {
    total,
    running,
    stopped,
    idle,
    utilizationRate: total > 0 ? (running / total) * 100 : 0
  };
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
  const items = costs.filter(c => 
    ['energia', 'insumos', 'manutenção', 'peças'].some(term => 
      c.cost_type.toLowerCase().includes(term)
    )
  );
  return items.reduce((acc, curr) => acc + curr.total_amount, 0);
});

const costAnalysisChart = computed(() => {
  const data: ICostItem[] = managerData.value?.costs_by_category || [];
  const categories = data.map(item => item.cost_type);
  const series = [{ name: 'Custo (R$)', data: data.map(item => item.total_amount) }];
  return { 
      series, 
      options: { 
          chart: { type: 'bar', toolbar: { show: false } }, 
          plotOptions: { bar: { borderRadius: 4, columnWidth: '40%' } },
          xaxis: { categories },
          colors: [colors.getPaletteColor('primary')],
          grid: { borderColor: '#f1f1f1' },
          dataLabels: { enabled: false }
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
            colors: ['#F2C037', '#21BA45', '#C10015'], 
            chart: { type: 'donut' },
            legend: { position: 'bottom' },
            dataLabels: { enabled: false },
            plotOptions: { donut: { size: '65%' } }
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
.dashboard-bg { background-color: #f8fafc; }
.dashboard-card { border-radius: 12px; border: 1px solid #e2e8f0; background: white; }
.letter-spacing-1 { letter-spacing: 1px; }
.hover-lift { transition: transform 0.2s ease, box-shadow 0.2s ease; &:hover { transform: translateY(-4px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important; } }
.hover-bg:hover { background-color: #f8fafc; }
.border-bottom-light { border-bottom: 1px solid #f1f5f9; }
.border-bottom-light-red { border-bottom: 1px solid rgba(255,0,0,0.1); }
.fade-in { animation: fadeIn 0.5s ease-out forwards; }
.animate-fade-down { animation: fadeDown 0.6s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
</style>
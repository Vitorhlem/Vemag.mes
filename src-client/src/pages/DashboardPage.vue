<template>
  <q-page class="dashboard-bg q-pa-md q-pa-lg-xl">
    
    <div class="row items-center justify-between q-mb-lg animate-fade-down">
      <div class="col-12 col-md-auto">
        <div class="text-caption text-uppercase text-grey-7 text-weight-bold letter-spacing-1">
          Visão Geral
        </div>
        <h1 class="text-h4 text-weight-bolder q-my-none text-primary">
          Painel de Controle
        </h1>
        <div class="text-subtitle2 text-grey-6 q-mt-xs">
          Bem-vindo, {{ authStore.user?.full_name?.split(' ')[0] }}. Resumo da operação em tempo real.
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
              :loading="dashboardStore.isLoading"
           />
           <q-btn-dropdown 
              color="primary" 
              icon="add" 
              label="Nova Ação" 
              unelevated 
              class="shadow-2"
              content-class="rounded-borders"
           >
            <q-list dense style="min-width: 220px">
              <q-item clickable v-close-popup @click="router.push('/vehicles')">
                <q-item-section avatar><q-icon name="precision_manufacturing" color="primary"/></q-item-section>
                <q-item-section>
                   <q-item-label>Cadastrar Equipamento</q-item-label>
                   <q-item-label caption>Novo ativo na planta</q-item-label>
                </q-item-section>
              </q-item>
              
              <q-item clickable v-close-popup @click="router.push('/journeys')">
                <q-item-section avatar><q-icon name="fact_check" color="secondary"/></q-item-section>
                <q-item-section>
                   <q-item-label>Ordem de Produção</q-item-label>
                   <q-item-label caption>Iniciar turno</q-item-label>
                </q-item-section>
              </q-item>
              
              <q-separator inset class="q-my-xs" />
              
              <q-item clickable v-close-popup @click="scheduleMaintenanceGeneral">
                <q-item-section avatar><q-icon name="build_circle" color="negative"/></q-item-section>
                <q-item-section>
                   <q-item-label>Solicitar Manutenção</q-item-label>
                   <q-item-label caption>Abrir OS Corretiva</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>
      </div>
    </div>

    <div v-if="dashboardStore.isLoading" class="row q-col-gutter-md">
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
            label="Ativos Totais" 
            :value="kpis?.total_vehicles ?? 0" 
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
            :value="kpis?.in_use_vehicles ?? 0" 
            icon="settings_motion" 
            color="positive" 
            :loading="dashboardStore.isLoading"
            to="/vehicles?status=IN_USE" 
            class="full-height shadow-1 hover-lift" 
          />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Disponível / Parada" 
            :value="kpis?.available_vehicles ?? 0" 
            icon="pause_circle_outline" 
            color="warning" 
            :loading="dashboardStore.isLoading"
            to="/vehicles?status=AVAILABLE" 
            class="full-height shadow-1 hover-lift" 
          />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-3">
          <StatCard 
            label="Em Manutenção" 
            :value="kpis?.maintenance_vehicles ?? 0" 
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
             title="Custo Médio Operacional" 
             :value="efficiencyKpis?.cost_per_km ?? 0" 
             unit="R$/h" 
             icon="attach_money" 
             color="deep-purple" 
             tooltip="Custo médio por hora de máquina ligada (baseado em apontamentos reais)"
           />
         </div>
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Eficiência Energética" 
             :value="efficiencyKpis?.fleet_avg_efficiency ?? 0" 
             unit="un/h" 
             icon="bolt" 
             color="blue-8" 
             tooltip="Consumo médio de energia/insumos por hora"
             :formatter="(v) => v.toFixed(1)" 
           />
         </div>
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Custo Variável (Mês)" 
             :value="variableCostTotal" 
             unit="R$" 
             icon="account_balance_wallet" 
             color="orange-9" 
             :formatter="(v) => `R$ ${v.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`" 
           />
         </div>
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Disponibilidade (OEE)" 
             :value="efficiencyKpis?.utilization_rate ?? 0" 
             unit="%" 
             icon="pie_chart" 
             color="teal" 
             :formatter="(v) => `${v.toFixed(1)}%`" 
           />
         </div>
      </div>

      <div class="row q-col-gutter-lg">
        
        <div class="col-12 col-lg-8 column q-gutter-y-lg">
          
          <div>
            <PremiumWidget title="Análise de Custos (30 dias)" icon="analytics" description="Distribuição de gastos reais por categoria.">
              <ApexChart 
                v-if="(costAnalysisChart.series[0]?.data.length || 0) > 0" 
                type="bar" 
                height="320" 
                :options="costAnalysisChart.options" 
                :series="costAnalysisChart.series" 
              />
              <div v-else class="text-center text-grey q-pa-xl column flex-center" style="height: 320px">
                 <q-icon name="bar_chart" size="4em" color="grey-3" />
                 <div class="q-mt-sm">Nenhum custo lançado no período.</div>
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
                 <q-btn flat dense color="primary" label="Ver Plano Completo" to="/costs" size="sm" />
              </q-card-section>
              
              <q-list separator>
                  <q-item 
                    v-for="item in mergedMaintenanceList" 
                    :key="item.id" 
                    class="q-py-md hover-bg"
                    :class="{'bg-red-1': item.is_overdue}"
                  >
                    <q-item-section avatar>
                       <q-avatar 
                          :color="item.is_overdue ? 'negative' : 'grey-2'" 
                          :text-color="item.is_overdue ? 'white' : 'primary'" 
                          :icon="item.is_overdue ? 'warning' : 'engineering'" 
                        />
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
                       <q-btn 
                          :outline="!item.is_overdue"
                          :unelevated="item.is_overdue"
                          dense 
                          size="sm" 
                          :color="item.is_overdue ? 'negative' : 'primary'" 
                          :label="item.is_overdue ? 'Abrir OM Urgente' : 'Abrir OS'" 
                          :icon="item.is_overdue ? 'add_alert' : undefined"
                          @click="scheduleMaintenance(item.id)" 
                        />
                    </q-item-section>
                  </q-item>
                  
                  <q-item v-if="!mergedMaintenanceList.length" class="q-pa-lg">
                     <q-item-section class="text-center text-grey-6">
                        <q-icon name="check_circle_outline" size="3em" class="q-mb-sm text-positive" />
                        <div>Nenhuma manutenção preventiva próxima.</div>
                        <div class="text-caption">Configure os planos de manutenção no cadastro das máquinas.</div>
                     </q-item-section>
                  </q-item>
              </q-list>
            </q-card>
         </div>
        </div>

        <div class="col-12 col-lg-4 column q-gutter-y-lg">
          
          <div>
            <PremiumWidget title="Disponibilidade da Planta" icon="donut_large" description="Ativos x Parados">
              <div class="flex flex-center relative-position" style="min-height: 280px">
                <ApexChart 
                    v-if="fleetStatusChart.series.length > 0 && fleetStatusChart.series.some(v => v > 0)" 
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
                    <q-item-section avatar>
                      <q-avatar icon="priority_high" color="negative" text-color="white" size="md" font-size="20px" />
                    </q-item-section>
                    <q-item-section>
                      <q-item-label class="text-weight-bold">{{ alert.title }}</q-item-label>
                      <q-item-label caption class="text-grey-8">{{ alert.subtitle }}</q-item-label>
                    </q-item-section>
                    <q-item-section side top>
                        <q-badge color="grey-3" text-color="grey-8" label="Hoje" />
                    </q-item-section>
                  </q-item>
                  
                  <div v-if="processedAlerts.length === 0" class="text-center q-pa-md text-grey-7 column flex-center full-height">
                      <q-icon name="verified_user" size="3em" color="positive" class="q-mb-xs" />
                      <div>Nenhum alerta crítico ativo.</div>
                      <div class="text-caption">Sua planta está operando normalmente.</div>
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

// Interface para tipagem das preventivas
interface UpcomingMaintenance {
    vehicle_id: number;
    vehicle_info: string;
    due_date?: string;
    due_km?: number;
}

// NOVO: Interface para itens unificados da lista
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
const kpis = computed(() => managerData.value?.kpis);
const efficiencyKpis = computed(() => managerData.value?.efficiency_kpis);
const upcomingMaintenances = computed(() => managerData.value?.upcoming_maintenances as UpcomingMaintenance[] || []);
const recentAlerts = computed(() => managerData.value?.recent_alerts);

const processedAlerts = computed(() => {
    return recentAlerts.value || [];
});

// [NOVO] Veículos Vencidos
const overdueVehicles = computed(() => {
   return vehicleStore.vehicles.filter(v => {
      if (v.next_maintenance_km && v.current_engine_hours) {
         return v.current_engine_hours >= v.next_maintenance_km;
      }
      return false;
   });
});

// [NOVO] Lista Unificada para o Card (CORRIGIDA TIPAGEM)
const mergedMaintenanceList = computed(() => {
    const list: UnifiedMaintenanceItem[] = []; // TIPAGEM EXPLÍCITA
    const addedIds = new Set<number>();

    // 1. Adiciona as Vencidas (Alta Prioridade)
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

    // 2. Adiciona as Próximas (Vindas do Dashboard)
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

// Calcula custo variável total
const variableCostTotal = computed(() => {
  const costs: ICostItem[] = managerData.value?.costs_by_category || [];
  const items = costs.filter(c => 
    ['combustível', 'energia', 'insumos', 'fluídos'].some(term => 
      c.cost_type.toLowerCase().includes(term)
    )
  );
  return items.reduce((acc, curr) => acc + curr.total_amount, 0);
});

// --- Configuração dos Gráficos ---
const costAnalysisChart = computed(() => {
  const data: ICostItem[] = managerData.value?.costs_by_category || [];
  const categories = data.map(item => {
      const type = item.cost_type;
      if (type === 'Combustível') return 'Energia/Insumos';
      if (type === 'Manutenção') return 'Peças Reposição';
      return type;
  });
  
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
    if (!kpis.value) return { series: [], options: {} };
    const series = [
        kpis.value.available_vehicles || 0, 
        kpis.value.in_use_vehicles || 0, 
        kpis.value.maintenance_vehicles || 0
    ];
    return {
        series,
        options: {
            labels: ['Paradas (Disp.)', 'Produzindo', 'Manutenção'],
            colors: ['#F2C037', '#21BA45', '#C10015'], 
            chart: { type: 'donut' },
            legend: { position: 'bottom' },
            dataLabels: { enabled: false },
            plotOptions: { donut: { size: '65%' } }
        }
    };
});

async function refreshData() {
    // Carrega dashboard
    await dashboardStore.fetchManagerDashboard('last_30_days');
    // Carrega veículos para calcular os alertas de preventivas
    await vehicleStore.fetchAllVehicles({ page: 1, rowsPerPage: 100 });
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
        void refreshData(); // void para ignorar a promise flutuante (ESLint)
    }
});
</script>

<style scoped lang="scss">
.dashboard-bg {
  background-color: #f8fafc; /* Slate-50 */
}

.dashboard-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: white;
}

.letter-spacing-1 {
    letter-spacing: 1px;
}

.hover-lift {
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    &:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
    }
}

.hover-bg:hover {
    background-color: #f8fafc;
}

.border-bottom-light {
    border-bottom: 1px solid #f1f5f9;
}

.border-bottom-light-red {
    border-bottom: 1px solid rgba(255,0,0,0.1);
}

.fade-in {
  animation: fadeIn 0.5s ease-out forwards;
}

.animate-fade-down {
    animation: fadeDown 0.6s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
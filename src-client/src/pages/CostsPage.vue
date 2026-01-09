<template>
  <q-page class="q-pa-md q-pa-lg-xl">
    
    <div class="row items-center justify-between q-mb-lg q-col-gutter-y-md">
      <div class="col-12 col-md-auto">
        <h1 class="text-h4 text-weight-bolder q-my-none text-primary flex items-center gap-sm">
          <q-icon name="attach_money" size="md" />
          Custos Industriais
        </h1>
        <div class="text-subtitle2 text-grey-7 q-mt-xs" :class="{ 'text-grey-5': $q.dark.isActive }">
          Controle financeiro da planta e manutenção (TCO)
        </div>
      </div>

      <div class="col-12 col-md-auto">
        <div class="d-inline-block relative-position">
          <q-btn 
            color="primary" 
            icon="post_add" 
            label="Lançar Despesa" 
            size="md"
            unelevated 
            class="shadow-2"
            @click="openAddCostDialog"
            :disable="isLimitReached"
          />
          <q-tooltip 
            v-if="isLimitReached" 
            class="bg-negative text-body2 shadow-4" 
            anchor="bottom middle" 
            self="top middle"
            :offset="[10, 10]"
          >
            <div class="row items-center no-wrap">
                <q-icon name="lock" size="sm" class="q-mr-sm" />
                <div>
                    <div class="text-weight-bold">Limite Atingido</div>
                    <div class="text-caption">Limite de {{ demoUsageLimitLabel }} lançamentos no plano Demo.</div>
                </div>
            </div>
          </q-tooltip>
        </div>
      </div>
    </div>
    
    <div v-if="isDemo" class="q-mb-xl animate-fade">
      <q-card flat bordered class="demo-card-gradient">
        <q-card-section class="q-pa-md">
          <div class="row items-center justify-between">
            <div class="col-grow row items-center q-gutter-x-md">
              <q-circular-progress
                show-value
                font-size="14px"
                :value="usagePercentage"
                size="60px"
                :thickness="0.22"
                :color="usageColor"
                track-color="white"
                class="text-white q-my-xs"
              >
                {{ usagePercentage }}%
              </q-circular-progress>
              
              <div>
                <div class="text-subtitle2 text-uppercase text-white text-opacity-80">Registros Mensais (Demo)</div>
                <div class="text-h4 text-white text-weight-bold">
                  {{ demoUsageCount }} <span class="text-h6 text-white text-opacity-70">/ {{ demoUsageLimitLabel }} Lançamentos</span>
                </div>
              </div>
            </div>
            
            <div class="col-auto">
               <q-btn flat dense color="white" icon="info" round>
                 <q-tooltip>Uso da cota mensal de registros financeiros.</q-tooltip>
               </q-btn>
            </div>
          </div>
          <q-linear-progress :value="usagePercentage / 100" class="q-mt-md rounded-borders" color="white" track-color="white-30" />
        </q-card-section>
      </q-card>
    </div>

    <q-card flat bordered class="q-mb-lg" :class="$q.dark.isActive ? '' : ''">
      <q-card-section class="row q-col-gutter-md items-center">
        <div class="col-12 col-md-4">
          <q-input outlined v-model="dateRangeText" label="Período de Análise" readonly dense :bg-color="$q.dark.isActive ? '' : 'white'">
            <template v-slot:prepend>
              <q-icon name="date_range" class="cursor-pointer text-primary">
                <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                  <q-date v-model="dateRange" range mask="YYYY-MM-DD" @update:model-value="applyFilters">
                    <div class="row items-center justify-end">
                      <q-btn v-close-popup label="Aplicar" color="primary" flat />
                    </div>
                  </q-date>
                </q-popup-proxy>
              </q-icon>
            </template>
          </q-input>
        </div>
        <div class="col-12 col-md-4">
          <q-select
            outlined
            v-model="categoryFilter"
            :options="costCategoryOptions"
            label="Categoria de Custo"
            dense
            clearable
            :bg-color="$q.dark.isActive ? '' : 'white'"
            @update:model-value="applyFilters"
          >
            <template v-slot:prepend><q-icon name="category" color="primary" /></template>
          </q-select>
        </div>
        <div class="col-12 col-md-4 text-right">
             <div class="text-caption text-grey-7" :class="$q.dark.isActive ? 'text-grey-5' : ''">
                 Exibindo {{ filteredCosts.length }} registros
             </div>
        </div>
      </q-card-section>
    </q-card>

    <q-banner v-if="isDemo && hasOlderData" class="bg-amber-1 text-amber-10 q-mb-lg rounded-borders border-amber">
      <template v-slot:avatar><q-icon name="lock_clock" color="amber-9" /></template>
      <div class="text-subtitle1">
        <strong>Histórico Limitado:</strong> Exibindo apenas os últimos 30 dias.
      </div>
      <div class="text-caption">A análise completa de TCO (Total Cost of Ownership) é exclusiva do Plano PRO.</div>
      <template v-slot:action>
        <q-btn flat color="amber-10" label="Ver Planos" @click="showComparisonDialog = true" />
      </template>
    </q-banner>

    <div class="row q-col-gutter-lg q-mb-lg">
      <div class="col-12 col-md-8">
        <q-card flat bordered class="full-height relative-position overflow-hidden">
          <q-card-section class="row items-center justify-between">
            <div>
                <div class="text-h6">Distribuição de Gastos</div>
                <div class="text-subtitle2 text-grey">Por Categoria Operacional</div>
            </div>
            <q-badge color="primary" outline label="Consolidado" />
          </q-card-section>
          
          <q-separator />
          
          <q-card-section class="q-pa-lg">
            <CostsPieChart v-if="filteredCosts.length > 0" :costs="filteredCosts" style="height: 320px;" />
            <div v-else class="text-center text-grey q-pa-xl column flex-center" style="min-height: 320px">
                <q-icon name="pie_chart_outline" size="64px" class="text-grey-4 q-mb-md" />
                Nenhum dado financeiro neste período.
            </div>
          </q-card-section>
          
          <div v-if="isDemo && isDateRangeBlocked" class="absolute-full flex flex-center blur-overlay z-top">
            <div class="text-center q-pa-xl rounded-borders shadow-10 bg-white text-black" style="max-width: 400px">
              <div class="bg-grey-2 q-pa-md rounded-borders inline-block q-mb-md">
                 <q-icon name="lock" size="xl" color="grey-6" />
              </div>
              <div class="text-h6 text-weight-bold">Período Bloqueado</div>
              <p class="text-grey-7 q-mt-sm">O plano Demo restringe a visualização aos últimos 30 dias.</p>
              <q-btn unelevated color="primary" label="Liberar Histórico Completo" class="q-mt-md full-width" @click="showComparisonDialog = true" />
            </div>
          </div>
        </q-card>
      </div>
      
      <div class="col-12 col-md-4">
        <div class="column q-gutter-y-md full-height">
          
          <q-card flat bordered class="col flex items-center p-relative overflow-hidden">
             <div class="absolute-right opacity-icon">
                 <q-icon name="account_balance_wallet" size="100px" :color="$q.dark.isActive ? '' : 'green-1'" />
             </div>
             <q-card-section class="q-pl-lg relative-position z-top">
                 <div class="text-overline text-green-7 text-weight-bold">CUSTO TOTAL</div>
                 <div class="text-h4 text-weight-bolder" :class="$q.dark.isActive ? 'text-white' : ''">
                     {{ formatCurrency(totalCost) }}
                 </div>
                 <div class="text-caption text-grey">Soma das despesas filtradas</div>
             </q-card-section>
          </q-card>

          <q-card flat bordered class="col flex items-center p-relative overflow-hidden">
             <div class="absolute-right opacity-icon">
                 <q-icon name="analytics" size="100px" :color="$q.dark.isActive ? '' : 'blue-1'" />
             </div>
             <q-card-section class="q-pl-lg relative-position z-top">
                 <div class="text-overline text-blue-7 text-weight-bold">MÉDIA POR LANÇAMENTO</div>
                 <div class="text-h4 text-weight-bolder" :class="$q.dark.isActive ? 'text-white' : ''">
                     {{ formatCurrency(averageCost) }}
                 </div>
                 <div class="text-caption text-grey">Ticket médio</div>
             </q-card-section>
          </q-card>

          <q-card flat bordered class="col flex items-center p-relative overflow-hidden">
             <div class="absolute-right opacity-icon">
                 <q-icon name="leaderboard" size="100px" :color="$q.dark.isActive ? '' : 'orange-1'" />
             </div>
             <q-card-section class="q-pl-lg relative-position z-top">
                 <div class="text-overline text-orange-8 text-weight-bold">MAIOR IMPACTO</div>
                 <div class="text-h4 text-weight-bolder text-primary ellipsis" style="max-width: 250px" :class="$q.dark.isActive ? 'text-white' : ''">
                     {{ topCostCategory }}
                 </div>
                 <div class="text-caption text-grey">Categoria de maior custo</div>
             </q-card-section>
          </q-card>

        </div>
      </div>
    </div>

    <q-card flat bordered>
      <q-table
        :rows="costsWithVehicleData"
        :columns="columns"
        row-key="id"
        :loading="costStore.isLoading || vehicleStore.isLoading"
        no-data-label="Nenhum registro encontrado."
        flat
        :rows-per-page-options="[10, 25, 50]"
        :card-class="$q.dark.isActive ? ' text-white' : ''"
        table-header-class="text-uppercase text-grey-7 bg-grey-2"
      >
        <template v-slot:top>
            <div class="text-h6 q-py-sm flex items-center">
               <q-icon name="list_alt" class="q-mr-sm" /> Detalhamento Financeiro
            </div>
        </template>
        
        <template v-slot:header="props">
            <q-tr :props="props" :class="$q.dark.isActive ? 'bg-' : 'bg-grey-1'">
                <q-th v-for="col in props.cols" :key="col.name" :props="props" class="text-weight-bold text-primary">
                    {{ col.label }}
                </q-th>
            </q-tr>
        </template>

        <template v-slot:body-cell-vehicle="props">
          <q-td :props="props">
            <router-link v-if="props.row.vehicle" :to="`/vehicles/${props.row.vehicle_id}`" class="text-primary text-weight-medium flex items-center no-wrap" style="text-decoration: none;">
              <q-icon name="precision_manufacturing" size="xs" class="q-mr-xs" />
              {{ props.row.vehicle.brand }} {{ props.row.vehicle.model }} 
              <span class="text-grey-6 q-ml-xs text-caption">({{ props.row.vehicle.license_plate || props.row.vehicle.identifier || 'S/N' }})</span>
            </router-link>
            <span v-else class="text-grey-5 text-italic">Geral / Não Identificado</span>
          </q-td>
        </template>
        
        <template v-slot:body-cell-cost_type="props">
            <q-td :props="props">
                <q-badge :color="$q.dark.isActive ? 'grey-7' : 'grey-3'" :text-color="$q.dark.isActive ? 'white' : 'grey-9'" class="q-px-sm q-py-xs">
                    {{ props.value }}
                </q-badge>
            </q-td>
        </template>

        <template v-slot:body-cell-amount="props">
            <q-td :props="props" class="text-weight-bold" :class="props.value > 1000 ? 'text-negative' : ''">
                {{ formatCurrency(props.row.amount) }}
            </q-td>
        </template>
      </q-table>
    </q-card>

    <q-dialog v-model="isAddCostDialogOpen">
      <AddCostDialog @close="isAddCostDialogOpen = false" @cost-added="refreshData" />
    </q-dialog>

    <q-dialog v-model="showComparisonDialog">
      <q-card style="width: 750px; max-width: 95vw;">
        <q-card-section class="bg-primary text-white q-py-lg text-center relative-position overflow-hidden">
          <div class="absolute-full opacity-10" style="transform: skewY(-5deg) scale(1.5); background: white;"></div>
          <q-icon name="insights" size="4em" class="q-mb-sm" />
          <div class="text-h4 text-weight-bold relative-position">Gestão Financeira Industrial</div>
          <div class="text-subtitle1 text-blue-2 relative-position">Controle total de TCO com o Plano PRO</div>
        </q-card-section>

        <q-card-section class="q-pa-none">
          <q-markup-table flat>
            <thead>
              <tr class="bg-grey-1 text-grey-7">
                <th class="text-left q-pa-md text-uppercase text-caption">Recurso</th>
                <th class="text-center text-weight-bold q-pa-md bg-amber-1 text-amber-9 border-left">Plano Demo</th>
                <th class="text-center text-weight-bold q-pa-md text-primary bg-blue-1">Plano PRO</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="text-weight-medium q-pa-md"><q-icon name="receipt_long" color="grey-6" size="xs" /> Lançamentos Mensais</td>
                <td class="text-center bg-amber-1 text-amber-10">{{ demoUsageLimitLabel }}</td>
                <td class="text-center text-primary text-weight-bold bg-blue-1"><q-icon name="check_circle" /> Ilimitado</td>
              </tr>
              <tr>
                <td class="text-weight-medium q-pa-md"><q-icon name="history" color="grey-6" size="xs" /> Histórico Financeiro</td>
                <td class="text-center bg-amber-1 text-amber-10">Últimos 30 dias</td>
                <td class="text-center text-primary text-weight-bold bg-blue-1"><q-icon name="check_circle" /> Completo</td>
              </tr>
              <tr>
                <td class="text-weight-medium q-pa-md"><q-icon name="trending_up" color="grey-6" size="xs" /> Análise de Depreciação</td>
                <td class="text-center bg-amber-1 text-amber-10">Básico</td>
                <td class="text-center text-primary text-weight-bold bg-blue-1">ROI & TCO</td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card-section>

        <q-card-actions align="center" class="q-pa-lg bg-grey-1">
          <div class="column items-center full-width q-gutter-y-md">
            <div class="text-h6 text-weight-bold">Quer reduzir o custo operacional da planta?</div>
            <q-btn color="positive" label="Falar com Consultor" size="lg" unelevated icon="whatsapp" class="full-width shadow-2" />
            <q-btn flat color="grey-7" label="Continuar avaliando" v-close-popup />
          </div>
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useVehicleCostStore } from 'stores/vehicle-cost-store';
import { useVehicleStore } from 'stores/vehicle-store';
import { useAuthStore } from 'stores/auth-store';
import { useDemoStore } from 'stores/demo-store';
import { useQuasar, type QTableColumn } from 'quasar';
import { format, parseISO } from 'date-fns';
import type { Vehicle } from 'src/models/vehicle-models';
import CostsPieChart from 'components/CostsPieChart.vue';
import AddCostDialog from 'components/AddCostDialog.vue';

const $q = useQuasar();
const costStore = useVehicleCostStore();
const vehicleStore = useVehicleStore();
const authStore = useAuthStore();
const demoStore = useDemoStore();

const isDemo = computed(() => authStore.user?.role === 'cliente_demo');
const showComparisonDialog = ref(false);
const isAddCostDialogOpen = ref(false);

const demoUsageCount = computed(() => demoStore.stats?.cost_count ?? 0);
const demoUsageLimit = computed(() => 15);
const demoUsageLimitLabel = computed(() => demoUsageLimit.value.toString());

const isLimitReached = computed(() => {
  if (!isDemo.value) return false;
  return demoUsageCount.value >= demoUsageLimit.value;
});

const usagePercentage = computed(() => {
  if (!isDemo.value || demoUsageLimit.value <= 0) return 0;
  const pct = Math.round((demoUsageCount.value / demoUsageLimit.value) * 100);
  return Math.min(pct, 100);
});

const hasOlderData = computed(() => {
    if (!costStore.costs.length) return false;
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    return costStore.costs.some(c => c.date && new Date(c.date) < thirtyDaysAgo);
});

// Corrige problema de tipo com dateRange que pode ser string ou objeto
const isDateRangeBlocked = computed(() => {
    if (!isDemo.value || !dateRange.value) return false;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const val = dateRange.value as any; 
    const dateStr = typeof val === 'string' ? val : val.from;
    const fromDate = new Date(dateStr);
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    return fromDate < thirtyDaysAgo;
});

const dateRange = ref(null);
const categoryFilter = ref<string | null>(null);
const costCategoryOptions = [
    "Manutenção Corretiva", 
    "Manutenção Preventiva", 
    "Energia Elétrica", 
    "Peças de Reposição", 
    "Lubrificantes/Óleo", 
    "Serviços Terceiros", 
    "Outros"
];

const usageColor = computed(() => {
  if (usagePercentage.value >= 100) return 'red-4';
  if (usagePercentage.value >= 80) return 'orange-4';
  return 'white';
});

const vehicleMap = computed(() => {
  const map = new Map<number, Vehicle>();
  if (vehicleStore.vehicles && Array.isArray(vehicleStore.vehicles)) {
    for (const vehicle of vehicleStore.vehicles) {
      map.set(vehicle.id, vehicle);
    }
  }
  return map;
});

const filteredCosts = computed(() => {
  let costs = costStore.costs || [];

  if (categoryFilter.value) {
    costs = costs.filter(cost => cost.cost_type === categoryFilter.value);
  }

  if (isDemo.value) {
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      costs = costs.filter(cost => cost.date && new Date(cost.date) >= thirtyDaysAgo);
  }

  return costs;
});

const costsWithVehicleData = computed(() => {
  return filteredCosts.value.map(cost => {
    return {
      ...cost, 
      vehicle: vehicleMap.value.get(cost.vehicle_id)
    };
  });
});

const totalCost = computed(() => filteredCosts.value.reduce((sum, cost) => sum + (cost.amount || 0), 0));
const averageCost = computed(() => {
    const len = filteredCosts.value.length;
    return len > 0 ? totalCost.value / len : 0;
});

const topCostCategory = computed(() => {
  if (filteredCosts.value.length === 0) return 'N/A';
  const costsByCategory: Record<string, number> = {};
  for (const cost of filteredCosts.value) {
    costsByCategory[cost.cost_type] = (costsByCategory[cost.cost_type] || 0) + (cost.amount || 0);
  }
  const sortedCategories = Object.entries(costsByCategory).sort((a, b) => b[1] - a[1]);
  return sortedCategories.length > 0 && sortedCategories[0] ? sortedCategories[0][0] : 'N/A';
});

const dateRangeText = computed(() => {
  if (dateRange.value) {
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const val = dateRange.value as any;
      const fromStr = typeof val === 'string' ? val : val.from;
      const toStr = typeof val === 'string' ? val : val.to;
      
      const from = format(parseISO(fromStr), 'dd/MM/yyyy');
      const to = toStr ? format(parseISO(toStr), 'dd/MM/yyyy') : from;
      return `${from} - ${to}`;
    } catch {
      return 'Período Selecionado';
    }
  }
  return 'Todo o período';
});

function formatCurrency(value: number | undefined | null) {
    return (value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

const columns: QTableColumn[] = [
  { 
    name: 'date', label: 'Data', field: 'date', align: 'left', sortable: true,
    format: (val) => val ? format(parseISO(val), 'dd/MM/yyyy') : '---' 
  },
  { name: 'description', label: 'Descrição', field: 'description', align: 'left', style: 'max-width: 300px; white-space: normal;' },
  { name: 'cost_type', label: 'Categoria', field: 'cost_type', align: 'center', sortable: true },
  { name: 'vehicle', label: 'Máquina', field: 'vehicle_id', align: 'left', sortable: true },
  { 
    name: 'amount', label: 'Valor', field: 'amount', align: 'right', sortable: true,
    format: (val) => formatCurrency(val) 
  },
];

function applyFilters() {
  let startDate = null;
  let endDate = null;

  if (dateRange.value) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const val = dateRange.value as any;
      const fromStr = typeof val === 'string' ? val : val.from;
      const toStr = typeof val === 'string' ? val : val.to;
      
      if (fromStr) startDate = new Date(fromStr);
      if (toStr) endDate = new Date(toStr);
  }

  const params = { startDate, endDate };
  void costStore.fetchAllCosts(params);
}

function openAddCostDialog() {
    if (isLimitReached.value) {
        showComparisonDialog.value = true;
        return;
    }
    isAddCostDialogOpen.value = true;
}

function refreshData() {
    applyFilters();
    if (authStore.isDemo) {
        void demoStore.fetchDemoStats(true);
    }
}

onMounted(() => {
  applyFilters();
  void vehicleStore.fetchAllVehicles({ page: 1, rowsPerPage: 9999 });
  if (authStore.isDemo) {
      void demoStore.fetchDemoStats();
  }
});
</script>

<style scoped lang="scss">
.demo-card-gradient {
  background: linear-gradient(135deg, var(--q-primary) 0%, darken($primary, 20%) 100%);
  border: none;
  border-radius: 12px;
}

.white-30 { color: rgba(255,255,255,0.3) !important; }
.opacity-10 { opacity: 0.1; }
.opacity-icon { opacity: 0.1; right: -20px; bottom: -20px; }
.blur-overlay { background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(6px); }
.body--dark .blur-overlay { background: rgba(0, 0, 0, 0.6); }
.border-amber { border: 1px solid #ffecb3; }
</style>
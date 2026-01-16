<!-- eslint-disable @typescript-eslint/no-explicit-any -->
<template>
  <q-page padding>
    <h1 class="text-h4 text-weight-bold q-my-md">Central de Relatórios (MES)</h1>

    <q-card flat bordered>
      <q-card-section>
        <div class="row q-col-gutter-md items-center">
          
          <div class="col-12 col-md-4">
            <q-select
              outlined
              v-model="filters.reportType"
              :options="reportOptions"
              label="1. Selecione o Tipo de Relatório"
              emit-value
              map-options
              dense
              option-disable="disable" 
            >
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.label }}</q-item-label>
                    <q-item-label caption class="text-grey-6">{{ scope.opt.caption }}</q-item-label>
                    <q-item-label caption v-if="scope.opt.disable" class="text-negative">
                      <q-icon name="lock" size="xs" /> Exclusivo Plano PRO
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
          </div>

          <div v-if="filters.reportType === 'vehicle_consolidated'" class="col-12 col-md-4">
            <q-select
              outlined
              v-model="filters.vehicleId"
              :options="machineOptions"
              label="2. Selecione a Máquina"
              emit-value
              map-options
              dense
              use-input
              @filter="filterMachines"
              :loading="isMachinesLoading"
            >
              <template v-slot:no-option>
                <q-item><q-item-section class="text-grey">Nenhuma máquina encontrada</q-item-section></q-item>
              </template>
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section avatar>
                    <q-icon name="precision_manufacturing" color="primary" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>{{ scope.opt.label }}</q-item-label>
                    <q-item-label caption>ID: {{ scope.opt.value }} | {{ scope.opt.category }}</q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
          </div>

          <div v-if="filters.reportType" class="col-12 col-md-4">
            <q-input
              outlined
              v-model="dateRangeText"
              :label="filters.reportType === 'vehicle_consolidated' ? '3. Selecione o Período' : '2. Selecione o Período'"
              readonly
              dense
            >
              <template v-slot:prepend><q-icon name="event" class="cursor-pointer" /></template>
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="filters.dateRange" range mask="YYYY-MM-DD" />
              </q-popup-proxy>
            </q-input>
          </div>
        </div>

        <div v-if="filters.reportType === 'vehicle_consolidated'" class="q-mt-md">
          <div class="text-subtitle1 q-mb-sm text-weight-bold text-grey-8">4. Dados para Incluir:</div>
          <div class="row q-col-gutter-sm">
            <div class="col-6 col-sm-4 col-md-3">
              <q-checkbox dense v-model="vehicleReportSections.performance_summary" label="Performance (OEE)" color="teal" />
            </div>
            <div class="col-6 col-sm-4 col-md-3">
              <q-checkbox dense v-model="vehicleReportSections.financial_summary" label="Resumo de Custos" color="teal" />
            </div>
            <div class="col-6 col-sm-4 col-md-3">
              <q-checkbox dense v-model="vehicleReportSections.costs_detailed" label="Detalhes de Produção" color="teal" />
            </div>
            <div class="col-6 col-sm-4 col-md-3">
              <q-checkbox dense v-model="vehicleReportSections.maintenance_detailed" label="Histórico de Manutenção" color="teal" />
            </div>
            <div class="col-6 col-sm-4 col-md-3">
              <q-checkbox dense v-model="vehicleReportSections.journeys_detailed" label="Turnos de Trabalho" color="teal" />
            </div>
            <div class="col-6 col-sm-4 col-md-3">
              <q-checkbox dense v-model="vehicleReportSections.documents_detailed" label="Documentação Técnica" color="teal" />
            </div>
          </div>
        </div>
      </q-card-section>

      <q-card-actions class="q-pa-md bg-grey-1" align="right">
        <q-btn
          @click="generateReport"
          color="primary"
          label="GERAR RELATÓRIO"
          icon="summarize"
          push
          size="lg"
          :loading="reportStore.isLoading"
          :disable="!isFormValid"
          class="q-px-xl"
        />
      </q-card-actions>
    </q-card>

    <div v-if="reportStore.isLoading" class="flex flex-center q-mt-xl column">
      <q-spinner-gears color="primary" size="4em" />
      <div class="q-mt-md text-h6 text-grey-7">Processando dados da fábrica...</div>
    </div>

    <div v-else-if="reportStore.vehicleReport" class="q-mt-md">
      <div class="text-h6 text-primary q-mb-sm"><q-icon name="precision_manufacturing" /> Relatório Detalhado de Máquina</div>
      <VehicleReportDisplay :report="reportStore.vehicleReport" />
    </div>

    <div v-else-if="reportStore.driverPerformanceReport" class="q-mt-md">
      <div class="text-h6 text-primary q-mb-sm"><q-icon name="groups" /> Análise de Desempenho de Operadores</div>
      <DriverPerformanceReportDisplay :report="reportStore.driverPerformanceReport" />
    </div>

    <div v-else-if="reportStore.fleetManagementReport" class="q-mt-md">
      <div class="text-h6 text-primary q-mb-sm"><q-icon name="insights" /> Relatório Gerencial de Produção</div>
      <FleetManagementReportDisplay :report="reportStore.fleetManagementReport" />
    </div>

    <div v-else class="flex flex-center column text-center q-pa-xl text-grey-5">
      <q-icon name="plagiarism" size="8em" />
      <p class="text-h5 q-mt-md">Nenhum relatório gerado.</p>
      <p class="text-body1">Utilize os filtros acima para buscar dados históricos.</p>
    </div>

  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useQuasar } from 'quasar';
import { format } from 'date-fns';
import { useReportStore } from 'stores/report-store';
import { useProductionStore } from 'stores/production-store'; // Nova Store
import { useAuthStore } from 'stores/auth-store';

// Componentes de Exibição (Mantidos os originais, pois o backend retorna a estrutura antiga)
import VehicleReportDisplay from 'components/reports/VehicleReportDisplay.vue';
import DriverPerformanceReportDisplay from 'components/reports/DriverPerformanceReportDisplay.vue';
import FleetManagementReportDisplay from 'components/reports/FleetManagementReportDisplay.vue';

const $q = useQuasar();
const reportStore = useReportStore();
const productionStore = useProductionStore(); // Usando ProductionStore ao invés de VehicleStore
const authStore = useAuthStore();

const isDemo = computed(() => authStore.user?.role === 'cliente_demo');
const isMachinesLoading = ref(false);

const filters = ref({
  reportType: null as 'vehicle_consolidated' | 'driver_performance' | 'fleet_management' | null,
  vehicleId: null as number | null, // Mantive o nome vehicleId para compatibilidade com a store de reports
  dateRange: null as { from: string, to: string } | null,
});

// Configuração das Seções (Mapeadas para nomes de fábrica na UI)
const vehicleReportSections = ref({
  performance_summary: true,
  financial_summary: true,
  costs_detailed: true,
  fuel_logs_detailed: false, // Menos relevante para máquinas estáticas, mas mantido
  maintenance_detailed: true, // Muito relevante
  fines_detailed: false, // Irrelevante para máquinas
  journeys_detailed: true, // Turnos
  documents_detailed: true,
  tires_detailed: false,
});

watch(() => filters.value.reportType, () => {
  filters.value.vehicleId = null;
  filters.value.dateRange = null;
  reportStore.clearReports();
});

// --- OPÇÕES DE RELATÓRIO (Adaptadas para MES) ---
const reportOptions = computed(() => [
  { 
    label: 'Dossiê da Máquina', 
    caption: 'Histórico completo, OEE, Manutenções e Custos',
    value: 'vehicle_consolidated',
    disable: isDemo.value 
  },
  { 
    label: 'Desempenho de Operadores', 
    caption: 'Produtividade, Eficiência e Ranking',
    value: 'driver_performance' 
  },
  { 
    label: 'Visão Geral da Fábrica', 
    caption: 'Consolidado de todas as máquinas e setores',
    value: 'fleet_management' 
  },
]);

// Lista de máquinas para o dropdown
const machineOptions = ref<{ label: string, value: number, category: string }[]>([]);

const dateRangeText = computed(() => {
  if (filters.value.dateRange) {
    // Tratamento para data única ou range
    const fromStr = typeof filters.value.dateRange === 'string' ? filters.value.dateRange : filters.value.dateRange.from;
    const toStr = typeof filters.value.dateRange === 'string' ? filters.value.dateRange : filters.value.dateRange.to;
    
    if(!fromStr) return '';

    const from = format(new Date(fromStr.replace(/-/g, '/')), 'dd/MM/yyyy');
    const to = toStr ? format(new Date(toStr.replace(/-/g, '/')), 'dd/MM/yyyy') : from;
    
    return `${from} - ${to}`;
  }
  return '';
});

const isFormValid = computed(() => {
  if (!filters.value.reportType || !filters.value.dateRange) return false;
  if (filters.value.reportType === 'vehicle_consolidated') {
    return !!filters.value.vehicleId;
  }
  return true;
});

// Filtro de Máquinas no Select
function filterMachines(val: string, update: (callback: () => void) => void) {
  update(() => {
    const needle = val.toLowerCase();
    machineOptions.value = productionStore.machinesList
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .filter((m: any) =>
        (m.brand?.toLowerCase().includes(needle) ||
         m.model?.toLowerCase().includes(needle) ||
         m.category?.toLowerCase().includes(needle))
      )
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .map((m: any) => ({
        label: `${m.brand} ${m.model}`,
        value: m.id,
        category: m.category || 'Geral'
      }));
  });
}

async function generateReport() {
  if (!isFormValid.value || !filters.value.dateRange) {
    $q.notify({ type: 'warning', message: 'Por favor, preencha todos os filtros obrigatórios.' });
    return;
  }

  // Normaliza datas (se o usuário selecionar apenas um dia, from e to são strings ou o objeto pode variar)
  let from = '';
  let to = '';
  
  if (typeof filters.value.dateRange === 'string') {
      from = filters.value.dateRange;
      to = filters.value.dateRange;
  } else {
      from = filters.value.dateRange.from;
      to = filters.value.dateRange.to;
  }

  // Mapeia chamadas para o Backend (Mantendo nomes antigos por compatibilidade)
  if (filters.value.reportType === 'vehicle_consolidated' && filters.value.vehicleId) {
    await reportStore.generateVehicleConsolidatedReport(
      filters.value.vehicleId, // Enviando ID da Máquina como VehicleID
      from,
      to,
      vehicleReportSections.value
    );
  } else if (filters.value.reportType === 'driver_performance') {
    await reportStore.generateDriverPerformanceReport(from, to);
  } else if (filters.value.reportType === 'fleet_management') {
    await reportStore.generateFleetManagementReport(from, to);
  }
}

onMounted(async () => {
  reportStore.clearReports();
  isMachinesLoading.value = true;
  await productionStore.fetchAvailableMachines(); // Busca máquinas da ProductionStore
  
  // Popula opções iniciais
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  machineOptions.value = productionStore.machinesList.map((m: any) => ({
      label: `${m.brand} ${m.model}`,
      value: m.id,
      category: m.category || 'Geral'
  }));
  
  isMachinesLoading.value = false;
});
</script>
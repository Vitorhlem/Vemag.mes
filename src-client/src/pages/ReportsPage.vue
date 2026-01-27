<template>
  <q-page padding class="bg-grey-1">
    <div class="row items-center justify-between q-mb-md">
      <div>
        <h1 class="text-h4 text-weight-bold text-blue-grey-9 q-my-none">Central de Relatórios (MES)</h1>
        <div class="text-subtitle2 text-grey-7">Análise consolidada de produção e eficiência</div>
      </div>
      <q-btn flat icon="refresh" label="Limpar Filtros" @click="resetFilters" color="primary" />
    </div>

    <q-card flat bordered class="bg-white shadow-1">
      <q-card-section>
        <div class="row q-col-gutter-md items-center">
          
          <div class="col-12 col-md-4">
            <q-select
              outlined
              v-model="filters.reportType"
              :options="reportOptions"
              label="1. Tipo de Relatório"
              emit-value
              map-options
              dense
              bg-color="white"
              option-disable="disable" 
            >
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section avatar>
                    <q-icon :name="scope.opt.icon" color="primary" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>{{ scope.opt.label }}</q-item-label>
                    <q-item-label caption class="text-grey-6">{{ scope.opt.caption }}</q-item-label>
                    <q-item-label caption v-if="scope.opt.disable" class="text-negative text-weight-bold">
                      <q-icon name="lock" size="xs" /> Exclusivo Plano PRO
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
          </div>

          <div v-if="filters.reportType === 'vehicle_consolidated'" class="col-12 col-md-4 animate-fade">
            <q-select
              outlined
              v-model="filters.vehicleId"
              :options="machineOptions"
              label="2. Selecione a Máquina"
              emit-value
              map-options
              dense
              use-input
              bg-color="white"
              @filter="filterMachines"
              :loading="isMachinesLoading"
            >
              <template v-slot:no-option>
                <q-item><q-item-section class="text-grey">Nenhuma máquina encontrada</q-item-section></q-item>
              </template>
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section avatar>
                    <q-icon name="precision_manufacturing" color="teal" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label class="text-weight-bold">{{ scope.opt.label }}</q-item-label>
                    <q-item-label caption>ID: {{ scope.opt.value }} | {{ scope.opt.category }}</q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
          </div>

          <div v-if="filters.reportType" class="col-12 col-md-4 animate-fade">
            <q-input
              outlined
              v-model="dateRangeText"
              label="3. Período de Análise"
              readonly
              dense
              bg-color="white"
              placeholder="Selecione as datas"
            >
              <template v-slot:prepend><q-icon name="event" class="cursor-pointer text-primary" /></template>
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="filters.dateRange" range mask="YYYY-MM-DD">
                  <div class="row items-center justify-end">
                    <q-btn v-close-popup label="Confirmar" color="primary" flat />
                  </div>
                </q-date>
              </q-popup-proxy>
            </q-input>
          </div>
        </div>

        <div v-if="filters.reportType === 'vehicle_consolidated'" class="q-mt-lg animate-fade">
          <div class="text-subtitle2 q-mb-sm text-weight-bold text-grey-8">Dados para Incluir no Relatório:</div>
          <div class="row q-col-gutter-sm bg-grey-2 q-pa-sm rounded-borders">
            <div class="col-6 col-sm-4 col-md-3">
              <q-checkbox dense v-model="vehicleReportSections.performance_summary" label="Performance (OEE)" color="teal" />
            </div>
            <div class="col-6 col-sm-4 col-md-3">
              <q-checkbox dense v-model="vehicleReportSections.financial_summary" label="Custos Operacionais" color="teal" />
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

      <q-card-actions class="q-pa-md bg-grey-1 border-top" align="right">
        <div class="text-caption text-grey-6 q-mr-md" v-if="!isFormValid">
          * Preencha os campos obrigatórios para gerar
        </div>
        <q-btn
          @click="handleGenerateReport"
          color="primary"
          label="GERAR RELATÓRIO"
          icon="summarize"
          push
          :loading="reportStore.isLoading"
          :disable="!isFormValid"
          class="q-px-xl"
        />
      </q-card-actions>
    </q-card>

    <div class="q-mt-lg relative-position min-height-result">
      
      <div v-if="reportStore.isLoading" class="absolute-center text-center">
        <q-spinner-gears color="primary" size="4em" />
        <div class="text-h6 text-grey-7 q-mt-md">Processando dados industriais...</div>
        <div class="text-caption text-grey-5">Calculando KPIs, OEE e Custos</div>
      </div>

      <div v-else-if="reportStore.vehicleReport && filters.reportType === 'vehicle_consolidated'" class="animate-fade-up">
        <div class="row items-center q-mb-md">
          <q-icon name="precision_manufacturing" size="md" color="teal" class="q-mr-sm" />
          <div class="text-h5 text-teal-9">Dossiê Consolidado de Máquina</div>
        </div>
        <VehicleReportDisplay :report="reportStore.vehicleReport" />
      </div>

      <div v-else-if="reportStore.driverPerformanceReport && filters.reportType === 'driver_performance'" class="animate-fade-up">
        <div class="row items-center q-mb-md">
          <q-icon name="groups" size="md" color="primary" class="q-mr-sm" />
          <div class="text-h5 text-primary">Análise de Performance de Operadores</div>
        </div>
        <DriverPerformanceReportDisplay :report="reportStore.driverPerformanceReport" />
      </div>

      <div v-else-if="reportStore.fleetManagementReport && filters.reportType === 'fleet_management'" class="animate-fade-up">
        <div class="row items-center q-mb-md">
          <q-icon name="domain" size="md" color="indigo" class="q-mr-sm" />
          <div class="text-h5 text-indigo-9">Relatório Gerencial da Fábrica</div>
        </div>
        <FleetManagementReportDisplay :report="reportStore.fleetManagementReport" />
      </div>

      <div v-else class="flex flex-center column text-center q-pa-xl text-grey-5 border-dashed">
        <q-icon name="assessment" size="6em" class="opacity-50" />
        <p class="text-h6 q-mt-md text-grey-6">Nenhum relatório visualizado</p>
        <p class="text-body2">Utilize os filtros acima para buscar dados históricos do sistema.</p>
      </div>

    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useQuasar } from 'quasar';
import { format, parseISO, isValid } from 'date-fns';
import { storeToRefs } from 'pinia';
import { useReportStore } from 'stores/report-store';
import { useProductionStore } from 'stores/production-store';
import { useAuthStore } from 'stores/auth-store';

// Componentes
import VehicleReportDisplay from 'components/reports/VehicleReportDisplay.vue';
import DriverPerformanceReportDisplay from 'components/reports/DriverPerformanceReportDisplay.vue';
import FleetManagementReportDisplay from 'components/reports/FleetManagementReportDisplay.vue';

const $q = useQuasar();
const reportStore = useReportStore();
const productionStore = useProductionStore();
const authStore = useAuthStore();

// Usar storeToRefs para garantir reatividade nos templates
const { machinesList } = storeToRefs(productionStore);

const isDemo = computed(() => authStore.user?.role === 'cliente_demo');
const isMachinesLoading = ref(false);

// Opções de Relatórios
const reportOptions = computed(() => [
  { 
    label: 'Dossiê da Máquina', 
    caption: 'OEE, Histórico, Custos e Manutenção',
    value: 'vehicle_consolidated',
    icon: 'precision_manufacturing',
    disable: isDemo.value 
  },
  { 
    label: 'Desempenho de Operadores', 
    caption: 'Ranking, Eficiência e Produtividade',
    value: 'driver_performance',
    icon: 'engineering'
  },
  { 
    label: 'Visão Geral da Fábrica', 
    caption: 'KPIs Globais, Custos Totais e Alertas',
    value: 'fleet_management',
    icon: 'domain' 
  },
]);

// Estado dos Filtros
const filters = ref({
  reportType: null as 'vehicle_consolidated' | 'driver_performance' | 'fleet_management' | null,
  vehicleId: null as number | null,
  dateRange: null as { from: string, to: string } | string | null,
});

// Configuração das Seções do Relatório de Máquina
const vehicleReportSections = ref({
  performance_summary: true,
  financial_summary: true,
  costs_detailed: true,
  fuel_logs_detailed: false,
  maintenance_detailed: true,
  fines_detailed: false,
  journeys_detailed: true,
  documents_detailed: true,
  tires_detailed: false,
});

// Lista de máquinas filtrável
const machineOptions = ref<{ label: string, value: number, category: string }[]>([]);

// --- COMPUTEDS ---

// Texto legível da data
const dateRangeText = computed(() => {
  if (!filters.value.dateRange) return '';
  
  let from = '', to = '';
  
  if (typeof filters.value.dateRange === 'string') {
    from = filters.value.dateRange;
    to = filters.value.dateRange;
  } else {
    from = filters.value.dateRange.from;
    to = filters.value.dateRange.to;
  }

  // Formata para BR
  const formatData = (d: string) => {
      // Normaliza 2023/10/01 -> 2023-10-01
      const normalized = d.replace(/\//g, '-'); 
      const dateObj = parseISO(normalized);
      return isValid(dateObj) ? format(dateObj, 'dd/MM/yyyy') : d;
  };

  return from === to ? formatData(from) : `${formatData(from)} até ${formatData(to)}`;
});

// Validação do Formulário
const isFormValid = computed(() => {
  if (!filters.value.reportType || !filters.value.dateRange) return false;
  if (filters.value.reportType === 'vehicle_consolidated') {
    return !!filters.value.vehicleId;
  }
  return true;
});

// --- WATCHERS ---

// Limpa dados ao mudar tipo de relatório
watch(() => filters.value.reportType, () => {
  reportStore.clearReports();
});

// --- MÉTODOS ---

function resetFilters() {
  filters.value = { reportType: null, vehicleId: null, dateRange: null };
  reportStore.clearReports();
}

function filterMachines(val: string, update: (callback: () => void) => void) {
  update(() => {
    const needle = val.toLowerCase();
    const source = machinesList.value || [];
    
    machineOptions.value = source
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .filter((m: any) =>
        (m.brand?.toLowerCase().includes(needle) ||
         m.model?.toLowerCase().includes(needle) ||
         m.identifier?.toLowerCase().includes(needle))
      )
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .map((m: any) => ({
        label: m.model ? `${m.brand || ''} ${m.model}` : m.identifier,
        value: m.id,
        category: m.status || 'Ativo'
      }));
  });
}

async function handleGenerateReport() {
  if (!isFormValid.value || !filters.value.dateRange) {
    $q.notify({ type: 'warning', message: 'Preencha todos os campos obrigatórios.' });
    return;
  }

  // NORMALIZAÇÃO DE DATAS (CRUCIAL PARA O BACKEND)
  let from = '';
  let to = '';
  
  if (typeof filters.value.dateRange === 'string') {
      // Caso selecionou um dia único: 2023/10/05
      from = filters.value.dateRange.replace(/\//g, '-');
      to = filters.value.dateRange.replace(/\//g, '-');
  } else {
      // Caso selecionou range: { from: '2023/10/01', to: '2023/10/10' }
      from = filters.value.dateRange.from.replace(/\//g, '-');
      to = filters.value.dateRange.to.replace(/\//g, '-');
  }

  try {
    if (filters.value.reportType === 'vehicle_consolidated' && filters.value.vehicleId) {
      await reportStore.generateVehicleConsolidatedReport(
        filters.value.vehicleId,
        from,
        to,
        vehicleReportSections.value
      );
    } else if (filters.value.reportType === 'driver_performance') {
      await reportStore.generateDriverPerformanceReport(from, to);
    } else if (filters.value.reportType === 'fleet_management') {
      await reportStore.generateFleetManagementReport(from, to);
    }
    
    $q.notify({ type: 'positive', message: 'Relatório gerado com sucesso!', icon: 'check_circle' });
    
  } catch (error) {
    console.error(error);
    $q.notify({ type: 'negative', message: 'Erro ao gerar relatório. Verifique se há dados no período.' });
  }
}

onMounted(async () => {
  reportStore.clearReports();
  isMachinesLoading.value = true;
  try {
    await productionStore.fetchAvailableMachines();
    // Popula lista inicial
    machineOptions.value = (machinesList.value || []).map((m: any) => ({
      label: m.model ? `${m.brand || ''} ${m.model}` : m.identifier,
      value: m.id,
      category: m.status || 'Ativo'
    }));
  } catch (e) {
    console.error("Erro ao carregar máquinas", e);
  } finally {
    isMachinesLoading.value = false;
  }
});
</script>

<style scoped>
.min-height-result {
  min-height: 400px;
}
.border-dashed {
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
}
.border-top {
  border-top: 1px solid #f0f0f0;
}
.opacity-50 {
  opacity: 0.5;
}
.animate-fade {
  animation: fadeIn 0.5s ease-out;
}
.animate-fade-up {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
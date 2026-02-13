<template>
  <div class="report-wrapper">
    <div class="row justify-end q-mb-sm print-hide">
      <q-btn 
        color="primary" 
        icon="print" 
        label="Imprimir Dossiê" 
        unelevated 
        @click="printReport"
      />
    </div>

    <div class="report-container bg-white q-pa-md rounded-borders print-area">
      
      <div class="row items-center justify-between q-mb-lg border-bottom q-pb-md">
        <div class="row items-center">
          <img src="/vemagdark.png" class="report-logo q-mr-lg" alt="VEMAG Logo" />
          
          <q-separator vertical class="q-mr-lg gt-xs" />

          <div class="row items-center">
            <q-avatar size="50px" font-size="24px" color="teal-1" text-color="teal-9" class="q-mr-md gt-xs">
              {{ report.vehicle_model.charAt(0) }}
            </q-avatar>
            <div>
              <div class="text-h5 text-weight-bold text-blue-grey-9">{{ report.vehicle_model }}</div>
              <div class="text-caption text-grey-7">ID: {{ report.vehicle_identifier }} | Dossiê de Performance</div>
            </div>
          </div>
        </div>
        
        <div class="text-right">
          <div class="text-subtitle2 text-teal-8">
            {{ formatDate(report.report_period_start) }} até {{ formatDate(report.report_period_end) }}
          </div>
          <div class="text-caption text-grey-5">Gerado em {{ new Date(report.generated_at).toLocaleString() }}</div>
        </div>
      </div>

      <div v-if="report.performance_summary" class="q-mb-xl">
        <div class="text-h6 text-teal-9 q-mb-md border-left-teal q-pl-sm">Performance Global (OEE)</div>
        
        <div class="row q-col-gutter-md">
          <div class="col-12 col-md-3">
            <q-card flat bordered class="text-center q-pa-md bg-teal-1 print-card">
              <div class="text-h3 text-weight-bolder text-teal-9">{{ report.performance_summary.oee_percent }}%</div>
              <div class="text-subtitle2 text-teal-8">Disponibilidade</div>
            </q-card>
          </div>
          <div class="col-12 col-md-3">
            <q-card flat bordered class="q-pa-sm print-card">
              <q-item>
                <q-item-section avatar><q-icon name="timer" color="primary" size="lg"/></q-item-section>
                <q-item-section>
                  <q-item-label class="text-h5">{{ report.performance_summary.availability_percent }}%</q-item-label>
                  <q-item-label caption>Disponibilidade</q-item-label>
                </q-item-section>
              </q-item>
            </q-card>
          </div>
          <div class="col-12 col-md-3">
            <q-card flat bordered class="q-pa-sm print-card">
              <q-item>
                <q-item-section avatar><q-icon name="healing" color="orange" size="lg"/></q-item-section>
                <q-item-section>
                  <q-item-label class="text-h5">{{ report.performance_summary.mtbf_hours }} h</q-item-label>
                  <q-item-label caption>MTBF (Médio entre Falhas)</q-item-label>
                </q-item-section>
              </q-item>
            </q-card>
          </div>
          <div class="col-12 col-md-3">
            <q-card flat bordered class="q-pa-sm print-card">
              <q-item>
                <q-item-section avatar><q-icon name="build_circle" color="red" size="lg"/></q-item-section>
                <q-item-section>
                  <q-item-label class="text-h5">{{ report.performance_summary.mttr_hours }} h</q-item-label>
                  <q-item-label caption>MTTR (Médio para Reparo)</q-item-label>
                </q-item-section>
              </q-item>
            </q-card>
          </div>
        </div>
      </div>

      <div v-if="report.performance_summary" class="row q-col-gutter-lg q-mb-xl page-break-inside-avoid">
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height print-card">
            <q-card-section>
              <div class="text-subtitle1 text-weight-bold">Distribuição do Tempo (Horas)</div>
            </q-card-section>
            <q-card-section>
              <ApexChart type="bar" height="300" :options="waterfallOptions" :series="waterfallSeries" />
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-md-6">
          <q-card flat bordered class="full-height print-card">
            <q-card-section>
              <div class="text-subtitle1 text-weight-bold">Top 5 Motivos de Parada (Pareto)</div>
            </q-card-section>
            <q-card-section>
              <ApexChart type="bar" height="300" :options="paretoOptions" :series="paretoSeries" />
            </q-card-section>
          </q-card>
        </div>
      </div>

      <div v-if="report.financial_summary" class="q-mb-xl page-break-inside-avoid">
        <div class="text-h6 text-teal-9 q-mb-md border-left-teal q-pl-sm">Análise Financeira</div>
        <div class="row q-col-gutter-md items-stretch">
          <div class="col-12 col-md-4">
             <q-card flat class="bg-grey-1 text-center q-pa-lg full-height flex flex-center column print-card">
                <div class="text-caption text-uppercase text-grey-7">Custo Total do Período</div>
                <div class="text-h4 text-weight-bolder text-teal-10 q-my-sm">
                  {{ formatCurrency(report.financial_summary.total_costs) }}
                </div>
                <div class="text-caption text-grey-6">
                  {{ formatCurrency(report.financial_summary.cost_per_metric) }} / hora produtiva
                </div>
             </q-card>
          </div>
          <div class="col-12 col-md-8">
             <q-markup-table flat bordered dense class="print-card">
               <thead>
                 <tr>
                   <th class="text-left">Categoria de Custo</th>
                   <th class="text-right">Valor</th>
                   <th class="text-right">%</th>
                 </tr>
               </thead>
               <tbody>
                 <tr v-for="(amount, cat) in report.financial_summary.costs_by_category" :key="cat">
                   <td>{{ cat }}</td>
                   <td class="text-right">{{ formatCurrency(amount) }}</td>
                   <td class="text-right">{{ ((amount / report.financial_summary.total_costs)*100).toFixed(1) }}%</td>
                 </tr>
               </tbody>
             </q-markup-table>
          </div>
        </div>
      </div>

      <div v-if="report.maintenance_detailed?.length" class="q-mb-lg page-break-before">
        <div class="text-h6 text-teal-9 q-mb-md border-left-teal q-pl-sm">Histórico de Intervenções</div>
        <q-table
          flat bordered
          :rows="report.maintenance_detailed"
          :columns="maintenanceColumns"
          row-key="id"
          dense
          hide-pagination
          :pagination="{ rowsPerPage: 0 }"
          class="print-card"
        >
          <template v-slot:body-cell-status="props">
            <q-td :props="props">
              <q-badge :color="props.value === 'CONCLUIDA' ? 'positive' : 'warning'" class="print-badge">
                {{ props.value }}
              </q-badge>
            </q-td>
          </template>
        </q-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { date } from 'quasar';
import ApexChart from 'vue3-apexcharts';
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const props = defineProps<{ report: any }>();

const formatDate = (val: string) => date.formatDate(val, 'DD/MM/YYYY');
const formatCurrency = (val: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

const printReport = () => {
  window.print();
};

const waterfallSeries = computed(() => [{
  name: 'Horas',
  data: [
    { x: 'Total Calendário', y: props.report.performance_summary?.time_distribution?.calendar || 0 },
    { x: 'Paradas Planejadas', y: props.report.performance_summary?.time_distribution?.planned_stop || 0 },
    { x: 'Paradas N/Planej.', y: props.report.performance_summary?.time_distribution?.unplanned_stop || 0 },
    { x: 'Tempo Produtivo', y: props.report.performance_summary?.time_distribution?.running || 0, fillColor: '#26A69A' }
  ]
}]);

const waterfallOptions = {
  chart: { type: 'bar', toolbar: { show: false } },
  plotOptions: { bar: { horizontal: false, columnWidth: '55%', borderRadius: 4 } },
  dataLabels: { enabled: true },
  xaxis: { type: 'category' },
  colors: ['#546E7A', '#FFB74D', '#EF5350', '#26A69A']
};

const paretoSeries = computed(() => [{
  name: 'Minutos',
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: (props.report.performance_summary?.stop_reasons || []).map((r: any) => r.duration_minutes)
}]);

const paretoOptions = computed(() => ({
  chart: { type: 'bar', toolbar: { show: false } },
  plotOptions: { bar: { horizontal: true, borderRadius: 4 } },
  dataLabels: { enabled: true },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  xaxis: { categories: (props.report.performance_summary?.stop_reasons || []).map((r: any) => r.reason) },
  colors: ['#EF5350']
}));

const maintenanceColumns = [
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  { name: 'date', label: 'Data', field: (row: any) => formatDate(row.created_at), align: 'left' },
  { name: 'type', label: 'Tipo', field: 'type', align: 'left' },
  { name: 'description', label: 'Descrição', field: 'description', align: 'left' },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  { name: 'reporter', label: 'Solicitante', field: (row: any) => row.reporter?.full_name || 'N/A', align: 'left' },
  { name: 'status', label: 'Status', field: 'status', align: 'center' },
];
</script>

<style scoped>
.report-container {
  font-family: 'Inter', sans-serif;
  max-width: 1200px;
  margin: 0 auto;
}
.report-logo {
  height: 50px;
  object-fit: contain;
}
.border-bottom { border-bottom: 2px solid #f0f0f0; }
.border-left-teal { border-left: 5px solid #009688; }

/* CSS CRÍTICO PARA IMPRESSÃO LIMPA */
@media print {
  /* 1. Oculta tudo que é filho direto do body, exceto se for nosso container (que será movido visualmente) */
  /* Nota: No Quasar/Vue, o app está dentro de #q-app. Vamos ocultar tudo dentro de body primeiro. */
  body > * {
    display: none !important;
  }

  /* 2. Reseta o body e html para permitir scroll completo e fundo branco */
  html, body {
    height: auto !important;
    overflow: visible !important;
    background: white !important;
    margin: 0 !important;
    padding: 0 !important;
  }

  /* 3. Força a exibição do relatório e o posiciona sobre tudo */
  .report-container {
    display: block !important;
    position: absolute; /* Absolute ou Fixed para sair do fluxo normal oculto */
    top: 0;
    left: 0;
    width: 100vw !important;
    min-height: 100vh;
    z-index: 99999;
    background-color: white !important;
    padding: 20px !important;
    margin: 0 !important;
    font-size: 12px; /* Ajuste opcional para caber melhor */
  }

  /* 4. Garante que os filhos do relatório sejam visíveis */
  .report-container * {
    visibility: visible;
  }

  /* 5. Oculta botões e elementos de tela */
  .print-hide { 
    display: none !important; 
  }
  
  /* 6. Estilização de Cards para papel (sem sombra, com borda) */
  .print-card {
    border: 1px solid #ccc !important;
    box-shadow: none !important;
    break-inside: avoid;
  }
  
  /* 7. Força impressão de cores de fundo (importante para gráficos e headers) */
  .bg-teal-1 { 
    background-color: #f0fdf4 !important; 
    -webkit-print-color-adjust: exact; 
    print-color-adjust: exact;
  }
  
  .bg-grey-1 {
    background-color: #f5f5f5 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  /* 8. Controles de quebra de página */
  .page-break-inside-avoid { break-inside: avoid; }
  .page-break-before { break-before: page; }
}
</style>
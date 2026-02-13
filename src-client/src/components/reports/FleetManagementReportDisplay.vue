<template>
  <div class="report-container bg-white q-pa-md rounded-borders print-area">
    
    <div class="row justify-end q-mb-sm print-hide">
      <q-btn 
        color="indigo" 
        icon="print" 
        label="Imprimir Relatório" 
        unelevated 
        @click="printReport"
      />
    </div>

    <div class="row items-center justify-between q-mb-lg border-bottom q-pb-md">
      <div class="row items-center">
        <img src="/vemagdark.png" class="report-logo q-mr-lg" alt="VEMAG Logo" />
        
        <q-separator vertical class="q-mr-lg gt-xs" />

        <div>
          <div class="text-h5 text-weight-bold text-indigo-9">Visão Geral da Fábrica</div>
          <div class="text-caption text-grey-7">Análise consolidada de {{ report.summary.active_machines_count }} ativos</div>
        </div>
      </div>
      <div class="text-right">
        <div class="text-subtitle2 text-indigo-8">
          {{ formatDate(report.report_period_start) }} até {{ formatDate(report.report_period_end) }}
        </div>
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-xl">
      <div class="col-12 col-md-3">
        <q-card flat bordered class="text-center q-pa-md bg-indigo-1 print-card">
          <div class="text-h3 text-weight-bolder text-indigo-9">{{ report.summary.global_oee }}%</div>
          <div class="text-subtitle2 text-indigo-8">Disponibilidade da Planta</div>
        </q-card>
      </div>
      <div class="col-12 col-md-3">
        <q-card flat bordered class="q-pa-sm print-card">
          <q-item>
            <q-item-section avatar><q-icon name="attach_money" color="green" size="lg"/></q-item-section>
            <q-item-section>
              <q-item-label class="text-h5">{{ formatCurrency(report.summary.total_cost) }}</q-item-label>
              <q-item-label caption>Custo Total Operacional</q-item-label>
            </q-item-section>
          </q-item>
        </q-card>
      </div>
      <div class="col-12 col-md-3">
        <q-card flat bordered class="q-pa-sm print-card">
          <q-item>
            <q-item-section avatar><q-icon name="precision_manufacturing" color="teal" size="lg"/></q-item-section>
            <q-item-section>
              <q-item-label class="text-h5">{{ report.summary.total_production_hours }} h</q-item-label>
              <q-item-label caption>Horas Produzindo</q-item-label>
            </q-item-section>
          </q-item>
        </q-card>
      </div>
      <div class="col-12 col-md-3">
        <q-card flat bordered class="q-pa-sm print-card">
          <q-item>
            <q-item-section avatar><q-icon name="warning" color="red" size="lg"/></q-item-section>
            <q-item-section>
              <q-item-label class="text-h5">{{ report.summary.total_downtime_hours }} h</q-item-label>
              <q-item-label caption>Horas Paradas (Gargalo)</q-item-label>
            </q-item-section>
          </q-item>
        </q-card>
      </div>
    </div>

    <div class="row q-col-gutter-lg q-mb-xl page-break-inside-avoid">
      <div class="col-12 col-md-6">
        <q-card flat bordered class="full-height print-card">
          <q-card-section>
            <div class="text-subtitle1 text-weight-bold text-positive">🏆 Top 5 Eficiência (OEE)</div>
          </q-card-section>
          <q-list separator>
            <q-item v-for="(v, i) in report.top_5_most_efficient_vehicles" :key="i">
              <q-item-section avatar>
                <q-avatar size="sm" color="green-1" text-color="green">{{ i + 1 }}</q-avatar>
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold">{{ v.vehicle_identifier }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <div class="text-weight-bold text-green-9">{{ v.value }}%</div>
                <div class="text-caption text-grey-6" v-if="v.secondary_value">{{ v.secondary_value.toFixed(1) }}h paradas</div>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>

      <div class="col-12 col-md-6">
        <q-card flat bordered class="full-height print-card">
          <q-card-section>
            <div class="text-subtitle1 text-weight-bold text-negative">⚠️ Top 5 Gargalos (Baixo OEE)</div>
          </q-card-section>
          <q-list separator>
            <q-item v-for="(v, i) in report.top_5_least_efficient_vehicles" :key="i">
              <q-item-section avatar>
                <q-avatar size="sm" color="red-1" text-color="red">{{ i + 1 }}</q-avatar>
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold">{{ v.vehicle_identifier }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-badge color="red" :label="v.value + '%'" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>
    </div>

    <div class="q-mb-lg page-break-inside-avoid">
      <div class="text-h6 text-indigo-9 q-mb-md">Distribuição de Custos Industriais</div>
      <div class="row q-col-gutter-md">
        <div class="col-12 col-md-8">
           <ApexChart type="bar" height="300" :options="costChartOptions" :series="costChartSeries" />
        </div>
        <div class="col-12 col-md-4">
           <q-list bordered separator class="rounded-borders print-card">
             <q-item v-for="(amount, cat) in report.costs_by_category" :key="cat">
               <q-item-section>{{ cat }}</q-item-section>
               <q-item-section side>{{ formatCurrency(amount) }}</q-item-section>
             </q-item>
           </q-list>
        </div>
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

const costChartSeries = computed(() => [{
  name: 'Custo (R$)',
  data: Object.values(props.report.costs_by_category || {})
}]);

const costChartOptions = computed(() => ({
  chart: { type: 'bar', toolbar: { show: false } },
  xaxis: { categories: Object.keys(props.report.costs_by_category || {}) },
  colors: ['#3F51B5'],
  plotOptions: { bar: { borderRadius: 4, horizontal: true } }
}));
</script>

<style scoped>
.report-container { font-family: 'Inter', sans-serif; max-width: 1200px; margin: 0 auto; }
.report-logo { height: 50px; object-fit: contain; }
.border-bottom { border-bottom: 2px solid #f0f0f0; }

@media print {
  .print-hide { display: none !important; }
  .report-container { width: 100% !important; max-width: none !important; padding: 0 !important; box-shadow: none !important; }
  .q-card { box-shadow: none !important; border: 1px solid #ddd !important; }
  .bg-indigo-1 { background-color: #e8eaf6 !important; -webkit-print-color-adjust: exact; }
  .page-break-inside-avoid { break-inside: avoid; }
}
</style>
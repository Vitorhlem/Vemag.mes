<template>
  <div class="report-container bg-white q-pa-md rounded-borders print-area">
    
    <div class="row justify-end q-mb-sm print-hide">
      <q-btn 
        color="amber-9" 
        icon="print" 
        label="Imprimir Ranking" 
        unelevated 
        @click="printReport"
      />
    </div>

    <div class="row items-center justify-between q-mb-lg border-bottom q-pb-md">
      <div class="row items-center">
        <img src="/vemagdark.png" class="report-logo q-mr-lg" alt="VEMAG Logo" />
        
        <q-separator vertical class="q-mr-lg gt-xs" />

        <div>
          <div class="text-h5 text-weight-bold text-primary">Performance Operacional</div>
          <div class="text-caption text-grey-7">Ranking de Eficiência e Produtividade</div>
        </div>
      </div>
      <div class="text-right">
        <div class="text-subtitle2 text-primary">{{ formatDate(report.report_period_start) }} - {{ formatDate(report.report_period_end) }}</div>
      </div>
    </div>

    <div class="row justify-center items-end q-mb-xl q-col-gutter-lg page-break-inside-avoid" v-if="report.drivers_performance.length >= 3">
      
      <div class="col-4 col-md-3 text-center">
        <q-avatar size="80px" class="q-mb-sm shadow-2 print-shadow-none">
          <img src="~assets/default-avatar.png" />
          <q-badge floating color="grey-5" rounded>2</q-badge>
        </q-avatar>
        <div class="text-weight-bold">{{ report.drivers_performance[1].driver_name }}</div>
        <div class="text-h6 text-grey-7">{{ report.drivers_performance[1].efficiency_percent }}%</div>
        <div class="podium-bar bg-grey-3"></div>
      </div>

      <div class="col-4 col-md-3 text-center">
        <q-icon name="emoji_events" color="amber" size="lg" class="q-mb-sm" />
        <q-avatar size="100px" class="q-mb-sm shadow-3 border-gold print-shadow-none">
          <img src="~assets/default-avatar.png" />
          <q-badge floating color="amber" rounded>1</q-badge>
        </q-avatar>
        <div class="text-weight-bold text-h6">{{ report.drivers_performance[0].driver_name }}</div>
        <div class="text-h4 text-amber-9">{{ report.drivers_performance[0].efficiency_percent }}%</div>
        <div class="text-caption text-grey">Eficiência Média</div>
        <div class="podium-bar bg-amber-2" style="height: 140px;"></div>
      </div>

      <div class="col-4 col-md-3 text-center">
        <q-avatar size="70px" class="q-mb-sm shadow-2 print-shadow-none">
          <img src="~assets/default-avatar.png" />
          <q-badge floating color="brown-4" rounded>3</q-badge>
        </q-avatar>
        <div class="text-weight-bold">{{ report.drivers_performance[2].driver_name }}</div>
        <div class="text-h6 text-grey-7">{{ report.drivers_performance[2].efficiency_percent }}%</div>
        <div class="podium-bar bg-brown-2" style="height: 70px;"></div>
      </div>
    </div>

    <q-table
      flat bordered
      :rows="report.drivers_performance"
      :columns="columns"
      row-key="driver_id"
      :pagination="{ rowsPerPage: 0 }"
      hide-pagination
      class="print-card"
    >
      <template v-slot:body-cell-efficiency_percent="props">
        <q-td :props="props">
          <div class="row items-center no-wrap">
            <q-linear-progress 
              :value="props.value / 100" 
              class="q-mr-sm print-hide" 
              style="width: 60px" 
              :color="getColor(props.value)" 
              track-color="grey-3"
            />
            <span class="text-weight-bold">{{ props.value }}%</span>
          </div>
        </q-td>
      </template>
    </q-table>

  </div>
</template>

<script setup lang="ts">
import { date } from 'quasar';
// eslint-disable-next-line @typescript-eslint/no-explicit-any
defineProps<{ report: any }>();
const formatDate = (val: string) => date.formatDate(val, 'DD/MM/YYYY');

const printReport = () => {
  window.print();
};

const getColor = (val: number) => {
  if (val >= 85) return 'positive';
  if (val >= 60) return 'warning';
  return 'negative';
};

const columns = [
  { name: 'name', label: 'Operador', field: 'driver_name', align: 'left', sortable: true },
  { name: 'days', label: 'Dias Trab.', field: 'total_journeys', align: 'center' },
  { name: 'productive', label: 'Horas Produtivas', field: 'productive_hours', align: 'center', format: (val: number) => val + ' h' },
  { name: 'efficiency_percent', label: 'Eficiência (OEE)', field: 'efficiency_percent', align: 'left', sortable: true },
];
</script>

<style scoped>
.report-container { font-family: 'Inter', sans-serif; max-width: 1000px; margin: 0 auto; }
.report-logo { height: 50px; object-fit: contain; }
.border-bottom { border-bottom: 2px solid #f0f0f0; }
.border-gold { border: 3px solid #FFC107; }
.podium-bar { width: 100%; border-radius: 8px 8px 0 0; margin-top: 10px; }

@media print {
  .print-hide { display: none !important; }
  .report-container { width: 100% !important; max-width: none !important; padding: 0 !important; box-shadow: none !important; border: none; }
  .print-shadow-none { box-shadow: none !important; border: 1px solid #ddd; }
  .print-card { border: 1px solid #ddd !important; }
  .page-break-inside-avoid { break-inside: avoid; }
  .podium-bar { border: 1px solid #ddd; }
  /* Forçar cores de fundo na impressão */
  .bg-amber-2 { background-color: #ffecb3 !important; -webkit-print-color-adjust: exact; }
  .bg-grey-3 { background-color: #eeeeee !important; -webkit-print-color-adjust: exact; }
  .bg-brown-2 { background-color: #bcaaa4 !important; -webkit-print-color-adjust: exact; }
}
</style>
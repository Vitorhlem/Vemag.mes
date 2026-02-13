<template>
  <q-page padding class="q-gutter-y-md bg-grey-2">
    <div class="row items-center q-mb-sm">
      <q-btn flat round icon="arrow_back" color="grey-8" @click="router.back()" />
      <div class="q-ml-sm">
        <div class="text-h5 text-weight-bold text-dark">
          {{ vehicleStore.selectedVehicle?.brand || 'Máquina' }} {{ vehicleStore.selectedVehicle?.model }}
        </div>
        <div class="text-caption text-grey-7 text-uppercase">Performance Industrial & OEE</div>
      </div>
      <q-space />
      
      <q-select
        v-model="dateRange"
        :options="rangeOptions"
        outlined dense bg-color="white"
        label="Período de Análise"
        style="width: 200px"
        @update:model-value="loadHistoricalData"
      />
      
      <q-btn icon="refresh" flat color="primary" @click="loadHistoricalData" class="q-ml-sm" />
    </div>

    <div class="row q-col-gutter-md">
      <div class="col-12 col-sm-6 col-md-3" v-for="kpi in kpis" :key="kpi.label">
        <q-card flat bordered class="kpi-card">
          <q-card-section>
            <div class="text-caption text-grey-7 text-uppercase">{{ kpi.label }}</div>
            <div class="row items-baseline justify-between">
              <div class="text-h4 text-weight-bolder" :class="`text-${kpi.color}`">{{ kpi.value }}</div>
              <q-icon :name="kpi.icon" size="sm" :color="kpi.color" />
            </div>
            <div class="text-caption q-mt-xs" :class="kpi.trend >= 0 ? 'text-positive' : 'text-negative'">
              <q-icon :name="kpi.trend >= 0 ? 'trending_up' : 'trending_down'" />
              {{ Math.abs(kpi.trend) }}% vs mês ant.
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <div class="row q-col-gutter-md">
      <div class="col-12 col-md-8">
        <q-card flat bordered class="full-height">
          <q-card-section class="row items-center justify-between">
            <div class="text-subtitle1 text-weight-bold">Utilização Diária (Horas)</div>
            <q-badge color="grey-3" text-color="grey-9" label="Empilhado" />
          </q-card-section>
          <q-card-section>
            <div id="productionChart" style="height: 300px;"></div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-4">
        <q-card flat bordered class="full-height">
          <q-card-section>
            <div class="text-subtitle1 text-weight-bold">Maiores Perdas (Horas)</div>
          </q-card-section>
          <q-card-section>
            <div id="paretoChart" style="height: 300px;"></div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <q-card flat bordered>
      <q-tabs v-model="tab" dense class="text-grey-7" active-color="primary" indicator-color="primary" align="justify">
        <q-tab name="history" icon="history" label="Timeline de Eventos" />
        <q-tab name="components" icon="extension" label="Componentes" />
        <q-tab name="maintenance" icon="build" label="Manutenção" />
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="tab" animated>
        <q-tab-panel name="history" class="q-pa-none">
          <q-table
            :rows="productionStore.machineHistory"
            :columns="historyColumns"
            flat
            dense
          />
        </q-tab-panel>
        </q-tab-panels>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import * as echarts from 'echarts';
import { useVehicleStore } from 'stores/vehicle-store';
import { useProductionStore } from 'stores/production-store';

const route = useRoute();
const router = useRouter();
const vehicleStore = useVehicleStore();
const productionStore = useProductionStore();

const tab = ref('history');
const dateRange = ref('Últimos 30 dias');
const rangeOptions = ['Últimos 7 dias', 'Últimos 30 dias', 'Últimos 90 dias'];

// KPIs de Exemplo (Mock)
const kpis = ref([
  { label: 'Disponibilidade', value: '84.2%', color: 'primary', icon: 'bolt', trend: 2.5 },
  { label: 'Utilização', value: '72.1%', color: 'secondary', icon: 'precision_manufacturing', trend: -1.2 },
  { label: 'Horas Produtivas', value: '412h', color: 'positive', icon: 'timer', trend: 5.4 },
  { label: 'MTTR (Médio)', value: '1.4h', color: 'negative', icon: 'build', trend: -10.0 },
]);

// Mock de Gráfico de Produção (30 dias)
function initCharts() {
  const prodDom = document.getElementById('productionChart');
  const paretoDom = document.getElementById('paretoChart');
  
  if (prodDom) {
    const chart = echarts.init(prodDom);
    chart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { bottom: 0, data: ['Produção', 'Setup', 'Manutenção', 'Ocioso'] },
      xAxis: { type: 'category', data: Array.from({length: 30}, (_, i) => `${i+1}/01`) },
      yAxis: { type: 'value', max: 24 },
      series: [
        { name: 'Produção', type: 'bar', stack: 'total', color: '#2d8cf0', data: Array.from({length: 30}, () => (Math.random() * 12 + 6).toFixed(1)) },
        { name: 'Setup', type: 'bar', stack: 'total', color: '#ff9900', data: Array.from({length: 30}, () => (Math.random() * 2).toFixed(1)) },
        { name: 'Manutenção', type: 'bar', stack: 'total', color: '#ed4014', data: Array.from({length: 30}, () => (Math.random() * 3).toFixed(1)) },
        { name: 'Ocioso', type: 'bar', stack: 'total', color: '#909399', data: Array.from({length: 30}, () => (Math.random() * 4).toFixed(1)) },
      ]
    });
  }

  if (paretoDom) {
    const chart = echarts.init(paretoDom);
    chart.setOption({
      tooltip: { trigger: 'item' },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: ['Ajuste Mec.', 'Falta Mat.', 'Limpeza', 'Quebra Elétrica'] },
      series: [
        { type: 'bar', color: '#ed4014', data: [45, 32, 18, 12] }
      ]
    });
  }
}

const historyColumns = [
  { name: 'timestamp', label: 'Horário', field: 'timestamp', format: (val: string) => new Date(val).toLocaleString('pt-BR'), align: 'left' },
  { name: 'event_type', label: 'Evento', field: 'event_type', align: 'left' },
  { name: 'operator', label: 'Operador', field: 'operator_name', align: 'left' },
  { name: 'reason', label: 'Motivo/Status', field: (row: any) => row.reason || row.new_status, align: 'left' },
];

onMounted(async () => {
  const id = Number(route.params.id);
  await vehicleStore.fetchVehicleById(id);
  await productionStore.fetchMachineHistory(id, { limit: 20 });
  
  // Inicializa gráficos após o DOM estar pronto
  setTimeout(() => initCharts(), 200);
});

function loadHistoricalData() {
  // Aqui você chamaria o backend passando o range
  console.log("Carregando histórico para:", dateRange.value);
}
</script>

<style scoped>
.kpi-card {
  border-radius: 12px;
  transition: transform 0.2s;
}
.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}
</style>
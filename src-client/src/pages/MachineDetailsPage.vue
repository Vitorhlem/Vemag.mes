<template>
  <q-page class="q-pa-lg bg-blue-grey-1">
    <div class="row items-center q-mb-xl">
      <q-btn icon="arrow_back" flat round color="primary" @click="$router.back()" class="q-mr-md" />
      <div>
        <div class="text-h4 text-weight-bolder text-grey-9">{{ machineInfo.name }}</div>
        <div class="text-subtitle1 text-grey-7">Análise de Disponibilidade & Eficiência Operacional</div>
      </div>
      <q-space />
      <div class="row q-gutter-sm">
        <q-select
          v-model="period"
          :options="periodOptions"
          label="Período de Análise"
          outlined dense bg-color="white"
          style="width: 220px"
          emit-value map-options
          @update:model-value="loadAllData"
        >
          <template v-slot:prepend><q-icon name="date_range" color="primary" /></template>
        </q-select>
        <q-btn color="primary" icon="refresh" label="Sincronizar" @click="loadAllData" :loading="loading" push />
      </div>
    </div>

    <div class="q-mb-md">
      <q-btn 
        color="orange-9" 
        icon="auto_fix_high" 
        label="Recalcular Métricas de Hoje" 
        @click="forceDayClosing" 
        :loading="closingLoading"
        flat
      >
        <q-tooltip>Processa logs atuais para atualizar os indicadores em tempo real</q-tooltip>
      </q-btn>
    </div>

    <div class="row q-col-gutter-lg q-mb-lg">
      <div class="col-12 col-md" v-for="card in stateCards" :key="card.label">
        <q-card class="state-card shadow-1" :class="`border-left-${card.color}`">
          <q-card-section class="row items-center no-wrap">
            <div class="col">
              <div class="text-overline text-grey-7">{{ card.label }}</div>
              <div class="text-h4 text-weight-bolder" :class="`text-${card.color === 'black' ? 'black' : card.color + '-9'}`">
                {{ (Number(card.value) || 0).toFixed(1) }}<span class="text-h6 text-weight-light">h</span>
              </div>
            </div>
            <q-icon :name="card.icon" :color="card.color" size="2.5rem" class="opacity-20" />
          </q-card-section>
        </q-card>
      </div>
    </div>

    <div class="row q-col-gutter-lg q-mb-lg">
      <div class="col-12 col-lg-8">
        <q-card class="chart-container shadow-2 border-radius-15">
          <q-card-section class="row items-center">
            <div>
              <div class="text-h6 text-weight-bold text-grey-8">Disponibilidade Diária (%)</div>
              <div class="text-caption text-grey-6">Métrica de utilização efetiva por dia</div>
            </div>
            <q-space />
            <div class="text-right">
              <div class="text-h6 text-primary text-weight-bolder">{{ summaryData.avg_availability.toFixed(1) }}%</div>
              <div class="text-caption">Média do Período</div>
            </div>
          </q-card-section>
          <q-card-section>
            <div id="availabilityBarChart" style="height: 400px; width: 100%;"></div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-lg-4">
        <q-card class="chart-container shadow-2 border-radius-15">
          <q-card-section>
            <div class="text-h6 text-weight-bold text-grey-8">Top Ofensores (Pareto)</div>
            <div class="text-caption text-grey-6 q-mb-md">Causas que mais consumiram tempo</div>
            <div id="stopReasonBarChart" style="height: 400px; width: 100%;"></div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <div class="row q-col-gutter-lg q-mb-lg">
      <div class="col-12">
        <q-card class="bg-white q-pa-md shadow-2 border-radius-15">
          <div class="row q-col-gutter-xl text-center">
            <div class="col-12 col-md-4">
              <div class="text-overline text-grey-6">MTBF</div>
              <div class="text-h4 text-weight-bolder text-teal-8">{{ summaryData.mtbf }}h</div>
              <div class="text-caption">Tempo Médio entre Falhas</div>
            </div>
            <div class="col-12 col-md-4" style="border-left: 1px solid #eee; border-right: 1px solid #eee;">
              <div class="text-overline text-grey-6">MTTR</div>
              <div class="text-h4 text-weight-bolder text-deep-orange-9">{{ summaryData.mttr }}h</div>
              <div class="text-caption">Tempo Médio de Reparo</div>
            </div>
            <div class="col-12 col-md-4">
              <div class="text-overline text-grey-6">Índice de Confiabilidade</div>
              <div class="text-h4 text-weight-bolder" :class="`text-${reliabilityStatus.color}`">
                {{ reliabilityStatus.label }}
              </div>
              <div class="text-caption">Status baseado no MTBF atual</div>
            </div>
          </div>
        </q-card>
      </div>
    </div>

    <div class="row">
      <div class="col-12">
        <q-card class="shadow-2 border-radius-15">
          <q-card-section class="row items-center q-pb-none">
            <div class="text-h6 text-weight-bold text-grey-8">Log de Eventos do Período</div>
            <q-space />
            <q-input v-model="logSearch" dense outlined placeholder="Pesquisar evento..." class="q-ml-md" style="width: 250px">
              <template v-slot:append><q-icon name="search" /></template>
            </q-input>
          </q-card-section>
          
          <q-card-section>
            <q-table
              :rows="detailedLogs"
              :columns="logColumns"
              row-key="id"
              flat
              :loading="loading"
              :pagination="{ rowsPerPage: 10 }"
              no-data-label="Nenhum log encontrado"
            >
              <template v-slot:body-cell-operator_name="props">
                <q-td :props="props">
                  <div v-if="props.row.operator_id" class="row items-center no-wrap cursor-pointer text-primary text-weight-bold" @click="$router.push(`/users/${props.row.operator_id}/stats`)">
                    <q-avatar size="24px" color="blue-1" text-color="primary" icon="person" class="q-mr-sm" />
                    <span>{{ props.value }}</span>
                    <q-tooltip>Ver perfil e estatísticas do operador</q-tooltip>
                  </div>
                  <div v-else class="row items-center text-grey-6 font-italic">
                    <q-icon name="smart_toy" size="18px" class="q-mr-xs" />
                    {{ props.value || 'Sistema' }}
                  </div>
                </q-td>
              </template>

              <template v-slot:body-cell-new_status="props">
                <q-td :props="props">
                  <q-chip dense :color="getStatusColor(props.value)" text-color="white" class="text-weight-bold">
                    {{ props.value }}
                  </q-chip>
                </q-td>
              </template>
            </q-table>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import * as echarts from 'echarts';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';

const $q = useQuasar();
const route = useRoute();
const machineId = route.params.id;

const loading = ref(false);
const closingLoading = ref(false);
const period = ref(30);
const machineInfo = ref({ name: 'Carregando...' });
const dailyMetrics = ref<any[]>([]);
const detailedLogs = ref<any[]>([]);
const logSearch = ref('');

const summaryData = ref({
  total_running: 0,
  total_setup: 0,
  total_micro_stops: 0,
  total_pause: 0,
  total_maintenance: 0,
  avg_availability: 0,
  stop_reasons: [],
  mtbf: 0,
  mttr: 0
});

const periodOptions = [
  { label: 'Últimos 7 dias', value: 7 },
  { label: 'Últimos 30 dias', value: 30 },
  { label: 'Últimos 90 dias', value: 90 }
];
const logColumns = [
  { name: 'timestamp', label: 'Data/Hora', align: 'left', field: 'timestamp', format: (val: string) => new Date(val).toLocaleString('pt-BR'), sortable: true },
  { name: 'event_type', label: 'Tipo', align: 'left', field: 'event_type', format: (val: string) => translateEventType(val), sortable: true },
  { name: 'new_status', label: 'Status Resultante', align: 'center', field: 'new_status' },
  { name: 'reason', label: 'Motivo/Ação', align: 'left', field: 'reason' },
  { name: 'operator_name', label: 'Responsável', align: 'left', field: 'operator_name' }
];
const reliabilityStatus = computed(() => {
  const mtbf = summaryData.value.mtbf;
  if (mtbf === 0) return { label: 'Em análise', color: 'grey-7' };
  if (mtbf >= 50) return { label: 'Excelente', color: 'positive' };
  if (mtbf >= 24) return { label: 'Estável', color: 'primary' };
  if (mtbf >= 10) return { label: 'Aceitável', color: 'warning' };
  return { label: 'Instável / Crítico', color: 'negative' };
});

const stateCards = computed(() => [
  { label: 'Em Operação', value: summaryData.value.total_running, color: 'green', icon: 'precision_manufacturing' },
  { label: 'Setup / Ajustes', value: summaryData.value.total_setup, color: 'purple', icon: 'settings_suggest' },
  { label: 'Micro-paradas', value: summaryData.value.total_micro_stops, color: 'black', icon: 'bolt' }, // Voltou para 'black'
  { label: 'Pausa / Ocioso', value: summaryData.value.total_pause, color: 'orange', icon: 'timer' },
  { label: 'Manutenção', value: summaryData.value.total_maintenance, color: 'red', icon: 'engineering' }
]);
function getStatusColor(status: string) {
  const s = String(status).toUpperCase();
  if (s.includes('USO') || s.includes('OPERAÇÃO')) return 'green-7';
  if (s.includes('SETUP')) return 'purple-7';
  if (s.includes('MANUTENÇÃO')) return 'red-8';
  if (s.includes('PARADA') || s.includes('PAUSA')) return 'orange-8';
  return 'grey-7';
}

function translateEventType(val: string) {
  const map: Record<string, string> = {
    'STATUS_CHANGE': 'Mudança de Status',
    'LOGOUT': 'Saída',
    'SESSION_START': 'Sessão Iniciada',
    'SESSION_END': 'Sessão Encerrada',
    'ANDON_OPEN': 'Chamado de Ajuda',
    'COUNT': 'Contagem de Produção',
    'STEP_START': 'Etapa Iniciada',
    'STEP_PAUSE': 'Etapa Pausada',
    'STEP_COMPLETE': 'Etapa Concluída'
  };
  return map[val] || val;
}

async function forceDayClosing() {
  $q.dialog({
    title: 'Confirmar Recálculo',
    message: 'Deseja reprocessar os eventos de hoje para atualizar os indicadores diários?',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    closingLoading.value = true;
    try {
      await api.post(`/production/consolidate/${machineId}`);
      $q.notify({ type: 'positive', message: 'Métricas recalculadas!' });
      await loadAllData();
    } catch (e) {
      $q.notify({ type: 'negative', message: 'Erro no processamento.' });
    } finally {
      closingLoading.value = false;
    }
  });
}

async function loadAllData() {
  loading.value = true;
  try {
    const resMac = await api.get(`/vehicles/${machineId}`);
    machineInfo.value = { name: `${resMac.data.brand} ${resMac.data.model}` };

    const resSummary = await api.get(`/production/stats/${machineId}/period-summary?days=${period.value}`);
    summaryData.value = resSummary.data;

    const resHistory = await api.get(`/production/stats/${machineId}/history?days=${period.value}`);
    dailyMetrics.value = resHistory.data;

    // Busca os logs detalhados para a tabela
    const resLogs = await api.get(`/production/history/${machineId}?limit=100`);
    detailedLogs.value = resLogs.data;

    renderBarCharts();
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Erro ao carregar dados analíticos.' });
  } finally {
    loading.value = false;
  }
}

function renderBarCharts() {
  const availChart = echarts.init(document.getElementById('availabilityBarChart'));
  availChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '40', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: dailyMetrics.value.map(m => new Date(m.date).toLocaleDateString('pt-BR')),
      axisLabel: { rotate: 45 }
    },
    yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    series: [{
      name: 'Disponibilidade',
      type: 'bar',
      barMaxWidth: 35,
      data: dailyMetrics.value.map(m => m.availability),
      label: { show: true, position: 'top', formatter: '{c}%', fontSize: 10 },
      itemStyle: {
        color: (params: any) => params.value >= 85 ? '#43a047' : (params.value >= 70 ? '#fb8c00' : '#e53935'),
        borderRadius: [4, 4, 0, 0]
      }
    }]
  });

  const stopChart = echarts.init(document.getElementById('stopReasonBarChart'));
  const stopData = summaryData.value.stop_reasons;
  stopChart.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}: <b>{c}h</b>' },
    grid: { left: '3%', right: '15%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', axisLabel: { formatter: '{value}h' } },
    yAxis: { 
      type: 'category', 
      data: stopData.map((i: any) => i.name),
      inverse: true
    },
    series: [{
      type: 'bar',
      data: stopData.map((i: any) => i.value),
      itemStyle: { color: '#ef5350', borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', formatter: '{c}h' }
    }]
  });
}

window.addEventListener('resize', () => {
  echarts.getInstanceByDom(document.getElementById('availabilityBarChart'))?.resize();
  echarts.getInstanceByDom(document.getElementById('stopReasonBarChart'))?.resize();
});

onMounted(loadAllData);
</script>

<style scoped>
.state-card {
  transition: all 0.3s ease;
  border-radius: 12px;
  background: white;
  min-height: 110px;
}
.state-card:hover { transform: translateY(-5px); box-shadow: 0 12px 24px rgba(0,0,0,0.12); }

/* ✅ A cor da borda das micro-paradas é definida aqui */
.border-left-green { border-left: 8px solid #43a047; }
.border-left-purple { border-left: 8px solid #8e24aa; }
.border-left-orange { border-left: 8px solid #fb8c00; }
.border-left-red { border-left: 8px solid #e53935; }
.border-left-black { border-left: 8px solid #263238; } /* Cinza bem escuro / Preto */
.chart-container { background: white; padding: 20px; }
.border-radius-15 { border-radius: 15px; }
.opacity-20 { opacity: 0.2; }
</style>
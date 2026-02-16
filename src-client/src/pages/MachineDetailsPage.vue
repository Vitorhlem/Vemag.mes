  <template>
    <q-page class="q-pa-lg bg-blue-grey-1">
      <div class="row items-center q-mb-xl">
        <q-btn icon="arrow_back" flat round color="primary" @click="$router.back()" class="q-mr-md" />
        <div>
          <div class="text-h4 text-weight-bolder text-grey-9">{{ machineInfo.name }}</div>
          <div class="text-subtitle1 text-grey-7">Análise de Disponibilidade & Comportamento do Ativo</div>
        </div>
        <q-space />
        <div class="row q-gutter-sm">
          <q-select
            v-model="period"
            :options="periodOptions"
            label="Período"
            outlined dense bg-color="white"
            style="width: 180px"
            emit-value map-options
            @update:model-value="loadAllData"
          >
            <template v-slot:prepend><q-icon name="history" color="primary" /></template>
          </q-select>
          <q-btn color="primary" icon="refresh" label="Atualizar" @click="loadAllData" :loading="loading" push />
        </div>
      </div>
      <q-btn 
    color="orange-9" 
    icon="auto_fix_high" 
    label="Forçar Fechamento Hoje" 
    @click="forceDayClosing" 
    :loading="closingLoading"
    flat
  >
    <q-tooltip>Processa os logs de HOJE e gera o histórico agora para teste</q-tooltip>
  </q-btn>

      <div class="row q-col-gutter-lg q-mb-lg">
        <div class="col-12 col-md-3" v-for="card in stateCards" :key="card.label">
          <q-card class="state-card shadow-1" :class="`border-left-${card.color}`">
            <q-card-section class="row items-center no-wrap">
              <div class="col">
                <div class="text-overline text-grey-7">{{ card.label }}</div>
                <div class="text-h4 text-weight-bolder" :class="`text-${card.color}-9 text-weight-bolder`">
                  {{ card.value.toFixed(1) }}<span class="text-h6 text-weight-light">h</span>
                </div>
              </div>
              <q-icon :name="card.icon" :color="card.color" size="2.5rem" class="opacity-20" />
            </q-card-section>
          </q-card>
        </div>
      </div>

      <div class="row q-col-gutter-lg">
        
        <div class="col-12 col-lg-8">
          <q-card class="chart-container shadow-2 border-radius-15">
            <q-card-section class="row items-center">
              <div>
                <div class="text-h6 text-weight-bold text-grey-8">Disponibilidade Diária (%)</div>
                <div class="text-caption text-grey-6">Comparativo de performance por dia</div>
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
              <div class="text-h6 text-weight-bold text-grey-8">Top Ofensores</div>
              <div class="text-caption text-grey-6 q-mb-md">Principais causas de indisponibilidade</div>
              <div id="stopReasonBarChart" style="height: 400px; width: 100%;"></div>
            </q-card-section>
          </q-card>
        </div>

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
                <div class="text-overline text-grey-6">Confiabilidade</div>
                <div class="text-h4 text-weight-bolder text-primary">Excelente</div>
                <div class="text-caption">Status baseado na estabilidade</div>
              </div>
            </div>
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
  const closingLoading = ref(false);
  const route = useRoute();
  const $q = useQuasar();
  const machineId = route.params.id;
  const loading = ref(false);
  const period = ref(30);

  const machineInfo = ref({ name: 'Carregando...' });
  const dailyMetrics = ref([]);
  const summaryData = ref({
    total_running: 0,
    total_setup: 0,
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

  const stateCards = computed(() => [
    { label: 'Em Operação', value: summaryData.value.total_running, color: 'green', icon: 'precision_manufacturing' },
    { label: 'Setup / Ajustes', value: summaryData.value.total_setup, color: 'purple', icon: 'settings_input_component' },
    { label: 'Pausa / Ocioso', value: summaryData.value.total_pause, color: 'orange', icon: 'hourglass_empty' },
    { label: 'Manutenção', value: summaryData.value.total_maintenance, color: 'red', icon: 'plumbing' }
  ]);

  async function forceDayClosing() {
    $q.dialog({
      title: 'Confirmar Consolidação',
      message: 'Isso irá processar todos os logs de HOJE e transformar em dados históricos. Deseja continuar?',
      cancel: true,
      persistent: true
    }).onOk(async () => {
      closingLoading.value = true;
      try {
        // Chama o endpoint de consolidação (Certifique-se que ele existe no production.py conforme blocos anteriores)
        await api.post(`/production/consolidate/${machineId}`);
        
        $q.notify({
          type: 'positive',
          message: 'Dados consolidados com sucesso! O gráfico foi atualizado.',
          icon: 'done_all'
        });
        
        // Recarrega a página para mostrar os novos dados no gráfico de barras
        await loadAllData();
      } catch (e) {
        console.error(e);
        $q.notify({ type: 'negative', message: 'Erro ao processar fechamento.' });
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

      renderBarCharts();
    } catch (e) {
      console.error(e);
      $q.notify({ type: 'negative', message: 'Erro ao carregar dados do servidor.' });
    } finally {
      loading.value = false;
    }
  }

  function renderBarCharts() {
    // 1. Gráfico de Disponibilidade (Barras Verticais)
    const availChart = echarts.init(document.getElementById('availabilityBarChart'));
    availChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      // Ajustamos o topo do grid para 40 para o número não ser cortado no topo
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
        barMaxWidth: 40,
        data: dailyMetrics.value.map(m => m.availability),
        // Adicionamos o bloco label abaixo:
        label: {
          show: true,           // Mostra o texto
          position: 'top',      // Posiciona acima da barra
          formatter: '{c}%',    // {c} é o valor do dado + o símbolo %
          fontWeight: 'bold',
          color: '#555',        // Cor do texto
          fontSize: 12
        },
        itemStyle: {
          color: (params) => {
            if (params.value >= 85) return '#4caf50'; // Verde
            if (params.value >= 70) return '#ffc107'; // Amarelo
            return '#f44336';                         // Vermelho
          },
          borderRadius: [4, 4, 0, 0]
        }
      }]
    });

    // 2. Gráfico de Motivos (Barras Horizontais)
    const stopChart = echarts.init(document.getElementById('stopReasonBarChart'));
    const stopData = summaryData.value.stop_reasons;
    stopChart.setOption({
      tooltip: { 
        trigger: 'axis', 
        formatter: '{b}: <b>{c} horas</b>' // Mostra a unidade no hover
      },
      grid: { left: '3%', right: '15%', bottom: '3%', containLabel: true },
      xAxis: { 
        type: 'value',
        name: 'Horas',
        axisLabel: { formatter: '{value} h' } 
      },
      yAxis: { 
        type: 'category', 
        data: stopData.map(i => i.name),
        inverse: true
      },
      series: [{
        name: 'Tempo Total',
        type: 'bar',
        data: stopData.map(i => i.value),
        itemStyle: { color: '#ef5350', borderRadius: [0, 4, 4, 0] },
        label: { 
          show: true, 
          position: 'right',
          formatter: '{c} h' // Mostra o valor com "h" na ponta da barra
        }
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
    transition: all 0.3s cubic-bezier(.25,.8,.25,1);
    border-radius: 12px;
    background: white;
  }
  .state-card:hover { transform: translateY(-4px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }

  .border-left-green { border-left: 8px solid #4caf50; }
  .border-left-purple { border-left: 8px solid #9c27b0; }
  .border-left-orange { border-left: 8px solid #ff9800; }
  .border-left-red { border-left: 8px solid #f44336; }

  .chart-container { background: white; padding: 20px; }
  .border-radius-15 { border-radius: 15px; }
  .opacity-20 { opacity: 0.2; }
  </style>
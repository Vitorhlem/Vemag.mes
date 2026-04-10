<template>
  <q-page class="q-pa-md bg-glass-layout">
    
    <div class="row items-center q-mb-md">
      <q-btn flat round icon="arrow_back" color="teal-9" @click="router.back()" />
      <div class="q-ml-sm">
        <div class="text-h5 text-weight-bold text-gradient-trucar">Ficha de Acompanhamento</div>
        <div class="text-caption text-teal-9 opacity-80">RG Digital da Peça</div>
      </div>
    </div>

    <div v-if="isLoading" class="flex flex-center q-pa-xl">
      <q-spinner-orbit color="primary" size="3em" />
      <div class="q-ml-md text-teal-9">Buscando histórico na fábrica...</div>
    </div>

    <div v-else-if="errorMsg" class="flex flex-center q-pa-xl column">
      <q-icon name="error_outline" color="negative" size="4em" />
      <div class="text-h6 text-negative q-mt-md">{{ errorMsg }}</div>
      <q-btn color="primary" outline label="Tentar Novamente" class="q-mt-md" @click="fetchData" />
    </div>

    <div v-else-if="trackerData">
      
      <q-card class="glass-card shadow-sm q-mb-md border-left-green">
        <q-card-section>
          <div class="row justify-between items-start">
            <div>
              <div class="text-overline text-teal-8 text-weight-bolder">
                {{ trackerData.header.is_service ? 'ORDEM DE SERVIÇO' : 'ORDEM DE PRODUÇÃO' }}
              </div>
              <div class="text-h4 text-weight-bold text-teal-10 q-mb-xs">
                {{ trackerData.header.op_number }}
              </div>
              <div class="text-subtitle1 text-grey-9 text-weight-medium">
                {{ trackerData.header.part_name }}
              </div>
              <q-badge color="teal-1" text-color="teal-10" class="q-mt-sm q-pa-xs text-weight-bold">
                Cód: {{ trackerData.header.item_code }}
              </q-badge>
            </div>
            
            <div class="text-right">
              <div class="text-caption text-grey-7">Qtd. Planejada</div>
              <div class="text-h5 text-weight-bold text-teal-9">
                {{ trackerData.header.planned_qty }} <span class="text-body2">{{ trackerData.header.uom }}</span>
              </div>
            </div>
          </div>
        </q-card-section>

        <q-separator opacity="0.1" />

        <q-card-section class="row q-col-gutter-sm">
          <div class="col-6">
            <div class="text-caption text-grey-7">Referência / Cliente</div>
            <div class="text-body2 text-weight-bold text-teal-10 truncate">{{ trackerData.header.custom_ref || '--' }}</div>
          </div>
          <div class="col-6 text-right">
            <div class="text-caption text-grey-7">Tempo Total Gasto</div>
            <div class="text-body2 text-weight-bold text-orange-9">{{ trackerData.header.total_time_spent_min }} min</div>
          </div>
        </q-card-section>
      </q-card>

      <q-btn 
        v-if="trackerData.header.drawing_code"
        color="teal-10" 
        icon="draw" 
        label="Abrir Desenho Técnico (PDF)" 
        class="full-width q-mb-lg shadow-4 text-weight-bold"
        size="lg"
        @click="openDrawing(trackerData.header.drawing_code)"
      />

      <div class="text-h6 text-teal-10 text-weight-bold q-mb-md q-ml-sm">
        <q-icon name="route" /> Roteiro de Produção
      </div>

      <q-card class="glass-card shadow-sm q-pa-md">
        <q-timeline color="teal-6">
          
          <q-timeline-entry 
            v-for="(step, index) in trackerData.routing" 
            :key="index"
            :title="`${step.seq} - ${step.name}`"
            :subtitle="step.resource"
            :color="getStepColor(step)"
            :icon="getStepIcon(step)"
          >
            <div class="text-body2 text-grey-8 q-mb-sm italic">
              "{{ step.description }}"
            </div>

            <div v-if="step.history && step.history.length > 0" class="bg-teal-1 q-pa-sm rounded-borders border-left-blue">
              <div class="text-caption text-weight-bold text-teal-9 q-mb-xs">Histórico de Apontamentos:</div>
              
              <div v-for="apt in step.history" :key="apt.id" class="row items-center justify-between q-mb-xs q-pb-xs" style="border-bottom: 1px solid rgba(0,0,0,0.05)">
                <div class="row items-center">
                  <q-icon name="person" size="xs" color="teal-7" class="q-mr-xs" />
                  <span class="text-caption text-weight-medium">{{ apt.operator }}</span>
                </div>
                <div class="text-caption text-grey-8">
                  <q-icon name="schedule" size="xs" /> {{ apt.duration_minutes }} min
                </div>
              </div>
              
              <div class="text-right text-caption text-weight-bold text-blue-9 q-mt-sm">
                Total nesta etapa: {{ step.time_spent }} min
              </div>
            </div>

            <div v-else class="text-caption text-grey-5 font-italic">
              Nenhum apontamento registrado ainda.
            </div>

          </q-timeline-entry>

        </q-timeline>
      </q-card>

    </div>

    <q-dialog v-model="isDrawingLoading" persistent>
      <q-card class="q-pa-lg text-center bg-teal-10 text-white" style="width: 300px">
        <q-spinner-gears size="50px" color="white" />
        <div class="text-h6 q-mt-md">Buscando Desenho...</div>
        <div class="text-caption opacity-80">O servidor está processando o PDF de {{ trackerData?.header?.drawing_code }}. Por favor, aguarde.</div>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';

const route = useRoute();
const router = useRouter();
const $q = useQuasar();

const isLoading = ref(true);
const errorMsg = ref('');

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const trackerData = ref<any>(null);
const isDrawingLoading = ref(false);

// Função para buscar os dados mágicos do Python
async function fetchData() {
  const opCode = route.params.opCode as string;
  
  if (!opCode) {
    errorMsg.value = 'Código da Ordem não fornecido.';
    isLoading.value = false;
    return;
  }

  isLoading.value = true;
  errorMsg.value = '';

  try {
    const response = await api.get(`/production/tracker/${opCode}`);
    trackerData.value = response.data;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
    console.error(error);
    if (error.response && error.response.status === 404) {
      errorMsg.value = `Ordem ${opCode} não encontrada no sistema.`;
    } else {
      errorMsg.value = 'Erro ao buscar dados da peça. Tente novamente.';
    }
  } finally {
    isLoading.value = false;
  }
}

// Lógica de Cores da Linha do Tempo
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
function getStepColor(step: any) {
  if (step.status === 'IN_PROGRESS' || (step.history && step.history.length > 0)) return 'positive';
  return 'grey-4';
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getStepIcon(step: any) {
  if (step.history && step.history.length > 0) return 'check_circle';
  if (step.status === 'IN_PROGRESS') return 'play_circle';
  return 'radio_button_unchecked';
}

// Lógica para Abrir o Desenho (Acorda o Celery)
function openDrawing(drawingCode: string) {
  if (!drawingCode) {
    $q.notify({ type: 'warning', message: 'Nenhum código de desenho atrelado a esta peça.' });
    return;
  }

  isDrawingLoading.value = true;

  // Usa a sua mesma rota do Celery! Como é um celular avulso, mandamos machine_id = 999
  api.post(`/drawings/request/${encodeURIComponent(drawingCode)}/999`)
    .then(() => {
      $q.notify({ 
        type: 'info', 
        message: 'Aviso enviado! O servidor está renderizando a imagem...', 
        timeout: 2000 
      });
      
      // Aqui, como você usa o WebSocket na tela principal para saber quando o Celery termina,
      // para o celular podemos usar um "Polling" simples: tenta baixar a imagem a cada 3 segundos
      checkDrawingReady(drawingCode);
    })
    .catch(() => {
      isDrawingLoading.value = false;
      $q.notify({ type: 'negative', message: 'Erro ao comunicar com o servidor de desenhos.' });
    });
}

// Fica "batendo na porta" do servidor até o Celery terminar de converter o PDF
function checkDrawingReady(drawingCode: string, attempts = 0) {
  const safeCode = drawingCode.trim().toLowerCase().replace('.pdf', '');
  
  // Tenta baixar a imagem renderizada
  api.get(`/drawings/render/${safeCode}.png`, { responseType: 'blob' })
    .then((res) => {
      // Se deu 200 OK, a imagem está pronta!
      isDrawingLoading.value = false;
      const url = window.URL.createObjectURL(new Blob([res.data]));
      
      // Abre a imagem em uma nova aba para o operador dar zoom à vontade no celular
      window.open(url, '_blank'); 
    })
    .catch(() => {
      // Se deu erro 404, o Celery ainda está trabalhando. Tenta de novo em 3 segundos.
      if (attempts < 10) { // Tenta por 30 segundos no máximo
        setTimeout(() => checkDrawingReady(drawingCode, attempts + 1), 3000);
      } else {
        isDrawingLoading.value = false;
        $q.notify({ type: 'negative', message: 'Tempo limite excedido ao buscar o desenho.' });
      }
    });
}

onMounted(() => {
  void fetchData();
});
</script>

<style scoped>
.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.italic {
  font-style: italic;
}
</style>
<template>
  <q-layout view="hHh lpR fFf" class="bg-blue-grey-1 text-dark font-inter" style="overflow: hidden;">
    
    <q-header bordered class="bg-white text-dark q-py-xs shadow-2" style="height: 60px;">
      <q-toolbar class="full-height q-px-md">
        
        <div class="row items-center q-mr-lg cursor-pointer">
          <img 
            :src="logoPath" 
            alt="Company Logo" 
            style="height: 40px; max-width: 160px; object-fit: contain;" 
            class="logo-hover" 
          />
        </div>

        <q-separator vertical inset class="q-mx-sm mobile-hide bg-grey-3" />

        <q-toolbar-title class="column justify-center q-ml-sm">
          <div class="text-caption text-uppercase text-grey-7 letter-spacing-1 lh-small" style="font-size: 0.7rem;">Célula de Manufatura</div>
          <div class="text-subtitle1 text-weight-bolder lh-small row items-center text-primary">
            TORNO CNC - MAZAK 01
            <q-badge rounded :color="statusColor" class="q-ml-sm shadow-1" :class="{ 'pulse-status': productionStore.activeOrder?.status === 'RUNNING' }">
              <q-icon :name="statusIcon" color="white" class="q-mr-xs" size="10px" />
              {{ productionStore.activeOrder?.status || 'OFFLINE' }}
            </q-badge>
          </div>
        </q-toolbar-title>

        <q-space />

        <div class="row items-center q-gutter-x-sm bg-grey-2 q-py-xs q-px-sm rounded-borders shadow-1">
          <q-avatar size="32px" class="shadow-1">
            <img :src="productionStore.currentOperator?.avatar || 'https://br.freepik.com/fotos-vetores-gratis/default'">
          </q-avatar>
          <div class="column items-start mobile-hide lh-small">
            <div class="text-weight-bold text-caption">{{ productionStore.currentOperator?.name?.split(' ')[0] || 'Operador' }}</div>
            <div class="text-caption text-grey-7" style="font-size: 0.65rem;">ID: {{ productionStore.currentOperator?.id || '--' }}</div>
          </div>
          <q-separator vertical inset class="q-mx-xs bg-grey-4" />
          <div class="text-h6 font-monospace text-dark text-weight-bold">{{ timeDisplay }}</div>
        </div>

        <q-btn flat round icon="logout" color="grey-8" size="md" class="q-ml-sm hover-rotate" @click="handleLogout">
          <q-tooltip>Sair</q-tooltip>
        </q-btn>
      </q-toolbar>
      <q-linear-progress :value="1" :color="statusColor" size="3px" />
    </q-header>

    <q-page-container>
      <q-page class="q-pa-sm full-height column no-wrap">
        
        <div v-if="!productionStore.activeOrder" class="col flex flex-center column fade-in-up">
          <q-card class="q-pa-lg text-center shadow-8 bg-white" style="border-radius: 16px; max-width: 400px;">
            <div class="bg-blue-grey-1 q-pa-md rounded-borders inline-block q-mb-md">
               <q-icon name="qr_code_scanner" size="60px" color="primary" class="animate-bounce-slow" />
            </div>
            <div class="text-h5 text-weight-bolder text-dark q-mb-xs">Aguardando O.S.</div>
            <div class="text-caption text-grey-7 q-mb-lg lh-small">
              A máquina está parada. Escaneie a Ordem de Serviço.
            </div>
            <q-btn push rounded color="primary" size="lg" icon="photo_camera" label="Ler QR Code" class="full-width shadow-4 hover-scale" @click="simulateOpScan" />
          </q-card>
        </div>

        <div v-else class="row q-col-gutter-sm col full-height items-stretch content-stretch">
          
          <div class="col-12 col-md-8 column q-gutter-y-sm fade-in-left">
            
            <q-card class="relative-position overflow-hidden shadow-4 bg-dark" style="border-radius: 16px; height: 150px; min-height: 150px;">
              <q-img 
                :src="productionStore.activeOrder.partImage" 
                class="absolute-full opacity-60 animate-slow-zoom" 
                fit="cover" 
              />
              <div class="absolute-full" style="background: linear-gradient(to right, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.5) 60%, rgba(0,0,0,0.1));"></div>
              
              <div class="absolute-full q-pa-md row items-center justify-between text-white">
                <div>
                    <div class="row items-center q-gutter-x-sm q-mb-xs">
                        <q-badge color="orange-9" label="PRIORIDADE 1" />
                        <q-badge outline color="white" label="AÇO 4340" />
                        <q-badge outline color="white" label="LOTE 2024-B" />
                    </div>
                    <div class="text-h4 text-weight-bolder q-mb-none text-shadow font-monospace">{{ productionStore.activeOrder.code }}</div>
                    <div class="text-subtitle1 text-grey-4 text-shadow">{{ productionStore.activeOrder.partName }}</div>
                </div>
                <q-btn push rounded color="white" text-color="dark" icon="list_alt" label="Ver Roteiro Completo" class="shadow-5 hover-scale" size="sm" @click="isDocDialogOpen = true" />
              </div>
            </q-card>

            <q-card class="col-grow shadow-3 column bg-white" style="border-radius: 12px; border-left: 6px solid var(--q-primary);">
              
              <q-card-section class="row items-center q-pb-none">
                 <div class="bg-blue-grey-1 text-primary q-px-md q-py-xs rounded-borders text-weight-bold">
                    {{ currentOp?.opCode }}
                 </div>
                 <q-space />
                 <div class="text-caption text-uppercase text-grey-6 text-weight-bold">
                    Passo {{ currentStepIndex + 1 }} de {{ productionStore.activeOrder.operations.length }}
                 </div>
              </q-card-section>

              <q-card-section class="col column justify-center q-pt-sm">
                 <div class="text-h4 text-weight-bolder text-dark lh-small q-mb-sm">
                    {{ currentOp?.title || 'Roteiro Finalizado' }}
                 </div>
                 
                 <div class="text-h6 text-grey-8 text-weight-regular" style="line-height: 1.4;">
                    {{ currentOp?.description }}
                 </div>

                 <div class="row q-mt-md q-gutter-sm" v-if="currentOp">
                    <q-badge color="orange-1" text-color="orange-9" class="q-py-xs q-px-sm" v-for="tool in currentOp.tools" :key="tool">
                      <q-icon name="handyman" size="14px" class="q-mr-xs"/> {{ tool }}
                    </q-badge>
                    <q-badge color="blue-1" text-color="blue-9" class="q-py-xs q-px-sm">
                      <q-icon name="speed" size="14px" class="q-mr-xs"/> {{ currentOp.params }}
                    </q-badge>
                 </div>
              </q-card-section>

              <q-card-actions align="right" class="q-pa-md bg-grey-1 border-top">
                 <q-btn 
                    push 
                    color="primary" 
                    icon="check_circle" 
                    label="CONCLUIR E AVANÇAR" 
                    class="full-width shadow-2" 
                    size="lg" 
                    :disable="!currentOp"
                    @click="nextStep"
                 />
              </q-card-actions>
              <q-linear-progress :value="(currentStepIndex + 1) / productionStore.activeOrder.operations.length" size="6px" color="primary" />
            </q-card>
          </div>

          <div class="col-12 col-md-4 column q-gutter-y-sm fade-in-right">
            
            <q-card class="bg-white text-center q-py-sm relative-position shadow-2" style="border-radius: 12px;">
               <div class="row items-center justify-center q-gutter-x-sm">
                  <q-icon name="timer" color="grey-7" size="sm" />
                  <div class="text-subtitle1 text-grey-9">
                    Tempo no Estado: <span class="text-weight-bold font-monospace">00:45:12</span>
                  </div>
               </div>
               <q-linear-progress stripe query :color="statusColor" size="4px" class="q-mt-xs absolute-bottom" />
            </q-card>

            <div class="col-grow relative-position">
               <q-btn 
                  v-if="['SETUP', 'RUNNING', 'PAUSED'].includes(productionStore.activeOrder.status)"
                  :color="productionStore.activeOrder.status === 'RUNNING' ? 'positive' : 'blue-grey-9'" 
                  class="fit shadow-4 hover-scale-producing" 
                  :class="{ 'pulse-btn': productionStore.activeOrder.status === 'RUNNING' }"
                  push 
                  style="border-radius: 16px;"
                  @click="toggleProduction"
               >
                  <div class="column items-center">
                    <q-icon size="60px" :name="productionStore.activeOrder.status === 'RUNNING' ? 'pause_circle' : 'play_circle_filled'" />
                    <div class="text-h4 text-weight-bolder q-mt-sm">
                       {{ productionStore.activeOrder.status === 'RUNNING' ? 'PAUSAR' : 'INICIAR' }}
                    </div>
                    <div class="text-subtitle2 text-uppercase letter-spacing-1 opacity-80">
                       {{ productionStore.activeOrder.status === 'RUNNING' ? 'Máquina em Produção' : 'Ciclo Parado' }}
                    </div>
                  </div>
               </q-btn>

               <q-btn 
                  v-else
                  color="grey-4" text-color="dark"
                  class="fit shadow-2"
                  style="border-radius: 16px; border: 2px dashed #999;"
                  flat
                  disable
               >
                  <div class="column items-center">
                     <q-icon name="lock" size="40px" color="grey-6" />
                     <div class="text-h6 text-grey-7">Aguardando Setup</div>
                  </div>
               </q-btn>
            </div>

            <div class="row q-gutter-x-sm" style="height: 120px;">
               <q-btn 
                  class="col shadow-3 hover-scale"
                  :color="productionStore.activeOrder.status === 'SETUP' ? 'warning' : 'blue-grey-2'"
                  :text-color="productionStore.activeOrder.status === 'SETUP' ? 'dark' : 'blue-grey-9'"
                  push
                  style="border-radius: 16px;"
                  @click="toggleSetup"
               >
                  <div class="column items-center">
                     <q-icon name="build" size="32px" class="q-mb-xs" />
                     <div class="text-weight-bold">SETUP</div>
                     <div class="text-caption" style="font-size: 0.6rem;">Troca/Ajuste</div>
                  </div>
               </q-btn>

               <q-btn 
                  class="col shadow-3 hover-scale"
                  color="negative"
                  outline
                  style="border-radius: 16px; background: white;"
                  @click="isAndonDialogOpen = true"
               >
                  <div class="column items-center">
                     <q-icon name="notifications_active" size="32px" class="q-mb-xs" />
                     <div class="text-weight-bold">AJUDA</div>
                     <div class="text-caption" style="font-size: 0.6rem;"></div>
                  </div>
               </q-btn>
            </div>

          </div>
        </div>
      </q-page>
    </q-page-container>

    <q-dialog v-model="isDocDialogOpen" maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-blue-grey-1">
        <q-toolbar class="bg-dark text-white q-py-sm">
          <q-btn flat round dense icon="arrow_back" v-close-popup />
          <q-toolbar-title class="text-subtitle1">Roteiro de O.S.: {{ productionStore.activeOrder?.code }}</q-toolbar-title>
          <q-btn flat icon="print" label="Imprimir" />
        </q-toolbar>
        <q-card-section class="row q-col-gutter-md scroll full-height">
          <div class="col-12 col-md-5">
            <q-card class="shadow-3 full-height" style="border-radius: 16px;">
               <q-card-section class="bg-grey-2 text-weight-bold text-caption text-uppercase q-pb-none">Sequência de Usinagem</q-card-section>
               <q-card-section>
                 <q-timeline color="primary">
                    <q-timeline-entry v-for="(op, index) in productionStore.activeOrder?.operations" :key="index" :title="op.title" :subtitle="op.opCode" :color="index <= currentStepIndex ? 'primary' : 'grey'" :icon="index <= currentStepIndex ? 'check' : 'radio_button_unchecked'">
                      <div class="text-grey-8">{{ op.description }}</div>
                      <div class="row q-gutter-xs q-mt-sm"><q-badge color="blue-1" text-color="primary" v-for="t in op.tools" :key="t">{{ t }}</q-badge></div>
                    </q-timeline-entry>
                 </q-timeline>
               </q-card-section>
            </q-card>
          </div>
          <div class="col-12 col-md-7">
            <q-card class="shadow-3 fit overflow-hidden column flex-center" style="border-radius: 16px; background: white;">
              <div class="text-h6 text-grey-5 q-mb-md">Desenho Técnico (PDF)</div>
              <q-icon name="picture_as_pdf" size="100px" color="grey-3" />
              <div class="text-caption text-grey-4">Arquivo: {{ productionStore.activeOrder?.code }}.pdf</div>
            </q-card>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isAndonDialogOpen" transition-show="scale" transition-hide="scale">
      <q-card style="width: 500px; border-radius: 16px;" class="shadow-10">
        <q-card-section class="bg-negative text-white text-center q-py-lg">
          <div class="text-h6 text-weight-bolder">Solicitar Apoio (Andon)</div>
        </q-card-section>
        <q-card-section class="row q-col-gutter-md q-pa-lg bg-grey-1">
          <div class="col-6"><q-btn color="white" text-color="negative" class="fit q-py-lg shadow-2" icon="build_circle" label="Mecânica" stack size="lg" rounded @click="triggerAndon('Manutenção Mecânica')" /></div>
          <div class="col-6"><q-btn color="white" text-color="orange-9" class="fit q-py-lg shadow-2" icon="bolt" label="Elétrica" stack size="lg" rounded @click="triggerAndon('Manutenção Elétrica')" /></div>
          <div class="col-6"><q-btn color="white" text-color="blue-9" class="fit q-py-lg shadow-2" icon="saved_search" label="Gerente" stack size="lg" rounded @click="triggerAndon('Qualidade')" /></div>
          <div class="col-6"><q-btn color="white" text-color="grey-9" class="fit q-py-lg shadow-2" icon="forklift" label="Logística" stack size="lg" rounded @click="triggerAndon('Logística')" /></div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isStopDialogOpen" persistent transition-show="fade" transition-hide="fade">
      <q-card style="width: 400px; border-radius: 16px;" class="shadow-5">
        <q-card-section class="text-center q-py-md">
          <div class="text-h6 text-weight-bold">Motivo da Parada</div>
        </q-card-section>
        <q-card-section class="q-gutter-y-sm q-px-lg q-pb-lg">
          <q-btn v-for="reason in ['Quebra de Máquina', 'Falta de Matéria-Prima', 'Ajuste de Qualidade', 'Refeição/Descanso', 'Outros']" :key="reason"
             push color="blue-grey-1" text-color="dark" class="full-width text-weight-bold shadow-1" padding="sm" rounded align="between" icon-right="chevron_right" :label="reason" @click="confirmStop(reason)" />
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar, QSpinnerGears } from 'quasar';
import { useProductionStore } from 'stores/production-store';

const router = useRouter();
const $q = useQuasar();
const productionStore = useProductionStore();

// --- CONFIGURAÇÃO DA LOGO ---
const logoPath = ref('/Logo-Oficial.png');

const isDocDialogOpen = ref(false);
const isStopDialogOpen = ref(false);
const isAndonDialogOpen = ref(false);
const currentStepIndex = ref(0);
const currentTime = ref(new Date());

let timerInterval: ReturnType<typeof setInterval>;

const statusColor = computed(() => {
  const status = productionStore.activeOrder?.status;
  if (status === 'RUNNING') return 'positive';
  if (status === 'SETUP') return 'warning';
  if (status === 'PAUSED') return 'negative';
  return 'grey-5';
});

const statusIcon = computed(() => {
    const status = productionStore.activeOrder?.status;
    if (status === 'RUNNING') return 'autorenew';
    if (status === 'SETUP') return 'handyman';
    if (status === 'PAUSED') return 'error_outline';
    return 'power_off';
})

const timeDisplay = computed(() => {
  return currentTime.value.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
});

const currentOp = computed(() => {
  if (!productionStore.activeOrder || !productionStore.activeOrder.operations) return null;
  return productionStore.activeOrder.operations[currentStepIndex.value];
});

function toggleSetup() {
  if (productionStore.activeOrder?.status === 'SETUP') {
    productionStore.activeOrder.status = 'PENDING';
    $q.notify({type: 'info', message: 'Setup Finalizado. Pronto para produzir.'})
  } else {
    if (productionStore.activeOrder) {
        productionStore.activeOrder.status = 'SETUP';
        $q.notify({type: 'warning', icon:'build', message: 'Máquina em modo de PREPARAÇÃO (Setup).'})
    }
  }
}

function toggleProduction() {
  if (productionStore.activeOrder?.status === 'RUNNING') {
    isStopDialogOpen.value = true;
  } else {
    productionStore.startProduction();
     $q.notify({type: 'positive', icon:'play_circle', message: 'Produção INICIADA.'})
  }
}

function nextStep() {
  if (productionStore.activeOrder && currentStepIndex.value < productionStore.activeOrder.operations.length - 1) {
    currentStepIndex.value++;
    $q.notify({type: 'positive', message: 'Operação concluída. Avançando.', position: 'top'})
  } else {
    $q.notify({ type: 'positive', icon: 'verified', message: 'Roteiro finalizado!', position: 'top' });
  }
}

function confirmStop(reason: string) {
  productionStore.pauseProduction(reason);
  isStopDialogOpen.value = false;
  $q.notify({type: 'negative', icon:'pause_circle', message: `Pausa: ${reason}`})
}

function handleLogout() {
  $q.dialog({
    title: 'Sair',
    message: 'Fazer logoff?',
    ok: { label: 'Sair', color: 'negative', flat: true },
    cancel: { label: 'Cancelar', flat: true },
    persistent: true
  }).onOk(() => {
    productionStore.logoutOperator();
    // CORREÇÃO: void para promessa flutuante
    void router.push({ name: 'machine-kiosk' });
  });
}

async function simulateOpScan() {
  $q.loading.show({
    spinner: QSpinnerGears, spinnerColor: 'primary', spinnerSize: 80,
    backgroundColor: 'white', message: 'Carregando O.S...', messageColor: 'dark'
  });
  await new Promise(resolve => setTimeout(resolve, 1500));
  await productionStore.loadOrderFromQr('OP-AUTO-4500');
  $q.loading.hide();
  currentStepIndex.value = 0;
}

function triggerAndon(sector: string) {
  $q.loading.show({message: `Chamando ${sector}...`})
  setTimeout(() => {
      $q.loading.hide();
      $q.notify({ type: 'negative', icon: 'campaign', message: `Chamado enviado para ${sector}!`, position: 'top' });
      isAndonDialogOpen.value = false;
  }, 1000)
}

onMounted(() => {
  timerInterval = setInterval(() => { currentTime.value = new Date(); }, 1000);
});
onUnmounted(() => { clearInterval(timerInterval); });
</script>

<style scoped>
.font-inter { font-family: 'Inter', 'Roboto', sans-serif; }
.font-monospace { font-family: 'JetBrains Mono', 'Courier New', monospace; letter-spacing: -1px; }
.lh-small { line-height: 1.1; }
.letter-spacing-1 { letter-spacing: 1px; }
.text-shadow { text-shadow: 1px 1px 3px rgba(0,0,0,0.5); }
.col-grow { flex-grow: 1; }
.opacity-60 { opacity: 0.6; }
.opacity-80 { opacity: 0.8; }
.z-top { z-index: 10; }
.border-top { border-top: 1px solid #e0e0e0; }

.logo-hover { transition: transform 0.3s; }
.logo-hover:hover { transform: scale(1.05); }

.hover-scale { transition: transform 0.2s; }
.hover-scale:hover { transform: scale(1.02); }
.hover-rotate { transition: transform 0.3s; }
.hover-rotate:hover { transform: rotate(90deg); }
.hover-scale-producing { transition: all 0.3s ease-in-out; }
.hover-scale-producing:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(33, 186, 69, 0.3); }

.animate-pulse-subtle { animation: pulse-subtle 3s infinite; }
@keyframes pulse-subtle { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.animate-bounce-slow { animation: bounce-slow 3s infinite; }
@keyframes bounce-slow { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
.animate-slow-zoom { animation: slow-zoom 60s infinite alternate linear; }
@keyframes slow-zoom { from { transform: scale(1); } to { transform: scale(1.1); } }

/* Animação do Botão Pulsante */
.pulse-btn { animation: pulse-green-btn 2s infinite; }
@keyframes pulse-green-btn { 0% { box-shadow: 0 0 0 0 rgba(33, 186, 69, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(33, 186, 69, 0); } 100% { box-shadow: 0 0 0 0 rgba(33, 186, 69, 0); } }

.pulse-status.bg-positive { animation: pulse-green 2s infinite; }
@keyframes pulse-green { 0% { box-shadow: 0 0 0 0 rgba(33, 186, 69, 0.7); } 70% { box-shadow: 0 0 0 5px rgba(33, 186, 69, 0); } 100% { box-shadow: 0 0 0 0 rgba(33, 186, 69, 0); } }

.fade-in-up { animation: fadeInUp 0.6s ease-out; }
.fade-in-left { animation: fadeInLeft 0.6s ease-out; }
.fade-in-right { animation: fadeInRight 0.6s ease-out; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeInLeft { from { opacity: 0; transform: translateX(-15px); } to { opacity: 1; transform: translateX(0); } }
@keyframes fadeInRight { from { opacity: 0; transform: translateX(15px); } to { opacity: 1; transform: translateX(0); } }
</style>
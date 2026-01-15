<template>
  <q-layout view="hHh lpR fFf" class="bg-grey-1 text-dark font-inter" style="overflow: hidden;">
    
    <q-header bordered class="q-py-xs shadow-2 text-white" style="height: 60px; background-color: #008C7A;">
      <q-toolbar class="full-height q-px-md">
        <div class="row items-center q-mr-lg">
          <img :src="logoPath" alt="Logo" style="height: 40px; max-width: 160px; object-fit: contain; filter: brightness(0) invert(1);" />
        </div>
        
        <q-separator vertical inset class="q-mx-sm mobile-hide bg-white opacity-50" />
        
        <q-toolbar-title class="column justify-center q-ml-sm">
          <div class="text-caption text-uppercase text-grey-3 letter-spacing-1 lh-small" style="font-size: 0.7rem;">
            {{ productionStore.machineSector }}
          </div>
          <div class="text-subtitle1 text-weight-bolder lh-small row items-center text-white">
            {{ productionStore.machineName }}
            <q-badge rounded :class="statusBgClass" class="q-ml-sm shadow-1 text-white q-py-xs q-px-sm">
              <q-icon :name="statusIcon" color="white" class="q-mr-xs" size="10px" />
              {{ normalizedStatus }}
            </q-badge>
          </div>
        </q-toolbar-title>
        
        <q-space />
        
        <div class="row items-center q-gutter-x-sm bg-white text-dark q-py-xs q-px-sm rounded-borders shadow-1">
          <q-avatar size="32px" class="shadow-1 vemag-bg-primary text-white" icon="person" />
          <div class="column items-start mobile-hide lh-small">
            <div class="text-weight-bold text-caption vemag-text-primary">Operador</div>
            <div class="text-caption text-grey-7" style="font-size: 0.65rem;">
              {{ productionStore.currentOperatorBadge || '---' }}
            </div>
          </div>
          <q-separator vertical inset class="q-mx-xs bg-grey-4" />
          <div class="text-h6 font-monospace vemag-text-primary text-weight-bold">{{ timeDisplay }}</div>
        </div>
        
        <q-btn flat round icon="logout" class="q-ml-sm text-white" size="md" @click="handleLogout" />
      </q-toolbar>
      <q-linear-progress :value="1" color="orange-4" class="q-mt-none" size="3px" />
    </q-header>

    <q-page-container>
      <q-page class="q-pa-sm full-height column no-wrap">
        
        <div v-if="!productionStore.activeOrder" class="col flex flex-center column">
          <q-card class="q-pa-lg text-center shadow-8 bg-white" style="border-radius: 16px; max-width: 400px;">
            <div class="vemag-bg-light q-pa-md rounded-borders inline-block q-mb-md">
               <q-icon name="qr_code_scanner" size="60px" class="vemag-text-primary" />
            </div>
            <div class="text-h5 text-weight-bolder vemag-text-primary q-mb-xs">Aguardando O.P.</div>
            <div class="text-caption text-grey-7 q-mb-lg">A máquina está parada. Escaneie a O.S. para iniciar.</div>
            <q-btn push rounded class="vemag-bg-primary text-white full-width" size="lg" icon="photo_camera" label="Ler QR Code" @click="simulateOpScan" />
          </q-card>
        </div>

        <div v-else class="row q-col-gutter-sm col full-height items-stretch content-stretch">
          
          <div class="col-12 col-md-8 column q-gutter-y-sm">
            <q-card class="relative-position overflow-hidden shadow-4 vemag-bg-primary" style="border-radius: 16px; height: 150px; min-height: 150px;">
              <q-img 
                :src="customOsBackgroundImage" 
                class="absolute-full opacity-60" 
                fit="cover" 
                error-src="https://placehold.co/600x150/008C7A/ffffff?text=Sem+Imagem"
              />
              <div class="absolute-full" style="background: linear-gradient(to right, rgba(0,140,122,0.95) 0%, rgba(0,140,122,0.7) 50%, rgba(0,140,122,0.3));"></div>
              <div class="absolute-full q-pa-md row items-center justify-between text-white">
                <div>
                    <div class="row items-center q-gutter-x-sm q-mb-xs">
                        <q-badge color="orange-9" label="PRIORIDADE 1" />
                        <q-badge outline color="white" :label="productionStore.activeOrder.code" />
                    </div>
                    <div class="text-h4 text-weight-bolder">{{ productionStore.activeOrder.part_name }}</div>
                    <div class="text-subtitle2 text-grey-3">Meta: {{ productionStore.activeOrder.target_quantity }} un</div>
                </div>
              </div>
            </q-card>

            <q-card class="col-grow shadow-3 column bg-white" style="border-radius: 12px; border-left: 6px solid #008C7A;">
              <q-card-section class="row items-center justify-between border-bottom-light">
                 <div>
                    <div class="text-subtitle1 text-weight-bold text-uppercase vemag-text-primary letter-spacing-1">
                       <q-icon name="list_alt" class="q-mr-sm" />Roteiro de Operação
                    </div>
                    <div class="text-caption text-grey-7">Passo {{ viewedStepIndex + 1 }} de {{ productionStore.activeOrder.steps?.length || 0 }}</div>
                 </div>
                 
                 <div class="row items-center q-gutter-md">
                    <q-btn flat dense color="primary" icon="image" label="Ver Desenho Técnico" @click="isDrawingDialogOpen = true" />
                    
                    <div class="text-right">
                        <div class="text-h4 text-weight-bolder vemag-text-primary">
                           {{ productionStore.activeOrder.produced_quantity }} <span class="text-h6 text-grey-5">/ {{ productionStore.activeOrder.target_quantity }}</span>
                        </div>
                        <div class="text-caption text-grey-7">Peças Produzidas</div>
                    </div>
                 </div>
              </q-card-section>
              
              <q-linear-progress :value="(productionStore.activeOrder.produced_quantity || 0) / (productionStore.activeOrder.target_quantity || 1)" class="vemag-text-primary" size="6px" />

              <q-card-section class="col scroll q-pa-lg">
                 <div v-if="currentViewedStep" class="column q-gutter-y-md">
                    <div class="row items-center justify-between">
                        <div class="text-h5 text-weight-bold text-dark">
                            <span class="text-grey-5 q-mr-sm">{{ currentViewedStep.seq }} | </span> 
                            {{ currentViewedStep.name }}
                        </div>
                        <q-badge color="grey-8" class="text-subtitle2 q-py-xs">
                            Recurso: {{ currentViewedStep.resource }}
                        </q-badge>
                    </div>
                    
                    <div class="bg-grey-1 q-pa-md rounded-borders text-body1" style="white-space: pre-line; border-left: 4px solid #008C7A;">
                        {{ currentViewedStep.description }}
                    </div>

                    <div class="row justify-end text-grey-7">
                        <q-icon name="schedule" class="q-mr-xs" />
                        Tempo Estimado: <strong>{{ currentViewedStep.timeEst }}h</strong>
                    </div>
                 </div>
                 
                 <div v-else class="text-center text-grey-5 q-pa-xl">
                    <q-icon name="sentiment_dissatisfied" size="4em" />
                    <div>Nenhum passo encontrado.</div>
                 </div>
              </q-card-section>

              <q-separator />
              
              <q-card-actions align="between" class="q-pa-md bg-grey-1">
                 <div class="row q-gutter-x-sm">
                    <q-btn outline color="primary" icon="arrow_back" label="Anterior" @click="prevStepView" :disable="viewedStepIndex === 0" />
                    <q-btn unelevated color="primary" icon-right="arrow_forward" label="Próximo" @click="nextStepView" :disable="!productionStore.activeOrder.steps || viewedStepIndex === productionStore.activeOrder.steps.length - 1" />
                 </div>

                 <q-btn 
                    outline color="negative" icon="delete_outline" 
                    label="Apontar Refugo" 
                    @click="productionStore.addProduction(1, true)"
                 />
              </q-card-actions>
            </q-card>
          </div>

          <div class="col-12 col-md-4 column q-gutter-y-sm">
            <q-card class="bg-white text-center q-py-sm relative-position shadow-2" style="border-radius: 12px;">
               <div class="row items-center justify-center q-gutter-x-sm">
                  <q-icon name="timer" class="vemag-text-secondary" size="sm" />
                  <div class="text-subtitle1 vemag-text-primary">
                    Tempo no Estado: <span class="text-weight-bold font-monospace">{{ elapsedTime }}</span>
                  </div>
               </div>
               <q-linear-progress stripe query :class="statusTextClass" size="4px" class="q-mt-xs absolute-bottom" />
            </q-card>

            <div class="col-grow relative-position">
               <q-btn 
                  class="fit shadow-4 hover-scale-producing" 
                  :class="normalizedStatus === 'RUNNING' ? 'vemag-bg-primary text-white' : 'bg-blue-grey-9 text-white'" 
                  push :loading="isLoadingAction"
                  style="border-radius: 16px;"
                  @click="toggleProduction"
               >
                  <div class="column items-center">
                    <q-icon size="60px" :name="normalizedStatus === 'RUNNING' ? 'pause_circle' : 'play_circle_filled'" />
                    <div class="text-h4 text-weight-bolder q-mt-sm">
                       {{ normalizedStatus === 'RUNNING' ? 'PAUSAR' : 'INICIAR' }}
                    </div>
                    <div class="text-subtitle2 text-uppercase letter-spacing-1 opacity-80">
                       {{ normalizedStatus === 'RUNNING' ? 'Máquina Rodando' : 'Iniciar Produção' }}
                    </div>
                  </div>
               </q-btn>
            </div>

            <div class="row q-gutter-x-sm" style="height: 80px;">
               <q-btn 
                  class="col shadow-3 hover-scale"
                  :color="normalizedStatus === 'SETUP' ? 'warning' : 'blue-grey-2'"
                  :text-color="normalizedStatus === 'SETUP' ? 'dark' : 'blue-grey-9'"
                  push style="border-radius: 16px;" :loading="isLoadingAction"
                  @click="toggleSetup"
               >
                  <div class="column items-center">
                     <q-icon name="build" size="24px" class="q-mb-none" />
                     <div class="text-weight-bold">SETUP</div>
                  </div>
               </q-btn>

               <q-btn 
                  class="col shadow-3 hover-scale vemag-bg-secondary text-white"
                  push style="border-radius: 16px;"
                  @click="isAndonDialogOpen = true"
               >
                  <div class="column items-center">
                     <q-icon name="notifications_active" size="24px" class="q-mb-none" />
                     <div class="text-weight-bold">AJUDA</div>
                  </div>
               </q-btn>
            </div>

            <div>
               <q-btn 
                  class="full-width shadow-3" color="red-10" text-color="white"
                  push size="lg" icon="stop_circle" label="FINALIZAR O.P."
                  style="border-radius: 16px;"
                  @click="confirmFinishOp"
                  :disable="normalizedStatus === 'RUNNING'"
               >
                  <q-tooltip v-if="normalizedStatus === 'RUNNING'" class="bg-negative text-body2">
                     Pause a máquina antes de finalizar!
                  </q-tooltip>
               </q-btn>
            </div>
          </div>
        </div>
      </q-page>
    </q-page-container>

    <q-dialog v-model="isDrawingDialogOpen" maximized transition-show="slide-up" transition-hide="slide-down">
        <q-card class="bg-black text-white">
            <q-bar class="bg-grey-9">
                <q-icon name="image" />
                <div class="text-h6 q-ml-sm">Desenho Técnico</div>
                <q-space />
                <q-btn dense flat icon="close" v-close-popup />
            </q-bar>
            <q-card-section class="flex flex-center full-height">
                <q-img 
                    :src="productionStore.activeOrder?.technical_drawing_url || '/desenho.jpg'"
                    style="max-width: 100%; max-height: 90vh;"
                    fit="contain"
                />
            </q-card-section>
        </q-card>
    </q-dialog>

    <q-dialog v-model="isStopDialogOpen" persistent maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-grey-2">
        <q-toolbar class="bg-white text-dark q-py-md">
          <q-toolbar-title class="text-weight-bold text-h6">
            <q-icon name="warning" color="warning" class="q-mr-sm"/> Informe o Motivo da Parada
          </q-toolbar-title>
        </q-toolbar>
        <q-card-section class="q-px-xl q-pt-lg">
           <q-input v-model="stopSearch" outlined bg-color="white" placeholder="Pesquisar motivo..." class="text-h6" autofocus clearable>
              <template v-slot:prepend><q-icon name="search" size="md" /></template>
           </q-input>
        </q-card-section>
        <q-card-section class="q-px-xl scroll" style="height: calc(100vh - 200px);">
           <div class="row q-col-gutter-md">
              <div v-for="(reason, idx) in filteredStopReasons" :key="idx" class="col-12 col-md-4 col-lg-3">
                 <q-btn 
                    color="white" 
                    text-color="dark" 
                    class="full-width full-height shadow-2" 
                    padding="lg" 
                    align="left" 
                    no-caps 
                    @click="handleReasonSelect(reason.label)"
                 >
                    <div class="row items-center no-wrap full-width">
                       <q-avatar :color="getCategoryColor(reason.category)" text-color="white" icon="priority_high" size="md" class="q-mr-md" />
                       <div class="column">
                          <div class="text-subtitle1 text-weight-bold">{{ reason.label }}</div>
                          <div class="text-caption text-grey">{{ reason.category }}</div>
                       </div>
                       <q-space />
                       <q-icon v-if="reason.requiresMaintenance" name="build_circle" color="red" size="sm" />
                    </div>
                 </q-btn>
              </div>
           </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isMaintenanceConfirmOpen" persistent>
       <q-card class="bg-red-9 text-white" style="width: 600px; max-width: 90vw;">
          <q-card-section class="row items-center">
             <q-avatar icon="warning" color="white" text-color="red-9" size="lg" font-size="32px" />
             <div class="text-h5 q-ml-md text-weight-bold">Atenção: Parada Crítica</div>
          </q-card-section>

          <q-card-section class="q-py-lg">
             <p class="text-h6">
               Você selecionou: <span class="text-weight-bolder text-yellow-3">"{{ pendingReason }}"</span>.
             </p>
             <p class="text-body1">
               Este motivo geralmente requer intervenção técnica. O que deseja fazer?
             </p>
          </q-card-section>

          <q-card-actions align="center" class="q-pa-md q-gutter-md">
             <q-btn 
                push color="white" text-color="red-9" size="lg" class="col-grow"
                icon="handyman" label="EU VOU AJUSTAR"
                @click="executeStop(false)" 
             />
             <q-btn 
                push color="red-10" text-color="white" size="lg" class="col-grow" style="border: 2px solid white"
                icon="assignment_turned_in" label="ENCERRAR O.P. & ABRIR O.M."
                @click="executeStop(true)"
             />
          </q-card-actions>
       </q-card>
    </q-dialog>

    <q-dialog v-model="isAndonDialogOpen" transition-show="scale" transition-hide="scale">
      <q-card style="width: 700px; max-width: 90vw; border-radius: 16px;">
        <q-card-section class="vemag-bg-primary text-white row items-center justify-between">
          <div class="text-h6 text-weight-bold row items-center">
            <q-icon name="campaign" size="md" class="q-mr-sm" />
            Central de Ajuda (Andon)
          </div>
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>
        <q-card-section class="q-pa-lg">
          <div class="text-subtitle1 q-mb-md vemag-text-primary">Selecione o setor responsável:</div>
          <div class="row q-col-gutter-md">
            <div v-for="opt in andonOptions" :key="opt.label" class="col-6 col-md-4">
              <q-btn 
                push class="full-width full-height column flex-center q-pa-md shadow-2 transition-hover"
                :class="`bg-${opt.color} text-white`"
                style="border-radius: 12px; min-height: 110px;"
                @click="triggerAndon(opt.label)"
              >
                <q-icon :name="opt.icon" size="36px" class="q-mb-sm" />
                <div class="text-weight-bold text-subtitle2">{{ opt.label }}</div>
              </q-btn>
            </div>
          </div>
          <div class="q-mt-lg">
            <q-input v-model="andonNote" outlined label="Observação (Opcional)" placeholder="Descreva..." dense bg-color="grey-1">
              <template v-slot:prepend><q-icon name="edit_note" class="vemag-text-primary" /></template>
            </q-input>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useProductionStore } from 'stores/production-store';
import { storeToRefs } from 'pinia';
import { STOP_REASONS } from 'src/data/stop-reasons';

const router = useRouter();
const $q = useQuasar();
const productionStore = useProductionStore();
const { activeOrder } = storeToRefs(productionStore); 

const logoPath = ref('/Logo-Oficial.png');
const isLoadingAction = ref(false);
const customOsBackgroundImage = ref('/a.jpg');

// --- Estados de Dialog ---
const isStopDialogOpen = ref(false);
const isAndonDialogOpen = ref(false);
const isMaintenanceConfirmOpen = ref(false);
const isDrawingDialogOpen = ref(false); // <--- NOVO: Estado do modal de desenho

const pendingReason = ref('');
const stopSearch = ref('');
const statusStartTime = ref(new Date());
const currentTime = ref(new Date());
let timerInterval: ReturnType<typeof setInterval>;
const andonNote = ref('');

// --- Navegação do Passo a Passo ---
const viewedStepIndex = ref(0);

// Computed para pegar o passo atual que está sendo visualizado
const currentViewedStep = computed(() => {
    if (!activeOrder.value?.steps) return null;
    return activeOrder.value.steps[viewedStepIndex.value];
});

function nextStepView() {
    if (activeOrder.value?.steps && viewedStepIndex.value < activeOrder.value.steps.length - 1) {
        viewedStepIndex.value++;
    }
}

function prevStepView() {
    if (viewedStepIndex.value > 0) {
        viewedStepIndex.value--;
    }
}

// --- Outras Computeds ---
const andonOptions = [
  { label: 'Mecânica', icon: 'build', color: 'blue-grey-9' },
  { label: 'Elétrica', icon: 'bolt', color: 'orange-9' },
  { label: 'Logística', icon: 'forklift', color: 'brown-6' },
  { label: 'Qualidade', icon: 'verified', color: 'purple-8' },
  { label: 'Processo', icon: 'engineering', color: 'teal-7' },
  { label: 'Segurança', icon: 'health_and_safety', color: 'red-9' }
];

const elapsedTime = computed(() => {
   const diff = Math.max(0, Math.floor((currentTime.value.getTime() - statusStartTime.value.getTime()) / 1000));
   const h = Math.floor(diff / 3600).toString().padStart(2, '0');
   const m = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
   const s = (diff % 60).toString().padStart(2, '0');
   return `${h}:${m}:${s}`;
});
const timeDisplay = computed(() => currentTime.value.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));

const normalizedStatus = computed(() => {
    const raw = activeOrder.value?.status || '';
    const s = String(raw).trim().toUpperCase();
    if (['RUNNING', 'EM USO', 'EM PRODUÇÃO', 'IN_USE', 'PRODUZINDO'].includes(s)) return 'RUNNING';
    if (['SETUP', 'EM SETUP', 'PREPARAÇÃO'].includes(s)) return 'SETUP';
    if (['PAUSED', 'STOPPED', 'PARADA', 'EM PAUSA', 'IDLE', 'AVAILABLE', 'DISPONÍVEL'].includes(s)) return 'PAUSED';
    return 'PAUSED'; 
});

const statusBgClass = computed(() => {
  if (normalizedStatus.value === 'RUNNING') return 'bg-positive'; 
  if (normalizedStatus.value === 'SETUP') return 'bg-warning';
  return 'bg-negative';
});
const statusTextClass = computed(() => {
    if (normalizedStatus.value === 'RUNNING') return 'vemag-text-primary';
    if (normalizedStatus.value === 'SETUP') return 'text-warning';
    return 'text-negative';
});
const statusIcon = computed(() => {
    if (normalizedStatus.value === 'RUNNING') return 'autorenew';
    if (normalizedStatus.value === 'SETUP') return 'handyman';
    return 'error_outline';
});

const filteredStopReasons = computed(() => {
   if (!stopSearch.value) return STOP_REASONS;
   const needle = stopSearch.value.toLowerCase();
   return STOP_REASONS.filter(r => r.label.toLowerCase().includes(needle) || r.category.toLowerCase().includes(needle));
});
function getCategoryColor(cat: string) {
   if (cat === 'Mecânica') return 'grey-9';
   if (cat === 'Elétrica') return 'orange-9';
   return 'blue-grey';
}
function resetTimer() { statusStartTime.value = new Date(); }

async function toggleSetup() {
  isLoadingAction.value = true;
  if (normalizedStatus.value === 'SETUP') {
    await productionStore.pauseProduction('Fim de Setup'); 
  } else {
    await productionStore.enterSetup(); 
  }
  resetTimer();
  isLoadingAction.value = false;
}

async function toggleProduction() {
  isLoadingAction.value = true;
  if (normalizedStatus.value === 'RUNNING') {
    isStopDialogOpen.value = true;
    stopSearch.value = '';
  } else {
    await productionStore.startProduction();
    resetTimer();
  }
  isLoadingAction.value = false;
}

function handleReasonSelect(reasonLabel: string) {
    const reasonObj = STOP_REASONS.find(r => r.label === reasonLabel);
    if (reasonObj?.requiresMaintenance) {
        pendingReason.value = reasonLabel;
        isStopDialogOpen.value = false; 
        isMaintenanceConfirmOpen.value = true; 
    } else {
        pendingReason.value = reasonLabel;
        isStopDialogOpen.value = false;
        void executeStop(false); 
    }
}

async function executeStop(isCriticalMaintenance: boolean) {
    isLoadingAction.value = true;
    isMaintenanceConfirmOpen.value = false; 

    await productionStore.pauseProduction(pendingReason.value);

    if (isCriticalMaintenance) {
        $q.loading.show({ message: 'Registrando Quebra...', backgroundColor: 'red-10' });
        await productionStore.setMachineStatus('MAINTENANCE');
        await productionStore.finishSession();
        await productionStore.logoutOperator('MAINTENANCE');
        $q.loading.hide();
        void router.push({ name: 'machine-kiosk' });
        $q.notify({ type: 'negative', icon: 'build', message: `Máquina parada. Abra a O.M.`, timeout: 5000 });
    } else {
        resetTimer();
        $q.notify({ type: 'warning', icon: 'pause', message: `Pausado: ${pendingReason.value}` });
    }
    isLoadingAction.value = false;
}

function confirmFinishOp() {
  $q.dialog({
    title: 'Finalizar O.P.',
    message: 'Encerrar ordem?',
    cancel: true,
    persistent: true,
    ok: { label: 'Finalizar', color: 'negative', push: true }
  }).onOk(() => {
     void (async () => {
        await productionStore.finishSession();
        resetTimer();
     })();
  });
}

function handleLogout() {
  $q.dialog({ title: 'Sair', message: 'Fazer logoff?', cancel: true }).onOk(() => {
    void (async () => {
        await productionStore.logoutOperator();
        await router.push({ name: 'machine-kiosk' });
    })();
  });
}

function triggerAndon(sector: string, note?: string) {
  productionStore.triggerAndon(sector, note);
  $q.notify({ type: 'info', icon: 'check_circle', message: `Chamado para: ${sector}` });
  andonNote.value = '';
  isAndonDialogOpen.value = false;
}

async function simulateOpScan() {
  await productionStore.loadOrderFromQr('OP-TESTE-4500');
  resetTimer();
}

onMounted(() => {
  timerInterval = setInterval(() => { currentTime.value = new Date(); }, 1000);
  resetTimer();
});
onUnmounted(() => { clearInterval(timerInterval); });
</script>
<style>
.vemag-bg-primary { background-color: #008C7A !important; }
.vemag-text-primary { color: #008C7A !important; }
.vemag-bg-secondary { background-color: #66B8B0 !important; }
.vemag-text-secondary { color: #66B8B0 !important; }
.vemag-bg-light { background-color: #E0F2F1 !important; }
.vemag-bg-light-accent { background-color: #B2DFDB !important; }
</style>

<style scoped>
.font-inter { font-family: 'Roboto', sans-serif; }
.font-monospace { font-family: 'Courier New', monospace; letter-spacing: -1px; }
.lh-small { line-height: 1.1; }
.col-grow { flex-grow: 1; }
.opacity-60 { opacity: 0.6; }
.opacity-50 { opacity: 0.5; }
.opacity-80 { opacity: 0.8; }
.hover-scale-producing { transition: all 0.3s ease-in-out; }
.hover-scale-producing:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(0, 140, 122, 0.4); }
.border-bottom-light { border-bottom: 1px solid #e0e0e0; }
.transition-hover:hover { filter: brightness(1.1); transform: translateY(-2px); }
</style>
<template>
  <q-layout view="hHh lpR fFf" class="bg-grey-2 text-dark font-inter window-height overflow-hidden">
    
    <q-header bordered class="q-py-sm shadow-3 text-white" style="height: 80px; background-color: #008C7A;">
      <q-toolbar class="full-height q-px-xl"> <div class="row items-center no-wrap">
          <img :src="logoPath" alt="Logo" style="height: 55px; max-width: 200px; object-fit: contain; filter: brightness(0) invert(1);" />
          
          <q-separator vertical inset class="q-mx-lg mobile-hide bg-white opacity-50" /> <div class="column justify-center">
            <div class="text-subtitle2 text-uppercase text-grey-3 letter-spacing-1" style="line-height: 1;">
              {{ productionStore.machineSector }}
            </div>
            <div class="row items-center q-mt-xs">
              <div class="text-h5 text-weight-bolder lh-small text-white q-mr-md">
                {{ productionStore.machineName }}
              </div>
              <q-badge rounded :class="statusBgClass" class="shadow-2 text-white q-py-xs q-px-md text-subtitle2">
                <q-icon :name="statusIcon" color="white" class="q-mr-xs" size="18px" />
                {{ normalizedStatus }}
              </q-badge>
            </div>
          </div>
        </div>
        
        <q-space />
        
        <div class="row items-center q-gutter-x-lg">
          
          <div class="row items-center bg-white text-dark q-py-xs q-px-md rounded-borders shadow-2" style="height: 50px; border-radius: 12px;">
            <q-avatar size="36px" class="shadow-1 vemag-bg-primary text-white" icon="person" font-size="22px" />
            
            <div class="column items-start justify-center q-ml-md mobile-hide" style="line-height: 1.1;">
              <div class="text-caption text-weight-bold vemag-text-primary text-uppercase" style="font-size: 0.7rem;">OPERADOR</div>
              <div class="text-body2 text-grey-9 text-weight-bold">
                {{ productionStore.currentOperatorBadge || '---' }}
              </div>
            </div>
            
            <q-separator vertical inset class="q-mx-md bg-grey-4" />
            
            <div class="text-h5 font-monospace vemag-text-primary text-weight-bold" style="margin-top: 2px;">
              {{ timeDisplay }}
            </div>
          </div>
          
          <q-btn flat round icon="logout" class="text-white" size="lg" padding="sm" @click="handleLogout" />
        </div>

      </q-toolbar>
      <q-linear-progress :value="1" color="green" class="q-mt-none" size="6px" />
    </q-header>

    <q-page-container class="full-height">
      <q-page class="q-pa-md full-height column no-wrap">
        
        <div v-if="!productionStore.activeOrder" class="col flex flex-center column">
          <q-card class="q-pa-xl text-center shadow-10 bg-white" style="border-radius: 24px; max-width: 600px; width: 90%;">
            <div class="vemag-bg-light q-pa-lg rounded-borders inline-block q-mb-lg">
               <q-icon name="qr_code_scanner" size="100px" class="vemag-text-primary" />
            </div>
            <div class="text-h3 text-weight-bolder vemag-text-primary q-mb-md">Aguardando O.P.</div>
            <div class="text-h5 text-grey-7 q-mb-xl">A máquina está parada.<br>Escaneie a Ordem de Serviço para iniciar.</div>
            <q-btn 
                push rounded 
                class="vemag-bg-primary text-white full-width shadow-4" 
                size="30px" 
                padding="lg"
                icon="photo_camera" 
                label="LER QR CODE" 
                @click="simulateOpScan" 
            />
          </q-card>
        </div>

        <div v-else class="col row q-col-gutter-md items-stretch content-stretch">
          
          <div class="col-12 col-md-8 column no-wrap full-height q-gutter-y-md">
            
            <q-card class="col column relative-position overflow-hidden shadow-4 bg-white" style="border-radius: 20px; border-left: 12px solid #008C7A;">
              
              <div class="col-auto relative-position bg-vemag-gradient text-white q-pa-md shadow-2">
                  <q-img :src="customOsBackgroundImage" class="absolute-full opacity-20" fit="cover" />
                  
                  <div class="row items-center justify-between relative-position z-top">
                      <div class="col-grow">
                          <div class="row items-center q-gutter-x-sm q-mb-xs">
                              <q-badge color="orange-9" label="PRIORIDADE 1" class="text-subtitle2 text-bold" />
                              <q-badge outline color="white" class="text-subtitle2 text-bold" :label="productionStore.activeOrder.code" />
                          </div>
                          <div class="text-h3 text-weight-bolder ellipsis">{{ productionStore.activeOrder.part_name }}</div>
                          <div class="text-subtitle1 text-grey-3">Meta: <strong>{{ productionStore.activeOrder.target_quantity }} un</strong></div>
                      </div>

                      <div class="column items-end q-gutter-y-sm">
                          <div class="row items-center bg-black-transparent q-px-md q-py-sm rounded-borders">
                              <div class="column items-end q-mr-md">
                                  <div class="text-caption text-grey-4 text-uppercase">Produzidas</div>
                                  <div class="text-h4 text-weight-bold lh-small">{{ productionStore.activeOrder.produced_quantity }}<span class="text-h6 text-grey-5">/{{ productionStore.activeOrder.target_quantity }}</span></div>
                              </div>
                              <q-circular-progress
                                  show-value
                                  font-size="12px"
                                  :value="((productionStore.activeOrder.produced_quantity || 0) / (productionStore.activeOrder.target_quantity || 1)) * 100"
                                  size="50px"
                                  :thickness="0.25"
                                  color="orange-5"
                                  track-color="grey-8"
                                  class="text-white text-bold"
                              >
                                  {{ Math.round(((productionStore.activeOrder.produced_quantity || 0) / (productionStore.activeOrder.target_quantity || 1)) * 100) }}%
                              </q-circular-progress>
                          </div>
                          <q-btn 
                              push color="blue-grey-9" text-color="white" 
                              icon="image" label="VER DESENHO" 
                              size="md" padding="sm md"
                              @click="isDrawingDialogOpen = true" 
                          />
                      </div>
                  </div>
              </div>

              <div class="col-auto bg-grey-2 q-px-lg q-py-md border-bottom-light row items-center justify-between" v-if="currentViewedStep">
                  <div class="row items-center">
                      <div class="text-h6 text-grey-6 q-mr-md text-weight-bold">#{{ currentViewedStep.seq }}</div>
                      <div class="text-h4 text-weight-bolder ellipsis" style="line-height: 1.1;">{{ productionStore.activeOrder.part_name }}</div>
                  </div>
                  <q-chip square color="blue-grey-9" text-color="white" icon="precision_manufacturing" :label="`Recurso: ${currentViewedStep.resource}`" class="text-subtitle1 text-weight-bold" />
              </div>

              <q-card-section class="col scroll q-pa-xl">
                 <div v-if="currentViewedStep" class="column q-gutter-y-lg">
                    <div class="text-dark" style="white-space: pre-line; font-size: 1.5rem; line-height: 1.5; font-weight: 500;">
                       {{ currentViewedStep.description }}
                    </div>

                    <div class="row justify-end text-grey-8 items-center q-mt-auto">
                       <q-icon name="schedule" size="32px" class="q-mr-sm" />
                       <span class="text-h5">Tempo Estimado: <strong>{{ currentViewedStep.timeEst }}h</strong></span>
                    </div>
                 </div>
                 <div v-else class="text-center text-grey-5 q-pa-xl column flex-center h-100">
                    <q-icon name="sentiment_dissatisfied" size="6em" />
                    <div class="text-h4 q-mt-md">Nenhum passo encontrado.</div>
                 </div>
              </q-card-section>

              <q-separator />
              
              <q-card-actions align="between" class="col-auto q-pa-md bg-grey-1">
                 <div class="row q-gutter-x-md col-7">
                    <q-btn 
                       push color="white" text-color="primary" 
                       icon="arrow_back" label="ANTERIOR" 
                       size="lg" class="col-grow shadow-1"
                       @click="prevStepView" 
                       :disable="viewedStepIndex === 0" 
                    />
                    <q-btn 
                       push color="primary" text-color="white" 
                       icon-right="arrow_forward" label="PRÓXIMO" 
                       size="lg" class="col-grow shadow-2"
                       @click="nextStepView" 
                       :disable="!productionStore.activeOrder.steps || viewedStepIndex === productionStore.activeOrder.steps.length - 1" 
                    />
                 </div>

                 <q-btn 
                    flat color="negative" icon="delete_outline" 
                    label="Apontar Refugo" 
                    size="lg"
                    class="bg-red-1 q-px-lg"
                    @click="productionStore.addProduction(1, true)"
                 />
              </q-card-actions>
            </q-card>
          </div>

          <div class="col-12 col-md-4 column no-wrap full-height justify-between">
            
            <q-card class="col-auto bg-white text-center q-py-md relative-position shadow-3" style="border-radius: 20px;">
               <div class="row items-center justify-center q-gutter-x-md">
                  <q-icon name="timer" class="vemag-text-secondary" size="36px" />
                  <div class="text-h6 vemag-text-primary text-uppercase font-weight-bold">
                    Tempo no Estado
                  </div>
               </div>
               <div class="text-h2 text-weight-bolder font-monospace q-my-sm text-dark">{{ elapsedTime }}</div>
               <q-linear-progress stripe query :class="statusTextClass" size="8px" class="q-mt-sm absolute-bottom" />
            </q-card>

            <div class="col relative-position q-mb-md q-mt-md">
               <q-btn 
    class="fit shadow-6 hover-scale-producing" 
    :class="normalizedStatus === 'EM OPERAÇÃO' ? 'vemag-bg-primary text-white' : 'bg-blue-grey-10 text-white'" 
    push :loading="isLoadingAction"
    style="border-radius: 24px;"
    @click="toggleProduction"
>
    <div class="column items-center justify-center full-height">
    <q-icon size="120px" :name="normalizedStatus === 'EM OPERAÇÃO' ? 'pause_circle' : 'play_circle_filled'" />
    
    <div class="text-h2 text-weight-bolder q-mt-lg">
        {{ normalizedStatus === 'EM OPERAÇÃO' ? 'PAUSAR' : 'INICIAR' }}
    </div>
    
    <div class="text-h5 text-uppercase letter-spacing-1 opacity-80 q-mt-sm">
        {{ normalizedStatus === 'EM OPERAÇÃO' ? 'MÁQUINA EM OPERAÇÃO' : 'INICIAR PRODUÇÃO' }}
    </div>
    </div>
</q-btn>
            </div>

            <div class="col-auto row q-gutter-x-md q-mb-md" style="height: 120px;">
               <q-btn 
    class="col shadow-3 hover-scale"
    :color="normalizedStatus === 'MANUTENÇÃO' ? 'warning' : 'blue-grey-2'"
    :text-color="normalizedStatus === 'MANUTENÇÃO' ? 'dark' : 'blue-grey-9'"
    push style="border-radius: 20px;" 
    :loading="isLoadingAction"
    @click="toggleSetup"
>
    <div class="column items-center justify-center">
        <q-icon name="build" size="48px" class="q-mb-sm" />
        <div class="text-h5 text-weight-bold">SETUP</div>
    </div>
</q-btn>

               <q-btn 
                  class="col shadow-3 hover-scale vemag-bg-secondary text-white"
                  push style="border-radius: 20px;"
                  @click="isAndonDialogOpen = true"
               >
                  <div class="column items-center justify-center">
                     <q-icon name="notifications_active" size="40px" class="q-mb-sm" />
                     <div class="text-h6 text-weight-bold">AJUDA</div>
                  </div>
               </q-btn>
            </div>

            <div class="col-auto">
               <q-btn 
    class="full-width shadow-4" color="red-10" text-color="white"
    push size="32px" icon="stop_circle" label="FINALIZAR O.P."
    style="border-radius: 20px; min-height: 100px;"
    @click="confirmFinishOp"
    :disable="normalizedStatus === 'EM OPERAÇÃO'"
>
</q-btn>
            </div>
          </div>
        </div>
      </q-page>
    </q-page-container>

    <q-dialog 
        v-model="isDrawingDialogOpen" 
        maximized 
        transition-show="slide-up" 
        transition-hide="slide-down"
        class="z-max"
        style="z-index: 9999;"
    >
        <q-card class="bg-black text-white column">
            <q-bar class="bg-grey-9 q-pa-md z-top" style="height: 80px;">
                <q-icon name="image" size="40px" />
                <div class="text-h4 q-ml-md">Desenho Técnico</div>
                <q-space />
                <q-btn dense flat icon="close" size="30px" v-close-popup />
            </q-bar>
            
            <q-card-section class="col flex flex-center relative-position" style="overflow: hidden;">
                <q-img 
                    :src="productionStore.activeOrder?.technical_drawing_url || '/desenho.jpg'"
                    style="max-width: 100%; max-height: 100%;"
                    fit="contain"
                />
            </q-card-section>
        </q-card>
    </q-dialog>
    <q-dialog v-model="isStopDialogOpen" persistent maximized transition-show="slide-up" transition-hide="slide-down" style="z-index: 9999;">
      <q-card class="bg-grey-2 column">
        <q-toolbar class="bg-white text-dark q-py-lg">
          <q-toolbar-title class="text-weight-bold text-h4 row items-center">
            <q-icon name="warning" color="warning" size="50px" class="q-mr-md"/> 
            SELECIONE O MOTIVO DA PARADA
          </q-toolbar-title>
          <q-btn flat round icon="close" size="xl" v-close-popup />
        </q-toolbar>
        
        <q-card-section class="col column q-pa-none">
            <div class="q-pa-xl">
               <q-input v-model="stopSearch" outlined bg-color="white" placeholder="Pesquisar motivo..." class="text-h5" input-class="q-pa-md" autofocus clearable>
                  <template v-slot:prepend><q-icon name="search" size="40px" /></template>
               </q-input>
            </div>
            <div class="col scroll q-px-xl q-pb-xl">
               <div class="row q-col-gutter-lg">
                  <div v-for="(reason, idx) in filteredStopReasons" :key="idx" class="col-12 col-md-6 col-lg-4">
                     <q-btn color="white" text-color="dark" class="full-width shadow-3" padding="xl" align="left" no-caps style="border-radius: 16px; min-height: 120px;" @click="handleReasonSelect(reason.label)">
                        <div class="row items-center no-wrap full-width">
                           <q-avatar :color="getCategoryColor(reason.category)" text-color="white" icon="priority_high" size="60px" font-size="32px" class="q-mr-lg" />
                           <div class="column">
                              <div class="text-h5 text-weight-bold">{{ reason.label }}</div>
                              <div class="text-h6 text-grey-7">{{ reason.category }}</div>
                           </div>
                           <q-space />
                           <q-icon v-if="reason.requiresMaintenance" name="build_circle" color="red" size="40px" />
                        </div>
                     </q-btn>
                  </div>
               </div>
            </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isMaintenanceConfirmOpen" persistent>
       <q-card class="bg-red-9 text-white" style="width: 800px; max-width: 95vw; border-radius: 24px;">
          <q-card-section class="row items-center q-pa-lg">
             <q-avatar icon="warning" color="white" text-color="red-9" size="80px" font-size="48px" />
             <div class="text-h3 q-ml-lg text-weight-bold">Atenção: Parada Crítica</div>
          </q-card-section>
          <q-card-section class="q-px-xl q-py-lg">
             <p class="text-h4">Você selecionou: <span class="text-weight-bolder text-yellow-3">"{{ pendingReason }}"</span>.</p>
             <p class="text-h5 q-mt-md opacity-80">Este motivo requer intervenção técnica. O que deseja fazer?</p>
          </q-card-section>
          <q-card-actions align="center" class="q-pa-xl q-gutter-xl">
             <q-btn push color="white" text-color="red-9" size="30px" class="col-grow shadow-5" padding="lg" style="border-radius: 16px;" icon="handyman" label="SÓ PAUSAR" @click="executeStop(false)" />
             <q-btn push color="red-10" text-color="white" size="30px" class="col-grow shadow-5" padding="lg" style="border: 3px solid white; border-radius: 16px;" icon="assignment_turned_in" label="ABRIR O.M." @click="executeStop(true)" />
          </q-card-actions>
       </q-card>
    </q-dialog>

    <q-dialog v-model="isAndonDialogOpen" transition-show="scale" transition-hide="scale">
      <q-card style="width: 900px; max-width: 95vw; border-radius: 24px;">
        <q-card-section class="vemag-bg-primary text-white row items-center justify-between q-pa-lg">
          <div class="text-h4 text-weight-bold row items-center"><q-icon name="campaign" size="50px" class="q-mr-md" />Central de Ajuda (Andon)</div>
          <q-btn icon="close" flat round size="xl" v-close-popup />
        </q-card-section>
        <q-card-section class="q-pa-xl">
          <div class="text-h5 q-mb-lg vemag-text-primary text-weight-bold">Selecione o setor responsável:</div>
          <div class="row q-col-gutter-lg">
            <div v-for="opt in andonOptions" :key="opt.label" class="col-6 col-md-4">
              <q-btn push class="full-width full-height column flex-center q-pa-lg shadow-3 transition-hover" :class="`bg-${opt.color} text-white`" style="border-radius: 20px; min-height: 160px;" @click="triggerAndon(opt.label)">
                <q-icon :name="opt.icon" size="60px" class="q-mb-md" />
                <div class="text-h5 text-weight-bold">{{ opt.label }}</div>
              </q-btn>
            </div>
          </div>
          <div class="q-mt-xl">
            <q-input v-model="andonNote" outlined label="Observação (Opcional)" placeholder="Descreva..." class="text-h6" bg-color="grey-1">
              <template v-slot:prepend><q-icon name="edit_note" size="40px" class="vemag-text-primary" /></template>
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

// --- Dialogs ---
const isStopDialogOpen = ref(false);
const isAndonDialogOpen = ref(false);
const isMaintenanceConfirmOpen = ref(false);
const isDrawingDialogOpen = ref(false);

const pendingReason = ref('');
const stopSearch = ref('');
const statusStartTime = ref(new Date());
const currentTime = ref(new Date());
let timerInterval: ReturnType<typeof setInterval>;
const andonNote = ref('');

// --- Navigation ---
const viewedStepIndex = ref(0);

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

// --- Configs ---
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

    // Mapeia tudo para "EM OPERAÇÃO"
    if (['RUNNING', 'EM USO', 'EM PRODUÇÃO', 'IN_USE', 'PRODUZINDO', 'EM OPERAÇÃO'].includes(s)) {
        return 'EM OPERAÇÃO';
    }
    
    // Mapeia tudo para "MANUTENÇÃO" (Inclui Setup)
    if (['SETUP', 'EM SETUP', 'PREPARAÇÃO', 'MANUTENÇÃO'].includes(s)) {
        return 'MANUTENÇÃO';
    }
    
    // Todo o resto é "PARADA"
    return 'PARADA'; 
});

// --- Classes Visuais baseadas no Status em PT ---
const statusBgClass = computed(() => {
  if (normalizedStatus.value === 'EM OPERAÇÃO') return 'bg-positive'; 
  if (normalizedStatus.value === 'MANUTENÇÃO') return 'bg-warning';
  return 'bg-negative';
});

const statusTextClass = computed(() => {
    if (normalizedStatus.value === 'EM OPERAÇÃO') return 'vemag-text-primary';
    if (normalizedStatus.value === 'MANUTENÇÃO') return 'text-warning';
    return 'text-negative';
});

const statusIcon = computed(() => {
    if (normalizedStatus.value === 'EM OPERAÇÃO') return 'autorenew';
    if (normalizedStatus.value === 'MANUTENÇÃO') return 'handyman';
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

// --- Actions ---

async function toggleSetup() {
  isLoadingAction.value = true;
  if (normalizedStatus.value === 'MANUTENÇÃO') {
    await productionStore.pauseProduction('Fim de Setup'); 
  } else {
    await productionStore.enterSetup(); 
  }
  resetTimer();
  isLoadingAction.value = false;
}

async function toggleProduction() {
  isLoadingAction.value = true;
  if (normalizedStatus.value === 'EM OPERAÇÃO') {
    // Se está rodando, abre modal de parada
    isStopDialogOpen.value = true;
    stopSearch.value = '';
  } else {
    // Se não está rodando, inicia
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
    ok: { label: 'Finalizar', color: 'negative', push: true, size: 'lg' }
  }).onOk(() => {
     void (async () => {
        await productionStore.finishSession();
        resetTimer();
     })();
  });
}

function handleLogout() {
  $q.dialog({ title: 'Sair', message: 'Fazer logoff?', cancel: true, ok: { size: 'lg', label: 'SAIR' } }).onOk(() => {
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
.bg-vemag-gradient { background: linear-gradient(135deg, #008C7A 0%, #00695C 100%); }
.bg-black-transparent { background-color: rgba(0,0,0,0.15); }
</style>

<style scoped>
.font-inter { font-family: 'Roboto', sans-serif; }
.font-monospace { font-family: 'Courier New', monospace; letter-spacing: -1px; }
.lh-small { line-height: 1.1; }
.col-grow { flex-grow: 1; }
.opacity-60 { opacity: 0.6; }
.opacity-50 { opacity: 0.5; }
.opacity-20 { opacity: 0.2; }
.opacity-80 { opacity: 0.8; }
.hover-scale-producing { transition: all 0.2s ease-in-out; }
.hover-scale-producing:active { transform: scale(0.98); }
.border-bottom-light { border-bottom: 2px solid #e0e0e0; }
.transition-hover:active { filter: brightness(0.9); }
</style>
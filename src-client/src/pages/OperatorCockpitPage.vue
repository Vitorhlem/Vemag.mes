<template>
  <q-layout view="hHh lpR fFf" class="bg-blue-grey-1 text-dark font-inter" style="overflow: hidden;">
    
    <q-header bordered class="bg-white text-dark q-py-xs shadow-2" style="height: 60px;">
      <q-toolbar class="full-height q-px-md">
        <div class="row items-center q-mr-lg">
          <img :src="logoPath" alt="Logo" style="height: 40px; max-width: 160px; object-fit: contain;" />
        </div>
        <q-separator vertical inset class="q-mx-sm mobile-hide bg-grey-3" />
        <q-toolbar-title class="column justify-center q-ml-sm">
          <div class="text-caption text-uppercase text-grey-7 letter-spacing-1 lh-small" style="font-size: 0.7rem;">
            {{ productionStore.machineSector }}
          </div>
          <div class="text-subtitle1 text-weight-bolder lh-small row items-center text-primary">
            {{ productionStore.machineName }}
            <q-badge rounded :color="statusColor" class="q-ml-sm shadow-1">
              <q-icon :name="statusIcon" color="white" class="q-mr-xs" size="10px" />
              {{ productionStore.activeOrder?.status || 'OFFLINE' }}
            </q-badge>
          </div>
        </q-toolbar-title>
        <q-space />
        <div class="row items-center q-gutter-x-sm bg-grey-2 q-py-xs q-px-sm rounded-borders shadow-1">
          <q-avatar size="32px" class="shadow-1" icon="person" color="grey-4" text-color="grey-8" />
          <div class="column items-start mobile-hide lh-small">
            <div class="text-weight-bold text-caption">Operador</div>
            <div class="text-caption text-grey-7" style="font-size: 0.65rem;">
              {{ productionStore.currentOperatorBadge || '---' }}
            </div>
          </div>
          <q-separator vertical inset class="q-mx-xs bg-grey-4" />
          <div class="text-h6 font-monospace text-dark text-weight-bold">{{ timeDisplay }}</div>
        </div>
        <q-btn flat round icon="logout" color="grey-8" size="md" class="q-ml-sm" @click="handleLogout" />
      </q-toolbar>
      <q-linear-progress :value="1" :color="statusColor" size="3px" />
    </q-header>

    <q-page-container>
      <q-page class="q-pa-sm full-height column no-wrap">
        
        <div v-if="!productionStore.activeOrder" class="col flex flex-center column">
          <q-card class="q-pa-lg text-center shadow-8 bg-white" style="border-radius: 16px; max-width: 400px;">
            <div class="bg-blue-grey-1 q-pa-md rounded-borders inline-block q-mb-md">
               <q-icon name="qr_code_scanner" size="60px" color="primary" />
            </div>
            <div class="text-h5 text-weight-bolder text-dark q-mb-xs">Aguardando O.P.</div>
            <div class="text-caption text-grey-7 q-mb-lg">A máquina está parada. Escaneie a O.S. para iniciar.</div>
            <q-btn push rounded color="primary" size="lg" icon="photo_camera" label="Ler QR Code" class="full-width" @click="simulateOpScan" />
          </q-card>
        </div>

        <div v-else class="row q-col-gutter-sm col full-height items-stretch content-stretch">
          
          <div class="col-12 col-md-8 column q-gutter-y-sm">
            <q-card class="relative-position overflow-hidden shadow-4 bg-dark" style="border-radius: 16px; height: 150px; min-height: 150px;">
              <q-img :src="productionStore.activeOrder.part_image_url" class="absolute-full opacity-60" fit="cover" />
              <div class="absolute-full" style="background: linear-gradient(to right, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.5) 60%, rgba(0,0,0,0.1));"></div>
              <div class="absolute-full q-pa-md row items-center justify-between text-white">
                <div>
                    <div class="row items-center q-gutter-x-sm q-mb-xs">
                        <q-badge color="orange-9" label="PRIORIDADE 1" />
                        <q-badge outline color="white" :label="productionStore.activeOrder.code" />
                    </div>
                    <div class="text-h4 text-weight-bolder">{{ productionStore.activeOrder.part_name }}</div>
                    <div class="text-subtitle2 text-grey-4">Meta: {{ productionStore.activeOrder.target_quantity }} un</div>
                </div>
              </div>
            </q-card>

            <q-card class="col-grow shadow-3 column bg-white" style="border-radius: 12px; border-left: 6px solid var(--q-primary);">
              <q-card-section class="col column justify-center q-pt-sm text-center">
                 <div class="text-h2 text-weight-bolder text-dark q-mb-md">
                    {{ productionStore.activeOrder.produced_quantity }} <span class="text-h5 text-grey">/ {{ productionStore.activeOrder.target_quantity }}</span>
                 </div>
                 <div class="text-subtitle1 text-uppercase text-grey-6 letter-spacing-1">Peças Produzidas</div>
                 
                 <div class="row justify-center q-gutter-md q-mt-lg">
                    <q-btn push round color="negative" icon="delete" size="xl" @click="productionStore.addProduction(1, true)">
                        <q-tooltip>Refugo</q-tooltip>
                    </q-btn>
                    <q-btn push round color="positive" icon="add" size="30px" class="q-pa-lg" @click="productionStore.addProduction(1, false)">
                        <q-tooltip>Peça Boa</q-tooltip>
                    </q-btn>
                 </div>
              </q-card-section>
            </q-card>
          </div>

          <div class="col-12 col-md-4 column q-gutter-y-sm">
            
            <q-card class="bg-white text-center q-py-sm relative-position shadow-2" style="border-radius: 12px;">
               <div class="row items-center justify-center q-gutter-x-sm">
                  <q-icon name="timer" color="grey-7" size="sm" />
                  <div class="text-subtitle1 text-grey-9">
                    Tempo no Estado: <span class="text-weight-bold font-monospace">{{ elapsedTime }}</span>
                  </div>
               </div>
               <q-linear-progress stripe query :color="statusColor" size="4px" class="q-mt-xs absolute-bottom" />
            </q-card>

            <div class="col-grow relative-position">
               <q-btn 
                  v-if="['SETUP', 'RUNNING', 'PAUSED', 'PENDING', 'IDLE', 'STOPPED'].includes(productionStore.activeOrder.status)"
                  :color="productionStore.activeOrder.status === 'RUNNING' ? 'positive' : 'blue-grey-9'" 
                  class="fit shadow-4 hover-scale-producing" 
                  push 
                  :loading="isLoadingAction"
                  style="border-radius: 16px;"
                  @click="toggleProduction"
               >
                  <div class="column items-center">
                    <q-icon size="60px" :name="productionStore.activeOrder.status === 'RUNNING' ? 'pause_circle' : 'play_circle_filled'" />
                    <div class="text-h4 text-weight-bolder q-mt-sm">
                       {{ productionStore.activeOrder.status === 'RUNNING' ? 'PAUSAR' : 'INICIAR' }}
                    </div>
                    <div class="text-subtitle2 text-uppercase letter-spacing-1 opacity-80">
                       {{ productionStore.activeOrder.status === 'RUNNING' ? 'Máquina Rodando' : 'Iniciar Produção' }}
                    </div>
                  </div>
               </q-btn>
            </div>

            <div class="row q-gutter-x-sm" style="height: 80px;">
               <q-btn 
                  class="col shadow-3 hover-scale"
                  :color="productionStore.activeOrder.status === 'SETUP' ? 'warning' : 'blue-grey-2'"
                  :text-color="productionStore.activeOrder.status === 'SETUP' ? 'dark' : 'blue-grey-9'"
                  push style="border-radius: 16px;"
                  :loading="isLoadingAction"
                  @click="toggleSetup"
               >
                  <div class="column items-center">
                     <q-icon name="build" size="24px" class="q-mb-none" />
                     <div class="text-weight-bold">SETUP</div>
                  </div>
               </q-btn>

               <q-btn 
                  class="col shadow-3 hover-scale"
                  color="negative" outline
                  style="border-radius: 16px; background: white;"
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
                  class="full-width shadow-3"
                  color="red-10" 
                  text-color="white"
                  push
                  size="lg"
                  icon="stop_circle"
                  label="FINALIZAR O.P."
                  style="border-radius: 16px;"
                  @click="confirmFinishOp"
                  :disable="productionStore.activeOrder.status === 'RUNNING'"
               >
                  <q-tooltip v-if="productionStore.activeOrder.status === 'RUNNING'" class="bg-negative text-body2">
                     Pause a máquina antes de finalizar!
                  </q-tooltip>
               </q-btn>
            </div>

          </div>
        </div>
      </q-page>
    </q-page-container>

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
                 <q-btn color="white" text-color="dark" class="full-width full-height shadow-2" padding="lg" align="left" no-caps @click="confirmStop(reason.label)">
                    <div class="row items-center no-wrap full-width">
                       <q-avatar :color="getCategoryColor(reason.category)" text-color="white" icon="priority_high" size="md" class="q-mr-md" />
                       <div class="column">
                          <div class="text-subtitle1 text-weight-bold">{{ reason.label }}</div>
                          <div class="text-caption text-grey">{{ reason.category }}</div>
                       </div>
                    </div>
                 </q-btn>
              </div>
           </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isAndonDialogOpen">
      <q-card style="width: 500px">
        <q-card-section class="bg-negative text-white text-center q-py-lg"><div class="text-h5 text-weight-bold">Solicitar Apoio</div></q-card-section>
        <q-card-section class="q-gutter-md q-pa-lg">
          <q-btn class="full-width" color="primary" label="Mecânica" @click="triggerAndon('Mecânica')" />
          <q-btn class="full-width" color="orange" label="Elétrica" @click="triggerAndon('Elétrica')" />
          <q-btn class="full-width" color="purple" label="Logística" @click="triggerAndon('Logística')" />
        </q-card-section>
        <q-card-actions align="right"><q-btn flat label="Cancelar" v-close-popup /></q-card-actions>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useProductionStore } from 'stores/production-store';
import { STOP_REASONS } from 'src/data/stop-reasons';

const router = useRouter();
const $q = useQuasar();
const productionStore = useProductionStore();

const logoPath = ref('/Logo-Oficial.png');
const isLoadingAction = ref(false);

const isStopDialogOpen = ref(false);
const isAndonDialogOpen = ref(false);
const stopSearch = ref('');
const statusStartTime = ref(new Date());
const currentTime = ref(new Date());
let timerInterval: ReturnType<typeof setInterval>;

const elapsedTime = computed(() => {
   const diff = Math.max(0, Math.floor((currentTime.value.getTime() - statusStartTime.value.getTime()) / 1000));
   const h = Math.floor(diff / 3600).toString().padStart(2, '0');
   const m = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
   const s = (diff % 60).toString().padStart(2, '0');
   return `${h}:${m}:${s}`;
});

const timeDisplay = computed(() => currentTime.value.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));

const statusColor = computed(() => {
  const status = productionStore.activeOrder?.status;
  if (status === 'RUNNING') return 'positive';
  if (status === 'SETUP') return 'warning';
  if (status === 'PAUSED' || status === 'STOPPED') return 'negative';
  return 'grey-5';
});

const statusIcon = computed(() => {
    const status = productionStore.activeOrder?.status;
    if (status === 'RUNNING') return 'autorenew';
    if (status === 'SETUP') return 'handyman';
    if (status === 'PAUSED' || status === 'STOPPED') return 'error_outline';
    return 'power_off';
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

function resetTimer() {
   statusStartTime.value = new Date();
}

async function toggleSetup() {
  isLoadingAction.value = true;
  if (productionStore.activeOrder?.status === 'SETUP') {
    await productionStore.pauseProduction('Fim de Setup'); 
  } else {
    await productionStore.sendEvent('STATUS_CHANGE', { new_status: 'SETUP', reason: 'Setup Iniciado' });
  }
  resetTimer();
  isLoadingAction.value = false;
}

async function toggleProduction() {
  isLoadingAction.value = true;
  if (productionStore.activeOrder?.status === 'RUNNING') {
    isStopDialogOpen.value = true;
    stopSearch.value = '';
  } else {
    await productionStore.startProduction();
    resetTimer();
  }
  isLoadingAction.value = false;
}

async function confirmStop(reason: string) {
  isLoadingAction.value = true;
  await productionStore.pauseProduction(reason);
  isStopDialogOpen.value = false;
  resetTimer();
  isLoadingAction.value = false;
}

// NOVO: AÇÃO DE FINALIZAR
function confirmFinishOp() {
  $q.dialog({
    title: 'Finalizar O.P.',
    message: 'Tem certeza que deseja encerrar a Ordem de Produção? Isso salvará o tempo total e liberará a máquina.',
    cancel: true,
    persistent: true,
    ok: { label: 'Finalizar', color: 'negative', push: true }
  }).onOk(async () => {
     await productionStore.finishSession();
     resetTimer();
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

function triggerAndon(sector: string) {
  void productionStore.triggerAndon(sector);
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

<style scoped>
.font-inter { font-family: 'Roboto', sans-serif; }
.font-monospace { font-family: 'Courier New', monospace; letter-spacing: -1px; }
.lh-small { line-height: 1.1; }
.col-grow { flex-grow: 1; }
.opacity-60 { opacity: 0.6; }
.hover-scale-producing { transition: all 0.3s ease-in-out; }
.hover-scale-producing:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(33, 186, 69, 0.3); }
</style>
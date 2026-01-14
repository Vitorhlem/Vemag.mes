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
              {{ productionStore.activeOrder?.status || 'OFFLINE' }}
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
                    <div class="text-caption text-grey-7">Instruções de processo</div>
                 </div>
                 <div class="text-right">
                    <div class="text-h4 text-weight-bolder vemag-text-primary">
                       {{ productionStore.activeOrder.produced_quantity }} <span class="text-h6 text-grey-5">/ {{ productionStore.activeOrder.target_quantity }}</span>
                    </div>
                    <div class="text-caption text-grey-7">Peças Produzidas</div>
                 </div>
              </q-card-section>
              
              <q-linear-progress :value="productionStore.activeOrder.produced_quantity / productionStore.activeOrder.target_quantity" class="vemag-text-primary" size="6px" />

              <q-card-section class="col scroll q-pa-none">
                 <q-list separator>
                    <q-item>
                       <q-item-section avatar><q-icon name="check_circle" color="positive" /></q-item-section>
                       <q-item-section>
                          <q-item-label class="text-weight-bold">1. Preparação de Matéria Prima</q-item-label>
                          <q-item-label caption>Verificar lote da bobina e posicionar no desbobinador.</q-item-label>
                       </q-item-section>
                    </q-item>
                    <q-item>
                       <q-item-section avatar><q-icon name="check_circle" color="positive" /></q-item-section>
                       <q-item-section>
                          <q-item-label class="text-weight-bold">2. Ajuste de Ferramenta (Setup)</q-item-label>
                          <q-item-label caption>Garantir alinhamento de 0.5mm conforme desenho técnico.</q-item-label>
                       </q-item-section>
                    </q-item>
                    
                    <q-item class="vemag-bg-light">
                       <q-item-section avatar><q-spinner-dots class="vemag-text-primary" size="24px" /></q-item-section>
                       <q-item-section>
                          <q-item-label class="text-weight-bold vemag-text-primary">3. Operação de Corte e Dobra</q-item-label>
                          <q-item-label caption class="text-dark">Acompanhar ciclo automático. Verificar rebarbas a cada 50 peças.</q-item-label>
                       </q-item-section>
                       <q-item-section side><q-badge class="vemag-bg-primary text-white">EM ANDAMENTO</q-badge></q-item-section>
                    </q-item>
                    
                    <q-item>
                       <q-item-section avatar><q-icon name="radio_button_unchecked" color="grey-5" /></q-item-section>
                       <q-item-section>
                          <q-item-label class="text-grey-7">4. Paletização</q-item-label>
                          <q-item-label caption>Acomodar em caixas padrão KLT (20 un/caixa).</q-item-label>
                       </q-item-section>
                    </q-item>
                 </q-list>
              </q-card-section>

              <q-separator />

              <q-card-actions align="right" class="q-pa-md bg-grey-1">
                 <div class="row items-center q-gutter-md">
                    <span class="text-caption text-grey-7 text-italic mobile-hide">Contagem de peças boas é automática via sensor.</span>
                    <q-btn 
                       outline 
                       color="negative" 
                       icon="delete_outline" 
                       label="Apontar Refugo / Peça Defeituosa" 
                       class="q-px-lg shadow-1 bg-white"
                       @click="productionStore.addProduction(1, true)"
                    />
                 </div>
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
                  v-if="['SETUP', 'RUNNING', 'PAUSED', 'PENDING', 'IDLE', 'STOPPED'].includes(productionStore.activeOrder.status)"
                  :class="productionStore.activeOrder.status === 'RUNNING' ? 'vemag-bg-primary text-white' : 'bg-blue-grey-9 text-white'" 
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
                  class="col shadow-3 hover-scale vemag-bg-secondary text-white"
                  push
                  style="border-radius: 16px;"
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
                push 
                class="full-width full-height column flex-center q-pa-md shadow-2 transition-hover"
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
            <q-input 
              v-model="andonNote" 
              outlined 
              label="Observação (Opcional)" 
              placeholder="Descreva brevemente o problema..." 
              dense
              bg-color="grey-1"
            >
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
import { STOP_REASONS } from 'src/data/stop-reasons';

const router = useRouter();
const $q = useQuasar();
const productionStore = useProductionStore();

const logoPath = ref('/Logo-Oficial.png');
const isLoadingAction = ref(false);

// --- PERSONALIZAÇÃO IMAGEM O.S. ---
// Altere este valor para mudar a imagem de fundo do carro
const customOsBackgroundImage = ref('/a.jpg');

// watch(() => productionStore.activeOrder, (newVal) => {
//     if (newVal?.part_image_url) customOsBackgroundImage.value = newVal.part_image_url;
// }, { immediate: true });

const isStopDialogOpen = ref(false);
const isAndonDialogOpen = ref(false);
const stopSearch = ref('');
const statusStartTime = ref(new Date());
const currentTime = ref(new Date());
let timerInterval: ReturnType<typeof setInterval>;

// Andon Config
const andonNote = ref('');
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

const statusBgClass = computed(() => {
  const status = productionStore.activeOrder?.status;
  if (status === 'RUNNING') return 'bg-positive'; // Ou 'vemag-bg-primary' se quiser tudo verde
  if (status === 'SETUP') return 'bg-warning';
  if (status === 'PAUSED' || status === 'STOPPED') return 'bg-negative';
  return 'bg-grey-5';
});

const statusTextClass = computed(() => {
    const status = productionStore.activeOrder?.status;
    if (status === 'RUNNING') return 'vemag-text-primary';
    if (status === 'SETUP') return 'text-warning';
    if (status === 'PAUSED' || status === 'STOPPED') return 'text-negative';
    return 'text-grey-5';
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

function confirmFinishOp() {
  $q.dialog({
    title: 'Finalizar O.P.',
    message: 'Tem certeza que deseja encerrar a Ordem de Produção? Isso salvará o tempo total e liberará a máquina.',
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
/* ESTILOS GLOBAIS NÃO ESCOPADOS PARA GARANTIR OVERRIDE 
   Cores baseadas na VEMAG
*/
.vemag-bg-primary {
  background-color: #008C7A !important;
}
.vemag-text-primary {
  color: #008C7A !important;
}

.vemag-bg-secondary {
  background-color: #66B8B0 !important;
}
.vemag-text-secondary {
  color: #66B8B0 !important;
}

.vemag-bg-light {
  background-color: #E0F2F1 !important;
}
.vemag-bg-light-accent {
  background-color: #B2DFDB !important;
}
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
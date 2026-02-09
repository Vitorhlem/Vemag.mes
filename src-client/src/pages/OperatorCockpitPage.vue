<template>
  <q-layout view="hHh lpR fFf" class="bg-grey-2 text-dark font-inter window-height overflow-hidden">
    
    <q-header bordered class="q-py-xs shadow-3 text-white" style="height: 65px; background-color: #008C7A;">
      <q-toolbar class="full-height q-px-md"> 
        
        <div class="row items-center no-wrap">
          <img :src="logoPath" alt="Logo" 
            :style="$q.screen.lt.md ? 'height: 30px' : 'height: 40px'" 
            style="max-width: 150px; object-fit: contain; filter: brightness(0) invert(1);" 
          />
          
          <q-separator vertical inset class="q-mx-md mobile-hide bg-white opacity-50" /> 
          
          <div class="column justify-center mobile-hide" style="max-width: 250px;">
            <div class="text-caption text-uppercase text-grey-3 letter-spacing-1 ellipsis" style="line-height: 1; font-size: 0.6rem;">
              {{ productionStore.machineSector }}
            </div>
            <div class="row items-center no-wrap q-mt-xs">
              <div class="text-h6 text-weight-bolder lh-small text-white q-mr-sm ellipsis">
                {{ productionStore.machineName }}
              </div>
              <q-badge rounded :class="statusBgClass" class="shadow-2 text-white q-py-xs q-px-sm text-caption no-wrap">
                <q-icon :name="statusIcon" color="white" class="q-mr-xs" size="14px" />
                {{ displayStatus }}
              </q-badge>
            </div>
          </div>
        </div>
        
        
        <q-space />
        
<div class="row items-center q-gutter-x-sm q-mr-md">
  <q-badge :color="isOnline ? 'positive' : 'negative'" class="q-pa-xs shadow-1">
    <q-icon :name="isOnline ? 'wifi' : 'wifi_off'" size="14px" />
    <span class="q-ml-xs text-bold">{{ isOnline ? 'ONLINE' : 'OFFLINE' }}</span>
  </q-badge>

  <q-chip 
    v-if="pendingSyncCount > 0" 
    dense 
    color="orange-9" 
    text-color="white" 
    icon="sync" 
    class="animate-pulse"
  >
    {{ pendingSyncCount }} Pendentes
    <q-tooltip>Dados aguardando conexão para envio ao SAP</q-tooltip>
  </q-chip>
</div>

<div class="row items-center no-wrap q-gutter-x-sm">
          <div class="row items-center no-wrap bg-white text-dark q-py-xs q-px-sm rounded-borders shadow-2" style="height: 42px; border-radius: 10px;">
            <q-avatar size="28px" class="shadow-1 vemag-bg-primary text-white" icon="person" font-size="18px" />
            
            <div class="column items-start justify-center q-ml-sm mobile-hide" style="line-height: 1.1; max-width: 120px;">
              <div class="text-caption text-weight-bold vemag-text-primary text-uppercase" style="font-size: 0.55rem;">OPERADOR</div>
              <div class="text-caption text-grey-9 text-weight-bold ellipsis full-width">
                {{ productionStore.currentOperator?.full_name || productionStore.currentOperatorBadge || '---' }}
              </div>
            </div>

            
            
            <q-separator vertical inset class="q-mx-sm bg-grey-4" />
            
            <div class="text-h6 font-monospace vemag-text-primary text-weight-bold no-wrap" style="margin-top: 1px;">
              {{ timeDisplay }}
            </div>
          </div>
          
          <q-btn flat round icon="logout" class="text-white" size="md" padding="xs" @click="handleLogout">
              <q-tooltip>Sair do Sistema</q-tooltip>
          </q-btn>
        </div>

      </q-toolbar>
      <q-linear-progress :value="1" color="green" class="q-mt-none" size="4px" />
    </q-header>

    <q-page-container class="full-height">
      <q-page class="q-pa-sm full-height column no-wrap">
        
        <div v-if="!productionStore.activeOrder" class="col flex flex-center column">
          <q-card class="q-pa-lg text-center shadow-10 bg-white" style="border-radius: 20px; max-width: 500px; width: 90%;">
            <div class="vemag-bg-light q-pa-md rounded-borders inline-block q-mb-md">
               <q-icon name="qr_code_scanner" size="60px" class="vemag-text-primary" />
            </div>
            <div class="text-h4 text-weight-bolder vemag-text-primary q-mb-sm">Aguardando O.P.</div>
            <div class="text-subtitle1 text-grey-7 q-mb-lg">A máquina está parada.<br>Selecione uma opção:</div>
            
            <div class="column q-gutter-y-md">
                <q-btn push rounded color="blue-grey-9" text-color="white" class="full-width shadow-3" size="18px" padding="md" icon="list_alt" label="SELECIONAR DA LISTA" @click="openOpListDialog" />
                <div class="text-caption text-grey-5">- OU -</div>
                <q-btn push rounded class="vemag-bg-primary text-white full-width shadow-4" size="18px" padding="md" icon="photo_camera" label="LER QR CODE" @click="simulateOpScan" />
            </div>
          </q-card>
        </div>

        

        <div v-else class="col row q-col-gutter-sm no-wrap items-stretch content-stretch">

          
          <div class="col-9 column no-wrap q-gutter-y-sm">
            
            <q-card class="col-auto q-px-md q-py-sm bg-white shadow-2" style="border-radius: 12px; border-top: 5px solid #008C7A;">
    <div class="row items-center justify-between no-wrap">
        <div class="row items-center q-gutter-x-sm">
            <q-badge color="orange-10" label="PRODUÇÃO" class="text-bold shadow-1" />
            
            <div class="text-h6 text-weight-bolder text-primary ellipsis" style="max-width: 350px;">
                {{ productionStore.activeOrder.part_name }}
            </div>
            
            <div class="column q-ml-md" style="line-height: 1.2;">
  <div class="text-subtitle1 text-weight-bold text-dark row items-baseline">
     <span 
       class="text-caption text-weight-bolder q-mr-xs" 
       :class="String(productionStore.activeOrder.code).startsWith('OS-') ? 'text-blue-9' : 'text-orange-9'"
       style="font-size: 1em; letter-spacing: 1px;"
     >
       {{ String(productionStore.activeOrder.code).startsWith('OS-') ? 'O.S:' : 'O.P:' }}
     </span>
     {{ productionStore.activeOrder.custom_ref || productionStore.activeOrder.code }}
  </div>
</div>
        </div>

        <div class="row items-center q-gutter-x-md">
            <div class="column items-end">
                <div class="text-overline text-grey-7" style="line-height: 1;">META TOTAL</div>
                <div class="text-subtitle1 text-weight-bold">
                    {{ productionStore.activeOrder.produced_quantity }} / {{ productionStore.activeOrder.target_quantity }} {{ productionStore.activeOrder.uom }}
                </div>
            </div>
            <q-circular-progress
                show-value font-size="10px"
                :value="((productionStore.activeOrder.produced_quantity || 0) / (productionStore.activeOrder.target_quantity || 1)) * 100"
                size="35px" :thickness="0.25" color="orange-8" track-color="grey-3" class="text-bold"
            >
                {{ Math.round(((productionStore.activeOrder.produced_quantity || 0) / (productionStore.activeOrder.target_quantity || 1)) * 100) }}%
            </q-circular-progress>
            
            </div>
    </div>
</q-card>

            <q-card class="col column no-wrap overflow-hidden shadow-6 bg-white" style="border-radius: 12px; border-left: 10px solid #008C7A;">
              
              <div class="col-auto bg-grey-2 q-px-md q-py-xs border-bottom-light row items-center justify-between" v-if="productionStore.currentActiveStep">
  <div class="row items-center">
      <template v-if="Number(productionStore.currentActiveStep.seq) === 999">
        <q-badge color="red-10" text-color="white" class="q-mr-md q-py-xs q-px-sm shadow-2 text-bold">
          <q-icon name="warning" size="14px" class="q-mr-xs" />
          ETAPA FORA DO ROTEIRO (IMPREVISTA)
        </q-badge>
      </template>
      <template v-else>
        <div class="text-subtitle2 text-grey-7 q-mr-sm text-weight-bold">#{{ productionStore.currentActiveStep.seq }}</div>
      </template>
      
      <div class="text-subtitle1 text-weight-bold ellipsis">{{ productionStore.currentActiveStep.name }}</div>
  </div>
  <q-chip square dense color="blue-grey-9" text-color="white" icon="precision_manufacturing" :label="productionStore.currentActiveStep.resource" class="text-caption" />
</div>
              <div class="col scroll bg-white q-pa-md relative-position">
                 <div class="row items-center q-mb-sm border-bottom-light q-pb-xs">
                    <q-icon name="menu_book" size="20px" class="text-primary q-mr-sm" /> 
                    <div class="text-subtitle2 text-weight-bold text-primary">INSTRUÇÕES DE TRABALHO</div>
                 </div>
                 <div class="text-body1 text-grey-10" style="white-space: pre-wrap; line-height: 1.6;">
                    {{ productionStore.currentActiveStep?.description || 'Nenhuma instrução disponível para esta etapa.' }}
                 </div>
              </div>

              <q-separator />

              <q-card-actions class="col-auto q-pa-sm bg-grey-1 row items-center justify-between">
    <div class="row items-center q-gutter-x-md q-ml-sm">
        <div class="column">
          <div class="text-caption text-grey-7 text-uppercase text-weight-bold" style="font-size: 0.6rem; line-height: 1;">Tempo Estimado</div>
          <div class="row items-center text-primary">
              <q-icon name="timer" size="18px" class="q-mr-xs" />
              <div class="text-h6 text-weight-bolder font-monospace">
                  {{ productionStore.currentActiveStep?.timeEst || 0 }}h
              </div>
          </div>
        </div>
    </div>
    
    <q-btn 
      push dense
      color="blue-grey-9" 
      text-color="white"
      icon="image" 
      label="VER DESENHO" 
      class="q-px-md shadow-2"
      @click="openDrawing"
    >
        <q-tooltip>Visualizar Desenho Técnico</q-tooltip>
    </q-btn>
</q-card-actions>
            </q-card>
          </div>

          <div class="col-3 column no-wrap q-gutter-y-sm">
            
            <q-card class="col-auto bg-white text-center q-py-sm relative-position shadow-3" style="border-radius: 12px;">
               <div class="row items-center justify-center q-gutter-x-sm">
                  <q-icon name="timer" class="vemag-text-secondary" size="24px" />
                  <div class="text-subtitle1 vemag-text-primary text-uppercase font-weight-bold">Tempo no Estado</div>
               </div>
               <div class="text-h3 text-weight-bolder font-monospace q-my-xs text-dark">{{ elapsedTime }}</div>
               <q-linear-progress stripe query :class="statusTextClass" size="6px" class="q-mt-xs absolute-bottom" />
            </q-card>

            <div class="col relative-position">
               <q-btn 
                  class="fit shadow-6 hover-scale-producing" 
                  :class="getButtonClass" 
                  push :loading="isLoadingAction"
                  style="border-radius: 20px;"
                  @click="handleMainButtonClick"
               >
                  <div class="column items-center justify-center full-height">
                    <q-icon size="60px" :name="isPaused ? 'play_arrow' : (normalizedStatus === 'EM OPERAÇÃO' ? 'pause_circle' : 'play_circle_filled')" />
                    <div class="text-h3 text-weight-bolder q-mt-sm">
                        {{ isPaused ? 'RETOMAR' : (normalizedStatus === 'EM OPERAÇÃO' ? 'PAUSAR' : 'INICIAR') }}
                    </div>
                  </div>
               </q-btn>
            </div>

            <div class="col-auto row q-col-gutter-x-sm" style="height: 90px;">
               <div class="col-6">
                  <q-btn 
                    class="full-width full-height shadow-3 hover-scale"
                    :class="productionStore.isInSetup ? 'bg-purple-9 text-white' : 'bg-blue-grey-2 text-blue-grey-9'"
                    push style="border-radius: 12px;" 
                    :loading="isLoadingAction"
                    @click="handleSetupClick"
                  >
                    <div class="column items-center justify-center">
                        <q-icon :name="productionStore.isInSetup ? 'check_circle' : 'build'" size="28px" class="q-mb-xs" />
                        <div class="text-caption text-weight-bold">{{ productionStore.isInSetup ? 'FIM SETUP' : 'SETUP' }}</div>
                    </div>
                  </q-btn>
               </div>
               <div class="col-6">
                  <q-btn 
                    class="full-width full-height shadow-3 hover-scale vemag-bg-secondary text-white"
                    push style="border-radius: 12px;"
                    @click="isAndonDialogOpen = true"
                  >
                    <div class="column items-center justify-center">
                        <q-icon name="notifications_active" size="28px" class="q-mb-xs" />
                        <div class="text-caption text-weight-bold">AJUDA</div>
                    </div>
                  </q-btn>
               </div>
            </div>

            <div class="col-auto">
               <q-btn 
                  class="full-width shadow-4" color="red-10" text-color="white"
                  push size="lg" icon="stop_circle" label="FINALIZAR O.P."
                  style="border-radius: 16px; min-height: 65px;"
                  @click="confirmFinishOp"
               />
            </div>
          </div>
        </div>
      </q-page>
    </q-page-container>

    <q-dialog v-model="showOpList" maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card>
        <q-bar class="vemag-bg-primary text-white">
          <q-icon name="list" />
          <div class="text-h6 q-ml-sm">Ordens de Produção Liberadas (SAP)</div>
          <q-space />
          <q-btn dense flat icon="close" v-close-popup />
        </q-bar>
        <q-card-section class="q-pa-none">
          <q-table :rows="openOps" :columns="opColumns" row-key="op_number" :loading="loadingOps" flat bordered separator="cell">
            <template v-slot:body="props">
              <q-tr @click="selectOp(props.row)" class="cursor-pointer hover-bg-grey-3">
                
                <q-td key="op_number" :props="props">
  <template v-if="String(props.row.op_number).startsWith('OS-')">
    <div class="text-weight-bold text-subtitle1">{{ props.row.op_number }}</div>
    <div class="text-caption text-grey-7">{{ props.row.custom_ref }}</div>
  </template>

  <template v-else>
    <div class="text-weight-bold text-subtitle1">{{ props.row.custom_ref || props.row.op_number }}</div>
    <div v-if="props.row.custom_ref" class="text-caption text-grey-7">DocNum: {{ props.row.op_number }}</div>
  </template>
</q-td>

                <q-td key="part_name" :props="props">
                  <div class="text-weight-medium">{{ props.row.part_name }}</div>
                  <div class="text-caption text-grey-6">{{ props.row.item_code }}</div>
                </q-td>

                <q-td key="planned_qty" :props="props" class="text-center text-weight-bold">
                  {{ props.row.planned_qty }} {{ props.row.uom }}
                </q-td>
                
                <q-td key="action" :props="props" class="text-center">
                  <q-btn round color="secondary" icon="arrow_forward" size="sm" />
                </q-td>

              </q-tr>
            </template>
          </q-table>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isShiftChangeDialogOpen" persistent>
      <q-card class="q-pa-md text-center" style="width: 400px; border-radius: 16px;">
        <q-icon name="groups" size="60px" color="primary" class="q-mb-sm" />
        <div class="text-h5 text-weight-bold">Troca de Turno</div>
        <div class="text-subtitle1 text-grey-8 q-my-md">A máquina vai parar ou o próximo operador assume imediatamente?</div>
        
        <div class="column q-gutter-y-md">
           <q-btn 
             push color="positive" size="lg" icon="autorenew" 
             label="CONTINUA RODANDO" 
             @click="executeShiftChange(true)" 
           />
           
           <q-separator />
           
           <q-btn 
             flat color="negative" icon="pause" 
             label="VAI PARAR A MÁQUINA" 
             @click="executeShiftChange(false)" 
           />
        </div>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isDrawingDialogOpen" maximized transition-show="slide-up" transition-hide="slide-down">
        <q-card class="bg-grey-10 text-white column">
            <q-bar class="bg-grey-9 q-pa-sm z-top" style="height: 60px;">
                <q-icon name="picture_as_pdf" size="24px" />
                <div class="text-h6 q-ml-md">Desenho: {{ productionStore.activeOrder?.part_code }}</div>
                <q-space /><q-btn dense flat icon="close" size="20px" v-close-popup />
            </q-bar>
            <q-card-section class="col q-pa-none bg-grey-3">
                <iframe v-if="drawingUrl" :src="drawingUrl" class="fit" style="border: none;"></iframe>
            </q-card-section>
        </q-card>
    </q-dialog>

    <q-dialog v-model="isStopDialogOpen" persistent maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-grey-2 column">
        <q-toolbar class="bg-white text-dark q-py-md shadow-2 z-top">
          <q-toolbar-title class="text-weight-bold text-h6 row items-center">
            <q-icon name="warning" color="warning" size="30px" class="q-mr-md"/> SELECIONE O MOTIVO
          </q-toolbar-title>
          <q-btn flat round icon="close" size="lg" v-close-popup />
        </q-toolbar>
        <q-card-section class="col column q-pa-none">
            <div class="q-pa-md"><q-input v-model="stopSearch" outlined bg-color="white" placeholder="Pesquisar..." dense autofocus clearable /></div>
            <div class="col scroll q-px-md q-pb-md">
               <div class="row q-col-gutter-md">
                  <div v-for="(reason, idx) in filteredStopReasons" :key="idx" class="col-12 col-sm-6 col-md-4">
  <q-btn 
    flat bordered 
    class="full-width reason-card" 
    :class="{ 
      'highlight-shift': reason.code === '111', 
      'highlight-maintenance': reason.requiresMaintenance 
    }"
    @click="handleSapPause(reason)"
  >
    <div class="row items-center no-wrap full-width q-pa-sm">
      <q-avatar 
        size="48px" 
        :color="reason.code === '111' ? 'orange-9' : (reason.requiresMaintenance ? 'red-10' : 'grey-3')" 
        :text-color="reason.code === '111' || reason.requiresMaintenance ? 'white' : 'grey-9'"
        :class="{ 'pulse-animation': reason.code === '111' || reason.requiresMaintenance }"
      >
        <q-icon 
          :name="reason.code === '111' ? 'groups' : (reason.requiresMaintenance ? 'engineering' : 'pause')" 
          size="28px" 
        />
      </q-avatar>

      <div class="column q-ml-md text-left">
        <div 
          class="text-subtitle1 text-weight-bolder" 
          :class="{ 'text-orange-10': reason.code === '111', 'text-red-10': reason.requiresMaintenance }"
        >
          {{ reason.label.toUpperCase() }}
        </div>
        <div v-if="reason.isSpecial" class="text-caption text-grey-6" style="line-height: 1;">Ação Prioritária</div>
      </div>
    </div>
  </q-btn>
                  </div>
               </div>
            </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isAndonDialogOpen" transition-show="scale" transition-hide="scale">
      <q-card style="width: 700px; max-width: 95vw; border-radius: 20px;">
        <q-card-section class="vemag-bg-primary text-white row items-center justify-between q-pa-md">
          <div class="text-h6 text-weight-bold row items-center"><q-icon name="campaign" size="30px" class="q-mr-sm" /> Central de Ajuda (Andon)</div>
          <q-btn icon="close" flat round size="md" v-close-popup />
        </q-card-section>
        <q-card-section class="q-pa-lg">
          <div class="row q-col-gutter-md">
            <div v-for="opt in andonOptions" :key="opt.label" class="col-6 col-md-4">
              <q-btn push class="full-width full-height column flex-center q-pa-md shadow-3 hover-scale" :class="`bg-${opt.color} text-white`" style="border-radius: 16px; min-height: 100px;" @click="confirmAndonCall(opt.label)">
                <q-icon :name="opt.icon" size="36px" class="q-mb-sm" />
                <div class="text-subtitle1 text-weight-bold">{{ opt.label }}</div>
              </q-btn>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { Notify, Loading, useQuasar } from 'quasar';
import { useProductionStore } from 'stores/production-store';
import { storeToRefs } from 'pinia';
import { ProductionService } from 'src/services/production-service';
import { useAuthStore } from 'stores/auth-store';
import { api } from 'boot/axios'; 
import { db } from 'src/db/offline-db';

import { getOperatorName } from 'src/data/operators'; 
import { getSapOperation, SAP_OPERATIONS_MAP } from 'src/data/sap-operations'; 
import { SAP_STOP_REASONS } from 'src/data/sap-stops';
import type { SapStopReason } from 'src/data/sap-stops';
import { ANDON_OPTIONS } from 'src/data/andon-options';

const router = useRouter();
const $q = useQuasar();
const productionStore = useProductionStore();
const authStore = useAuthStore();
const { activeOrder } = storeToRefs(productionStore); 
const isShiftChangeDialogOpen = ref(false);
const logoPath = ref('/Logo-Oficial.png');
const isLoadingAction = ref(false);
const opNumberToSend = computed(() => {
  if (!productionStore.activeOrder) return '';
  const order = productionStore.activeOrder;
  if (order.is_service) {
    return String(order.code); 
  }
  return order.custom_ref || order.code;
});

const isPaused = ref(false);
const currentPauseObj = ref<{
  startTime: Date;
  reasonCode: string;
  reasonLabel: string;
} | null>(null);

const isStopDialogOpen = ref(false);
const isAndonDialogOpen = ref(false);
const isDrawingDialogOpen = ref(false);
const drawingUrl = ref('');
const showOpList = ref(false);
const loadingOps = ref(false);

const stopSearch = ref('');
const statusStartTime = ref(new Date());
const currentTime = ref(new Date());
let timerInterval: ReturnType<typeof setInterval>;
const andonNote = ref('');

const andonOptions = ANDON_OPTIONS; 

// --- Tabela Atualizada ---
const openOps = ref([]);
const opColumns = [
  // MUDANÇA: Rótulo da coluna atualizado
  { name: 'op_number', label: 'Nome / Identificação', align: 'left', field: 'op_number', sortable: true },
  { name: 'part_name', label: 'Produto / Item', align: 'left', field: 'part_name', sortable: true },
  { name: 'planned_qty', label: 'Qtd', align: 'center', field: 'planned_qty' },
  { name: 'action', label: 'Selecionar', align: 'center' }
];

const viewedStepIndex = ref(0);

const currentViewedStep = computed(() => {
    if (activeOrder.value?.steps && activeOrder.value.steps.length > 0) {
        return activeOrder.value.steps[viewedStepIndex.value];
    }
    return { 
        seq: '---', 
        name: 'Aguardando Roteiro', 
        description: 'Buscando operações no SAP...', 
        resource: '---', 
        timeEst: 0 
    };
});

const isOnline = ref(window.navigator.onLine);

async function checkSyncQueue() {
  pendingSyncCount.value = await db.sync_queue.where('status').equals('pending').count();
  
  if (isOnline.value && pendingSyncCount.value > 0) {
    const items = await db.sync_queue.where('status').equals('pending').toArray();
    try {
      await api.post('/production/sync-batch', items);
      await db.sync_queue.clear(); 
      pendingSyncCount.value = 0;
      $q.notify({ type: 'positive', message: 'Sincronização concluída com sucesso!' });
    } catch (e) {
      console.error('Falha ao sincronizar lote', e);
    }
  }
}

window.addEventListener('online', () => { isOnline.value = true; checkSyncQueue(); });
window.addEventListener('offline', () => { isOnline.value = false; });

const elapsedTime = computed(() => {
   const diff = Math.max(0, Math.floor((currentTime.value.getTime() - statusStartTime.value.getTime()) / 1000));
   const h = Math.floor(diff / 3600).toString().padStart(2, '0');
   const m = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
   const s = (diff % 60).toString().padStart(2, '0');
   return `${h}:${m}:${s}`;
});
const timeDisplay = computed(() => currentTime.value.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }));

const normalizedStatus = computed(() => {
    if (productionStore.isInSetup) return 'MANUTENÇÃO';

    const raw = activeOrder.value?.status || '';
    const s = String(raw).trim().toUpperCase();
    
    const m = String(productionStore.currentMachine?.status || '').toUpperCase();

    if (['RUNNING', 'EM USO', 'EM OPERAÇÃO', 'IN_USE'].includes(s)) return 'EM OPERAÇÃO';
    
    if (['SETUP', 'MAINTENANCE', 'EM MANUTENÇÃO', 'MANUTENÇÃO'].includes(s) || 
        ['MAINTENANCE', 'EM MANUTENÇÃO', 'MANUTENÇÃO'].includes(m)) {
        return 'MANUTENÇÃO';
    }

    if (['PAUSED', 'PARADA', 'STOPPED', 'AVAILABLE', 'DISPONÍVEL'].includes(s)) return 'PARADA'; 
    
    return 'PARADA'; 
});
const displayStatus = computed(() => {
  if (productionStore.isInSetup) return 'EM PREPARAÇÃO (SETUP)';
  
  if (isPaused.value) return 'EM PAUSA - ' + (currentPauseObj.value?.reasonLabel || '');
  
  const rawStatus = activeOrder.value?.status?.toUpperCase() || '';
  if (['AVAILABLE', 'DISPONÍVEL', 'PENDING'].includes(rawStatus)) {
      return 'AGUARDANDO INÍCIO'; 
  }
  
  return normalizedStatus.value;
});

const statusBgClass = computed(() => {
  if (productionStore.isInSetup) return 'bg-purple-9 text-white';
  
  if (isPaused.value) return 'bg-orange-9 text-white'; 
  
  if (normalizedStatus.value === 'EM OPERAÇÃO') return 'bg-positive text-white';
  
  return 'bg-blue-grey-9 text-white';
});

const statusTextClass = computed(() => {
    if (isPaused.value) return 'text-warning';
    if (normalizedStatus.value === 'EM OPERAÇÃO') return 'vemag-text-primary';
    return 'text-negative';
});

const statusIcon = computed(() => {
    if (productionStore.isInSetup) return 'build_circle';
    if (isPaused.value) return 'pause_circle_filled'; 
    if (normalizedStatus.value === 'EM OPERAÇÃO') return 'autorenew';
    return 'hourglass_empty';
});
const getButtonClass = computed(() => {
  if (isPaused.value) return 'bg-orange-9 text-white'; 
  if (normalizedStatus.value === 'EM OPERAÇÃO') return 'vemag-bg-primary text-white';
  return 'bg-blue-grey-10 text-white';
});

const filteredStopReasons = computed(() => {
   if (!stopSearch.value) return SAP_STOP_REASONS;
   const needle = stopSearch.value.toLowerCase();
   return SAP_STOP_REASONS.filter(r => r.label.toLowerCase().includes(needle));
});


function resetTimer() { statusStartTime.value = new Date(); }

const pendingSyncCount = ref(0);
const isSyncing = ref(false);

async function syncOfflineData() {
  if (!isOnline.value || isSyncing.value) return;

  pendingSyncCount.value = await db.sync_queue.where('status').equals('pending').count();
  
  if (pendingSyncCount.value === 0) return;

  try {
    isSyncing.value = true;
    
    const items = await db.sync_queue.where('status').equals('pending').toArray();
    
    await api.post('/production/sync-batch', items);

    await db.sync_queue.where('status').equals('pending').delete();
    
    pendingSyncCount.value = 0;
    
    Notify.create({ 
      type: 'positive', 
      icon: 'cloud_done',
      message: 'Sincronização concluída!',
      caption: `${items.length} apontamentos enviados ao SAP.`,
      position: 'top'
    });

  } catch (error) {
    console.error('Falha na sincronização de lote:', error);
    Notify.create({ 
      type: 'negative', 
      message: 'Erro ao sincronizar dados offline. Tentaremos novamente em breve.' 
    });
  } finally {
    isSyncing.value = false;
  }
}

const updateOnlineStatus = () => {
  const status = window.navigator.onLine;
  isOnline.value = status;
  
  if (status) {
    void syncOfflineData();
  } else {
    Notify.create({ 
      group: 'network', 
      type: 'warning', 
      icon: 'cloud_off',
      message: 'Você está Offline. O sistema continuará salvando seus dados localmente.',
      timeout: 0, 
      actions: [{ label: 'Entendi', color: 'white' }]
    });
  }
};

async function openOpListDialog() {
  showOpList.value = true;
  loadingOps.value = true;
  try {
    openOps.value = await ProductionService.getOpenOrders();
  } catch (error) {
    console.error(error);
    $q.notify({ type: 'negative', message: 'Erro ao carregar OPs' });
  } finally {
    loadingOps.value = false;
  }
}
async function selectOp(op: any) {
  console.log(`🎯 [MES] Selecionando OP: ${op.op_number} - ${op.part_name}`);

  productionStore.activeOrder = {
    code: String(op.op_number),
    part_name: op.part_name,
    part_code: op.item_code,
    target_quantity: Number(op.planned_qty),
    uom: op.uom || 'pç',
    produced_quantity: 0,
    scrap_quantity: 0,
    status: 'PENDING',
    custom_ref: op.custom_ref || '',
    drawing: op.drawing || '',
    is_service: String(op.op_number).startsWith('OS-'),
    steps: op.steps || [] 
  };

  try {
    $q.loading.show({ 
      message: `Buscando roteiro técnico no SAP para ${op.op_number}...`,
      backgroundColor: 'teal-10'
    });

    await productionStore.loadOrderFromQr(String(op.op_number));
    
    const currentIndex = productionStore.currentStepIndex;

    if (currentIndex !== -1) {
      const step = productionStore.activeOrder.steps[currentIndex];
      
      if (Number(step.seq) === 999) {
        $q.notify({
          type: 'warning',
          icon: 'report_problem',
          message: 'ATENÇÃO: Esta máquina executará uma ETAPA IMPREVISTA (999).',
          caption: `Operação: ${step.name}`,
          timeout: 8000,
          position: 'top',
          actions: [{ label: 'Ciente', color: 'white' }]
        });
      } else {
        $q.notify({
          type: 'positive',
          icon: 'check_circle',
          message: `Etapa identificada: #${step.seq} - ${step.name}`,
          timeout: 3000
        });
      }
      
      viewedStepIndex.value = currentIndex;

    } else {
      $q.loading.hide();
      $q.notify({
        type: 'negative',
        icon: 'error',
        message: 'ERRO DE ROTEIRO',
        caption: `Nenhuma etapa (Prevista ou 999) deste item é compatível com esta máquina (${productionStore.machineName}).`,
        timeout: 10000
      });
      
      productionStore.activeOrder = null;
    }

  } catch (error) {
    console.error("❌ [MES] Falha crítica ao carregar roteiro:", error);
    $q.notify({ type: 'negative', message: 'Erro de comunicação com o servidor SAP.' });
    productionStore.activeOrder = null;
  } finally {
    showOpList.value = false;
    $q.loading.hide();
    if (typeof resetTimer === 'function') resetTimer(); 
  }
}

function openDrawing() {
  if (!productionStore.activeOrder?.part_code) {
      $q.notify({ type: 'warning', message: 'O.P. sem código de item definido.' });
      return;
  }

  const itemCode = productionStore.activeOrder.part_code;
  
  const baseUrl = 'http://localhost:8000'; 
  drawingUrl.value = `${baseUrl}/drawings/${encodeURIComponent(itemCode)}?t=${new Date().getTime()}`;
  
  isDrawingDialogOpen.value = true;
}
async function handleMainButtonClick() {
  if (isPaused.value) {
    await finishPauseAndResume();
    return;
  }

  if (normalizedStatus.value === 'EM OPERAÇÃO') {
      isStopDialogOpen.value = true;
      return;
  }

  if (productionStore.isInSetup) {
    $q.loading.show({ message: 'Encerrando Setup e iniciando produção...' });
    
    try {
      const now = new Date();
      const startSetup = statusStartTime.value;
      
      let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
      if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
      
      const operatorName = getOperatorName(String(badge).trim());
      const machineRes = productionStore.machineResource || '4.02.01';
      
      const setupPayload = {
          op_number: '', 
          position: '', operation: '', operation_desc: '',    
          resource_code: machineRes,
          resource_name: productionStore.machineName,
          operator_name: operatorName,
          operator_id: String(badge),
          vehicle_id: productionStore.machineId || 0,
          start_time: startSetup.toISOString(),
          end_time: now.toISOString(),
          stop_reason: '52', 
          stop_description: 'Setup' 
      };
      
      await ProductionService.sendAppointment(setupPayload);
      
      productionStore.activeOrder.status = 'PENDING'; 
      
    } catch (error) {
      console.error("Erro ao finalizar setup:", error);
      $q.notify({ type: 'negative', message: 'Falha ao encerrar setup no SAP.' });
      $q.loading.hide();
      return;
    }
  }
  
  isLoadingAction.value = true;
  try {
    await productionStore.startProduction();
    
    statusStartTime.value = new Date();
    isPaused.value = false;
    
    $q.notify({ type: 'positive', message: 'Produção Iniciada!', icon: 'play_arrow' });
  } catch (e) {
    console.error("Erro ao iniciar produção:", e);
    $q.notify({ type: 'negative', message: 'Erro ao registrar início de produção.' });
  } finally {
    isLoadingAction.value = false;
    $q.loading.hide();
  }
}

function handleSapPause(stopReason: SapStopReason) {
  const now = new Date();
  currentPauseObj.value = { 
    startTime: now, 
    reasonCode: stopReason.code, 
    reasonLabel: stopReason.label 
  };

  if (stopReason.code === '111' || stopReason.label.toLowerCase().includes('troca de turno')) {
      isStopDialogOpen.value = false;      
      isShiftChangeDialogOpen.value = true; 
      return; 
  }

  if (stopReason.requiresMaintenance) {
    isStopDialogOpen.value = false;
    void triggerCriticalBreakdown(); 
} else {
    void applyNormalPause(); 
}
}
async function applyNormalPause() {
  if (!currentPauseObj.value) return;

  $q.loading.show({ message: 'Encerrando apontamento atual...' });

  try {
    const now = new Date();
    const prodStart = new Date(statusStartTime.value);
    const order = productionStore.activeOrder;

    const badge = productionStore.activeOperator?.badge || productionStore.currentOperatorBadge;
    const operatorName = getOperatorName(String(badge || ''));
    const machineRes = productionStore.machineResource || '4.02.01';
    const machineName = productionStore.machineName || '';

    const position = currentViewedStep.value?.seq?.toString().padStart(3, '0') || '010';
    
    const sapData = getCurrentSapData(position);

    if (order && order.code) {
      let payload = {};

      if (order.is_service) {
        payload = {
          op_number: String(opNumberToSend.value),
          item_code: order.part_code || '',
          position: position,
          operation: sapData.code || '',
          resource_code: machineRes,
          operator_id: String(badge || '0'),
          DataSource: 'I',
          start_time: prodStart.toISOString(),
          end_time: now.toISOString(),
          part_description: order.part_name || '',
          operation_desc: sapData.description || '',
          resource_name: machineName,
          operator_name: operatorName,
          vehicle_id: productionStore.machineId
        };
      } else {
        payload = {
          op_number: String(opNumberToSend.value),
          position: position,
          operation: sapData.code || '',
          resource_code: machineRes,
          DataSource: 'I',
          operator_id: String(badge || '0'),
          start_time: prodStart.toISOString(),
          end_time: now.toISOString(),
          part_description: order.part_name || '',
          operation_desc: sapData.description || '',
          resource_name: machineName,
          operator_name: operatorName,
          vehicle_id: productionStore.machineId
        };
      }

      console.log(`📤 Enviando fechamento de ${order.is_service ? 'O.S' : 'O.P'}:`, payload);
      await ProductionService.sendAppointment(payload);
    }
    await productionStore.sendEvent('STATUS_CHANGE', { 
        new_status: 'STOPPED', 
        reason: currentPauseObj.value.reasonLabel 
    });

    isPaused.value = true;
    if (activeOrder.value) activeOrder.value.status = 'PAUSED';
    await productionStore.setMachineStatus('STOPPED');
    statusStartTime.value = new Date(); 

    $q.notify({ type: 'warning', message: 'Produção encerrada. Máquina em Pausa.' });
    isStopDialogOpen.value = false;

  } catch (error) {
    console.error("Erro ao pausar:", error);
    $q.notify({ type: 'negative', message: 'Erro ao comunicar com o servidor.' });
  } finally {
    $q.loading.hide();
  }
}


async function executeShiftChange(keepRunning: boolean) {
    isShiftChangeDialogOpen.value = false;
    const now = new Date();
    
    if (!keepRunning) {
        $q.loading.show({ message: 'Encerrando turno e parando máquina...' });
        
        try {
            currentPauseObj.value = {
                startTime: now,
                reasonCode: '111',
                reasonLabel: 'Troca de Turno'
            };

            await applyNormalPause(); 

            const badge = productionStore.activeOperator?.badge || productionStore.currentOperatorBadge;
            const operatorName = getOperatorName(String(badge || ''));
            const machineRes = productionStore.machineResource || '4.02.01';
            const machineName = productionStore.machineName || '';

            const stopPayload = {
                op_number: '',            
                resource_code: machineRes,
                resource_name: machineName,
                operator_id: String(badge),
                operator_name: operatorName,
                start_time: now.toISOString(),
                end_time: now.toISOString(), 
                stop_reason: '111',
                stop_description: 'Troca de Turno',
                DataSource: 'I'
            };
            
            console.log("📤 [SAP] Enviando Apontamento de Parada (Tipo 2):", stopPayload);
            await ProductionService.sendAppointment(stopPayload);

            await productionStore.logoutOperator('STOPPED', true); 

            await router.push({ name: 'machine-kiosk' });
            
            $q.notify({ 
                type: 'info', 
                icon: 'pause_circle', 
                message: 'Turno encerrado. Máquina pausada para troca.' 
            });

        } catch (error) {
            console.error("Erro ao encerrar turno com parada:", error);
            $q.notify({ type: 'negative', message: 'Erro ao processar troca de turno.' });
        } finally {
            $q.loading.hide();
        }
        return;
    }

    $q.loading.show({ message: 'Processando Troca de Turno no SAP...' });

    try {
        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
        if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
        
        const operatorName = getOperatorName(String(badge).trim());
        const machineRes = productionStore.machineResource || '4.02.01';
        const machineName = productionStore.machineName || '';

        const rawSeq = Number(currentViewedStep.value?.seq || 10);
        const stageStr = rawSeq === 999 ? '999' : Math.floor(rawSeq / 10 * 10).toString().padStart(3, '0');
        const sapData = getCurrentSapData(stageStr);

        if (activeOrder.value?.code) {
            const prodPayload = {
                op_number: String(opNumberToSend.value),
                position: stageStr,
                operation: sapData.code || '',
                operation_desc: sapData.description || '',
                part_description: activeOrder.value?.part_name || '',
                resource_code: machineRes,
                resource_name: machineName,
                operator_id: String(badge),
                operator_name: operatorName,
                start_time: statusStartTime.value.toISOString(),
                end_time: now.toISOString(),
                DataSource: 'I',
                stop_reason: '', 
                stop_description: ''
            };
            await ProductionService.sendAppointment(prodPayload);
        }

        const stopPayload = {
            op_number: '', 
            resource_code: machineRes,
            resource_name: machineName,
            operator_id: String(badge),
            operator_name: operatorName,
            start_time: now.toISOString(),
            end_time: now.toISOString(),
            stop_reason: '111', 
            stop_description: 'Troca de Turno',
            DataSource: 'I'
        };
        await ProductionService.sendAppointment(stopPayload);
        await productionStore.logoutOperator('RUNNING', true); 
        
        await router.push({ name: 'machine-kiosk' });
        $q.notify({ type: 'positive', message: 'Turno encerrado. Próximo operador pode assumir.' });

    } catch (error) {
        console.error("Erro na Troca de Turno quente:", error);
        $q.notify({ type: 'negative', message: 'Erro ao sincronizar com SAP.' });
    } finally {
        $q.loading.hide();
    }
}

async function triggerCriticalBreakdown() {
    if (!currentPauseObj.value) return;
    
    $q.loading.show({ 
        message: '🚨 Parando Máquina no SAP...', 
        backgroundColor: 'red-10'
    });

    try {
        const now = new Date();
        const productionStart = statusStartTime.value;
        const eventTime = now.toISOString();
        
        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
        if (!badge && authStore.user?.employee_id && authStore.user.role !== 'admin') {
             badge = authStore.user.employee_id;
        }
        const operatorName = getOperatorName(String(badge).trim());
        const machineRes = productionStore.machineResource || '4.02.01';
        
        const machineName = productionStore.machineName || '';

        if (activeOrder.value?.code) {
            const rawSeq = Number(currentViewedStep.value?.seq || 10);
            const stageStr = rawSeq === 999 ? '999' : Math.floor(rawSeq / 10 * 10).toString().padStart(3, '0');
            
            const sapData = getCurrentSapData(stageStr);

            const productionPayload = {
                op_number: String(opNumberToSend.value),
                position: stageStr,
                operation: sapData.code || '',        
                operation_desc: sapData.description || '', 
                part_description: activeOrder.value.part_name || '',
                item_code: activeOrder.value.part_code || '',
                service_code: '',
                DataSource: 'I',
                resource_code: machineRes,
                resource_name: machineName,            
                operator_name: operatorName || '',
                operator_id: String(badge),
                vehicle_id: productionStore.machineId || 0,
                start_time: productionStart.toISOString(),
                end_time: eventTime,
                stop_reason: '', 
                stop_description: '' 
            };

            console.log("📤 [1/2] Fechando Produção (Manutenção):", productionPayload);
            await ProductionService.sendAppointment(productionPayload);
        }

        const stopPayload = {
            op_number: '',
            position: '', operation: '', operation_desc: '',
            part_description: '', item_code: '', service_code: '',
            resource_code: machineRes,
            resource_name: machineName,                
            operator_name: operatorName || '',
            operator_id: String(badge),
            vehicle_id: productionStore.machineId || 0,
            DataSource: 'I',
            start_time: eventTime,
            end_time: eventTime, 
            stop_reason: currentPauseObj.value.reasonCode, 
            stop_description: 'Manutenção'
        };

        console.log("📤 [2/2] Registrando Parada de Recurso:", stopPayload);
        await ProductionService.sendAppointment(stopPayload);

        await productionStore.setMachineStatus('MAINTENANCE');
        await productionStore.finishSession();
        await productionStore.logoutOperator('MAINTENANCE');

        await router.push({ 
            name: 'machine-kiosk', 
            query: { 
                state: 'maintenance',
                last_operator: String(badge)
            } 
        });
        
        $q.notify({ type: 'warning', icon: 'build', message: 'Máquina parada para Manutenção.' });

    } catch (error) {
        console.error("Erro ao processar quebra de máquina:", error);
        $q.notify({ type: 'negative', message: 'Erro ao registrar parada no SAP.' });
    } finally {
        $q.loading.hide();
    }
}

async function finishPauseAndResume() {
  if (!currentPauseObj.value) return;
  
  $q.loading.show({ message: 'Registrando tempo de parada...' });
  
  try {
    const now = new Date();
    const pauseStart = new Date(statusStartTime.value); 
    
    const badge = productionStore.activeOperator?.badge || productionStore.currentOperatorBadge;
    const operatorName = getOperatorName(String(badge || ''));
    const machineRes = productionStore.machineResource || '4.02.01';
    const machineName = productionStore.machineName || '';

    const stopPayload = {
      stop_reason: String(currentPauseObj.value.reasonCode), 
      resource_code: machineRes,                             
      operator_id: String(badge || '0'),                     
      start_time: pauseStart.toISOString(),                  
      end_time: now.toISOString(),                           
      stop_description: currentPauseObj.value.reasonLabel,   
      resource_name: machineName,                            
      operator_name: operatorName,                           
      vehicle_id: productionStore.machineId                  
    };

    console.log("📤 Enviando Apontamento de Parada:", stopPayload);
    await ProductionService.sendAppointment(stopPayload);

    await productionStore.sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' });
    await productionStore.setMachineStatus('RUNNING'); 

    isPaused.value = false;
    currentPauseObj.value = null; 
    if (activeOrder.value) activeOrder.value.status = 'RUNNING';
    
    statusStartTime.value = new Date(); 
    
    $q.notify({ type: 'positive', message: 'Parada registrada. Produção retomada!' });

  } catch (error) {
    console.error("Erro ao retomar:", error);
    $q.notify({ type: 'negative', message: 'Erro ao registrar fim da parada.' });
  } finally {
    $q.loading.hide();
  }
}

function confirmFinishOp() {
  let badge = productionStore.currentOperatorBadge;

  if (!badge && authStore.user?.employee_id) {
      const role = authStore.user.role || '';
      if (role !== 'admin' && role !== 'manager') badge = authStore.user.employee_id;
  }

  if (!badge || badge.includes('@')) {
      $q.dialog({
        title: 'Identificação Obrigatória',
        message: 'Bipe seu crachá:',
        prompt: { model: '', type: 'text', isValid: val => val.length > 0 },
        cancel: true, persistent: true
      }).onOk(data => {
        productionStore.currentOperatorBadge = data;
        confirmFinishOp(); 
      });
      return; 
  }

  const operatorName = getOperatorName(String(badge).trim());

  $q.dialog({
    title: 'Finalizar O.P.',
    message: `Encerrar O.P. e liberar a máquina?`,
    cancel: true, persistent: true,
    ok: { label: 'Finalizar e Sair', color: 'negative', push: true }
  // eslint-disable-next-line @typescript-eslint/no-misused-promises
  }).onOk(async () => {
     $q.loading.show({ message: 'Enviando ao SAP e Finalizando...' });
     
     try {
       const endTime = new Date();
       
       const rawSeq = currentViewedStep.value?.seq || 999;
       const stageStr = rawSeq.toString().padStart(3, '0');
       
       const sapData = getCurrentSapData(stageStr);

       const machineRes = productionStore.machineResource || sapData.resourceCode || '4.02.01';
       const machineName = productionStore.machineName || sapData.resourceName || '';

       const payload = {
         op_number: String(opNumberToSend.value),
         service_code: '', 
         position: stageStr, 
         operation: sapData.code || '', 
         operation_desc: sapData.description || '',
         resource_code: machineRes, 
         DataSource: 'I',
         resource_name: machineName,
         part_description: activeOrder.value?.part_name || '', 
         operator_name: operatorName || '', 
         operator_id: String(badge),
         start_time: statusStartTime.value.toISOString(),
         end_time: endTime.toISOString(),
         item_code: activeOrder.value?.part_code || '', 
         stop_reason: '', 
         vehicle_id: productionStore.machineId || 0
       };

       console.log("📤 [FINALIZAR] Enviando O.P. final:", payload);
       await ProductionService.sendAppointment(payload);

       await productionStore.finishSession();
       await productionStore.setMachineStatus('AVAILABLE');
       await productionStore.logoutOperator();
       await router.push({ name: 'machine-kiosk' });

       $q.notify({ type: 'positive', message: 'O.P. Finalizada. Máquina Disponível!' });

     } catch (error) {
       console.error("Erro SAP:", error);
       $q.notify({ type: 'negative', message: 'Erro ao registrar no SAP.' });
     } finally {
       $q.loading.hide();
     }
  });
}

function getCurrentSapData(stageStr: string) {
  let sapData = getSapOperation(stageStr);

  if (stageStr === '999' || !sapData.code) {
    const step = currentViewedStep.value;
    if (step && step.resource && SAP_OPERATIONS_MAP[step.resource]) {
      sapData = SAP_OPERATIONS_MAP[step.resource];
    }
  }
  return sapData;
}

function handleLogout() {
  $q.dialog({ title: 'Sair', message: 'Fazer logoff?', cancel: true }).onOk(() => {
    void (async () => {
        await productionStore.logoutOperator();
        await router.push({ name: 'machine-kiosk' });
    })();
  });
}

async function simulateOpScan() {
  await productionStore.loadOrderFromQr('OP-TESTE-4500');
  resetTimer();
}

async function confirmAndonCall(sector: string) {
    isAndonDialogOpen.value = false;
    await productionStore.triggerAndon(sector, andonNote.value);
    andonNote.value = '';
}



async function handleSetupClick() {
  if (productionStore.isInSetup) {
      $q.dialog({
          title: 'Finalizar Setup',
          message: 'Deseja encerrar a preparação e VOLTAR A PRODUZIR agora?',
          cancel: true,
          persistent: true,
          ok: { label: 'Finalizar e Iniciar O.P.', color: 'positive', push: true }
      // eslint-disable-next-line @typescript-eslint/no-misused-promises
      }).onOk(async () => {
          $q.loading.show({ message: 'Enviando Setup e reiniciando produção...' });
          isLoadingAction.value = true;
          
          try {
              const now = new Date();
              const startSetup = statusStartTime.value; 

              let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
              if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
              
              const operatorName = getOperatorName(String(badge).trim());
              const machineRes = productionStore.machineResource || '4.02.01';
              const machineName = productionStore.machineName || '';

              const setupPayload = {
                  op_number: '', 
                  position: '', operation: '', operation_desc: '',    
                  part_description: '', item_code: '', service_code: '',
                  resource_code: machineRes,
                  resource_name: machineName, 
                  DataSource: 'I',
                  operator_name: operatorName || '',
                  operator_id: String(badge),
                  vehicle_id: productionStore.machineId || 0,
                  start_time: startSetup.toISOString(),
                  end_time: now.toISOString(),
                  stop_reason: '52', 
                  stop_description: 'Setup' 
              };
              await ProductionService.sendAppointment(setupPayload);

              await productionStore.toggleSetup();

              const step = currentViewedStep.value; 
              const startPayload = {
                op_number: String(productionStore.activeOrder.code),
                step_seq: String(step.seq || ''),
                machine_id: Number(productionStore.machineId),
                operator_badge: String(badge)
              };

              const response = await api.post('/production/session/start', startPayload);
              
              if (response.data.status === 'success') {
                statusStartTime.value = new Date();
                if (activeOrder.value) activeOrder.value.status = 'RUNNING';
                await productionStore.setMachineStatus('RUNNING');
                $q.notify({ type: 'positive', message: 'Setup registrado. Produção retomada!' });
              }

          } catch (error) {
              console.error("Erro na transição de Setup:", error);
              $q.notify({ type: 'negative', message: 'Erro ao processar fim de Setup.' });
          } finally {
              $q.loading.hide();
              isLoadingAction.value = false;
          }
      });
  } 
  
  else {
      isLoadingAction.value = true;
      try {
          const now = new Date();
          
          if (normalizedStatus.value === 'EM OPERAÇÃO' && activeOrder.value?.code) {
              $q.loading.show({ message: 'Encerrando produção para iniciar Setup...' });
              
              const productionStart = statusStartTime.value;
              let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
              if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
              
              const operatorName = getOperatorName(String(badge).trim());
              const machineRes = productionStore.machineResource || '4.02.01';
              const machineName = productionStore.machineName || '';

              const rawSeq = Number(currentViewedStep.value?.seq || 10);
              const stageStr = rawSeq === 999 ? '999' : Math.floor(rawSeq / 10 * 10).toString().padStart(3, '0');
              
              const sapData = getCurrentSapData(stageStr);

              const productionPayload = {
                  op_number: String(opNumberToSend.value),
                  position: stageStr,
                  operation: sapData.code || '',
                  operation_desc: sapData.description || '',
                  part_description: activeOrder.value.part_name || '',
                  item_code: activeOrder.value.part_code || '',
                  service_code: '',
                  DataSource: 'I',
                  resource_code: machineRes,
                  resource_name: machineName, 
                  operator_name: operatorName || '',
                  operator_id: String(badge),
                  vehicle_id: productionStore.machineId || 0,
                  start_time: productionStart.toISOString(),
                  end_time: now.toISOString(),
                  stop_reason: '', 
                  stop_description: '' 
              };
              
              console.log("📤 [SETUP] Fechando Produção para iniciar Setup:", productionPayload);
              await ProductionService.sendAppointment(productionPayload);
          }

          await productionStore.toggleSetup();
          await productionStore.setMachineStatus('MAINTENANCE'); 
          statusStartTime.value = new Date(); 
          
          $q.notify({ type: 'info', message: 'Produção salva. Modo Setup Iniciado.', icon: 'build' });
      } catch (e) {
          console.error("Erro ao iniciar setup:", e);
          $q.notify({ type: 'negative', message: 'Erro ao iniciar Setup.' });
      } finally {
          $q.loading.hide();
          isLoadingAction.value = false;
      }
  }
}
let scanBuffer = '';
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let scanTimeout: any = null;
const onKeydown = (e: KeyboardEvent) => {
    void handleGlobalKeydown(e);
};
async function handleGlobalKeydown(event: KeyboardEvent) {
  if ((event.target as HTMLElement).tagName === 'INPUT') return;

  if (event.key === 'Enter') {
      if (scanBuffer.length > 2) {
          const scannedBadge = scanBuffer.trim();
          $q.loading.show({ message: `Autenticando...` });
          try {
              await authStore.loginByBadge(scannedBadge);
              if (authStore.user?.employee_id) {
                  productionStore.currentOperatorBadge = authStore.user.employee_id;
                  $q.notify({ type: 'positive', message: `Olá, ${authStore.user.full_name}` });
              } else {
                  productionStore.currentOperatorBadge = scannedBadge;
              }
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          } catch (e) {
              $q.notify({ type: 'negative', message: 'Crachá inválido.' });
          } finally {
              $q.loading.hide();
              scanBuffer = '';
          }
      }
      scanBuffer = ''; 
  } else {
      if (event.key.length === 1) {
          scanBuffer += event.key;
          clearTimeout(scanTimeout);
          scanTimeout = setTimeout(() => { scanBuffer = ''; }, 2000);
      }
  }
}

onMounted(async () => {
  if (productionStore.currentStepIndex !== -1) {
    viewedStepIndex.value = productionStore.currentStepIndex;
  }

  timerInterval = setInterval(() => { 
    currentTime.value = new Date(); 
  }, 1000);

  resetTimer();

  window.addEventListener('keydown', onKeydown);
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);

  await syncOfflineData();

  if (!productionStore.currentOperatorBadge && authStore.user?.employee_id && authStore.user.role !== 'admin') {
      productionStore.currentOperatorBadge = authStore.user.employee_id;
  }
});

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown);
  window.removeEventListener('online', updateOnlineStatus);
  window.removeEventListener('offline', updateOnlineStatus);

  if (timerInterval) {
    clearInterval(timerInterval);
  }
});
</script>

<style>
.vemag-bg-primary { background-color: #008C7A !important; }
.vemag-text-primary { color: #008C7A !important; }
.vemag-bg-secondary { background-color: #66B8B0 !important; }
.vemag-text-secondary { color: #66B8B0 !important; }
.vemag-bg-light { background-color: #E0F2F1 !important; }
.bg-vemag-gradient { background: linear-gradient(135deg, #008C7A 0%, #00695C 100%); }
.bg-black-transparent { background-color: rgba(0,0,0,0.15); }
.hover-bg-grey-3:hover { background-color: #eeeeee; }
</style>

<style scoped>
.reason-card {
  border-radius: 12px;
  background: white;
  transition: all 0.3s ease;
  border: 1px solid #e0e0e0;
  min-height: 85px;
}

.reason-card:hover {
  background: #f5f5f5;
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

/* Destaque para os itens Especiais (Troca de Turno e Manutenção) */
.special-active {
  border: 2px solid #008C7A !important; /* Borda cor da marca */
  background: #f0fdfa !important;
}

/* Animação de pulsação discreta no ícone sinalizado */
.pulse-animation {
  animation: pulse-shadow 2s infinite;
}

@keyframes pulse-shadow {
  0% { box-shadow: 0 0 0 0 rgba(0, 140, 122, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(0, 140, 122, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 140, 122, 0); }
}

.lh-tight {
  line-height: 1.2;
}
.font-inter { font-family: 'Roboto', sans-serif; }
.maintenance-dialog {
  width: 550px; 
  max-width: 95vw; 
  border-radius: 24px; 
  overflow: hidden;
  background: #ffffff;
}

/* Pulsação do ícone de aviso para atrair atenção */
.pulse-animation {
  animation: pulse-red 2s infinite;
  box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7);
  border-radius: 50%;
}

@keyframes pulse-red {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 15px rgba(255, 255, 255, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
}

img, iframe {
  max-width: 100%;
}
/* Força o scroll se o conteúdo for maior que a tela mobile */
.q-page {
  min-height: auto !important;
}

/* Botão de confirmação com destaque */
.q-btn--push.text-weight-bolder {
  border: 1px solid rgba(255, 255, 255, 0.3);
}
.maintenance-card {
  width: 600px;
  max-width: 95vw;
  border-radius: 20px;
}

.sub-reason-btn {
  border-radius: 12px;
  height: 80px;
  border: 1px solid #e0e0e0;
  color: #616161;
  background: #fafafa;
  transition: all 0.2s ease;
}

.sub-reason-active {
  background: #ffebee !important;
  border: 2px solid #b71c1c !important;
  color: #b71c1c !important;
  transform: scale(1.03);
}

.letter-spacing-1 {
  letter-spacing: 1px;
}
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
.highlight-shift {
  border: 2px solid #ef6c00 !important; /* Laranja forte */
  background: #fff3e0 !important; /* Fundo laranja claríssimo */
  box-shadow: 0 4px 12px rgba(239, 108, 0, 0.2) !important;
}

/* Destaque para Manutenção */
.highlight-maintenance {
  border: 2px solid #b71c1c !important; /* Vermelho forte */
  background: #ffebee !important; /* Fundo vermelho claríssimo */
  box-shadow: 0 4px 12px rgba(183, 28, 28, 0.2) !important;
}

/* Animação para chamar atenção nos itens especiais */
.pulse-animation {
  animation: pulse-ring 2s infinite;
}

@keyframes pulse-ring {
  0% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0.2); }
  70% { box-shadow: 0 0 0 10px rgba(0, 0, 0, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0); }
}

.reason-card {
  height: 90px;
  border-radius: 15px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.reason-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 15px rgba(0,0,0,0.1);
}
</style>
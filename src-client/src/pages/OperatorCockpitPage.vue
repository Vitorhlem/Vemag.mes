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
    :class="(productionStore.activeOrder.is_service || String(productionStore.activeOrder.code).startsWith('OS-')) ? 'text-blue-9' : 'text-orange-9'"
    style="font-size: 1em; letter-spacing: 1px;"
  >
    {{ (productionStore.activeOrder.is_service || String(productionStore.activeOrder.code).startsWith('OS-')) ? 'O.S:' : 'O.P:' }}
  </span>
  
  {{ 
     (productionStore.activeOrder.is_service || String(productionStore.activeOrder.code).startsWith('OS-'))
     ? (productionStore.activeOrder.code) 
     : (productionStore.activeOrder.custom_ref || productionStore.activeOrder.code)
  }}
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

            <div class="col">
               <q-btn 
                 class="fit shadow-3 hover-scale vemag-bg-secondary text-white"
                 push 
                 style="border-radius: 12px;"
                 @click="isAndonDialogOpen = true"
               >
                 <div class="column items-center justify-center">
                     <q-icon name="notifications_active" size="60px" class="q-mb-md" />
                     <div class="text-h5 text-weight-bold">CHAMAR AJUDA</div>
                     <div class="text-caption text-white opacity-80">(Andon)</div>
                 </div>
               </q-btn>
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
  <q-card style="min-width: 350px">
    <q-card-section>
      <div class="text-h6 text-teal-9">Troca de Turno</div>
      <div class="text-subtitle2 text-grey-8">Como deseja prosseguir?</div>
    </q-card-section>

    <q-card-section class="q-pt-none">
      A máquina continuará produzindo durante a troca?
    </q-card-section>

    <q-card-actions align="right" class="text-primary">
      <q-btn flat label="Cancelar" v-close-popup color="grey" />
      
      <q-btn 
        flat 
        label="Não, Vai Parar" 
        color="orange" 
        @click="handleShiftChange(false)" 
      />

      <q-btn 
        push 
        label="Sim, Continua Rodando" 
        color="primary" 
        icon="autorenew"
        @click="handleShiftChange(true)" 
      />
    </q-card-actions>
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

        <div class="q-pa-md bg-white border-bottom-light">
            <q-banner rounded class="bg-red-1 text-center q-mb-sm shadow-1">
                <template v-slot:avatar>
                    <q-icon name="help_outline" color="red-10" />
                </template>
                <div class="text-subtitle1 text-red-10 text-weight-bold">O trabalho nesta etapa terminou?</div>
            </q-banner>
            
            <q-btn 
                push 
                color="red-10" 
                text-color="white" 
                class="full-width shadow-3" 
                size="lg" 
                padding="md"
                @click="confirmFinishOp"
            >
                <div class="row items-center justify-center full-width">
    <span class="text-weight-bolder q-mr-md">ENCERRAR ETAPA</span>
    <q-icon name="stop_circle" size="32px" />
</div>
            </q-btn>
        </div>

        <q-card-section class="col column q-pa-none">
            <div class="q-pa-md">
                <q-input v-model="stopSearch" outlined bg-color="white" placeholder="Pesquisar motivo de parada..." dense autofocus clearable />
            </div>
            
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
      <q-card style="width: 800px; max-width: 95vw; border-radius: 20px;">
        
        <q-card-section class="vemag-bg-primary text-white row items-center justify-between q-pa-md">
          <div class="text-h6 text-weight-bold row items-center">
            <q-icon name="campaign" size="30px" class="q-mr-sm" /> 
            Central de Ajuda (Andon)
          </div>
          <q-btn icon="close" flat round size="md" v-close-popup />
        </q-card-section>

        <q-card-section class="q-pt-md q-px-lg">
            <div class="text-subtitle2 text-grey-7 q-mb-xs">Observação / Detalhe do Problema (Opcional):</div>
            <q-input 
              v-model="andonNote" 
              outlined 
              type="textarea" 
              rows="2"
              placeholder="Ex: Falta parafuso M8..." 
              bg-color="grey-1"
              class="text-h6"
            />
        </q-card-section>

        <q-separator inset />

        <q-card-section class="q-pa-lg">
          <div class="text-subtitle2 text-center text-grey-8 q-mb-md text-uppercase">Selecione o setor para chamar:</div>
          
          <div class="row q-col-gutter-md">
            <div v-for="opt in andonOptions" :key="opt.label" class="col-6 col-md-3">
              <q-btn 
                push 
                class="full-width full-height column flex-center q-pa-sm shadow-3 hover-scale" 
                :class="`bg-${opt.color} text-white`" 
                style="border-radius: 16px; min-height: 90px;" 
                @click="confirmAndonCall(opt.label)"
              >
                <q-icon :name="opt.icon" size="32px" class="q-mb-xs" />
                <div class="text-subtitle2 text-weight-bold" style="line-height: 1.1;">{{ opt.label }}</div>
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
import { Notify, useQuasar } from 'quasar';
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
const isSocketConnected = ref(false);
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
  
  const codeStr = String(order.code || '').trim();
  const customRef = String(order.custom_ref || '').trim();
  const opNum = String(order.op_number || '').trim();

  // 1. É ORDEM DE SERVIÇO? (Começa com OS- ou tem a flag)
  // Regra: Enviar o código completo (ex: "OS-4595-1").
  // O Backend vai detectar "OS-", cortar o prefixo e o sufixo, e sobrar o DocNum (4595).
  if (order.is_service || codeStr.startsWith('OS-')) {
     // Se por acaso o código estiver limpo "4595", forçamos o prefixo para o backend entender
     if (!codeStr.startsWith('OS-')) return `OS-${codeStr}`;
     return codeStr; 
  }

  // 2. É ORDEM DE PRODUÇÃO (O.P.)
  // Regra: CustomRef (que na O.P é o DocNum) > OpNumber > Code
  // Proteção: Se custom_ref tiver "Cliente:", ignoramos (pois é nome, não número)
  if (customRef.toUpperCase().includes('CLIENTE:')) {
     return opNum || codeStr;
  }

  return customRef || opNum || codeStr;
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

window.addEventListener('online', () => { isOnline.value = true; void checkSyncQueue(); });
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
  // Pega o status direto do objeto da máquina (vindo do Backend/WebSocket)
  const s = productionStore.currentMachine?.status || '';

  if (s === 'Em uso') return 'EM OPERAÇÃO';
  if (s === 'Produção Autônoma') return 'AUTÔNOMO';
  if (s === 'Setup') return 'SETUP';
  if (s === 'Em manutenção') return 'MANUTENÇÃO';
  if (s === 'Parada') return 'PARADA';
  if (s === 'Ociosidade') return 'OCIOSO'; // Novo estado explícito

  return 'DISPONÍVEL';
});
const displayStatus = computed(() => {
  // Se estiver em pausa manual (tela vermelha aberta ou aguardando), mostra o motivo
  if (isPaused.value) return 'PAUSADA - ' + (currentPauseObj.value?.reasonLabel || '');
  
  // Senão, mostramos o status real da máquina
  return normalizedStatus.value;
});
const statusBgClass = computed(() => {
  const s = normalizedStatus.value;
  if (s === 'SETUP') return 'bg-purple-9 text-white';
  if (s === 'MANUTENÇÃO') return 'bg-red-10 text-white';
  if (s === 'AUTÔNOMO') return 'bg-blue-6 text-white'; // Azul claro diferenciado
  if (s === 'EM OPERAÇÃO') return 'bg-positive text-white';
  if (s === 'PARADA') return 'bg-orange-9 text-white';
  if (s === 'OCIOSO') return 'bg-grey-7 text-white'; // Cinza para ocioso
  
  return 'bg-blue-grey-9 text-white'; // Disponível
});

const statusTextClass = computed(() => {
  const s = normalizedStatus.value;
  if (s === 'EM OPERAÇÃO' || s === 'AUTÔNOMO') return 'vemag-text-primary';
  if (s === 'SETUP') return 'text-purple-9';
  if (s === 'MANUTENÇÃO') return 'text-red-10';
  return 'text-grey-8';
});

const statusIcon = computed(() => {
  const s = normalizedStatus.value;
  if (s === 'SETUP') return 'build_circle';
  if (s === 'MANUTENÇÃO') return 'engineering';
  if (s === 'AUTÔNOMO') return 'smart_toy'; // Ícone de robô para autônomo
  if (s === 'EM OPERAÇÃO') return 'autorenew';
  if (s === 'PARADA') return 'pause_circle_filled';
  return 'hourglass_empty';
});

const getButtonClass = computed(() => {
  const s = normalizedStatus.value;
  if (s === 'EM OPERAÇÃO' || s === 'AUTÔNOMO') return 'vemag-bg-primary text-white';
  if (isPaused.value || s === 'PARADA') return 'bg-orange-9 text-white';
  return 'bg-blue-grey-10 text-white';
});

const filteredStopReasons = computed(() => {
   if (!stopSearch.value) return SAP_STOP_REASONS;
   const needle = stopSearch.value.toLowerCase();
   return SAP_STOP_REASONS.filter(r => r.label.toLowerCase().includes(needle));
});


function resetTimer() { statusStartTime.value = new Date(); }

function openShiftChangeDialog() {
  console.log("🔄 Abrindo diálogo de troca de turno..."); // Debug para ver se o botão funciona
  isShiftChangeDialogOpen.value = true;
}

async function handleShiftChange(keepRunning: boolean) {
    isShiftChangeDialogOpen.value = false;
    
    // Chama a função da store que acabamos de criar
    const success = await productionStore.executeShiftChange(keepRunning);
    
    if (success) {
        // Redireciona para a tela de Login/Descanso
        router.push({ name: 'machine-kiosk' });
    }
}

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
// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function selectOp(op: any) {
  // 1. Apenas define os dados básicos
  productionStore.activeOrder = {
    code: String(op.op_number),
    part_name: op.part_name,
    part_code: op.item_code,
    target_quantity: Number(op.planned_qty),
    uom: op.uom || 'pç',
    produced_quantity: 0,
    scrap_quantity: 0,
    status: 'PENDING',
    steps: op.steps || [] 
  };

  // 2. Delega todo o processo de início (Session Start + Setup Log) para a Store
  // Isso evita o "double log" no momento da seleção
  await productionStore.loadOrderFromQr(String(op.op_number));
  
  connectWebSocket();
  if (productionStore.currentStepIndex !== -1) {
    viewedStepIndex.value = productionStore.currentStepIndex;
  }
  
  showOpList.value = false;
  resetTimer();
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
  // 1. Se estiver pausado (tela vermelha ou sem motivo), tenta retomar
  if (isPaused.value || normalizedStatus.value === 'PARADA') {
    await finishPauseAndResume();
    return;
  }

  // 2. Se já estiver rodando, o botão serve para PAUSAR (abrir diálogo)
  if (normalizedStatus.value === 'EM OPERAÇÃO') {
      isStopDialogOpen.value = true;
      return;
  }

  // 3. Se estiver em Setup, finaliza o Setup antes de iniciar produção
  if (normalizedStatus.value === 'SETUP' || productionStore.isInSetup) {
    $q.loading.show({ message: 'Encerrando Setup e iniciando produção...' });
    
    try {
      const now = new Date();
      const startSetup = statusStartTime.value;
      
      let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
      if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
      
      const operatorName = getOperatorName(String(badge).trim());
      const machineRes = productionStore.machineResource || '4.02.01';
      
      // Envia apontamento de SETUP para o SAP (Tipo 2 - Parada Planejada)
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
          stop_reason: '52', // Código SAP para Setup
          stop_description: 'Setup',
          DataSource: 'I',
          U_TipoDocumento: '2'
      };
      
      await ProductionService.sendAppointment(setupPayload);
      
      // Sai do modo setup na store
      await productionStore.toggleSetup(); 
      productionStore.activeOrder.status = 'PENDING'; 
      
    } catch (error) {
      console.error("Erro ao finalizar setup:", error);
      $q.notify({ type: 'negative', message: 'Falha ao encerrar setup no SAP.' });
      $q.loading.hide();
      return;
    }
  }
  
  // 4. Inicia a Produção
  isLoadingAction.value = true;
  try {
    // startProduction agora deve enviar status '1' ou 'RUNNING' ao backend
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

async function handleSapPause(stopReason: any) {
  console.log(`🛑 [UI] Motivo Selecionado: ${stopReason.label} (${stopReason.code})`);

  // 1. Atualiza o objeto local (apenas visual e para o payload de retorno futuro)
  if (!currentPauseObj.value) {
      currentPauseObj.value = { 
          startTime: new Date(), 
          reasonCode: stopReason.code, 
          reasonLabel: stopReason.label 
      };
  } else {
      currentPauseObj.value.reasonCode = stopReason.code;
      currentPauseObj.value.reasonLabel = stopReason.label;
  }

  // 2. Avisa o backend IMEDIATAMENTE sobre o motivo (Atualiza o log "SEM MOTIVO")
  try {
      await productionStore.sendEvent('STATUS_CHANGE', { 
          new_status: 'STOPPED', 
          reason: stopReason.label 
      });
  } catch (e) {
      console.error("Erro ao atualizar motivo no backend:", e);
  }

  // 3. Fecha o diálogo (NÃO ENVIA NADA AO SAP AQUI)
  isStopDialogOpen.value = false;

  // --- TRATAMENTO DE CASOS ESPECIAIS ---

  // A. SETUP (Cód 52) - Transforma a parada em Setup
  if (stopReason.code === '52') {
      productionStore.setMachineStatus('SETUP');
      productionStore.sendEvent('STATUS_CHANGE', { new_status: 'SETUP', reason: 'Preparação / Setup' });
      productionStore.isInSetup = true; // Ativa modo visual setup
      
      $q.notify({ type: 'info', color: 'purple-9', icon: 'build_circle', message: 'Modo Setup Ativado.' });
      return;
  }

  // B. MANUTENÇÃO (Cód 21)
  if (stopReason.code === '21' || stopReason.requiresMaintenance) {
      void triggerCriticalBreakdown(); 
      return;
  }

  // C. TROCA DE TURNO (Cód 111)
  if (stopReason.code === '111') {
      isShiftChangeDialogOpen.value = true; 
      return;
  }

  $q.notify({ type: 'info', message: `Motivo registrado: ${stopReason.label}`, icon: 'timer' });
}
async function applyNormalPause(fromPlc = false) {
  console.log("%c🛑 INICIANDO PROCESSO DE PAUSA...", "color: orange; font-weight: bold; font-size: 14px");

  const currentOrder = productionStore.activeOrder;
  const currentBadge = productionStore.activeOperator?.badge || productionStore.currentOperatorBadge;
  const now = new Date();
  
  // ✅ CORREÇÃO CRUCIAL: Usamos a variável computada que sabe achar o número '4152'
  const codeToSend = opNumberToSend.value;

  // Se não tiver ordem ou número de OP, aborta o apontamento de produção
  if (!currentOrder || !codeToSend) {
      console.warn("⚠️ Sem ordem ativa ou código inválido. Pulando apontamento de produção.");
      
      // Apenas muda o visual para parada
      isPaused.value = true;
      if (productionStore.currentMachine) productionStore.currentMachine.status = 'Parada';
      isStopDialogOpen.value = true;
      return;
  }

  // Garante objeto para a tela de motivos
  if (!currentPauseObj.value) {
    currentPauseObj.value = { startTime: now, reasonCode: '0', reasonLabel: 'SEM MOTIVO' };
  }

  // Bloqueio visual
  isPaused.value = true;
  $q.loading.show({ message: 'Encerrando ciclo de produção...' });

  try {
    // --- APONTAMENTO DE PRODUÇÃO (FECHAR O CICLO ANTERIOR) ---
    // Pega o horário que começou a produzir (statusStartTime)
    const prodStart = statusStartTime.value ? new Date(statusStartTime.value) : new Date();
    
    console.log(`🕒 Intervalo Produção: ${prodStart.toLocaleTimeString()} até ${now.toLocaleTimeString()}`);

    // Dados auxiliares
    const rawSeq = Number(currentViewedStep.value?.seq || 10);
    const position = rawSeq === 999 ? '999' : Math.floor(rawSeq / 10 * 10).toString().padStart(3, '0');
    const sapData = getCurrentSapData(position);

    // Monta o Payload igual ao que gerou o log de sucesso
    const productionPayload = {
        op_number: String(opNumberToSend.value), 
        position: position, 
        operation: sapData.code || '', 
        operation_desc: sapData.description || '', 
        part_description: currentOrder.part_name || '', 
        
        // ✅ CORREÇÃO: Tenta ler 'item_code' (da API) OU 'part_code' (local)
        item_code: currentOrder.item_code || currentOrder.part_code || '', 
        
        resource_code: productionStore.machineResource || '4.02.01',
        resource_name: productionStore.machineName || 'Máquina',
        operator_id: String(currentBadge || '0'),
        operator_name: getOperatorName(String(currentBadge || '')),
        vehicle_id: productionStore.machineId,
        start_time: prodStart.toISOString(),
        end_time: now.toISOString(),
        stop_reason: '', 
        DataSource: 'I',
        U_TipoDocumento: '1' 
    };

    console.log("🚀 Enviando Payload de Produção:", productionPayload);

    // Envia ao Backend
    try {
        const resp = await ProductionService.sendAppointment(productionPayload);
        console.log("✅ Produção registrada com sucesso!", resp);
    } catch (innerError) {
        console.error("❌ Erro ao enviar produção:", innerError);
        // Não travamos a parada se o apontamento falhar (ex: erro de rede), mas avisamos
        $q.notify({ type: 'warning', message: 'Aviso: Falha ao registrar tempo de produção.' });
    }

    // --- ATUALIZA STATUS PARA PARADO ---
    if (activeOrder.value) activeOrder.value.status = 'PAUSED';
    if (productionStore.currentMachine) productionStore.currentMachine.status = 'Parada';

    // Se foi manual, avisa o backend da mudança de status
    if (!fromPlc) {
      await productionStore.setMachineStatus('STOPPED');
      await productionStore.sendEvent('STATUS_CHANGE', { 
          new_status: 'STOPPED', 
          reason: currentPauseObj.value.reasonLabel 
      });
    }

    // Reinicia o relógio para contar o tempo de PARADA a partir de agora
    statusStartTime.value = new Date(); 
    
    // Abre tela de motivos
    isStopDialogOpen.value = true;

  } catch (error) {
    console.error("🔥 ERRO CRÍTICO NA PAUSA:", error);
    isPaused.value = false; // Reverte se der erro fatal
  } finally {
    $q.loading.hide();
  }
}

async function executeShiftChange(keepRunning: boolean) {
    isShiftChangeDialogOpen.value = false;
    
    // Mostramos o loading apenas para a troca de estado no banco de dados
    $q.loading.show({ message: 'Finalizando turno e liberando tablet...' });

    try {
        // 1. DEFINIÇÃO DE ESTADO NO BACKEND
        // Avisamos o backend do novo status (Autônomo ou Ocioso)
        // Isso fecha a fatia de tempo atual no banco de dados local (OEE)
        if (keepRunning) {
            await productionStore.setMachineStatus('IN_USE_AUTONOMOUS');
            // Logout mantendo a ordem ativa (true)
            await productionStore.logoutOperator('IN_USE_AUTONOMOUS', true); 
        } else {
            await productionStore.setMachineStatus('OCIOSO');
            // Logout mantendo a ordem ativa (true)
            await productionStore.logoutOperator('OCIOSO', true); 
        }

        // 2. NAVEGAÇÃO
        // O router joga para o Kiosk. Como o activeOrder não foi apagado do 
        // localStorage (pela flag 'true' acima), o próximo a logar já entra nela.
        await router.push({ name: 'machine-kiosk' });

        $q.notify({ 
            type: 'positive', 
            message: 'Turno trocado com sucesso!',
            caption: keepRunning ? 'Máquina segue operando.' : 'Máquina em ociosidade.'
        });

    } catch (error) {
        console.error("Erro operacional na troca:", error);
        $q.notify({ type: 'negative', message: 'Erro ao processar troca de estado.' });
    } finally {
        $q.loading.hide();
    }
}
async function triggerCriticalBreakdown() {
    if (!currentPauseObj.value) return;
    
    $q.loading.show({ 
        message: '🚨 Registrando Manutenção no SAP...', 
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

        // 1. Encerra a Produção atual (se houver OP ativa)
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
                resource_code: machineRes,
                resource_name: machineName,            
                operator_name: operatorName || '',
                operator_id: String(badge),
                vehicle_id: productionStore.machineId || 0,
                start_time: productionStart.toISOString(),
                end_time: eventTime,
                stop_reason: '', 
                DataSource: 'I',
                U_TipoDocumento: '1' // Produção
            };

            console.log("📤 [1/2] Fechando Produção (Manutenção):", productionPayload);
            await ProductionService.sendAppointment(productionPayload);
        }

        // 2. Registra a Parada de Manutenção (Tipo 2)
        const stopPayload = {
            op_number: '',
            resource_code: machineRes,
            resource_name: machineName,                
            operator_name: operatorName || '',
            operator_id: String(badge),
            vehicle_id: productionStore.machineId || 0,
            DataSource: 'I',
            start_time: eventTime,
            end_time: eventTime, 
            stop_reason: currentPauseObj.value.reasonCode, // Deve ser '21' ou similar
            stop_description: 'Manutenção',
            U_TipoDocumento: '2'
        };

        console.log("📤 [2/2] Registrando Parada de Recurso:", stopPayload);
        await ProductionService.sendAppointment(stopPayload);

        // 3. MUDANÇA CRÍTICA: Envia status explícito 'MAINTENANCE' ao Backend
        await productionStore.sendEvent('STATUS_CHANGE', { 
            new_status: 'MAINTENANCE', 
            reason: 'Manutenção / Conserto' 
        });

        // 4. Atualiza estado local e desloga
        await productionStore.setMachineStatus('Em manutenção');
        await productionStore.finishSession();
        await productionStore.logoutOperator('MAINTENANCE'); // Passa o motivo para log

        await router.push({ 
            name: 'machine-kiosk', 
            query: { 
                state: 'maintenance',
                last_operator: String(badge)
            } 
        });
        
        $q.notify({ type: 'warning', icon: 'build', message: 'Máquina em Manutenção.' });

    } catch (error) {
        console.error("Erro ao processar quebra de máquina:", error);
        $q.notify({ type: 'negative', message: 'Erro ao registrar parada no SAP.' });
    } finally {
        $q.loading.hide();
    }
}

async function finishPauseAndResume(fromPlc = false) {
  if (!currentPauseObj.value) return;
  
  // 1. BLOQUEIO IMEDIATO DE DUPLICIDADE
  if (!isPaused.value) {
      console.warn("⚠️ Tentativa de retomada duplicada ignorada.");
      return;
  }

  isPaused.value = false;
  if (activeOrder.value) activeOrder.value.status = 'RUNNING';
  
  // Atualiza visualmente local
  if (productionStore.currentMachine) productionStore.currentMachine.status = 'Em uso';

  const isSetupReturn = currentPauseObj.value.reasonCode === '52';
  const msgLoading = isSetupReturn ? 'Finalizando Setup no SAP...' : 'Registrando Parada no SAP...';

  $q.loading.show({ message: msgLoading });
  
  try {
    const now = new Date();
    const pauseStart = new Date(currentPauseObj.value.startTime || statusStartTime.value); 
    const badge = productionStore.activeOperator?.badge || productionStore.currentOperatorBadge;

    const stopPayload = {
      op_number: '', 
      position: '',
      operation: '',
      stop_reason: String(currentPauseObj.value.reasonCode), 
      stop_description: currentPauseObj.value.reasonLabel,
      resource_code: productionStore.machineResource || '4.02.01',
      resource_name: productionStore.machineName || 'a a',
      operator_id: String(badge || '0'),
      operator_name: getOperatorName(String(badge || '')),
      vehicle_id: productionStore.machineId,
      start_time: pauseStart.toISOString(),
      end_time: now.toISOString(),
      DataSource: 'I',
      U_TipoDocumento: '2' // Setup também é tipo 2 (Parada Planejada) no seu Addon
    };

    await ProductionService.sendAppointment(stopPayload);

    // 2. LÓGICA DE STATUS
    // Se veio do PLC, o backend já recebeu o sinal 1. 
    // Porém, se estávamos em SETUP, o backend ignorou o sinal 1 (por causa da trava).
    // Então, AGORA precisamos forçar o status 'RUNNING' explicitamente.
    
    if (!fromPlc || isSetupReturn) {
      // Se era Setup, TEMOS que avisar que acabou, mesmo que tenha vindo do PLC
      console.log("🚀 Enviando status RUNNING (Fim de Pausa/Setup)");
      await productionStore.setMachineStatus('RUNNING');
      await productionStore.sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' });
    } else {
      console.log("ℹ️ Retomada via PLC: Backend já atualizado.");
    }

    currentPauseObj.value = null; 
    statusStartTime.value = new Date(); 
    
    if (isSetupReturn) {
        $q.notify({ type: 'positive', message: 'Setup Finalizado! Produção iniciada.', icon: 'check_circle' });
    }

  } catch (error) {
    console.error("Erro ao retomar:", error);
    isPaused.value = true; // Reverte erro
  } finally {
    $q.loading.hide();
  }
}
function confirmFinishOp() {
  let badge = productionStore.currentOperatorBadge;

  // Verificação de segurança do crachá
  if (!badge && authStore.user?.employee_id) {
      const role = authStore.user.role || '';
      if (role !== 'admin' && role !== 'manager') badge = authStore.user.employee_id;
  }

  if (!badge || badge.includes('@')) {
      $q.dialog({
        title: 'Identificação Obrigatória',
        message: 'Bipe seu crachá para confirmar o encerramento:',
        prompt: { model: '', type: 'text', isValid: val => val.length > 0 },
        cancel: true, persistent: true
      }).onOk(data => {
        productionStore.currentOperatorBadge = data;
        confirmFinishOp(); 
      });
      return; 
  }

  // Diálogo de confirmação final
  $q.dialog({
    title: 'Encerrar Etapa / O.P.',
    message: 'Tem certeza que deseja finalizar esta etapa? A máquina ficará DISPONÍVEL.',
    cancel: true, persistent: true,
    ok: { label: 'SIM, ENCERRAR', color: 'negative', push: true, size: 'lg' }
  }).onOk(async () => {
      
      $q.loading.show({ message: 'Encerrando sessão...' });
      
      try {
        // NÃO enviamos apontamento para o SAP aqui.
        // O apontamento de produção já foi enviado pelo 'applyNormalPause' 
        // quando a máquina parou (sinal 0) e abriu esta tela.

        // 1. Fecha a sessão no Backend (Calcula totais, fecha logs abertos)
        await productionStore.finishSession();

        // 2. Muda o status da máquina para DISPONÍVEL (Verde/Cinza)
        await productionStore.setMachineStatus('AVAILABLE');
        
        // 3. Registra evento de log para rastreabilidade
        await productionStore.sendEvent('STATUS_CHANGE', { 
            new_status: 'AVAILABLE', 
            reason: 'Etapa Finalizada pelo Operador' 
        });

        // 4. Logout e Redirecionamento
        await productionStore.logoutOperator();
        await router.push({ name: 'machine-kiosk' });

        $q.notify({ type: 'positive', message: 'Etapa concluída com sucesso!', icon: 'check_circle', timeout: 3000 });

      } catch (error) {
        console.error("Erro ao finalizar:", error);
        $q.notify({ type: 'negative', message: 'Erro ao comunicar com o servidor.' });
      } finally {
        $q.loading.hide();
        isStopDialogOpen.value = false; // Fecha o diálogo se algo der errado mas não sair da tela
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
    
    // Envia o setor e a nota digitada
    await productionStore.triggerAndon(sector, andonNote.value);
    
    // Limpa o campo para a próxima vez
    andonNote.value = ''; 
    
    $q.notify({
        type: 'info',
        message: `Chamado enviado para: ${sector}`,
        icon: 'campaign'
    });
}



async function handleSetupClick() {
  // --- CENÁRIO A: SAINDO DO SETUP PARA VOLTAR A PRODUZIR ---
  if (productionStore.isInSetup) {
      $q.dialog({
          title: 'Finalizar Setup',
          message: 'Deseja encerrar a preparação e VOLTAR A PRODUZIR agora?',
          cancel: true,
          persistent: true,
          ok: { label: 'Finalizar e Iniciar O.P.', color: 'positive', push: true }
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

              // 1. Registra o tempo que a máquina ficou em SETUP no SAP (Tipo 2)
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
                  stop_reason: '52', // Código SAP para Setup
                  stop_description: 'Setup',
                  U_TipoDocumento: '2' // PARADA PLANEJADA
              };
              await ProductionService.sendAppointment(setupPayload);

              // 2. Toggle local para sair do modo setup visual
              await productionStore.toggleSetup();

              // 3. Abre uma nova sessão de produção no Banco de Dados
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
                
                // ✅ FORÇA STATUS "Em uso" NO BACKEND
                await productionStore.setMachineStatus('RUNNING');
                
                $q.notify({ type: 'positive', message: 'Setup registrado. Produção retomada!', icon: 'check_circle' });
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
  
  // --- CENÁRIO B: ENTRANDO EM MODO SETUP (VINDO DA PRODUÇÃO) ---
  else {
      isLoadingAction.value = true;
      try {
          const now = new Date();
          
          // Se estava produzindo, precisamos "cortar" a produção e enviar o tempo ao SAP (Tipo 1)
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
                  stop_description: '',
                  U_TipoDocumento: '1' // PRODUÇÃO
              };
              
              console.log("📤 [SETUP] Fechando Produção (Tipo 1) para iniciar Setup:", productionPayload);
              await ProductionService.sendAppointment(productionPayload);
          }

          // ✅ MUDANÇA CRÍTICA: Ativa modo SETUP explícito no Backend e na Store
          await productionStore.toggleSetup();
          await productionStore.setMachineStatus('SETUP'); 
          
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
let scanTimeout: ReturnType<typeof setTimeout> | null = null;

// Esta é a função que o erro diz estar "missing"
const onKeydown = (e: KeyboardEvent) => {
  void handleGlobalKeydown(e);
};

async function handleGlobalKeydown(event: KeyboardEvent) {
  // Ignora se o foco estiver em um campo de input (para não bugar digitação normal)
  if ((event.target as HTMLElement).tagName === 'INPUT') return;

  if (event.key === 'Enter') {
    if (scanBuffer.length > 2) {
      const scannedBadge = scanBuffer.trim();
      $q.loading.show({ message: `Autenticando crachá...` });
      
      try {
        // Tenta logar o operador no AuthStore
        await authStore.loginByBadge(scannedBadge);
        
        if (authStore.user?.employee_id) {
          productionStore.currentOperatorBadge = authStore.user.employee_id;
          $q.notify({ 
            type: 'positive', 
            message: `Olá, ${authStore.user.full_name}`,
            icon: 'person' 
          });
        } else {
          // Fallback caso o user não venha completo
          productionStore.currentOperatorBadge = scannedBadge;
        }
      } catch (e) {
        console.error("Erro ao ler crachá:", e);
        $q.notify({ type: 'negative', message: 'Crachá não reconhecido ou erro de conexão.' });
      } finally {
        $q.loading.hide();
        scanBuffer = '';
      }
    }
    scanBuffer = ''; 
  } else {
    // Adiciona o caractere ao buffer se for uma tecla comum
    if (event.key.length === 1) {
      scanBuffer += event.key;
      
      // Limpa o buffer se o operador demorar mais de 2 segundos entre teclas
      if (scanTimeout) clearTimeout(scanTimeout);
      scanTimeout = setTimeout(() => { scanBuffer = ''; }, 2000);
    }
  }
}

async function finishAutoSetup() {
    $q.loading.show({ message: 'Máquina ligada! Finalizando Setup...' });
    
    try {
        const now = new Date();
        const startSetup = statusStartTime.value; 
        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;

        // 1. Envia o Apontamento de SETUP ao SAP (Tipo 2 - Parada)
        await ProductionService.sendAppointment({
            op_number: '', 
            resource_code: productionStore.machineResource,
            resource_name: productionStore.machineName, 
            operator_id: String(badge),
            operator_name: getOperatorName(String(badge || '')),
            start_time: startSetup.toISOString(),
            end_time: now.toISOString(),
            stop_reason: '52', 
            stop_description: 'Preparação / Setup',
            DataSource: 'I',
            U_TipoDocumento: '2'
        });

        // 2. Transição de Estado Local
        productionStore.isInSetup = false; 
        statusStartTime.value = new Date(); // Zera relógio para produção
        if (activeOrder.value) activeOrder.value.status = 'RUNNING';
        
        // 3. Atualiza Backend para 'Em Uso' (Sem gerar apontamento extra agora)
        await productionStore.setMachineStatus('RUNNING');
        await productionStore.sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' });

        $q.notify({ type: 'positive', message: 'Setup Finalizado. Produção Iniciada!', icon: 'rocket_launch' });

    } catch (error) {
        console.error("Erro na transição automática:", error);
    } finally {
        $q.loading.hide();
    }
}

const isProcessingSignal = ref(false); // Trava para evitar loop infinito de eventos

let socket: WebSocket | null = null;

function connectWebSocket() {
  // SE já existir, mata o anterior para garantir que o 'onmessage' 
  // esteja vinculado às variáveis DESTE componente atual.
  if (socket) {
      socket.close();
      socket = null;
  }

  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // Ajuste o IP/Porta conforme sua env
  const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/ws/${productionStore.machineId}`;

  console.log(`🔌 Conectando ao WebSocket: ${wsUrl}`);
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("✅ WebSocket Conectado!");
    isSocketConnected.value = true;
  };

  socket.onmessage = async (event) => {
    // 🛡️ TRAVA DE SEGURANÇA: TROCA DE TURNO
    // Se o operador está com o diálogo "Vai parar ou continuar?" aberto,
    // IGNORAMOS qualquer sinal do PLC. Isso evita que, se ele parar a máquina
    // para decidir, o sistema gere um evento de "Parada" indesejado.
    if (isShiftChangeDialogOpen.value) {
        console.log("⏸️ WebSocket ignorado: Decisão de Troca de Turno em andamento.");
        return;
    }

    try {
      const data = JSON.parse(event.data);
      
      // Filtra apenas eventos de mudança de estado da MINHA máquina
      if (
        data.type === 'MACHINE_STATE_CHANGED' && 
        Number(data.machine_id) === Number(productionStore.machineId) &&
        !isProcessingSignal.value // Evita processar dois sinais ao mesmo tempo
      ) {
        const rawStatus = String(data.new_status).toUpperCase();
        
        // --- CENÁRIO: SAÍDA AUTOMÁTICA DE SETUP (Sinal 1) ---
        if (['1', 'RUNNING', 'PRODUCING', 'EM USO', 'IN_USE'].includes(rawStatus) && productionStore.isInSetup) {
             console.log("🚀 Detectado início de produção! Finalizando Setup...");
             isProcessingSignal.value = true;
             await finishAutoSetup(); 
             isProcessingSignal.value = false;
             return;
        }

        // --- CENÁRIO: PARADA (Sinal 0 - UNPLANNED) ---
        if (data.category === 'UNPLANNED_STOP') {
          // Se está em setup, ignora paradas (o setup já é uma parada planejada)
          if (productionStore.isInSetup) return;

          // Se JÁ ESTÁ pausado (isPaused = true), IGNORA para não duplicar envio
          if (isPaused.value) {
             console.log("🛑 WebSocket: Sinal 0 recebido, mas sistema JÁ está em pausa. Ignorando.");
             return; 
          }

          console.log("🛑 WebSocket: Sinal de Parada Recebido (Iniciando Pausa).");
          isProcessingSignal.value = true;
          await applyNormalPause(true); // true = veio do PLC
          isProcessingSignal.value = false;
        }
        
        // --- CENÁRIO: RETOMADA DE PAUSA (Sinal 1 - PRODUCING) ---
        else if (data.category === 'PRODUCING') {
          // Se estava pausado, retoma a produção e fecha o diálogo
          if (isPaused.value) {
            console.log("🚀 WebSocket: Sinal de Retomada Recebido.");
            isProcessingSignal.value = true;
            isStopDialogOpen.value = false; 
            await finishPauseAndResume(true); // true = veio do PLC
            isProcessingSignal.value = false;
          }
        }
      }
    } catch (e) {
      console.error("Erro ao processar mensagem WebSocket:", e);
      isProcessingSignal.value = false;
    }
  };

  socket.onclose = () => {
    console.warn("⚠️ WebSocket Desconectado.");
    isSocketConnected.value = false;
    // Tenta reconectar a cada 5s se a ordem ainda estiver ativa
    if (productionStore.activeOrder && !socket) {
        setTimeout(() => {
            if (productionStore.activeOrder) connectWebSocket();
        }, 5000); 
    }
  };

  socket.onerror = (error) => {
    console.error("❌ Erro no WebSocket:", error);
  };
}



onMounted(async () => {
  // 1. Inicialização de Roteiro e Timers
  if (productionStore.currentStepIndex !== -1) {
    viewedStepIndex.value = productionStore.currentStepIndex;
  }

  // Inicia cronômetro visual (Atualiza currentTime a cada segundo)
  timerInterval = setInterval(() => { 
    currentTime.value = new Date(); 
  }, 1000);
  resetTimer();

  // 2. Listeners de Sistema
  window.addEventListener('keydown', onKeydown);
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);

  // 3. Recuperação de Sessão (Login / Troca de Turno)
  // Se veio do login, o authStore tem o crachá correto
  if (!productionStore.currentOperatorBadge && authStore.user?.employee_id) {
      productionStore.currentOperatorBadge = authStore.user.employee_id;
  }

  // 4. Sincronização de Dados
  await syncOfflineData();
  
  // Força atualização do estado da máquina do servidor
  // Isso é vital para saber se o estado real é 'AUTÔNOMO', 'EM USO' ou 'PARADA'
  if (productionStore.machineId) {
      await productionStore.fetchMachine(productionStore.machineId);
  }

  // 5. Lógica de "Reivindicação" (Troca de Turno Quente)
  // Se tem ordem ativa E a máquina está em modo Autônomo (Deixada pelo turno anterior)
  // O operador loga e "pega o bastão" sem parar a máquina.
  if (productionStore.activeOrder && (normalizedStatus.value === 'AUTÔNOMO' || normalizedStatus.value === 'OCIOSO')) {
      console.log("👤 Operador assumindo o posto (Troca Quente). Reivindicando máquina...");
      
      // A. Atualiza VISUALMENTE agora (Otimistic Update)
      // Garante que a tela fique verde imediatamente
      if (productionStore.currentMachine) {
          productionStore.currentMachine.status = 'Em uso'; 
          isPaused.value = false; // Garante que não mostre tela de pausa
      }

      // B. Avisa o Backend que agora é Produção Humana
      // O Backend vai fechar a fatia 'Autônoma' e abrir 'Em uso'
      await productionStore.setMachineStatus('RUNNING');
      
      // Envia evento apenas para registro (O backend já trataria o status change, mas garantimos o motivo)
      await productionStore.sendEvent('STATUS_CHANGE', { 
          new_status: 'RUNNING', 
          reason: 'Operador assumiu máquina em movimento' 
      });

      resetTimer(); 
  }

  // 6. CONEXÃO WEBSOCKET (Fundamental)
  // Só conecta agora, depois que já definimos o operador e ajustamos o status inicial
  if (productionStore.activeOrder && productionStore.activeOrder.code) {
      console.log("🔌 Iniciando conexão com PLC...");
      connectWebSocket();
  }
});

onUnmounted(() => {
  // 1. Limpeza de Listeners
  window.removeEventListener('keydown', onKeydown);
  window.removeEventListener('online', updateOnlineStatus);
  window.removeEventListener('offline', updateOnlineStatus);

  if (timerInterval) {
    clearInterval(timerInterval);
  }

  // 2. FECHAMENTO DO SOCKET (CRUCIAL PARA EVITAR DUPLICIDADE)
  // Se não fechar, o componente antigo continua recebendo sinais e disparando logs duplicados
  if (socket) {
    socket.close();
    socket = null;
    console.log("🔌 WebSocket desconectado (Componente desmontado).");
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
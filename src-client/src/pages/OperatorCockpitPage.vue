<template>
  <q-layout view="hHh lpR fFf" class="bg-grey-2 text-dark font-inter window-height overflow-hidden">
    
    <CockpitHeader
      :logo-path="logoPath"
      :machine-sector="productionStore.machineSector"
      :machine-name="productionStore.machineName"
      :status-bg-class="statusBgClass"
      :status-icon="statusIcon"
      :display-status="displayStatus"
      :operator-name="productionStore.currentOperator?.full_name || productionStore.currentOperatorBadge || '---'"
      :time-display="timeDisplay"
      @logout="handleLogout"
    />

    <q-page-container class="full-height">
      <q-page class="q-pa-sm full-height column no-wrap">
        
        <CockpitWaitingState
          v-if="!productionStore.activeOrder"
          @open-list="openOpListDialog"
          @scan-qr="simulateOpScan"
        />

        <div v-else class="col row q-col-gutter-md items-stretch content-stretch">
          
          <div class="col-12 col-md-8 column no-wrap full-height q-gutter-y-md">
            <OrderInfoCard
              :order="productionStore.activeOrder"
              :current-step="currentViewedStep"
              :step-index="viewedStepIndex"
              :background-image="customOsBackgroundImage"
              @open-drawing="openDrawing"
              @prev-step="prevStepView"
              @next-step="nextStepView"
              @add-scrap="productionStore.addProduction(1, true)"
            />
          </div>

          <ControlPanel
            :elapsed-time="elapsedTime"
            :status-text-class="statusTextClass"
            :get-button-class="getButtonClass"
            :is-loading-action="isLoadingAction"
            :is-paused="isPaused"
            :normalized-status="normalizedStatus"
            :is-in-setup="productionStore.isInSetup"
            @main-action="handleMainButtonClick"
            @setup-action="handleSetupClick"
            @open-andon="isAndonDialogOpen = true"
            @finish-op="confirmFinishOp"
          />
        </div>
      </q-page>
    </q-page-container>

    <OpListDialog
      v-model="showOpList"
      :rows="openOps"
      :columns="opColumns"
      :loading="loadingOps"
      @select-op="selectOp"
    />

    <DrawingDialog
      v-model="isDrawingDialogOpen"
      :url="drawingUrl"
      :part-code="productionStore.activeOrder?.part_code || ''"
      @refresh="openDrawing"
    />

    <StopReasonDialog
      v-model="isStopDialogOpen"
      v-model:stop-search="stopSearch"
      :filtered-reasons="filteredStopReasons"
      @select-reason="handleSapPause"
    />

    <MaintenanceDialog
      v-model="isMaintenanceConfirmOpen"
      v-model:sub-reason="maintenanceSubReason"
      v-model:note="maintenanceNote"
      :sub-reason-options="subReasonOptions"
      @cancel="cancelMaintenanceSelection"
      @confirm="triggerCriticalBreakdown"
    />

    <ShiftChangeDialog
      v-model="isShiftChangeDialogOpen"
      @confirm="executeShiftChange"
    />

    <AndonDialog
      v-model="isAndonDialogOpen"
      v-model:note="andonNote"
      :options="andonOptions"
      @confirm="confirmAndonCall"
    />

  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useProductionStore } from 'stores/production-store';
import { storeToRefs } from 'pinia';
import { ProductionService } from 'src/services/production-service';
import { useAuthStore } from 'stores/auth-store';
import { api } from 'boot/axios';

// --- COMPONENTES IMPORTADOS ---
import CockpitHeader from 'components/cockpit/CockpitHeader.vue';
import CockpitWaitingState from 'components/cockpit/CockpitWaitingState.vue';
import OrderInfoCard from 'components/cockpit/OrderInfoCard.vue';
import ControlPanel from 'components/cockpit/ControlPanel.vue';
import OpListDialog from 'components/cockpit/dialogs/OpListDialog.vue';
import DrawingDialog from 'components/cockpit/dialogs/DrawingDialog.vue';
import StopReasonDialog from 'components/cockpit/dialogs/StopReasonDialog.vue';
import MaintenanceDialog from 'components/cockpit/dialogs/MaintenanceDialog.vue';
import ShiftChangeDialog from 'components/cockpit/dialogs/ShiftChangeDialog.vue';
import AndonDialog from 'components/cockpit/dialogs/AndonDialog.vue';

// --- DADOS ---
import { findBestStepIndex } from 'src/data/sap-operations';
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

const logoPath = ref('/Logo-Oficial.png');
const isLoadingAction = ref(false);
const customOsBackgroundImage = ref('/a.jpg');

// --- Estados ---
const isPaused = ref(false);
const currentPauseObj = ref<{
  startTime: Date;
  reasonCode: string;
  reasonLabel: string;
} | null>(null);

// Dialogs State
const isStopDialogOpen = ref(false);
const isAndonDialogOpen = ref(false);
const isMaintenanceConfirmOpen = ref(false);
const isShiftChangeDialogOpen = ref(false);
const isDrawingDialogOpen = ref(false);
const showOpList = ref(false);
const loadingOps = ref(false);

const drawingUrl = ref('');
const stopSearch = ref('');
const statusStartTime = ref(new Date());
const currentTime = ref(new Date());
let timerInterval: ReturnType<typeof setInterval>;
const andonNote = ref('');

// Maintenance State
const maintenanceSubReason = ref('Mecânica');
const maintenanceNote = ref('');
const subReasonOptions = [
  { label: 'Falha Mecânica', value: 'Mecânica', icon: 'settings' },
  { label: 'Falha Elétrica', value: 'Elétrica', icon: 'bolt' },
  { label: 'Hidráulica / Vazamento', value: 'Hidráulica', icon: 'water_drop' },
  { label: 'Pneumática / Ar', value: 'Pneumática', icon: 'air' },
  { label: 'Erro de Software / CNC', value: 'Software', icon: 'terminal' }
];

const andonOptions = ANDON_OPTIONS; 

// --- Tabela ---
const openOps = ref([]);
const opColumns = [
  { name: 'op_number', label: 'OP / Ref', align: 'left', field: 'op_number', sortable: true },
  { name: 'part_name', label: 'Produto / Item', align: 'left', field: 'part_name', sortable: true },
  { name: 'planned_qty', label: 'Qtd', align: 'center', field: 'planned_qty' },
  { name: 'action', label: 'Selecionar', align: 'center' }
];

// --- Navigation ---
const viewedStepIndex = ref(0);

const currentViewedStep = computed(() => {
    if (activeOrder.value?.steps && activeOrder.value.steps.length > 0) {
        return activeOrder.value.steps[viewedStepIndex.value];
    }
    return { seq: '---', name: 'Aguardando Roteiro', description: 'Buscando operações no SAP...', resource: '---', timeEst: 0 };
});

const opNumberToSend = computed(() => {
  if (!productionStore.activeOrder) return '';
  const order = productionStore.activeOrder;
  if (order.is_service) return String(order.code);
  return order.custom_ref || order.code;
});

// --- Computeds Visuais ---
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
    if (['SETUP', 'MAINTENANCE', 'EM MANUTENÇÃO', 'MANUTENÇÃO'].includes(s) || ['MAINTENANCE', 'EM MANUTENÇÃO', 'MANUTENÇÃO'].includes(m)) return 'MANUTENÇÃO';
    return 'PARADA'; 
});

const displayStatus = computed(() => {
  if (productionStore.isInSetup) return 'EM PREPARAÇÃO (SETUP)';
  if (isPaused.value) return 'EM PAUSA - ' + (currentPauseObj.value?.reasonLabel || '');
  const rawStatus = activeOrder.value?.status?.toUpperCase() || '';
  if (['AVAILABLE', 'DISPONÍVEL', 'PENDING'].includes(rawStatus)) return 'AGUARDANDO INÍCIO';
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

// --- HELPER FUNCTIONS ---
function resetTimer() { statusStartTime.value = new Date(); }
function nextStepView() { if (activeOrder.value?.steps && viewedStepIndex.value < activeOrder.value.steps.length - 1) viewedStepIndex.value++; }
function prevStepView() { if (viewedStepIndex.value > 0) viewedStepIndex.value--; }

function cancelMaintenanceSelection() {
  isMaintenanceConfirmOpen.value = false;
  maintenanceNote.value = '';
  maintenanceSubReason.value = 'Mecânica';
  currentPauseObj.value = null;
  isStopDialogOpen.value = true; 
}

// --- ACTIONS ---

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
    $q.loading.show({ message: `Buscando roteiro para ${op.op_number}...` });
    await productionStore.loadOrderFromQr(String(op.op_number));
    
    if (productionStore.activeOrder?.steps && productionStore.activeOrder.steps.length > 0) {
      const idx = findBestStepIndex(productionStore.machineResource, productionStore.activeOrder.steps);
      if (idx !== -1) {
        productionStore.currentStepIndex = idx;
        viewedStepIndex.value = idx;
      } else {
        productionStore.currentStepIndex = 0;
      }
    }
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Erro ao carregar roteiro.' });
  } finally {
    showOpList.value = false;
    $q.loading.hide();
    resetTimer();
  }
}

function openDrawing() {
  if (!productionStore.activeOrder?.part_code) return;
  const baseUrl = 'http://localhost:8000';
  drawingUrl.value = `${baseUrl}/drawings/${encodeURIComponent(productionStore.activeOrder.part_code)}?t=${new Date().getTime()}`;
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
      
      const setupPayload = {
          op_number: '', service_code: '', position: '', operation: '', operation_desc: '',    
          resource_code: productionStore.machineResource || '4.02.01',
          resource_name: productionStore.machineName,
          operator_name: getOperatorName(String(badge).trim()),
          operator_id: String(badge),
          vehicle_id: productionStore.machineId || 0,
          start_time: startSetup.toISOString(),
          end_time: now.toISOString(),
          stop_reason: '52', stop_description: 'Setup' 
      };
      await ProductionService.sendAppointment(setupPayload);
      productionStore.activeOrder.status = 'PENDING'; 
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Falha ao encerrar setup.' });
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
    $q.notify({ type: 'negative', message: 'Erro ao registrar início.' });
  } finally {
    isLoadingAction.value = false;
    $q.loading.hide();
  }
}

function handleSapPause(stopReason: SapStopReason) {
  const now = new Date();
  currentPauseObj.value = { startTime: now, reasonCode: stopReason.code, reasonLabel: stopReason.label };

  if (stopReason.label.toLowerCase().includes('troca de turno') || stopReason.code === '111') {
      isStopDialogOpen.value = false;
      isShiftChangeDialogOpen.value = true; 
      return;
  }
  if (stopReason.requiresMaintenance) {
      isStopDialogOpen.value = false;
      isMaintenanceConfirmOpen.value = true; 
  } else {
      applyNormalPause();
  }
}

async function applyNormalPause() {
    isStopDialogOpen.value = false;
    isMaintenanceConfirmOpen.value = false;
    $q.loading.show({ message: 'Registrando parada...' });

    try {
        const now = new Date();
        const prodStart = statusStartTime.value;
        const reason = currentPauseObj.value;
        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
        const machineRes = productionStore.machineResource || '4.02.01';

        if (activeOrder.value?.code) {
            const prodPayload = {
                op_number: String(opNumberToSend.value),
                service_code: activeOrder.value.is_service ? activeOrder.value.part_code : '',
                position: currentViewedStep.value?.seq?.toString().padStart(3, '0') || '010',
                operation: '', operation_desc: '',
                resource_code: machineRes,
                operator_id: String(badge),
                start_time: prodStart.toISOString(),
                end_time: now.toISOString(),
                stop_reason: '', stop_description: ''
            };
            await ProductionService.sendAppointment(prodPayload);
        }

        const stopPayload = {
            op_number: '', resource_code: machineRes, operator_id: String(badge),
            start_time: now.toISOString(), end_time: now.toISOString(),
            stop_reason: reason?.reasonCode || '100', stop_description: reason?.reasonLabel || 'Pausa'
        };
        await ProductionService.sendAppointment(stopPayload);

        isPaused.value = true;
        if (activeOrder.value) activeOrder.value.status = 'PAUSED';
        await productionStore.setMachineStatus('STOPPED'); 
        statusStartTime.value = new Date(); 
        $q.notify({ type: 'warning', message: 'Máquina em Pausa.' });
    } catch (error) {
        console.error("Erro ao pausar:", error);
    } finally {
        $q.loading.hide();
    }
}

async function executeShiftChange(keepRunning: boolean) {
    isShiftChangeDialogOpen.value = false;
    const now = new Date();
    
    if (!keepRunning) {
        currentPauseObj.value = { startTime: now, reasonCode: '111', reasonLabel: 'Troca de Turno' };
        void applyNormalPause();
        return;
    }

    $q.loading.show({ message: 'Trocando turno...' });
    try {
        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
        if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
        const machineRes = productionStore.machineResource || '4.02.01';
        
        if (activeOrder.value?.code) {
            const prodPayload = {
                op_number: String(opNumberToSend.value),
                service_code: activeOrder.value.is_service ? activeOrder.value.part_code : '',
                position: currentViewedStep.value?.seq?.toString().padStart(3, '0') || '010',
                resource_code: machineRes,
                resource_name: productionStore.machineName,
                part_description: activeOrder.value.part_name || '',
                item_code: activeOrder.value.part_code || '',
                operator_name: getOperatorName(String(badge).trim()),
                operator_id: String(badge),
                start_time: statusStartTime.value.toISOString(),
                end_time: now.toISOString(),
                stop_reason: '', stop_description: ''
            };
            await ProductionService.sendAppointment(prodPayload);
        }

        const stopPayload = {
            op_number: '', resource_code: machineRes, operator_id: String(badge),
            start_time: now.toISOString(), end_time: now.toISOString(),
            stop_reason: '111', stop_description: 'Troca de Turno'
        };
        await ProductionService.sendAppointment(stopPayload);

        await productionStore.logoutOperator(undefined, true); 
        await router.push({ name: 'machine-kiosk' });
        $q.notify({ type: 'positive', message: 'Turno encerrado.' });
    } catch (error) {
        $q.notify({ type: 'negative', message: 'Erro na troca de turno.' });
    } finally {
        $q.loading.hide();
    }
}

async function triggerCriticalBreakdown() {
    if (!currentPauseObj.value) return;
    const finalDesc = `[${maintenanceSubReason.value}] ${maintenanceNote.value}`.trim();
    isMaintenanceConfirmOpen.value = false;
    $q.loading.show({ message: 'Registrando Quebra...', backgroundColor: 'red-10' });

    try {
        const now = new Date();
        const eventTime = now.toISOString();
        let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
        if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
        const machineRes = productionStore.machineResource || '4.02.01';
        
        if (activeOrder.value?.code) {
            const prodPayload = {
                op_number: String(opNumberToSend.value),
                service_code: '',
                position: currentViewedStep.value?.seq?.toString().padStart(3, '0') || '010',
                resource_code: machineRes,
                operator_id: String(badge),
                start_time: statusStartTime.value.toISOString(),
                end_time: eventTime,
                stop_reason: '', stop_description: '' 
            };
            await ProductionService.sendAppointment(prodPayload);
        }

        const stopPayload = {
            op_number: '', resource_code: machineRes, operator_id: String(badge),
            start_time: eventTime, end_time: eventTime,
            stop_reason: currentPauseObj.value.reasonCode, stop_description: finalDesc
        };
        await ProductionService.sendAppointment(stopPayload);

        await productionStore.setMachineStatus('MAINTENANCE');
        await productionStore.finishSession();
        await productionStore.logoutOperator('MAINTENANCE');
        await router.push({ name: 'machine-kiosk', query: { state: 'maintenance' } });
        $q.notify({ type: 'negative', icon: 'build', message: 'Máquina parada. O.M. solicitada.' });
    } catch (error) {
        $q.notify({ type: 'negative', message: 'Erro ao registrar quebra.' });
    } finally {
        $q.loading.hide();
    }
}

async function finishPauseAndResume() {
  if (!currentPauseObj.value) return;
  $q.loading.show({ message: 'Retomando...' });
  try {
    const endTime = new Date();
    const pauseStart = currentPauseObj.value.startTime;
    let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
    if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
    const machineRes = productionStore.machineResource || '4.02.01'; 

    const stopPayload = {
      op_number: '', resource_code: machineRes, operator_id: String(badge), vehicle_id: productionStore.machineId || 0,
      start_time: pauseStart.toISOString(), end_time: endTime.toISOString(),
      stop_reason: currentPauseObj.value.reasonCode, stop_description: currentPauseObj.value.reasonLabel
    };
    await ProductionService.sendAppointment(stopPayload);
    await productionStore.sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' });
    await productionStore.setMachineStatus('RUNNING'); 

    isPaused.value = false;
    currentPauseObj.value = null;
    if (productionStore.activeOrder) productionStore.activeOrder.status = 'RUNNING';
    statusStartTime.value = new Date(); 
    $q.notify({ type: 'positive', message: 'Produção Iniciada!', icon: 'play_circle' });
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Erro ao retomar.' });
    isPaused.value = false;
    statusStartTime.value = new Date();
  } finally { 
    $q.loading.hide(); 
  }
}

function confirmFinishOp() {
  let badge = productionStore.currentOperatorBadge;
  if (!badge && authStore.user?.employee_id && authStore.user.role !== 'admin') badge = authStore.user.employee_id;

  if (!badge || badge.includes('@')) {
      $q.dialog({ title: 'Identificação Obrigatória', message: 'Bipe seu crachá:', prompt: { model: '', type: 'text', isValid: val => val.length > 0 }, cancel: true, persistent: true })
        .onOk(data => { productionStore.currentOperatorBadge = data; confirmFinishOp(); });
      return; 
  }

  $q.dialog({ title: 'Finalizar O.P.', message: `Encerrar O.P. e liberar a máquina?`, cancel: true, persistent: true, ok: { label: 'Finalizar', color: 'negative', push: true } })
    .onOk(async () => {
      $q.loading.show({ message: 'Finalizando...' });
      try {
        const endTime = new Date();
        const machineRes = productionStore.machineResource || '4.02.01';
        const payload = {
          op_number: String(opNumberToSend.value), service_code: '',
          position: currentViewedStep.value?.seq?.toString().padStart(3, '0') || '010',
          resource_code: machineRes,
          operator_id: String(badge),
          start_time: statusStartTime.value.toISOString(), end_time: endTime.toISOString(),
          stop_reason: '', vehicle_id: productionStore.machineId || 0
        };
        await ProductionService.sendAppointment(payload);
        await productionStore.finishSession();
        await productionStore.setMachineStatus('AVAILABLE');
        await productionStore.logoutOperator();
        await router.push({ name: 'machine-kiosk' });
        $q.notify({ type: 'positive', message: 'O.P. Finalizada.' });
      } catch (error) {
        $q.notify({ type: 'negative', message: 'Erro ao finalizar.' });
      } finally {
        $q.loading.hide();
      }
  });
}

function handleLogout() {
  $q.dialog({ title: 'Sair', message: 'Fazer logoff?', cancel: true }).onOk(() => {
    void (async () => { await productionStore.logoutOperator(); await router.push({ name: 'machine-kiosk' }); })();
  });
}

async function simulateOpScan() { await productionStore.loadOrderFromQr('OP-TESTE-4500'); resetTimer(); }
async function confirmAndonCall(sector: string) { isAndonDialogOpen.value = false; await productionStore.triggerAndon(sector, andonNote.value); andonNote.value = ''; }

async function handleSetupClick() {
  if (productionStore.isInSetup) {
      $q.dialog({ title: 'Finalizar Setup', message: 'Confirmar o fim da preparação?', cancel: true, persistent: true, ok: { label: 'Finalizar', color: 'positive' } })
        .onOk(async () => {
          $q.loading.show({ message: 'Registrando Setup...' });
          isLoadingAction.value = true;
          try {
              const now = new Date();
              const startSetup = statusStartTime.value;
              let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
              if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
              
              const setupPayload = {
                  op_number: '', resource_code: productionStore.machineResource || '4.02.01',
                  operator_id: String(badge), vehicle_id: productionStore.machineId || 0,
                  start_time: startSetup.toISOString(), end_time: now.toISOString(),
                  stop_reason: '52', stop_description: 'Setup' 
              };
              await ProductionService.sendAppointment(setupPayload);
              await productionStore.toggleSetup();
              
              const step = currentViewedStep.value; 
              const startPayload = { op_number: String(productionStore.activeOrder.code), step_seq: String(step.seq || ''), machine_id: Number(productionStore.machineId), operator_badge: String(badge) };
              const response = await api.post('/production/session/start', startPayload);
              
              if (response.data.status === 'success') {
                statusStartTime.value = new Date();
                if (activeOrder.value) activeOrder.value.status = 'RUNNING';
                await productionStore.setMachineStatus('RUNNING');
                $q.notify({ type: 'positive', message: 'Produção retomada!' });
              }
          } catch (error) {
              $q.notify({ type: 'negative', message: 'Erro no Setup.' });
          } finally {
              $q.loading.hide();
              isLoadingAction.value = false;
          }
      });
  } else {
      isLoadingAction.value = true;
      try {
          const now = new Date();
          if (normalizedStatus.value === 'EM OPERAÇÃO' && activeOrder.value?.code) {
              $q.loading.show({ message: 'Iniciando Setup...' });
              const productionStart = statusStartTime.value;
              let badge = productionStore.activeOperator.badge || productionStore.currentOperatorBadge;
              if (!badge && authStore.user?.employee_id) badge = authStore.user.employee_id;
              
              const productionPayload = {
                  op_number: String(opNumberToSend.value), position: currentViewedStep.value?.seq?.toString().padStart(3, '0') || '010',
                  resource_code: productionStore.machineResource || '4.02.01',
                  operator_id: String(badge), vehicle_id: productionStore.machineId || 0,
                  start_time: productionStart.toISOString(), end_time: now.toISOString(),
                  stop_reason: '', stop_description: '' 
              };
              await ProductionService.sendAppointment(productionPayload);
          }
          await productionStore.toggleSetup();
          await productionStore.setMachineStatus('MAINTENANCE'); 
          statusStartTime.value = new Date(); 
          $q.notify({ type: 'info', message: 'Modo Setup Iniciado.' });
      } catch (e) {
          $q.notify({ type: 'negative', message: 'Erro ao iniciar Setup.' });
      } finally {
          $q.loading.hide();
          isLoadingAction.value = false;
      }
  }
}

let scanBuffer = '';
let scanTimeout: any = null;
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

onMounted(() => {
  if (productionStore.currentStepIndex !== -1) viewedStepIndex.value = productionStore.currentStepIndex;
  timerInterval = setInterval(() => { currentTime.value = new Date(); }, 1000);
  resetTimer();
  window.addEventListener('keydown', handleGlobalKeydown);
  if (!productionStore.currentOperatorBadge && authStore.user?.employee_id && authStore.user.role !== 'admin') {
      productionStore.currentOperatorBadge = authStore.user.employee_id;
  }
});

onUnmounted(() => {
    window.removeEventListener('keydown', handleGlobalKeydown);
    clearInterval(timerInterval);
});
</script>

<style scoped>
.font-inter { font-family: 'Roboto', sans-serif; }
</style>
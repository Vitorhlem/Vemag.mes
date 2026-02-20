<template>
  <q-layout view="lHh Lpr fff" class="bg-dark text-white overflow-hidden">
    <q-page-container>
      <q-page class="flex flex-center column relative-position fullscreen-bg">
        
        <div class="absolute-full bg-industrial-gradient"></div>
        
        <div class="absolute-top text-center q-pt-md z-top">
           <img src="/Logo-Oficial.png" style="height: 45px; filter: brightness(0) invert(1) opacity(0.8);" />
        </div>

        <q-card 
          class="kiosk-card shadow-24 fade-in-up relative-position column" 
          :class="{'border-red': isMaintenanceMode, 'border-vemag': !isMaintenanceMode}"
        >
          <div class="absolute-top-right q-pa-sm">
             <q-badge 
                rounded 
                :color="isMaintenanceMode ? 'red-10' : 'positive'" 
                class="q-py-xs q-px-sm text-subtitle2 shadow-2"
             >
                <q-icon :name="isMaintenanceMode ? 'build_circle' : 'wifi'" class="q-mr-xs" />
                {{ isMaintenanceMode ? 'MANUTENÇÃO' : 'ONLINE' }}
             </q-badge>
          </div>

          <q-card-section class="col flex flex-center column q-pa-lg text-center">
            
            <div class="status-avatar-container q-mb-md">
                <q-avatar 
                    size="100px" 
                    font-size="50px" 
                    :color="isMaintenanceMode ? 'red-10' : 'white'" 
                    :text-color="isMaintenanceMode ? 'white' : 'teal-9'" 
                    :icon="isMaintenanceMode ? 'report_problem' : 'precision_manufacturing'" 
                    class="shadow-10 relative-position"
                    :class="{'animate-pulse-red': isMaintenanceMode}"
                >
                   <div v-if="!isMaintenanceMode" class="absolute-full ring-pulse"></div>
                </q-avatar>
            </div>
            
            <div class="text-h4 text-weight-bolder q-mb-xs text-white letter-spacing-1">
              {{ productionStore.machineName || 'Carregando...' }}
            </div>
            <div class="text-h6 text-grey-4 text-uppercase letter-spacing-2 q-mb-md">
              {{ productionStore.machineSector || '---' }}
            </div>
            
            <q-separator color="grey-8" class="full-width q-mb-md" />

            <div v-if="isLoading" class="column items-center q-gutter-y-md">
              <q-spinner-orbit color="vemag-green" size="4em" />
              <div class="text-h6 animate-blink text-vemag-green">Processando...</div>
            </div>

            <div v-else-if="isMaintenanceMode" class="column q-gutter-y-md full-width animate-fade-in">
                <div class="bg-red-9 q-pa-sm rounded-borders shadow-2">
                    <div class="text-h5 text-weight-bold text-white">EQUIPAMENTO PARADO</div>
                    <div class="text-subtitle1 text-red-2">Aguardando intervenção técnica.</div>
                </div>

                <q-btn 
                  push color="white" text-color="red-10" 
                  size="18px" padding="md"
                  icon="assignment_late" 
                  label="SOLICITAR MANUTENÇÃO (O.M.)" 
                  class="full-width shadow-10 hover-scale"
                  style="border-radius: 12px;"
                  @click="openMaintenanceDialog"
                />

                <q-btn flat color="grey-5" icon="lock_open" label="Liberar Máquina (Supervisor)" size="md" @click="unlockMachine" />
            </div>

            <div v-else class="column q-gutter-y-md full-width animate-fade-in items-center">
              <div v-if="!productionStore.isKioskConfigured" class="bg-red-10 text-white q-pa-sm rounded-borders text-subtitle1 text-weight-bold full-width">
                <q-icon name="warning" class="q-mr-sm" /> TERMINAL NÃO VINCULADO
              </div>

              <div class="text-h6 text-grey-4">Toque abaixo para iniciar o turno</div>
              
              <q-btn 
                push 
                class="full-width vemag-btn-primary shadow-10 hover-scale relative-position overflow-hidden" 
                size="22px" 
                padding="20px"
                @click="openBadgeScanner"
                :disable="!productionStore.isKioskConfigured"
                style="border-radius: 16px;"
              >
              
                <div class="row items-center no-wrap">
                    <q-icon name="qr_code_scanner" size="36px" class="q-mr-md" />
                    <div class="text-weight-bold">LER CRACHÁ</div>
                </div>
                <div class="shine-effect"></div>
              </q-btn>
              <q-btn 
  flat 
  color="white" 
  icon="keyboard" 
  label="Digitar Crachá (Manual)" 
  class="q-mt-sm full-width"
  @click="openManualLogin"
/>
              
              <q-btn flat color="grey-6" label="Configuração / Supervisor" size="sm" class="q-mt-sm opacity-50 hover-opacity-100" @click="openConfigDialog" />
            </div>
          </q-card-section>
          
          <q-card-section class="bg-black-transparent text-center q-py-sm">
            <div class="text-caption text-grey-6 font-monospace">
               ID TERMINAL: <span class="text-white">{{ productionStore.machineId || '--' }}</span>
            </div>
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>
    <q-dialog v-model="isManualLoginOpen" backdrop-filter="blur(4px)">
  <q-card style="min-width: 350px; border-radius: 16px;">
    <q-card-section class="bg-vemag-green text-white row items-center">
      <div class="text-h6">Acesso Manual</div>
      <q-space />
      <q-btn icon="close" flat round dense v-close-popup />
    </q-card-section>

    <q-card-section class="q-pt-lg">
      <q-input 
        outlined 
        v-model="manualBadgeInput" 
        label="Número do Crachá/Matrícula" 
        autofocus
        @keyup.enter="submitManualLogin"
        color="teal"
      >
        <template v-slot:prepend>
          <q-icon name="badge" />
        </template>
      </q-input>
    </q-card-section>

    <q-card-actions align="right" class="text-primary">
      <q-btn flat label="Cancelar" color="grey" v-close-popup />
      <q-btn push label="Entrar" color="teal-9" @click="submitManualLogin" />
    </q-card-actions>
  </q-card>
</q-dialog>

    <q-dialog v-model="isConfigOpen" backdrop-filter="blur(8px)">
      <q-card style="width: 450px; border-radius: 16px;" class="shadow-24">
        <q-card-section class="bg-vemag-green text-white q-py-sm">
          <div class="text-h6 text-weight-bold">Vincular Terminal</div>
        </q-card-section>
        <q-card-section class="q-pt-lg q-gutter-y-md">
          <div class="text-body2 text-grey-8">Selecione qual equipamento este tablet irá controlar.</div>
          <q-select 
            outlined dense
            v-model="selectedMachineOption" 
            :options="machineOptions" 
            label="Máquinas Disponíveis" 
            option-label="label" 
            option-value="value" 
            emit-value map-options 
            bg-color="grey-1"
            color="teal"
            :loading="isLoadingList" 
          />
          <q-input 
            outlined dense
            v-model="adminPassword" 
            type="password" 
            label="Senha de Supervisor" 
            bg-color="grey-1"
            color="teal"
          />
        </q-card-section>
        <q-card-actions align="right" class="bg-grey-1 q-pa-md">
          <q-btn flat label="Cancelar" color="grey-8" v-close-popup />
          <q-btn unelevated label="Salvar" color="teal-9" @click="saveConfig" :disable="adminPassword !== 'admin123' || !selectedMachineOption" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isMaintenanceDialogOpen" persistent transition-show="slide-up" transition-hide="slide-down">
  <q-card class="maintenance-card shadow-24 bg-white text-dark">
    <q-card-section class="bg-red-10 text-white row items-center q-py-lg">
      <q-avatar icon="engineering" color="white" text-color="red-10" size="50px" class="q-mr-md shadow-3" />
      <div class="column">
        <div class="text-h5 text-weight-bolder uppercase letter-spacing-1">Solicitar Técnico</div>
        <div class="text-caption opacity-80">Informe o problema para agilizar o reparo.</div>
      </div>
      <q-space />
      <q-btn icon="close" flat round dense v-close-popup />
    </q-card-section>

    <q-card-section class="q-pa-lg">
  <div class="text-overline text-grey-7 q-mb-sm">Onde está o problema?</div>
  <div class="row q-col-gutter-sm q-mb-lg">
    <div v-for="opt in subReasonOptions" :key="opt.value" class="col-6 col-sm-4">
      <q-btn 
        flat 
        bordered 
        class="full-width sub-reason-btn" 
        :class="{ 'sub-reason-active': maintenanceSubReason === opt.value }"
        @click="maintenanceSubReason = opt.value"
      >
        <div class="column items-center">
          <q-icon :name="opt.icon" size="24px" class="q-mb-xs" />
          <div class="text-caption text-weight-bold">{{ opt.label }}</div>
        </div>
      </q-btn>
    </div>
  </div>

  <div class="bg-grey-2 q-pa-md rounded-borders q-mb-md border-left-info">
      <div class="row items-center q-mb-xs">
          <q-icon name="person" size="xs" class="text-grey-7 q-mr-xs" />
          <span class="text-caption text-weight-bold text-grey-8">Solicitante:</span>
          <span class="text-caption q-ml-xs">{{ maintenanceOperatorName }}</span>
      </div>
      <div class="row items-center">
          <q-icon name="event" size="xs" class="text-grey-7 q-mr-xs" />
          <span class="text-caption text-weight-bold text-grey-8">Data/Hora:</span>
          <span class="text-caption q-ml-xs">{{ maintenanceTime }}</span>
      </div>
  </div>

  <div class="text-overline text-grey-7 q-mb-sm">Detalhes da Ocorrência:</div>
  <q-input
    v-model="maintenanceNote"
    filled
    type="textarea"
    placeholder="Descreva o defeito aqui..."
    bg-color="white"
    rows="3"
    class="text-subtitle1 shadow-1"
  />
</q-card-section>

    <q-card-actions align="between" class="q-px-lg q-pb-lg">
      <q-btn 
        flat 
        label="CANCELAR" 
        color="grey-7" 
        size="lg" 
        @click="cancelMaintenance" 
      />
      <q-btn 
        push 
        rounded
        :loading="isLoading"
        label="CONFIRMAR CHAMADO" 
        color="red-10" 
        icon-right="send"
        size="lg" 
        class="q-px-xl text-weight-bolder" 
        @click="submitMaintenance" 
      />
    </q-card-actions>
  </q-card>
</q-dialog>

    <q-dialog v-model="showScanner" maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-black text-white column">
        <q-bar class="bg-vemag-green q-pa-sm" style="height: 60px;">
          <q-icon name="qr_code_scanner" size="30px" />
          <div class="text-h6 q-ml-md text-weight-bold">Leitor de Crachá</div>
          <q-space />
          <q-btn dense flat icon="close" size="20px" v-close-popup @click="stopScanner">
            <q-tooltip>Fechar Câmera</q-tooltip>
          </q-btn>
        </q-bar>

        <q-card-section class="col flex flex-center column relative-position">
          <div class="scanner-frame relative-position">
              <div id="reader" style="width: 100%; height: 100%; background: #000;"></div>
              <div class="scan-line"></div>
          </div>
          
          <div class="text-h5 q-mt-lg text-grey-4 text-center text-weight-bold">
              Posicione o Código de Barras
          </div>
          <div class="text-subtitle1 text-vemag-green q-mt-sm">Matrícula ou Crachá</div>
          
          <div v-if="lastScannedCode" class="q-mt-md bg-white text-black q-pa-sm rounded-borders text-h5 text-weight-bold animate-blink shadow-10">
              LIDO: {{ lastScannedCode }}
          </div>

          <q-btn flat color="white" icon="cameraswitch" label="Trocar Câmera" size="md" class="q-mt-lg" @click="switchCamera" />
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useProductionStore } from 'stores/production-store';
import { useQuasar } from 'quasar';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';
import { useAuthStore } from 'stores/auth-store';
import { getOperatorName } from 'src/data/operators';

const router = useRouter();
const route = useRoute();
const productionStore = useProductionStore();
const $q = useQuasar();

// --- Estados ---
const isLoading = ref(false);
const isLoadingList = ref(false);
const isConfigOpen = ref(false);
const adminPassword = ref('');
const selectedMachineOption = ref<number | null>(null);
const authStore = useAuthStore();
const isMaintenanceDialogOpen = ref(false);
const maintenanceSubReason = ref('Mecânica');
const maintenanceOperatorName = ref('');
const maintenanceTime = ref('');
const maintenanceNote = ref('');
const subReasonOptions = [
  { label: 'Falha Mecânica', value: 'Mecânica', icon: 'settings' },
  { label: 'Falha Elétrica', value: 'Elétrica', icon: 'bolt' },
  { label: 'Hidráulica / Vazamento', value: 'Hidráulica', icon: 'water_drop' },
  { label: 'Pneumática / Ar', value: 'Pneumática', icon: 'air' },
  { label: 'Erro de Software / CNC', value: 'Software', icon: 'terminal' }
];

// ❌ pollingTimer REMOVIDO! Sistema agora é 100% Real-Time
let socket: WebSocket | null = null; 

const forcedMaintenance = ref(false);

// --- Scanner ---
const showScanner = ref(false);
const lastScannedCode = ref('');
let html5QrCode: Html5Qrcode | null = null;
const facingMode = ref<"user" | "environment">("environment");

// --- Computed ---
const machineOptions = computed(() => {
  return productionStore.machinesList.map(m => ({
    label: `${m.brand} ${m.model} (${m.license_plate || 'ID:' + m.id})`,
    value: m.id
  }));
});

// Verifica se a máquina está quebrada (Status MAINTENANCE)
const isMaintenanceMode = computed(() => {
    const status = (productionStore.currentMachine?.status || '').toUpperCase();
    
    if (status.includes('DISPONÍVEL') || status.includes('AVAILABLE') || status.includes('EM USO') || status.includes('EM OPERAÇÃO')) {
        return false;
    }

    if (route.query.state === 'maintenance' || forcedMaintenance.value) return true;

    return productionStore.isMachineBroken || status.includes('MAINTENANCE') || status.includes('MANUTENÇÃO');
});


// =========================================================
// 🔄 ESCUTA DO WEBSOCKET (Atualização Instantânea)
// =========================================================
function listenForMachineStatus() {
  if (!productionStore.machineId) return;

  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  
  // ✅ CORREÇÃO: Conectando no canal específico da máquina para evitar o erro 403!
  // (Caso o seu backend exija 'andon' na rota, mude para /ws/andon/${productionStore.machineId})
  const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/ws/${productionStore.machineId}`;

  socket = new WebSocket(wsUrl);

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      // Quando a manutenção for finalizada e o backend avisar...
      if (data.type === 'MACHINE_STATUS_CHANGED' || data.type === 'STATUS_CHANGE') {
          console.log(`📡 Rádio Kiosk: Novo status recebido -> ${data.status}`);
          
          if (productionStore.currentMachine) {
              productionStore.currentMachine.status = data.status;
          }

          const s = String(data.status).toUpperCase();
          if (s.includes('DISPONÍVEL') || s.includes('AVAILABLE') || s.includes('EM USO') || s.includes('RUNNING')) {
              forcedMaintenance.value = false;
              if (route.query.state === 'maintenance') {
                  void router.replace({ query: {} }); // Limpa a URL
              }
          }
      }
    } catch (e) {
      console.error("Erro ao ler rádio", e);
    }
  };

  socket.onclose = () => {
     // Auto-reconecta caso a internet pisque
     setTimeout(() => { 
       if (!socket || socket.readyState === WebSocket.CLOSED) listenForMachineStatus(); 
     }, 3000);
  };
}


// --- Ciclo de Vida ---
onMounted(async () => {
  await productionStore.loadKioskConfig();
  
  if (productionStore.machineId) {
    selectedMachineOption.value = productionStore.machineId;
    
    // ✅ 1. Busca o status REAL apenas uma vez ao abrir a tela
    await productionStore.fetchMachine(productionStore.machineId);
    
    // ✅ 2. Liga o rádio para ficar escutando
    listenForMachineStatus(); 
  }
  
  if (route.query.state === 'maintenance') {
      forcedMaintenance.value = true;
  }

  // ❌ TODO O BLOCO DO setInterval FOI REMOVIDO! A máquina não vai mais bombardear o servidor.

  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
   // ❌ clearInterval(pollingTimer) removido
   window.removeEventListener('keydown', handleKeydown);
   void stopScanner();
   if (socket) {
     socket.onclose = null; // Evita loop de reconexão ao sair da página
     socket.close();
   }
});

// --- SCANNER DE CÂMERA ---
function openBadgeScanner() {
  if (!productionStore.isKioskConfigured) {
    $q.notify({ type: 'warning', message: 'Necessário configurar terminal.' });
    return;
  }
  showScanner.value = true;
  lastScannedCode.value = '';
  setTimeout(() => { void startScanner(); }, 500);
}

async function startScanner() {
    try {
        if (html5QrCode) await stopScanner();
        html5QrCode = new Html5Qrcode("reader");
        
        const config = { 
            fps: 20, 
            qrbox: { width: 400, height: 150 },
            aspectRatio: 1.0,
            formatsToSupport: [ 
                Html5QrcodeSupportedFormats.QR_CODE,
                Html5QrcodeSupportedFormats.CODE_128,
                Html5QrcodeSupportedFormats.CODE_39,
                Html5QrcodeSupportedFormats.EAN_13,
                Html5QrcodeSupportedFormats.UPC_A,
                Html5QrcodeSupportedFormats.ITF
            ],
            experimentalFeatures: {
                useBarCodeDetectorIfSupported: true
            }
        };
        
        await html5QrCode.start(
            { facingMode: facingMode.value }, 
            config, 
            (decodedText) => { void onScanSuccess(decodedText) }, 
        );
    } catch(e) { 
        console.error("Erro ao iniciar camera:", e);
        $q.notify({type:'negative', message:'Erro ao acessar câmera.'});
        showScanner.value = false;
    }
}

async function stopScanner() {
    if (html5QrCode) {
        try { if (html5QrCode.isScanning) await html5QrCode.stop(); html5QrCode.clear(); } catch (err) { console.error(err); }
        html5QrCode = null;
    }
}

async function onScanSuccess(decodedText: string) {
    console.log("CÓDIGO LIDO:", decodedText);
    lastScannedCode.value = decodedText;
    await stopScanner();
    showScanner.value = false;
    await handleLogin(decodedText);
}

async function switchCamera() {
    facingMode.value = facingMode.value === "environment" ? "user" : "environment";
    await startScanner();
}


const isManualLoginOpen = ref(false);
const manualBadgeInput = ref('');

function openManualLogin() {
  manualBadgeInput.value = '';
  isManualLoginOpen.value = true;
}

async function submitManualLogin() {
  if (!manualBadgeInput.value || manualBadgeInput.value.length < 3) {
    $q.notify({ type: 'warning', message: 'Digite um código válido.' });
    return;
  }
  isManualLoginOpen.value = false;
  await handleLogin(manualBadgeInput.value);
}

// --- LEITOR USB (TECLADO) ---
let keyBuffer = '';
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let keyTimeout: any = null;

function handleKeydown(event: KeyboardEvent) {
    const target = event.target as HTMLElement;
    if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return; 
    }

    if (isMaintenanceMode.value) return;

    if (event.key === 'Enter') {
        if (keyBuffer.length > 2) {
            const code = keyBuffer;
            keyBuffer = ''; 
            void handleLogin(code);
        }
        keyBuffer = '';
    } else {
        if (event.key.length === 1) {
            keyBuffer += event.key;
            clearTimeout(keyTimeout);
            keyTimeout = setTimeout(() => { keyBuffer = ''; }, 2000);
        }
    }
}

// --- LOGIN DO OPERADOR ---
async function handleLogin(code: string) {
    if (isMaintenanceMode.value) {
        $q.notify({ type: 'warning', message: 'Máquina em manutenção. Operação bloqueada.' });
        return;
    }

    isLoading.value = true;
    try {
        await productionStore.loginOperator(code);
        if (productionStore.isShiftActive) {
             void router.push({ 
                name: 'operator-cockpit', 
                params: { machineId: productionStore.machineId } 
             });
        }
    } catch (e) {
        console.error(e);
        $q.notify({ type: 'negative', message: 'Crachá inválido ou erro de conexão.' });
    } finally {
        isLoading.value = false;
    }
}

// --- CONFIGURAÇÃO ---
async function openConfigDialog() {
  adminPassword.value = '';
  selectedMachineOption.value = productionStore.machineId; 
  isConfigOpen.value = true;
  isLoadingList.value = true;
  await productionStore.fetchAvailableMachines();
  isLoadingList.value = false;
}

async function saveConfig() {
  if (adminPassword.value !== 'admin123') {
    $q.notify({ type: 'negative', message: 'Senha incorreta.' });
    return;
  }
  if (selectedMachineOption.value) {
    await productionStore.configureKiosk(selectedMachineOption.value);
    isConfigOpen.value = false;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
       listenForMachineStatus();
    }
  }
}

// --- MANUTENÇÃO (ABRIR O.M.) ---
function openMaintenanceDialog() {
    let badge = route.query.last_operator;

    if (!badge) {
        badge = productionStore.activeOperator?.badge || productionStore.currentOperatorBadge;
    }
    
    if (!badge && authStore.user?.employee_id) {
        badge = authStore.user.employee_id;
    }
    
    let displayName = '';
    
    if (badge) {
        const nameFromList = getOperatorName(String(badge));
        displayName = nameFromList || `Crachá: ${String(badge)}`;
    }
    
    maintenanceOperatorName.value = displayName || 'Operador não identificado';
    maintenanceTime.value = new Date().toLocaleString('pt-BR');
    maintenanceSubReason.value = 'Mecânica';
    maintenanceNote.value = '';
    
    isMaintenanceDialogOpen.value = true;
}

function cancelMaintenance() {
    isMaintenanceDialogOpen.value = false;
    maintenanceNote.value = '';
}

async function submitMaintenance() {
    isLoading.value = true;
    
    const finalDescription = `
[SOLICITAÇÃO DE MANUTENÇÃO]
👤 Solicitante: ${maintenanceOperatorName.value}
📅 Abertura: ${maintenanceTime.value}
⚠️ Categoria: ${maintenanceSubReason.value}
-----------------------------------
📝 Relato: ${maintenanceNote.value || 'Sem detalhes adicionais.'}
`.trim();

    try {
        await productionStore.createMaintenanceOrder(finalDescription);
        
        isMaintenanceDialogOpen.value = false;
        maintenanceNote.value = '';
        $q.notify({ type: 'positive', icon: 'check_circle', message: 'O.M. Enviada com sucesso!' });
    } catch (e) {
        console.error(e);
        $q.notify({ type: 'negative', message: 'Erro ao criar O.M.' });
    } finally {
        isLoading.value = false;
    }
}

// --- DESBLOQUEIO DE MÁQUINA ---
function unlockMachine() {
    $q.dialog({
        title: 'Desbloqueio Supervisão',
        message: 'Senha de supervisor para liberar:',
        prompt: { model: '', type: 'password' },
        cancel: true,
        persistent: true,
        ok: { label: 'LIBERAR', color: 'positive' }
    }).onOk((inputPassword: string) => {
        void (async () => { 
            const pass = String(inputPassword).trim();

            if (pass === '1234' || pass === 'admin123') {
                $q.loading.show({ message: 'Liberando sistema...' });
                
                try {
                    await productionStore.sendEvent('STATUS_CHANGE', { 
                        new_status: 'AVAILABLE', 
                        reason: 'Fim de Manutenção (Desbloqueio Manual)' 
                    }, 'SUPERVISOR'); 

                    await productionStore.setMachineStatus('AVAILABLE');
                    
                    forcedMaintenance.value = false;
                    await router.replace({ query: {} });

                    $q.notify({ type: 'positive', message: 'Máquina Liberada com sucesso!' });
                } catch (e) {
                    console.error(e);
                    forcedMaintenance.value = false;
                    $q.notify({ type: 'warning', message: 'Liberado localmente (Sincronizando...)' });
                } finally {
                    $q.loading.hide();
                }
            } else {
                $q.notify({ type: 'negative', icon: 'lock', message: 'Senha incorreta.' });
            }
        })(); 
    }); 
}

</script>
<style scoped>
/* CORES VEMAG */
.text-vemag-green { color: #008C7A !important; }
.bg-vemag-green { background-color: #008C7A !important; }
.bg-industrial-gradient {
    background: radial-gradient(circle at top right, #2a2a2a 0%, #121212 100%);
    background-image: url('/vemag.png'); 
    background-size: cover;
    background-blend-mode: overlay;
    opacity: 0.6;
}

/* BOTÃO PRINCIPAL */
.vemag-btn-primary {
    background: linear-gradient(135deg, #008C7A 0%, #00695C 100%);
    transition: all 0.3s ease;
}
.vemag-btn-primary:active { transform: scale(0.98); filter: brightness(0.9); }

/* CARD ESTILIZADO */
.kiosk-card {
    width: 500px; 
    max-width: 90vw;
    border-radius: 24px;
    background: #1e1e1e; 
    border: 1px solid rgba(255,255,255,0.1);
    z-index: 10;
}
.border-vemag { border-top: 6px solid #008C7A; }
.border-red { border-top: 6px solid #b71c1c; box-shadow: 0 0 20px rgba(183, 28, 28, 0.4); }

.bg-black-transparent { background: rgba(0,0,0,0.4); }

/* ANIMAÇÕES */
.hover-scale { transition: transform 0.2s; }
.hover-scale:hover { transform: scale(1.02); }

.hover-opacity-100 { transition: opacity 0.3s; }
.hover-opacity-100:hover { opacity: 1; }

.animate-blink { animation: blink 2s infinite; }
.animate-pulse-red { animation: pulseRed 2s infinite; }
.fade-in-up { animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); }
.animate-fade-in { animation: fadeIn 0.5s ease-in; }

.ring-pulse {
    border: 2px solid #008C7A;
    border-radius: 50%;
    animation: ringPulse 2s infinite;
}

/* SCANNER OVERLAY */
.scanner-frame {
    width: 90%;
    max-width: 500px;
    height: 250px;
    border: 3px solid rgba(255,255,255,0.3);
    border-radius: 16px;
    overflow: hidden;
    position: relative;
    box-shadow: 0 0 0 1000px rgba(0,0,0,0.7);
}
.scan-line {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: #008C7A;
    box-shadow: 0 0 8px #008C7A;
    animation: scanMove 2s infinite linear;
}
.maintenance-card {
  width: 600px;
  max-width: 95vw;
  border-radius: 20px;
}

.border-left-info {
  border-left: 4px solid #008C7A;
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

.letter-spacing-1 { letter-spacing: 1px; }
.opacity-80 { opacity: 0.8; }

/* SHINE EFFECT */
.shine-effect {
    position: absolute;
    top: 0; left: -100%;
    width: 50%; height: 100%;
    background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0) 100%);
    transform: skewX(-20deg);
    animation: shine 3s infinite;
}

/* KEYFRAMES */
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(40px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes pulseRed { 0% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); } 70% { box-shadow: 0 0 0 20px rgba(255, 0, 0, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); } }
@keyframes ringPulse { 0% { transform: scale(1); opacity: 1; } 100% { transform: scale(1.3); opacity: 0; } }
@keyframes scanMove { 0% { top: 0; } 50% { top: 100%; } 100% { top: 0; } }
@keyframes shine { 0% { left: -100%; } 20% { left: 200%; } 100% { left: 200%; } }

.opacity-50 { opacity: 0.5; }
.opacity-60 { opacity: 0.6; }
.opacity-30 { opacity: 0.3; }
.opacity-80 { opacity: 0.8; }
.letter-spacing-1 { letter-spacing: 1px; }
.letter-spacing-2 { letter-spacing: 2px; }
.font-monospace { font-family: monospace; }
.fullscreen-bg { width: 100vw; height: 100vh; overflow: hidden; }
</style>
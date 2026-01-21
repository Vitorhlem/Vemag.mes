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
              <div class="text-h6 animate-blink text-vemag-green">Carregando...</div>
            </div>

            <div v-else-if="isMaintenanceMode" class="column q-gutter-y-md full-width animate-fade-in">
                <div class="bg-red-9 q-pa-sm rounded-borders shadow-2">
                    <div class="text-h5 text-weight-bold text-white">EQUIPAMENTO PARADO</div>
                    <div class="text-subtitle1 text-red-2">Aguardando manutenção.</div>
                </div>

                <q-btn 
                  push color="white" text-color="red-10" 
                  size="18px" padding="md"
                  icon="assignment_late" 
                  label="ABRIR O.M. (CONFIRMAR)" 
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

              <div class="text-h6 text-grey-4">Toque para iniciar turno</div>
              
              <q-btn 
                push 
                class="full-width vemag-btn-primary shadow-10 hover-scale relative-position overflow-hidden" 
                size="22px" padding="20px"
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
              
              <q-btn flat color="grey-6" label="Configuração" size="sm" @click="openConfigDialog" />
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

    <q-dialog v-model="isMaintenanceDialogOpen" persistent maximized transition-show="slide-up" transition-hide="slide-down">
       <q-card class="bg-red-50 text-dark">
          <q-toolbar class="bg-red-10 text-white">
             <q-icon name="report_problem" size="30px" class="q-mr-md" />
             <q-toolbar-title class="text-h6 text-weight-bold">Detalhes da Quebra</q-toolbar-title>
             <q-btn flat round icon="close" size="lg" v-close-popup />
          </q-toolbar>
          <q-card-section class="q-pa-lg column flex-center h-100">
             <div class="full-width" style="max-width: 600px;">
                 <div class="text-h6 text-grey-8">Equipamento: {{ productionStore.machineName }}</div>
                 <q-input v-model="omDescription" type="textarea" outlined rows="5" placeholder="Descreva o problema..." class="text-body1 bg-white shadow-1" autofocus />
                 <div class="row q-mt-lg q-gutter-md">
                     <q-btn flat label="Cancelar" color="grey-8" size="lg" class="col" v-close-popup />
                     <q-btn push color="red-10" label="CONFIRMAR ABERTURA" icon="send" size="lg" class="col shadow-5" :loading="isLoading" @click="submitMaintenance" />
                 </div>
             </div>
          </q-card-section>
       </q-card>
    </q-dialog>

    <q-dialog v-model="showScanner" maximized>
        <q-card class="bg-black text-white column">
            <q-bar class="bg-vemag-green q-pa-sm" style="height: 60px;">
                <q-icon name="badge" size="30px" />
                <div class="text-h6 q-ml-md text-weight-bold">Posicione o Crachá</div>
                <q-space />
                <q-btn dense flat icon="close" size="20px" v-close-popup @click="stopScanner" />
            </q-bar>
            
            <q-card-section class="col flex flex-center column relative-position q-pa-none bg-black">
                <div id="reader" style="width: 100%; height: 100%; position: absolute; top: 0; left: 0; z-index: 0;"></div>
                
                <div class="scanner-overlay z-top flex flex-center">
                    <div class="scanner-frame relative-position">
                        <div class="scan-line"></div>
                        <div class="corner-tl"></div>
                        <div class="corner-tr"></div>
                        <div class="corner-bl"></div>
                        <div class="corner-br"></div>
                    </div>
                </div>

                <div class="absolute-bottom text-center q-pb-xl z-top">
                    <div class="text-h6 text-white bg-black-transparent q-px-md q-py-sm rounded-borders inline-block">
                        Aponte a câmera para o código
                    </div>
                    <div class="q-mt-md">
                        <q-btn round color="white" text-color="black" icon="cameraswitch" size="lg" @click="switchCamera" />
                    </div>
                </div>
            </q-card-section>
        </q-card>
    </q-dialog>

    <q-dialog v-model="isConfigOpen">
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

  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router'; 
import { useProductionStore } from 'stores/production-store';
import { useAuthStore } from 'stores/auth-store';
import { useQuasar } from 'quasar';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';

const router = useRouter();
const route = useRoute(); 
const productionStore = useProductionStore();
const authStore = useAuthStore();
const $q = useQuasar();

// --- Estados ---
const isLoading = ref(false);
const isLoadingList = ref(false);
const isConfigOpen = ref(false);
const adminPassword = ref('');
const selectedMachineOption = ref<number | null>(null);
const machineOptions = computed(() => productionStore.machinesList.map(m => ({ label: m.brand, value: m.id })));

const isMaintenanceDialogOpen = ref(false);
const omDescription = ref('');
const showScanner = ref(false);
const lastScannedCode = ref('');
let html5QrCode: Html5Qrcode | null = null;
const facingMode = ref<"user" | "environment">("environment");
let pollingTimer: ReturnType<typeof setInterval>;

// --- LÓGICA DE DETECÇÃO DE MANUTENÇÃO ---
const forcedMaintenance = ref(false);

const isMaintenanceMode = computed(() => {
    if (route.query.state === 'maintenance' || forcedMaintenance.value) return true;
    const status = (productionStore.currentMachine?.status || '').toUpperCase();
    return productionStore.isMachineBroken || status.includes('MAINTENANCE') || status.includes('MANUTENÇÃO');
});

// --- Ciclo de Vida ---
onMounted(async () => {
  await productionStore.loadKioskConfig();
  if (productionStore.machineId) {
    selectedMachineOption.value = productionStore.machineId;
  }
  
  if (route.query.state === 'maintenance') {
      forcedMaintenance.value = true;
  }

  pollingTimer = setInterval(async () => {
      if(productionStore.machineId) {
          await productionStore.loadKioskConfig();
          const status = (productionStore.currentMachine?.status || '').toUpperCase();
          const isBackendBroken = productionStore.isMachineBroken || status.includes('MAINTENANCE') || status.includes('MANUTENÇÃO');
          if ((forcedMaintenance.value || route.query.state === 'maintenance') && !isBackendBroken) {
              forcedMaintenance.value = false;
              await router.replace({ query: {} }); 
              $q.notify({ type: 'positive', message: 'Máquina Liberada!' });
          }
      }
  }, 3000);

  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
   clearInterval(pollingTimer);
   window.removeEventListener('keydown', handleKeydown);
   void stopScanner();
});

// --- FUNÇÕES ---

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
        
        // Configuração ajustada para priorizar leitura vertical (Crachá)
        await html5QrCode.start(
            { facingMode: facingMode.value }, 
            { 
                fps: 15, 
                qrbox: { width: 250, height: 350 }, // Formato Retangular Vertical
                aspectRatio: 1.0 
            }, 
            (decodedText) => { void onScanSuccess(decodedText) }, 
            undefined
        );
    } catch(e) { 
        console.error(e);
        $q.notify({type:'negative', message:'Câmera indisponível'});
        showScanner.value = false;
    }
}

async function stopScanner() {
    if(html5QrCode) { 
        try { if(html5QrCode.isScanning) await html5QrCode.stop(); html5QrCode.clear(); } catch(e){ console.error(e); }
        html5QrCode = null;
    }
}

async function onScanSuccess(decodedText: string) {
    lastScannedCode.value = decodedText;
    await stopScanner();
    showScanner.value = false;
    void handleLogin(decodedText);
}

let keyBuffer = '';
let keyTimeout: any = null;
function handleKeydown(event: KeyboardEvent) {
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

async function handleLogin(code: string) {
    if (isMaintenanceMode.value) return $q.notify({type:'warning', message: 'Máquina Quebrada.'});
    isLoading.value = true;
    try {
        await productionStore.loginOperator(code);
        if (productionStore.isShiftActive) router.push({ name: 'operator-cockpit' });
    } catch(e) {
        $q.notify({type:'negative', message: 'Erro no login.'});
    } finally {
        isLoading.value = false;
    }
}

function openMaintenanceDialog() {
    const now = new Date().toLocaleString('pt-BR');
    omDescription.value = `Parada reportada em ${now}.\nMotivo: Falha no equipamento detectada pelo operador.`;
    isMaintenanceDialogOpen.value = true;
}

async function submitMaintenance() {
    isLoading.value = true;
    await productionStore.createMaintenanceOrder(omDescription.value || 'Quebra reportada');
    isMaintenanceDialogOpen.value = false;
    isLoading.value = false;
    $q.notify({ type: 'positive', message: 'O.M. Confirmada!' });
}

function unlockMachine() {
    $q.dialog({ title: 'Senha Supervisor', prompt: { model: '', type: 'password' } }).onOk(pass => {
        if(pass === '1234') {
            forcedMaintenance.value = false; 
            void productionStore.setMachineStatus('AVAILABLE');
            router.replace({ query: {} }); 
            $q.notify({ type: 'positive', message: 'Liberada.' });
        } else {
            $q.notify({ type: 'negative', message: 'Senha incorreta.' });
        }
    });
}

function openConfigDialog() { isConfigOpen.value = true; adminPassword.value = ''; void productionStore.fetchAvailableMachines(); }

async function saveConfig() {
    if(adminPassword.value !== 'admin123') return $q.notify({type:'negative', message:'Senha incorreta'});
    if(selectedMachineOption.value) {
        await productionStore.configureKiosk(selectedMachineOption.value);
        isConfigOpen.value = false;
    }
}

function switchCamera() { 
    facingMode.value = facingMode.value === "environment" ? "user" : "environment";
    void startScanner();
}
</script>

<style scoped>
.bg-industrial-gradient {
    background: radial-gradient(circle at top right, #2a2a2a 0%, #121212 100%);
    background-image: url('/vemag.png'); 
    background-size: cover;
    background-blend-mode: overlay;
    opacity: 0.6;
}
.vemag-btn-primary {
    background: linear-gradient(135deg, #008C7A 0%, #00695C 100%);
    transition: all 0.3s ease;
}
.vemag-btn-primary:active { transform: scale(0.98); filter: brightness(0.9); }
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
.hover-scale { transition: transform 0.2s; }
.hover-scale:hover { transform: scale(1.02); }
.hover-opacity-100 { transition: opacity 0.3s; }
.hover-opacity-100:hover { opacity: 1; }
.animate-blink { animation: blink 2s infinite; }
.animate-pulse-red { animation: pulseRed 2s infinite; }
.fade-in-up { animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); }
.animate-fade-in { animation: fadeIn 0.5s ease-in; }
.ring-pulse { border: 2px solid #008C7A; border-radius: 50%; animation: ringPulse 2s infinite; }

/* === NOVO ESTILO DO SCANNER === */
.scanner-overlay {
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.7); /* Escurece tudo em volta */
    position: absolute;
    top: 0; left: 0;
}

.scanner-frame {
    width: 300px; /* Largura crachá */
    height: 450px; /* Altura crachá */
    border: 3px solid rgba(0, 140, 122, 0.6); /* Verde Vemag */
    border-radius: 20px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 0 1000px rgba(0,0,0,0.6); /* Máscara forte em volta */
    background: transparent;
}

/* Cantos decorativos para parecer viewfinder */
.corner-tl, .corner-tr, .corner-bl, .corner-br {
    position: absolute;
    width: 40px; height: 40px;
    border-color: #008C7A;
    border-style: solid;
    border-width: 0;
}
.corner-tl { top: 0; left: 0; border-top-width: 5px; border-left-width: 5px; border-top-left-radius: 20px; }
.corner-tr { top: 0; right: 0; border-top-width: 5px; border-right-width: 5px; border-top-right-radius: 20px; }
.corner-bl { bottom: 0; left: 0; border-bottom-width: 5px; border-left-width: 5px; border-bottom-left-radius: 20px; }
.corner-br { bottom: 0; right: 0; border-bottom-width: 5px; border-right-width: 5px; border-bottom-right-radius: 20px; }

/* Laser de Escaneamento */
.scan-line {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: #00ffcc;
    box-shadow: 0 0 15px #00ffcc, 0 0 30px #008C7A;
    animation: scanAnimation 2.5s infinite linear;
    opacity: 0.8;
}

@keyframes scanAnimation {
    0% { top: 0; opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { top: 100%; opacity: 0; }
}

.shine-effect { position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0) 100%); transform: skewX(-20deg); animation: shine 3s infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(40px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes pulseRed { 0% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); } 70% { box-shadow: 0 0 0 20px rgba(255, 0, 0, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); } }
@keyframes ringPulse { 0% { transform: scale(1); opacity: 1; } 100% { transform: scale(1.3); opacity: 0; } }
@keyframes shine { 0% { left: -100%; } 20% { left: 200%; } 100% { left: 200%; } }
.opacity-50 { opacity: 0.5; } .opacity-60 { opacity: 0.6; } .opacity-30 { opacity: 0.3; } .opacity-80 { opacity: 0.8; }
.letter-spacing-1 { letter-spacing: 1px; } .letter-spacing-2 { letter-spacing: 2px; }
.font-monospace { font-family: monospace; }
.fullscreen-bg { width: 100vw; height: 100vh; overflow: hidden; }
</style>
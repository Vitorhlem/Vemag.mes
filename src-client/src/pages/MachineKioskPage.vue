<template>
  <q-layout view="lHh Lpr fff" class="bg-dark text-white overflow-hidden">
    <q-page-container>
      <q-page class="flex flex-center column relative-position fullscreen-bg">
        
        <div class="absolute-full bg-industrial-gradient"></div>
        
        <div class="absolute-top text-center q-pt-xl z-top">
           <img src="/Logo-Oficial.png" style="height: 60px; filter: brightness(0) invert(1) opacity(0.8);" />
        </div>

        <q-card 
          class="kiosk-card shadow-24 fade-in-up relative-position column" 
          :class="{'border-red': productionStore.isMachineBroken, 'border-vemag': !productionStore.isMachineBroken}"
        >
          <div class="absolute-top-right q-pa-md">
             <q-badge 
                rounded 
                :color="productionStore.isMachineBroken ? 'red-10' : 'positive'" 
                class="q-py-sm q-px-md text-subtitle1 shadow-2"
             >
                <q-icon :name="productionStore.isMachineBroken ? 'build_circle' : 'wifi'" class="q-mr-sm" />
                {{ productionStore.isMachineBroken ? 'MANUTENÇÃO' : 'ONLINE' }}
             </q-badge>
          </div>

          <q-card-section class="col flex flex-center column q-pa-xl text-center">
            
            <div class="status-avatar-container q-mb-lg">
                <q-avatar 
                    size="140px" 
                    font-size="80px" 
                    :color="productionStore.isMachineBroken ? 'red-10' : 'white'" 
                    :text-color="productionStore.isMachineBroken ? 'white' : 'teal-9'" 
                    :icon="productionStore.isMachineBroken ? 'report_problem' : 'precision_manufacturing'" 
                    class="shadow-10 relative-position"
                    :class="{'animate-pulse-red': productionStore.isMachineBroken}"
                >
                   <div v-if="!productionStore.isMachineBroken" class="absolute-full ring-pulse"></div>
                </q-avatar>
            </div>
            
            <div class="text-h3 text-weight-bolder q-mb-sm text-white letter-spacing-1">
              {{ productionStore.machineName }}
            </div>
            <div class="text-h5 text-grey-4 text-uppercase letter-spacing-2 q-mb-xl">
              {{ productionStore.machineSector }}
            </div>
            
            <q-separator color="grey-8" class="full-width q-mb-xl" />

            <div v-if="isLoading" class="column items-center q-gutter-y-lg">
              <q-spinner-orbit color="vemag-green" size="6em" />
              <div class="text-h5 animate-blink text-vemag-green">Validando Acesso...</div>
            </div>

            <div v-else-if="productionStore.isMachineBroken" class="column q-gutter-y-lg full-width animate-fade-in">
                <div class="bg-red-9 q-pa-md rounded-borders shadow-2">
                    <div class="text-h4 text-weight-bold text-white">EQUIPAMENTO PARADO</div>
                    <div class="text-h6 text-red-2 q-mt-sm">Reportado falha/quebra. Necessário abrir O.M.</div>
                </div>

                <q-btn 
                  push color="white" text-color="red-10" 
                  size="24px" padding="lg"
                  icon="assignment_late" 
                  label="ABRIR ORDEM DE MANUTENÇÃO" 
                  class="full-width shadow-10 hover-scale"
                  style="border-radius: 16px;"
                  @click="openMaintenanceDialog"
                />

                <q-btn flat color="grey-5" icon="lock_open" label="Liberar (Supervisor)" size="lg" class="q-mt-md" @click="unlockMachine" />
            </div>

            <div v-else class="column q-gutter-y-lg full-width animate-fade-in items-center">
              <div v-if="!productionStore.isKioskConfigured" class="bg-red-10 text-white q-pa-md rounded-borders text-h6 text-weight-bold full-width">
                <q-icon name="warning" class="q-mr-sm" /> TERMINAL NÃO VINCULADO
              </div>

              <div class="text-h5 text-grey-4">Toque abaixo para iniciar o turno</div>
              
              <q-btn 
                push 
                class="full-width vemag-btn-primary shadow-10 hover-scale relative-position overflow-hidden" 
                size="32px" 
                padding="30px"
                @click="openBadgeScanner"
                :disable="!productionStore.isKioskConfigured"
                style="border-radius: 20px;"
              >
                <div class="row items-center no-wrap">
                    <q-icon name="qr_code_scanner" size="50px" class="q-mr-md" />
                    <div class="text-weight-bold">ESCANEAR CRACHÁ</div>
                </div>
                <div class="shine-effect"></div>
              </q-btn>
              
              <q-btn flat color="grey-6" label="Configuração / Supervisor" size="md" class="q-mt-lg opacity-50 hover-opacity-100" @click="openConfigDialog" />
            </div>
          </q-card-section>
          
          <q-card-section class="bg-black-transparent text-center q-py-md">
            <div class="text-subtitle1 text-grey-6 font-monospace">
               ID TERMINAL: <span class="text-white">{{ productionStore.machineId || '--' }}</span>
            </div>
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>

    <q-dialog v-model="isConfigOpen" backdrop-filter="blur(8px)">
      <q-card style="width: 500px; border-radius: 16px;" class="shadow-24">
        <q-card-section class="bg-vemag-green text-white">
          <div class="text-h5 text-weight-bold">Vincular Terminal</div>
        </q-card-section>
        <q-card-section class="q-pt-lg q-gutter-y-lg">
          <div class="text-body1 text-grey-8">Selecione qual equipamento este tablet irá controlar.</div>
          <q-select 
            outlined 
            v-model="selectedMachineOption" 
            :options="machineOptions" 
            label="Máquinas Disponíveis" 
            option-label="label" 
            option-value="value" 
            emit-value map-options 
            bg-color="grey-1"
            color="teal"
            class="text-h6"
            :loading="isLoadingList" 
          />
          <q-input 
            outlined 
            v-model="adminPassword" 
            type="password" 
            label="Senha de Supervisor" 
            class="text-h6"
            bg-color="grey-1"
            color="teal"
          />
        </q-card-section>
        <q-card-actions align="right" class="bg-grey-1 q-pa-md">
          <q-btn flat label="Cancelar" color="grey-8" size="lg" v-close-popup />
          <q-btn unelevated label="Salvar Vínculo" color="teal-9" size="lg" @click="saveConfig" :disable="adminPassword !== 'admin123' || !selectedMachineOption" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isMaintenanceDialogOpen" persistent maximized transition-show="slide-up" transition-hide="slide-down">
       <q-card class="bg-red-50 text-dark">
          <q-toolbar class="bg-red-10 text-white q-py-md">
             <q-icon name="report_problem" size="40px" class="q-mr-md" />
             <q-toolbar-title class="text-h4 text-weight-bold">Abertura de O.M. - Corretiva</q-toolbar-title>
             <q-btn flat round icon="close" size="xl" v-close-popup />
          </q-toolbar>
          
          <q-card-section class="q-pa-xl column flex-center h-100">
             <div class="full-width" style="max-width: 800px;">
                 <div class="text-h5 text-grey-8 q-mb-sm">Equipamento</div>
                 <div class="text-h3 text-weight-bold text-dark q-mb-xl">{{ productionStore.machineName }}</div>
                 
                 <div class="text-h5 text-grey-8 q-mb-sm">Descrição do Problema</div>
                 <q-input 
                    v-model="omDescription" 
                    type="textarea" 
                    outlined 
                    rows="6" 
                    placeholder="Descreva o detalhe da quebra aqui..." 
                    class="text-h5 bg-white shadow-1"
                    autofocus 
                 />
                 
                 <div class="row q-mt-xl q-gutter-lg">
                     <q-btn flat label="Cancelar" color="grey-8" size="xl" class="col" v-close-popup />
                     <q-btn push color="red-10" label="CONFIRMAR ABERTURA" icon="send" size="xl" class="col shadow-5" :loading="isLoading" @click="submitMaintenance" :disable="!omDescription" />
                 </div>
             </div>
          </q-card-section>
       </q-card>
    </q-dialog>

    <q-dialog v-model="showScanner" maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-black text-white column">
        <q-bar class="bg-vemag-green q-pa-md" style="height: 80px;">
          <q-icon name="qr_code_scanner" size="40px" />
          <div class="text-h4 q-ml-md text-weight-bold">Leitor de Crachá</div>
          <q-space />
          <q-btn dense flat icon="close" size="30px" v-close-popup @click="stopScanner">
            <q-tooltip>Fechar Câmera</q-tooltip>
          </q-btn>
        </q-bar>

        <q-card-section class="col flex flex-center column relative-position">
          
          <div class="scanner-frame relative-position">
              <div id="reader" style="width: 100%; height: 100%; background: #000;"></div>
              <div class="scan-line"></div>
          </div>
          
          <div class="text-h4 q-mt-xl text-grey-4 text-center text-weight-bold">
             Posicione o Código de Barras
          </div>
          <div class="text-h6 text-vemag-green q-mt-sm">Matrícula ou Crachá</div>
          
          <div v-if="lastScannedCode" class="q-mt-lg bg-white text-black q-pa-md rounded-borders text-h4 text-weight-bold animate-blink shadow-10">
             LIDO: {{ lastScannedCode }}
          </div>

          <q-btn flat color="white" icon="cameraswitch" label="Trocar Câmera" size="lg" class="q-mt-xl" @click="switchCamera" />
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useProductionStore } from 'stores/production-store';
import { useQuasar } from 'quasar';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';

const router = useRouter();
const productionStore = useProductionStore();
const $q = useQuasar();

// --- Estados da Página ---
const isLoading = ref(false);
const isLoadingList = ref(false);
const isConfigOpen = ref(false);
const adminPassword = ref('');
const selectedMachineOption = ref<number | null>(null);

const isMaintenanceDialogOpen = ref(false);
const omDescription = ref('');
let pollingTimer: ReturnType<typeof setInterval>;

// --- Estados do Scanner ---
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

// --- Ciclo de Vida ---
onMounted(() => {
  void productionStore.loadKioskConfig();
  if (productionStore.machineId) {
    selectedMachineOption.value = productionStore.machineId;
  }
  
  pollingTimer = setInterval(() => {
      if(productionStore.machineId) {
          void productionStore.loadKioskConfig();
      }
  }, 5000);
});

onUnmounted(() => {
   clearInterval(pollingTimer);
   void stopScanner();
});

// --- LÓGICA DO SCANNER ---

function openBadgeScanner() {
  if (!productionStore.isKioskConfigured) {
    $q.notify({ type: 'warning', message: 'Necessário configurar terminal.' });
    return;
  }
  showScanner.value = true;
  lastScannedCode.value = '';
  
  setTimeout(() => {
     void startScanner();
  }, 500);
}

async function startScanner() {
    try {
        if (html5QrCode) {
            await stopScanner();
        }

        html5QrCode = new Html5Qrcode("reader");
        
        const config = { 
            fps: 10, 
            qrbox: { width: 400, height: 150 }, // Box mais largo para código de barras
            aspectRatio: 1.0,
            formatsToSupport: [
                Html5QrcodeSupportedFormats.CODE_128,
                Html5QrcodeSupportedFormats.CODE_39,
                Html5QrcodeSupportedFormats.EAN_13,
                Html5QrcodeSupportedFormats.UPC_A,
                Html5QrcodeSupportedFormats.ITF
            ]
        };
        
        await html5QrCode.start(
            { facingMode: facingMode.value },
            config,
            (decodedText) => { void onScanSuccess(decodedText) }, 
            undefined 
        );
    } catch (err) {
        console.error("Erro ao iniciar câmera:", err);
        $q.notify({ type: 'negative', message: 'Não foi possível acessar a câmera.' });
        showScanner.value = false;
    }
}

async function stopScanner() {
    if (html5QrCode) {
        try {
            if (html5QrCode.isScanning) {
                await html5QrCode.stop();
            }
            html5QrCode.clear();
        } catch (err) {
            console.error("Erro ao parar scanner:", err);
        }
        html5QrCode = null;
    }
}

async function onScanSuccess(decodedText: string) {
    console.log("CÓDIGO LIDO:", decodedText);
    lastScannedCode.value = decodedText;
    
    // Feedback sonoro (opcional) e visual
    // const audio = new Audio('/beep.mp3'); audio.play();

    await stopScanner();
    showScanner.value = false;
    
    isLoading.value = true;
    try {
        await productionStore.loginOperator(decodedText);
        
        if (productionStore.isShiftActive) {
             void router.push({ 
                name: 'operator-cockpit', 
                params: { machineId: productionStore.machineId } 
             });
        }
    } catch (e) {
        console.error(e);
    } finally {
        isLoading.value = false;
    }
}

async function switchCamera() {
    facingMode.value = facingMode.value === "environment" ? "user" : "environment";
    await startScanner();
}

// --- CONFIGURAÇÃO E MANUTENÇÃO ---

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
  }
}

function openMaintenanceDialog() {
    const now = new Date().toLocaleString('pt-BR');
    omDescription.value = `Parada por quebra reportada em ${now}.\nMotivo: Falha no equipamento detectada pelo operador.`;
    isMaintenanceDialogOpen.value = true;
}

async function submitMaintenance() {
    isLoading.value = true;
    await productionStore.createMaintenanceOrder(omDescription.value);
    isMaintenanceDialogOpen.value = false;
    omDescription.value = '';
    isLoading.value = false;
    $q.notify({ type: 'positive', message: 'O.M. Aberta com sucesso!' });
}

function unlockMachine() {
    $q.dialog({
        title: 'Desbloqueio Supervisão',
        message: 'Senha de supervisor para liberar:',
        prompt: { model: '', type: 'password' },
        cancel: true,
        ok: { label: 'LIBERAR', color: 'positive', size: 'lg' }
    }).onOk((data: string) => {
        void (async () => {
            if(data === '1234') { 
                await productionStore.setMachineStatus('IDLE');
                $q.notify({ type: 'positive', message: 'Liberado.' });
            } else {
                $q.notify({ type: 'negative', message: 'Senha inválida.' });
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
    background-image: url('/vemag.png'); /* Certifique-se que existe ou remova */
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
    width: 650px;
    max-width: 95vw;
    border-radius: 30px;
    background: #1e1e1e; /* Dark Card */
    border: 1px solid rgba(255,255,255,0.1);
    z-index: 10;
}
.border-vemag { border-top: 8px solid #008C7A; }
.border-red { border-top: 8px solid #b71c1c; box-shadow: 0 0 30px rgba(183, 28, 28, 0.4); }

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
    width: 600px;
    height: 300px;
    border: 4px solid rgba(255,255,255,0.3);
    border-radius: 20px;
    overflow: hidden;
    position: relative;
    box-shadow: 0 0 0 1000px rgba(0,0,0,0.7); /* Escurece em volta */
}
.scan-line {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: #008C7A;
    box-shadow: 0 0 10px #008C7A;
    animation: scanMove 2s infinite linear;
}

/* SHINE EFFECT NO BOTÃO */
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
.letter-spacing-1 { letter-spacing: 1px; }
.letter-spacing-2 { letter-spacing: 2px; }
.font-monospace { font-family: monospace; }
.fullscreen-bg { width: 100vw; height: 100vh; overflow: hidden; }
</style>
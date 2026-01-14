<!-- eslint-disable @typescript-eslint/no-misused-promises -->
<template>
  <q-layout view="lHh Lpr fff" class="bg-grey-10 text-white">
    <q-page-container>
      <q-page class="flex flex-center column relative-position overflow-hidden">
        
        <div class="absolute-full" :style="`background: radial-gradient(circle at center, transparent 30%, #000000 100%), url('${backgroundPath}') ${backgroundPosition} / ${backgroundSize} no-repeat; filter: brightness(0.6); z-index: 0;`"></div>

        <q-card class="bg-grey-9 shadow-24 fade-in-up relative-position" style="width: 500px; max-width: 90vw; border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; z-index: 1;">
          <q-card-section class="text-center q-pa-xl">
            
            <q-avatar v-if="!productionStore.isMachineBroken" size="100px" font-size="52px" color="primary" text-color="white" icon="precision_manufacturing" class="shadow-10 q-mb-md" />
            <q-avatar v-else size="100px" font-size="52px" color="red-10" text-color="white" icon="build_circle" class="shadow-10 q-mb-md animate-bounce" />
            
            <div class="text-h4 text-weight-bold q-mb-xs text-white">
              {{ productionStore.machineName }}
            </div>
            <div class="text-subtitle1 text-grey-5 text-uppercase letter-spacing-2">
              {{ productionStore.machineSector }}
            </div>
            
            <q-separator color="grey-8" class="q-my-lg" />

            <div v-if="isLoading" class="column items-center q-gutter-y-md">
              <q-spinner-orbit color="primary" size="4em" />
              <div class="text-body1 animate-blink text-primary">Conectando ao MES...</div>
            </div>

            <div v-else-if="productionStore.isMachineBroken" class="column q-gutter-y-md animate-fade-in">
                <div class="text-h5 text-weight-bold text-red-5">EQUIPAMENTO PARADO</div>
                <div class="text-body1 text-grey-4">
                   Reportado falha/quebra. Necessário abrir O.M.
                </div>

                <q-btn 
                  push color="red-10" size="lg" icon="assignment_late" 
                  label="ABRIR ORDEM DE MANUTENÇÃO" 
                  class="full-width q-py-md shadow-5 hover-scale"
                  @click="openMaintenanceDialog"
                />

                <q-btn flat color="grey-6" icon="lock_open" label="Liberar (Supervisor)" size="sm" class="q-mt-sm" @click="unlockMachine" />
            </div>

            <div v-else class="column q-gutter-y-md animate-fade-in">
              <div v-if="!productionStore.isKioskConfigured" class="text-negative text-weight-bold q-mb-md bg-red-1 q-pa-sm rounded-borders">
                ⚠ TERMINAL NÃO VINCULADO
              </div>

              <p class="text-h6 text-weight-regular text-grey-3">Aguardando Operador</p>
              
              <q-btn 
                push color="primary" size="xl" icon="qr_code_scanner" 
                label="Escanear Crachá" 
                class="full-width q-py-md shadow-5 hover-scale"
                @click="simulateScan"
                :disable="!productionStore.isKioskConfigured"
              />
              
              <q-btn flat color="grey-6" label="Configuração / Supervisor" size="sm" class="q-mt-sm" @click="openConfigDialog" />
            </div>
          </q-card-section>
          
          <q-card-section class="bg-black text-center q-py-sm">
            <div class="text-caption text-grey-7">
               ID: {{ productionStore.machineId || '--' }} • 
               <span v-if="productionStore.isMachineBroken" class="text-red-5">● Manutenção</span>
               <span v-else class="text-green-5">● Online</span>
            </div>
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>

    <q-dialog v-model="isConfigOpen" backdrop-filter="blur(4px)">
      <q-card style="width: 450px" class="shadow-24">
        <q-card-section class="bg-primary text-white">
          <div class="text-h6">Vincular Terminal</div>
        </q-card-section>
        <q-card-section class="q-pt-md q-gutter-y-md">
          <div class="text-body2 text-grey-8">Selecione qual equipamento este tablet irá controlar.</div>
          <q-select outlined v-model="selectedMachineOption" :options="machineOptions" label="Máquinas Disponíveis" option-label="label" option-value="value" emit-value map-options bg-color="white" :loading="isLoadingList" />
          <q-input outlined v-model="adminPassword" type="password" label="Senha de Supervisor" dense />
        </q-card-section>
        <q-card-actions align="right" class="bg-grey-1">
          <q-btn flat label="Cancelar" color="grey" v-close-popup />
          <q-btn unelevated label="Salvar Vínculo" color="primary" @click="saveConfig" :disable="adminPassword !== 'admin123' || !selectedMachineOption" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isMaintenanceDialogOpen" persistent>
       <q-card style="width: 600px; max-width: 90vw;">
          <q-card-section class="bg-red-10 text-white row items-center">
             <q-icon name="report_problem" size="md" class="q-mr-sm" />
             <div class="text-h6">Abertura de O.M. - Corretiva</div>
          </q-card-section>
          <q-card-section class="q-pa-md">
             <div class="text-subtitle2 q-mb-xs text-grey-8">Equipamento</div>
             <div class="text-h6 text-dark q-mb-md">{{ productionStore.machineName }}</div>
             <div class="text-subtitle2 q-mb-xs text-grey-8">Descrição do Problema</div>
             <q-input v-model="omDescription" type="textarea" outlined rows="5" placeholder="Descreva o detalhe da quebra..." autofocus />
          </q-card-section>
          <q-card-actions align="right" class="bg-grey-1 q-pa-md">
             <q-btn flat label="Cancelar" color="grey-8" v-close-popup />
             <q-btn push color="red-10" label="CONFIRMAR ABERTURA" icon="send" :loading="isLoading" @click="submitMaintenance" :disable="!omDescription" />
          </q-card-actions>
       </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useProductionStore } from 'stores/production-store';
import { useQuasar } from 'quasar';

const router = useRouter();
const productionStore = useProductionStore();
const $q = useQuasar();

const isLoading = ref(false);
const isLoadingList = ref(false);
const isConfigOpen = ref(false);
const adminPassword = ref('');
const selectedMachineOption = ref<number | null>(null);

const backgroundPath = ref('/vemag.png');
const backgroundSize = ref('contain'); 
const backgroundPosition = ref('center'); 

const isMaintenanceDialogOpen = ref(false);
const omDescription = ref('');
let pollingTimer: ReturnType<typeof setInterval>;

const machineOptions = computed(() => {
  return productionStore.machinesList.map(m => ({
    label: `${m.brand} ${m.model} (${m.license_plate || 'ID:' + m.id})`,
    value: m.id
  }));
});

onMounted(async () => {
  await productionStore.loadKioskConfig();
  if (productionStore.machineId) {
    selectedMachineOption.value = productionStore.machineId;
  }
  
  // Polling a cada 5 segundos
  pollingTimer = setInterval(() => {
      if(productionStore.machineId) {
          // 'void' diz ao linter que não vamos aguardar a promise aqui
          void productionStore.loadKioskConfig();
      }
  }, 5000);
});

onUnmounted(() => {
    clearInterval(pollingTimer);
});

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
        cancel: true
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

async function simulateScan() {
  if (!productionStore.isKioskConfigured) {
    $q.notify({ type: 'warning', message: 'Necessário configurar terminal.' });
    return;
  }
  isLoading.value = true;
  try {
    await productionStore.loginOperator('BADGE-123');
    void router.push({ 
      name: 'operator-cockpit', 
      params: { machineId: productionStore.machineId } 
    });
  } catch (e) { 
    // Ignora erros de login ou loga no console
    console.error(e); 
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.opacity-20 { opacity: 0.2; }
.letter-spacing-2 { letter-spacing: 2px; }
.hover-scale { transition: transform 0.2s; }
.hover-scale:hover { transform: scale(1.02); }
.animate-blink { animation: blink 1.5s infinite; }
.fade-in-up { animation: fadeInUp 1s ease-out; }
.animate-bounce { animation: bounce 2s infinite; }
.animate-fade-in { animation: fadeIn 0.5s ease-in; }

@keyframes blink { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
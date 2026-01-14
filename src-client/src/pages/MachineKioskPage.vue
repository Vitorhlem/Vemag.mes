<template>
  <q-layout view="lHh Lpr fff" class="bg-grey-10 text-white">
    <q-page-container>
      <q-page class="flex flex-center column relative-position overflow-hidden">
        
        <div class="absolute-full" :style="`background: radial-gradient(circle at center, transparent 30%, #000000 100%), url('${backgroundPath}') ${backgroundPosition} / ${backgroundSize} no-repeat; filter: brightness(0.6); z-index: 0;`"></div>

        <q-card class="bg-grey-9 shadow-24 fade-in-up relative-position" style="width: 500px; max-width: 90vw; border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; z-index: 1;">
          <q-card-section class="text-center q-pa-xl">
            <q-avatar size="100px" font-size="52px" color="primary" text-color="white" icon="precision_manufacturing" class="shadow-10 q-mb-md" />
            
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

            <div v-else class="column q-gutter-y-md">
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
            <div class="text-caption text-grey-7">ID: {{ productionStore.machineId || '--' }} • <span class="text-green-5">● Online</span></div>
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
          <div class="text-body2 text-grey-8">
            Selecione qual equipamento este tablet irá controlar.
          </div>
          
          <q-select
            outlined
            v-model="selectedMachineOption"
            :options="machineOptions"
            label="Máquinas Disponíveis"
            option-label="label"
            option-value="value"
            emit-value
            map-options
            bg-color="white"
            :loading="isLoadingList"
          >
            <template v-slot:prepend><q-icon name="precision_manufacturing" /></template>
            <template v-slot:no-option>
              <q-item><q-item-section class="text-grey">Nenhuma máquina encontrada.</q-item-section></q-item>
            </template>
          </q-select>

          <q-separator spaced />

          <q-input outlined v-model="adminPassword" type="password" label="Senha de Supervisor" dense>
             <template v-slot:prepend><q-icon name="lock" /></template>
          </q-input>
        </q-card-section>

        <q-card-actions align="right" class="bg-grey-1">
          <q-btn flat label="Cancelar" color="grey" v-close-popup />
          <q-btn unelevated label="Salvar Vínculo" color="primary" @click="saveConfig" :disable="adminPassword !== 'admin123' || !selectedMachineOption" />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
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

// Configuração Visual
const backgroundPath = ref('/vemag.png');
const backgroundSize = ref('contain'); 
const backgroundPosition = ref('center'); 

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
});

async function openConfigDialog() {
  adminPassword.value = '';
  selectedMachineOption.value = productionStore.machineId; 
  isConfigOpen.value = true;
  
  isLoadingList.value = true;
  // Busca lista real do backend
  await productionStore.fetchAvailableMachines();
  isLoadingList.value = false;
}

async function saveConfig() {
  if (adminPassword.value !== 'admin123') {
    $q.notify({ type: 'negative', message: 'Senha incorreta.' });
    return;
  }

  if (selectedMachineOption.value) {
    // CORREÇÃO: await
    await productionStore.configureKiosk(selectedMachineOption.value);
    isConfigOpen.value = false;
  }
}

async function simulateScan() {
  if (!productionStore.isKioskConfigured) {
    $q.notify({ type: 'warning', message: 'Necessário configurar terminal.' });
    return;
  }

  isLoading.value = true;
  try {
    await productionStore.loginOperator('BADGE-123');
    // CORREÇÃO: void para ignorar promise flutuante
    void router.push({ 
      name: 'operator-cockpit', 
      params: { machineId: productionStore.machineId } 
    });
  } catch { // 'e' removido
    // Erro tratado na store
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
.opacity-20 { opacity: 0.2; }
.letter-spacing-2 { letter-spacing: 2px; }
.animate-blink { animation: blink 1.5s infinite; }
.fade-in-up { animation: fadeInUp 1s ease-out; }
.hover-scale { transition: transform 0.2s; }
.hover-scale:hover { transform: scale(1.02); }
@keyframes blink { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
</style>
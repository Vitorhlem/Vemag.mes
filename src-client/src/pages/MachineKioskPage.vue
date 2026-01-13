<template>
  <q-layout view="lHh Lpr fff" class="bg-grey-10 text-white">
    <q-page-container>
      <q-page class="flex flex-center column relative-position overflow-hidden">
        
        <div class="absolute-full" :style="`background: radial-gradient(circle at center, transparent 30%, #000000 100%), url('${backgroundPath}') ${backgroundPosition} / ${backgroundSize} no-repeat; filter: brightness(0.7);`"></div>
        <div class="absolute-full opacity-20" style="background: radial-gradient(circle, transparent 20%, #000 90%);"></div>

        <q-card class="z-top bg-grey-9 shadow-24 fade-in-up" style="width: 500px; max-width: 90vw; border: 1px solid rgba(255,255,255,0.1); border-radius: 20px;">
          <q-card-section class="text-center q-pa-xl">
            <q-avatar size="100px" font-size="52px" color="primary" text-color="white" icon="precision_manufacturing" class="shadow-10 q-mb-md" />
            <div class="text-h4 text-weight-bold q-mb-xs text-white">CNC - TORNO 01</div>
            <div class="text-subtitle1 text-grey-5 text-uppercase letter-spacing-2">Setor de Usinagem</div>
            <q-separator color="grey-8" class="q-my-lg" />

            <div v-if="isLoading" class="column items-center q-gutter-y-md">
              <q-spinner-orbit color="primary" size="4em" />
              <div class="text-body1 animate-blink text-primary">A autenticar Operador...</div>
            </div>

            <div v-else class="column q-gutter-y-md">
              <p class="text-h6 text-weight-regular text-grey-3">Terminal Bloqueado</p>
              <q-btn push color="primary" size="xl" icon="qr_code_scanner" label="Escanear Crachá" class="full-width q-py-md shadow-5 hover-scale" @click="simulateScan" />
              <q-btn flat color="grey-6" label="Acesso de Supervisor" size="sm" class="q-mt-sm" />
            </div>
          </q-card-section>
          <q-card-section class="bg-black text-center q-py-sm">
            <div class="text-caption text-grey-7">Sistema TruMachine v2.0 • <span class="text-green-5">● Online</span></div>
          </q-card-section>
        </q-card>

      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useProductionStore } from 'stores/production-store';

const router = useRouter();
const productionStore = useProductionStore();
const isLoading = ref(false);

const backgroundPath = ref('/vemag.png');
const backgroundSize = ref('cover'); 
const backgroundPosition = ref('center'); 

async function simulateScan() {
  isLoading.value = true;
  await productionStore.loginOperator('BADGE-123');
  isLoading.value = false;
  
  // CORREÇÃO: Usar void para ignorar a Promise flutuante, já que não precisamos esperar o roteamento
  void router.push({ name: 'operator-cockpit', params: { machineId: 1 } });
}
</script>

<style scoped>
.opacity-20 { opacity: 0.2; }
.letter-spacing-2 { letter-spacing: 2px; }
.z-top { z-index: 10; }
.animate-blink { animation: blink 1.5s infinite; }
.fade-in-up { animation: fadeInUp 1s ease-out; }
.hover-scale { transition: transform 0.2s; }
.hover-scale:hover { transform: scale(1.02); }
@keyframes blink { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
</style>
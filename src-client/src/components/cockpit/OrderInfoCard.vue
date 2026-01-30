<template>
  <q-card class="col column no-wrap relative-position overflow-hidden shadow-6 bg-white" style="border-radius: 20px; border-left: 10px solid #008C7A;">
    
    <div class="col-auto relative-position bg-vemag-gradient text-white q-pa-lg shadow-3">
      <q-img :src="backgroundImage" class="absolute-full opacity-10" fit="cover" />
      
      <div class="row no-wrap items-center justify-between relative-position z-top">
        <div class="col-grow" style="min-width: 0;">
          <div class="row items-center q-gutter-x-sm q-mb-xs">
            <q-badge color="orange-10" class="text-bold shadow-2 q-px-sm" label="PRODUÇÃO" />
            <q-badge outline color="white" class="text-bold" :label="`OP #${order.code || '---'}`" />
            <q-chip v-if="order.drawing" dense square color="blue-grey-9" text-color="white" icon="architecture" size="sm">
              DESENHO: {{ order.drawing }}
            </q-chip>
          </div>
          <div class="text-h4 text-weight-bolder ellipsis q-mt-sm" style="max-width: 100%;">{{ order.part_name }}</div>
          <div class="text-subtitle2 text-grey-3 q-mt-xs">Cód. Item: <span class="text-white text-bold">{{ order.part_code }}</span></div>
        </div>

        <div class="col-auto column items-end q-ml-md" style="min-width: 180px;">
          <div class="row no-wrap items-center bg-black-transparent q-px-md q-py-sm rounded-borders shadow-1">
            <div class="column items-end q-mr-md">
              <div class="text-overline text-grey-4" style="line-height: 1;">META TOTAL</div>
              <div class="text-h5 text-weight-bolder no-wrap">
                {{ order.produced_quantity }} 
                <span class="text-subtitle1 text-grey-5">/ {{ order.target_quantity }} {{ order.uom }}</span>
              </div>
            </div>
            <q-circular-progress show-value font-size="12px" :value="progressPercentage" size="50px" :thickness="0.25" color="orange-5" track-color="grey-9" class="text-white text-bold">
              {{ progressPercentage }}%
            </q-circular-progress>
          </div>
          <q-btn push color="blue-grey-9" text-color="white" icon="image" label="DESENHO" size="sm" padding="xs sm" class="q-mt-sm" @click="$emit('open-drawing')" />
        </div>
      </div>
    </div>

    <div class="col-auto bg-grey-2 q-px-md q-py-sm border-bottom-light row items-center justify-between" v-if="currentStep">
      <div class="row items-center" style="min-width: 0;">
        <div class="text-subtitle1 text-grey-7 q-mr-sm text-weight-bold">#{{ currentStep.seq }}</div>
        <div class="text-h6 text-weight-bold ellipsis">{{ currentStep.name }}</div>
      </div>
      <q-chip square dense color="blue-grey-9" text-color="white" icon="precision_manufacturing" :label="currentStep.resource" class="text-caption text-weight-bold" />
    </div>

    <div class="col scroll bg-grey-1 q-pa-md">
      <div class="text-dark rounded-borders" style="white-space: pre-wrap; font-size: 1.25rem; line-height: 1.5; border: 2px dashed #008C7A; padding: 20px; min-height: 100%; font-family: monospace;">
        <div class="text-weight-bold text-primary q-mb-md row items-center">
          <q-icon name="menu_book" size="sm" class="q-mr-sm" /> INSTRUÇÕES DE TRABALHO:
        </div>
        {{ currentStep?.description || 'Carregando instruções técnicas do SAP...' }}
      </div>
    </div>

    <div class="col-auto q-pa-sm bg-grey-1 border-top-light">
      <div class="row justify-between items-center q-mb-sm q-px-sm">
         <div class="text-caption text-grey-7">
            <q-icon name="info" /> Centro de Trabalho: <strong>{{ currentStep?.resource_name || 'Geral' }}</strong>
         </div>
         <q-chip outline color="primary" icon="timer" dense>
           Tempo Est: <strong>{{ currentStep?.timeEst || 0 }}h</strong>
         </q-chip>
      </div>
      <q-separator />
      <div class="row items-center justify-between q-pt-sm">
        <div class="row q-gutter-x-sm col-8">
          <q-btn flat color="primary" icon="arrow_back" label="ANTERIOR" class="col-grow" @click="$emit('prev-step')" :disable="stepIndex === 0" />
          <q-btn push color="primary" icon-right="arrow_forward" label="PRÓXIMO" class="col-grow" @click="$emit('next-step')" :disable="!order.steps || stepIndex === order.steps.length - 1" />
        </div>
        <q-btn flat color="negative" icon="delete_outline" label="Refugo" @click="$emit('add-scrap')" />
      </div>
    </div>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  order: any;
  currentStep: any;
  stepIndex: number;
  backgroundImage: string;
}>();

const emit = defineEmits(['open-drawing', 'prev-step', 'next-step', 'add-scrap']);

const progressPercentage = computed(() => {
  return Math.round(((props.order.produced_quantity || 0) / (props.order.target_quantity || 1)) * 100);
});
</script>

<style scoped>
.bg-vemag-gradient { background: linear-gradient(135deg, #008C7A 0%, #00695C 100%); }
.bg-black-transparent { background-color: rgba(0,0,0,0.15); }
.border-bottom-light { border-bottom: 2px solid #e0e0e0; }
.border-top-light { border-top: 2px solid #e0e0e0; }
.col-grow { flex-grow: 1; }
</style>
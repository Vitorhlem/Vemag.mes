<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" transition-show="scale" transition-hide="scale">
    <q-card style="width: 700px; max-width: 95vw; border-radius: 20px;">
      <q-card-section class="vemag-bg-primary text-white row items-center justify-between q-pa-md">
        <div class="text-h6 text-weight-bold row items-center">
            <q-icon name="campaign" size="30px" class="q-mr-sm" /> Central de Ajuda (Andon)
        </div>
        <q-btn icon="close" flat round size="md" v-close-popup />
      </q-card-section>
      
      <q-card-section class="q-pa-lg">
        <div class="text-subtitle1 q-mb-md vemag-text-primary text-weight-bold">Qual setor você precisa chamar?</div>
        
        <div class="row q-col-gutter-md">
          <div v-for="opt in options" :key="opt.label" class="col-6 col-md-4">
            <q-btn push class="full-width full-height column flex-center q-pa-md shadow-3 hover-scale" :class="`bg-${opt.color} text-white`" style="border-radius: 16px; min-height: 100px;" @click="$emit('confirm', opt.label)">
              <q-icon :name="opt.icon" size="36px" class="q-mb-sm" />
              <div class="text-subtitle1 text-weight-bold">{{ opt.label }}</div>
            </q-btn>
          </div>
        </div>

        <div class="q-mt-lg">
          <q-input :model-value="note" @update:model-value="$emit('update:note', $event)" outlined label="Observação (Opcional)" placeholder="Ex: Falta parafuso M5" dense class="text-subtitle1" bg-color="grey-1" />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
defineProps<{ modelValue: boolean; options: any[]; note: string }>();
defineEmits(['update:modelValue', 'update:note', 'confirm']);
</script>

<style scoped>
.vemag-bg-primary { background-color: #008C7A !important; }
.vemag-text-primary { color: #008C7A !important; }
.hover-scale:active { transform: scale(0.98); }
</style>
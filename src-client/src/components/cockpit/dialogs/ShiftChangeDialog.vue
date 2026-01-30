<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" persistent>
    <q-card class="q-pa-md text-center" style="width: 400px; border-radius: 16px;">
      <q-icon name="groups" size="60px" color="primary" class="q-mb-sm" />
      <div class="text-h5 text-weight-bold">Troca de Turno</div>
      <div class="text-subtitle1 text-grey-8 q-my-md">A máquina vai parar ou o próximo operador assume imediatamente?</div>
      
      <div class="column q-gutter-y-md">
         <q-btn push color="positive" size="lg" icon="autorenew" label="CONTINUA RODANDO" @click="$emit('confirm', true)" />
         <div class="text-caption text-grey">O apontamento atual será fechado e a OP ficará aguardando o próximo login.</div>
         <q-separator />
         <q-btn flat color="negative" icon="pause" label="VAI PARAR A MÁQUINA" @click="$emit('confirm', false)" />
      </div>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
defineProps<{ modelValue: boolean }>();
defineEmits(['update:modelValue', 'confirm']);
</script>
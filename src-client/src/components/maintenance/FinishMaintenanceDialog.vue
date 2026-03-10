<template>
  <q-dialog :model-value="modelValue" @update:model-value="val => emit('update:modelValue', val)" persistent>
    <q-card style="min-width: 450px">
      <q-card-section class="bg-positive text-white">
        <div class="text-h6">Encerrar Ordem de Manutenção</div>
      </q-card-section>

      <q-card-section>
        <div class="text-body2 q-mb-md">
          A OS será fechada. Deseja agendar a próxima preventiva para esta máquina?
        </div>
        
        <q-form @submit="onSubmit">
          <q-input 
            v-model="form.manager_notes" 
            label="Relatório Técnico / Solução" 
            outlined 
            type="textarea" 
            autogrow 
            class="q-mb-md"
            :rules="[val => !!val || 'Informe a solução aplicada']"
          />

          <q-separator class="q-mb-md" />
          <div class="text-subtitle2 q-mb-sm text-primary">Próxima Preventiva (PMP):</div>

          <q-input 
            v-model="form.next_maintenance_date" 
            label="Data Limite *" 
            type="date" 
            outlined 
            dense 
            stack-label 
          />

          <q-card-actions align="right" class="q-mt-lg">
            <q-btn flat label="Cancelar" v-close-popup color="grey-8" />
            <q-btn unelevated label="Concluir OS" type="submit" color="positive" />
          </q-card-actions>
        </q-form>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { MaintenanceRequest, MaintenanceRequestUpdate } from 'src/models/maintenance-models';
import { MaintenanceStatus } from 'src/models/maintenance-models';

const props = defineProps<{
  modelValue: boolean;
  request: MaintenanceRequest | null;
}>();

const emit = defineEmits(['update:modelValue', 'confirm']);

const form = ref<MaintenanceRequestUpdate>({
  status: MaintenanceStatus.CONCLUIDA,
  manager_notes: '',
  next_maintenance_date: ''
});

watch(() => props.modelValue, (isOpen) => {
  if (isOpen && props.request?.machine) {
    // Sugere +180 dias (semestral) para a próxima preventiva
    const today = new Date();
    today.setDate(today.getDate() + 180); 
    const dateStr = today.toISOString().split('T')[0];
    
    form.value.next_maintenance_date = dateStr || null;
    form.value.manager_notes = props.request.manager_notes || '';
  }
});

function onSubmit() {
  emit('confirm', { ...form.value });
  emit('update:modelValue', false);
}
</script>
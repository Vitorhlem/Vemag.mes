<template>
  <q-dialog :model-value="modelValue" @update:model-value="val => emit('update:modelValue', val)">
    <q-card style="width: 600px; max-width: 90vw;" class="rounded-borders" v-if="request">
      <q-card-section class="bg-dark text-white row items-center justify-between">
        <div class="text-h6">Gestão Rápida da OS #{{ request.id }}</div>
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section class="q-pa-md">
         <div class="row q-col-gutter-md">
             <div class="col-12">
                 <div class="text-caption text-grey">Equipamento</div>
                 <div class="text-h6">{{ request.vehicle?.brand }} {{ request.vehicle?.model }}</div>
                 <div class="text-subtitle2 text-grey-8">{{ request.problem_description }}</div>
             </div>
         </div>
      </q-card-section>

      <q-separator />

      <q-card-section v-if="!isClosed" class="q-gutter-sm text-center">
        <q-btn @click="() => handleUpdateStatus(MaintenanceStatus.APROVADA)" color="primary" label="Aprovar Início" icon="play_arrow" style="min-width: 140px" />
        <q-btn @click="() => handleUpdateStatus(MaintenanceStatus.EM_ANDAMENTO)" color="info" label="Em Execução" icon="engineering" style="min-width: 140px" />
        <q-btn @click="() => handleUpdateStatus(MaintenanceStatus.REJEITADA)" color="negative" label="Rejeitar" icon="cancel" flat />
      </q-card-section>

      <q-card-section v-else class="text-center text-grey-7 q-pa-lg">
        <q-icon name="lock" size="2em" />
        <div>Esta OS já foi finalizada.</div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useQuasar } from 'quasar';
import { useMaintenanceStore } from 'stores/maintenance-store';
import { MaintenanceStatus, type MaintenanceRequest, type MaintenanceRequestUpdate } from 'src/models/maintenance-models';

const props = defineProps<{ modelValue: boolean, request: MaintenanceRequest | null }>();
const emit = defineEmits(['update:modelValue']);
const $q = useQuasar();
const maintenanceStore = useMaintenanceStore();

const isClosed = computed(() => 
  props.request?.status === MaintenanceStatus.CONCLUIDA ||
  props.request?.status === MaintenanceStatus.REJEITADA
);

function handleUpdateStatus(newStatus: MaintenanceStatus) {
  if (!props.request) return;

  const performUpdate = async (notes?: string) => {
    if (!props.request) return;
    const payload: MaintenanceRequestUpdate = { 
      status: newStatus,
      manager_notes: notes ?? props.request.manager_notes,
    };
    await maintenanceStore.updateRequest(props.request.id, payload);
    emit('update:modelValue', false);
  };

  if (newStatus === MaintenanceStatus.REJEITADA) {
    $q.dialog({
      title: 'Justificativa',
      message: 'Motivo da rejeição:',
      prompt: { model: '', type: 'textarea' },
      cancel: true
    }).onOk((data: string) => void performUpdate(data));
  } else {
    void performUpdate();
  }
}
</script>
<template>
  <q-dialog :model-value="modelValue" @update:model-value="val => emit('update:modelValue', val)">
    <q-card style="min-width: 500px">
      <q-card-section>
        <div class="text-h6">Nova Ordem de Manutenção (OM)</div>
      </q-card-section>

      <q-card-section>
        <q-form @submit="onSubmit">
          <q-select
            v-model="form.vehicle_id"
            :options="vehicleOptions"
            label="Máquina / Equipamento *"
            option-value="id"
            option-label="identifier"
            emit-value
            map-options
            outlined
            dense
            :rules="[val => !!val || 'Campo obrigatório']"
            class="q-mb-md"
          />
          
          <div class="row q-col-gutter-md">
             <div class="col-6">
                <q-select
                    v-model="form.maintenance_type"
                    :options="['CORRETIVA', 'PREVENTIVA', 'PREDITIVA']"
                    label="Tipo de Manutenção *"
                    outlined
                    dense
                    class="q-mb-md"
                />
             </div>
             <div class="col-6">
                <q-select
    v-model="form.category"
    :options="categoryOptions"
    label="Especialidade *"
    outlined
    dense
    emit-value   map-options  class="q-mb-md"
/>
             </div>
          </div>

          <q-input
            v-model="form.problem_description"
            label="Descrição do Problema / Serviço *"
            type="textarea"
            outlined
            dense
            autogrow
            class="q-mb-md"
            :rules="[val => !!val || 'Descreva o problema']"
          />

          <div class="row justify-end q-gutter-sm">
            <q-btn label="Cancelar" color="negative" flat v-close-popup />
            <q-btn label="Abrir OM" type="submit" color="primary" unelevated :loading="loading" />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useVehicleStore } from 'stores/vehicle-store';
import { useMaintenanceStore } from 'stores/maintenance-store';
import { MaintenanceCategory } from 'src/models/maintenance-models';

const props = defineProps<{
  modelValue: boolean;
  preSelectedVehicleId?: number | null;
  maintenanceType?: 'PREVENTIVA' | 'CORRETIVA';
}>();

const emit = defineEmits(['update:modelValue', 'request-created']);

const vehicleStore = useVehicleStore();
const maintenanceStore = useMaintenanceStore();

const loading = ref(false);

interface VehicleOption {
  id: number;
  identifier: string;
}
const vehicleOptions = ref<VehicleOption[]>([]);

// Categorias Industriais
const categoryOptions = [
    { label: 'Mecânica', value: MaintenanceCategory.MECHANICAL },
    { label: 'Elétrica', value: MaintenanceCategory.ELECTRICAL },
    { label: 'Hidráulica', value: MaintenanceCategory.HYDRAULIC }, 
    { label: 'Pneumática', value: MaintenanceCategory.PNEUMATIC }
];

const form = ref({
  vehicle_id: null as number | null,
  problem_description: '',
  category: MaintenanceCategory.MECHANICAL,
  maintenance_type: 'CORRETIVA' as string
});

onMounted(async () => {
  await vehicleStore.fetchAllVehicles({ rowsPerPage: 100 });
  vehicleOptions.value = vehicleStore.vehicles.map(v => ({
    id: v.id,
    identifier: `${v.brand} ${v.model} (Tag: ${v.license_plate || v.identifier || 'N/A'})`
  }));
});

watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    if (props.preSelectedVehicleId) {
      form.value.vehicle_id = props.preSelectedVehicleId;
    } else {
      form.value.vehicle_id = null;
    }
    form.value.maintenance_type = props.maintenanceType || 'CORRETIVA';
    
    if (form.value.maintenance_type === 'PREVENTIVA') {
       form.value.problem_description = 'Preventiva Programada (Plano 500h)';
    } else {
       form.value.problem_description = '';
    }
    form.value.category = MaintenanceCategory.MECHANICAL;
  }
});

async function onSubmit() {
  if (!form.value.vehicle_id) return;
  
  loading.value = true;
  const success = await maintenanceStore.createRequest({
    vehicle_id: form.value.vehicle_id,
    problem_description: form.value.problem_description,
    category: form.value.category,
    // CORREÇÃO: Envia o tipo selecionado (Preventiva/Corretiva) para o Backend
    maintenance_type: form.value.maintenance_type 
  });
  loading.value = false;

  if (success) {
    emit('update:modelValue', false);
    emit('request-created');
  }
}
</script>
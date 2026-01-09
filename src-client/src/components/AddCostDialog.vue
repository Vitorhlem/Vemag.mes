<template>
  <q-card style="width: 500px; max-width: 90vw;" :dark="$q.dark.isActive">
    <q-card-section>
      <div class="text-h6">Adicionar Novo Custo</div>
    </q-card-section>

    <q-form @submit.prevent="handleSubmit">
      <q-card-section class="q-gutter-y-md">
        
        <q-select
          v-if="!vehicleId"
          outlined
          v-model="localVehicleId"
          :options="vehicleOptions"
          label="Selecione a Máquina *"
          emit-value
          map-options
          :rules="[val => !!val || 'Selecione uma máquina']"
          :loading="isLoadingVehicles"
        />

        <q-select
          outlined
          v-model="formData.cost_type"
          :options="costTypeOptions"
          label="Categoria do Custo *"
          :rules="[val => !!val || 'Campo obrigatório']"
        />
        
        <q-input
          outlined
          v-model="formData.description"
          label="Descrição / Detalhes *"
          type="textarea"
          autogrow
          :rules="[val => !!val || 'Campo obrigatório']"
        />
        
        <q-input
          outlined
          v-model.number="formData.amount"
          type="number"
          label="Valor (R$) *"
          prefix="R$"
          :step="0.01"
          :rules="[val => val > 0 || 'O valor deve ser maior que zero']"
        />
        
        <q-input
          outlined
          v-model="formData.date"
          type="date"
          stack-label
          label="Data de Competência *"
          :rules="[val => !!val || 'Campo obrigatório']"
        />
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Cancelar" v-close-popup />
        <q-btn
          type="submit"
          unelevated
          color="primary"
          label="Adicionar Custo"
          :loading="isSubmitting"
        />
      </q-card-actions>
    </q-form>
  </q-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useQuasar } from 'quasar';
import { useVehicleCostStore } from 'stores/vehicle-cost-store';
import { useVehicleStore } from 'stores/vehicle-store';
import type { VehicleCostCreate, CostType } from 'src/models/vehicle-cost-models';

const props = defineProps<{
  vehicleId?: number;
}>();

const emit = defineEmits(['close', 'cost-added']);
const $q = useQuasar();

const costStore = useVehicleCostStore();
const vehicleStore = useVehicleStore();

const isSubmitting = ref(false);
const isLoadingVehicles = ref(false);
const localVehicleId = ref<number | null>(null);

const vehicleOptions = computed(() => 
  vehicleStore.vehicles.map(v => ({
    label: `${v.brand} ${v.model} (${v.license_plate || v.identifier})`,
    value: v.id
  }))
);

const costTypeOptions: CostType[] = [
    'Manutenção Corretiva', 
    'Manutenção Preventiva', 
    'Energia Elétrica', 
    'Peças de Reposição', 
    'Insumos/Consumíveis', 
    'Serviços Terceiros', 
    'Outros'
];

const formData = ref<VehicleCostCreate>({
  description: '',
  amount: 0,
  date: new Date().toISOString().split('T')[0] || '',
  cost_type: 'Outros', 
});

onMounted(async () => {
  if (!props.vehicleId) {
    isLoadingVehicles.value = true;
    await vehicleStore.fetchAllVehicles({ page: 1, rowsPerPage: 1000 });
    isLoadingVehicles.value = false;
  }
});

async function handleSubmit() {
  const targetVehicleId = props.vehicleId || localVehicleId.value;

  if (!targetVehicleId) {
    $q.notify({ type: 'warning', message: 'Selecione uma máquina.' });
    return;
  }

  isSubmitting.value = true;
  try {
    await costStore.addCost(targetVehicleId, formData.value);
    $q.notify({ type: 'positive', message: 'Custo registrado com sucesso!' });
    emit('cost-added');
    emit('close');
  } catch (error) {
    console.error(error);
    // CORREÇÃO: Cast explícito dentro do bloco catch para evitar erro do ESLint
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const err = error as any; 
    const msg = err.response?.data?.detail 
        ? JSON.stringify(err.response.data.detail) 
        : 'Erro ao registrar custo.';
    $q.notify({ type: 'negative', message: msg });
  } finally {
    isSubmitting.value = false;
  }
}
</script>
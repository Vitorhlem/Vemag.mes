<template>
  <div>
    <div class="flex items-center justify-between q-mb-md">
      <div class="text-h6 flex items-center">
         <q-icon name="attach_money" class="q-mr-sm" />
         Custos da Máquina
      </div>
      <q-btn
        @click="openAddDialog"
        color="primary"
        icon="add"
        label="Lançar Despesa"
        unelevated
      />
    </div>

    <q-table
      :rows="costsStore.costs"
      :columns="columns"
      row-key="id"
      :loading="costsStore.isLoading"
      flat
      bordered
      no-data-label="Nenhum custo registrado para esta máquina."
    >
      <template v-slot:body-cell-amount="props">
        <q-td :props="props" class="text-weight-bold text-primary">
          {{ props.row.amount.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) }}
        </q-td>
      </template>
    </q-table>

    <q-dialog v-model="isDialogOpen">
      <q-card style="width: 400px">
        <q-card-section class="bg-primary text-white">
          <div class="text-h6">Novo Lançamento</div>
        </q-card-section>

        <q-form @submit.prevent="onFormSubmit">
          <q-card-section class="q-gutter-y-md">
            <q-select
              outlined
              v-model="formData.cost_type"
              :options="costTypeOptions"
              label="Categoria *"
              :rules="[val => !!val || 'Campo obrigatório']"
            />
            <q-input
              outlined
              v-model.number="formData.amount"
              type="number"
              label="Valor Total (R$) *"
              prefix="R$"
              step="0.01"
              :rules="[val => val > 0 || 'O valor deve ser positivo']"
            />
            <q-input outlined v-model="formData.date" type="date" stack-label label="Data de Competência *" :rules="[val => !!val || 'Campo obrigatório']" />
            
            <q-input
              outlined
              v-model="formData.description"
              type="textarea"
              label="Detalhes / Nota Fiscal"
              autogrow
            />
          </q-card-section>

          <q-card-actions align="right" class="q-pa-md">
            <q-btn flat label="Cancelar" v-close-popup />
            <q-btn type="submit" unelevated color="primary" label="Lançar" :loading="isSubmitting" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useVehicleCostStore } from 'stores/vehicle-cost-store';
import type { QTableProps } from 'quasar';
import { format, parse } from 'date-fns';
import type { VehicleCostCreate, CostType } from 'src/models/vehicle-cost-models';

const props = defineProps<{
  vehicleId: number;
}>();

const costsStore = useVehicleCostStore();
const isDialogOpen = ref(false);
const isSubmitting = ref(false);

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
  cost_type: 'Outros',
  amount: 0,
  // CORREÇÃO AQUI: Adicionado || '' para evitar tipo undefined
  date: new Date().toISOString().split('T')[0] || '', 
  description: '',
});

const columns: QTableProps['columns'] = [
  { name: 'date', label: 'Data', field: 'date', align: 'left', sortable: true, format: (val) => format(new Date(val), 'dd/MM/yyyy') || '--' },
  { name: 'cost_type', label: 'Categoria', field: 'cost_type', align: 'left', sortable: true },
  { name: 'description', label: 'Descrição', field: 'description', align: 'left' },
  { name: 'amount', label: 'Valor', field: 'amount', align: 'right', sortable: true },
];

function resetForm() {
  formData.value = {
    cost_type: 'Outros',
    amount: 0,
    // CORREÇÃO AQUI TAMBÉM
    date: new Date().toISOString().split('T')[0] || '',
    description: '',
  };
}

function openAddDialog() {
  resetForm();
  isDialogOpen.value = true;
}

async function onFormSubmit() {
  isSubmitting.value = true;
  try {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const parsedDate = parse(formData.value.date, 'yyyy-MM-dd', new Date()); // O input date retorna yyyy-MM-dd
    
    const payload: VehicleCostCreate = {
      cost_type: formData.value.cost_type,
      amount: formData.value.amount,
      date: formData.value.date, // Já está no formato correto do input type="date"
      description: formData.value.description
    };
    
    await costsStore.addCost(props.vehicleId, payload);
    isDialogOpen.value = false;
  } finally {
    isSubmitting.value = false;
  }
}

onMounted(() => {
  void costsStore.fetchCosts(props.vehicleId); 
});
</script>
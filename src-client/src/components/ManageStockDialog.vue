<template>
  <q-dialog :model-value="modelValue" @update:model-value="val => emit('update:modelValue', val)" >
    <q-card style="width: 500px; max-width: 90vw;" v-if="part">
      <q-form @submit.prevent="handleSubmit">
        <q-card-section class="bg-primary text-white">
          <div class="text-h6">{{ part.name }}</div>
          <div class="text-subtitle2">Movimentação de Estoque (Atual: {{ part.stock }})</div>
        </q-card-section>

        <q-card-section class="q-gutter-y-md q-pt-md">
          <q-select 
            outlined 
            v-model="formData.transaction_type" 
            :options="filteredTransactionOptions" 
            label="Tipo de Operação *" 
            :rules="[val => !!val || 'Campo obrigatório']" 
          />

          <q-input 
            v-if="formData.transaction_type === 'Entrada'"
            outlined 
            v-model.number="formData.quantity" 
            type="number" 
            label="Quantidade a Adicionar *" 
            :rules="[val => val > 0 || 'Deve ser maior que zero']" 
          />

          <template v-if="formData.transaction_type === 'Saída para Uso' || formData.transaction_type === 'Fim de Vida'">
              <div class="text-caption text-grey-8">Selecione o item específico (Rastreabilidade):</div>
              <q-select
                outlined
                dense
                v-model="formData.item_id"
                :options="filteredItemOptions"
                label="Buscar por Serial ou Lote"
                :loading="partStore.isItemsLoading"
                :rules="[val => !!val || 'Selecione um item']"
                emit-value map-options
                use-input
                @filter="filterItems"
              >
                <template v-slot:option="scope">
                  <q-item v-bind="scope.itemProps">
                    <q-item-section>
                      <q-item-label>{{ scope.opt.label }}</q-item-label>
                    </q-item-section>
                    <q-item-section side>
                      <q-btn
                        icon="visibility"
                        flat dense round
                        size="sm"
                        @click.stop="goToItemDetails(scope.opt.value)"
                        title="Ver detalhes"
                      />
                    </q-item-section>
                  </q-item>
                </template>
              </q-select>
          </template>
          
          <q-select 
            v-if="formData.transaction_type === 'Saída para Uso'" 
            outlined 
            v-model="formData.related_vehicle_id" 
            :options="vehicleOptions" 
            label="Destino: Máquina / Equipamento *" 
            emit-value map-options clearable 
            use-input @filter="filterVehicles" 
            :loading="vehicleStore.isLoading"
            :rules="[val => !!val || 'Selecione a máquina de destino']"
          />

          <q-input outlined v-model="formData.notes" type="textarea" label="Justificativa / OS" autogrow />
        </q-card-section>

        <q-card-actions align="right" class="q-pa-md">
          <q-btn flat label="Cancelar" v-close-popup />
          <q-btn type="submit" unelevated color="primary" label="Confirmar" :loading="partStore.isLoading || componentStore.isLoading" />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useRouter } from 'vue-router';
import { usePartStore } from 'stores/part-store';
import { useVehicleStore } from 'stores/vehicle-store';
import { useVehicleComponentStore } from 'stores/vehicle-component-store';
import type { Part } from 'src/models/part-models';
import type { TransactionType, TransactionCreate } from 'src/models/inventory-transaction-models';
import { InventoryItemStatus } from 'src/models/inventory-item-models';
import { Notify } from 'quasar';

const props = defineProps<{ modelValue: boolean, part: Part | null }>();
const emit = defineEmits(['update:modelValue']);

const router = useRouter();
const partStore = usePartStore();
const vehicleStore = useVehicleStore();
const componentStore = useVehicleComponentStore();

const baseTransactionOptions: TransactionType[] = ["Entrada", "Saída para Uso", "Fim de Vida"];

const formData = ref<Partial<TransactionCreate & { item_id: number | null }>>({});
const vehicleOptions = ref<{label: string, value: number}[]>([]);
const filteredItemOptions = ref<{label: string, value: number}[]>([]);

const filteredTransactionOptions = computed(() => {
  // Pneus/Ferramentas geralmente não têm 'Saída para Uso' simples sem OS, 
  // mas vamos deixar flexível aqui.
  return baseTransactionOptions;
});

function filterItems(val: string, update: (callbackFn: () => void) => void) {
  update(() => {
    const needle = val.toLowerCase();
    const options = partStore.availableItems
      .filter(item => 
        !val || String(item.item_identifier).includes(needle)
      )
      .map(item => ({
        label: `Serial: #${item.item_identifier} (Entrada: ${new Date(item.created_at).toLocaleDateString()})`,
        value: item.id
      }));
    filteredItemOptions.value = options;
  });
}

watch(() => props.modelValue, async (isOpening) => {
  if (isOpening && props.part) {
    formData.value = { quantity: 1, item_id: null, transaction_type: 'Entrada' };
    void vehicleStore.fetchAllVehicles({rowsPerPage: 9999});
    await partStore.fetchAvailableItems(props.part.id);
    filterItems('', (fn) => fn()); 
  }
});

watch(() => formData.value.transaction_type, async (newType) => {
  if (props.part && (newType === 'Saída para Uso' || newType === 'Fim de Vida')) {
    await partStore.fetchAvailableItems(props.part.id);
    filterItems('', (fn) => fn());
  }
});

function filterVehicles (val: string, update: (callbackFn: () => void) => void) {
  update(() => {
    const needle = val.toLowerCase();
    // Filtro local nas máquinas já carregadas
    const source = vehicleStore.vehicles; 
    
    if (val === '') {
      vehicleOptions.value = source.map(v => ({ label: `${v.brand} ${v.model} (${v.license_plate || v.identifier})`, value: v.id }));
    } else {
      vehicleOptions.value = source
        .filter(v => JSON.stringify(v).toLowerCase().includes(needle))
        .map(v => ({ label: `${v.brand} ${v.model} (${v.license_plate || v.identifier})`, value: v.id }));
    }
  });
}

function goToItemDetails(itemId: number) {
  emit('update:modelValue', false);
  void router.push({ name: 'item-details', params: { id: itemId } });
}

async function handleSubmit() {
  if (!props.part) return;

  const type = formData.value.transaction_type;
  const notes = formData.value.notes;
  let success = false;

  try {
    if (type === 'Entrada') {
      const qty = formData.value.quantity;
      if (!qty || qty <= 0) {
        Notify.create({ type: 'negative', message: 'A quantidade deve ser positiva.' });
        return;
      }
      success = await partStore.addItems(props.part.id, qty, notes);

    } else if (type === 'Saída para Uso' || type === 'Fim de Vida') {
      const itemId = formData.value.item_id;
      if (!itemId) {
        Notify.create({ type: 'negative', message: 'Selecione um item específico para dar baixa.' });
        return;
      }
      
      const newStatus: InventoryItemStatus = type === 'Saída para Uso' ? InventoryItemStatus.EM_USO : InventoryItemStatus.FIM_DE_VIDA;
      const vehicleId = formData.value.related_vehicle_id;
      
      success = await partStore.setItemStatus(props.part.id, itemId, newStatus, vehicleId, notes);
    
    } else {
      Notify.create({ type: 'warning', message: 'Operação inválida.' });
      return;
    }

    if (success) {
      emit('update:modelValue', false);
    }
  } catch { 
     Notify.create({ type: 'negative', message: 'Erro ao processar movimentação.' });
  }
}
</script>
<template>
  <q-dialog
    :model-value="modelValue"
    @update:model-value="(val) => emit('update:modelValue', val)"
    persistent
  >
    <q-card style="width: 500px; max-width: 90vw">
      <q-form @submit.prevent="handleSubmit">
        <q-card-section class="bg-warning text-black">
          <div class="text-h6">Substituição de Peça</div>
          <div class="text-caption">Registra a saída da peça defeituosa e entrada de uma nova.</div>
        </q-card-section>

        <q-card-section v-if="componentToReplace" class="q-pt-md">
          <div class="text-weight-bold text-negative">1. Item a Remover (Defeituoso)</div>
          <q-item dense class="q-pa-none bg-red-1 q-mb-md rounded-borders">
            <q-item-section avatar>
                <q-icon name="delete" color="negative" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ componentToReplace.part?.name }}</q-item-label>
              <q-item-label caption>
                Serial: {{ componentToReplace.inventory_transaction?.item?.item_identifier || 'N/A' }}
              </q-item-label>
            </q-item-section>
          </q-item>

          <q-select
            v-model="form.old_item_status"
            :options="oldItemStatusOptions"
            label="Destino da Peça Antiga *"
            emit-value
            map-options
            outlined
            dense
            :rules="[(val) => !!val || 'Selecione um destino']"
          />
          
          <q-input
            v-model="form.notes"
            label="Motivo da Troca / Laudo Técnico"
            type="textarea"
            autogrow
            outlined
            dense
            class="q-mt-sm"
          />
        </q-card-section>

        <q-separator />

        <q-card-section>
          <div class="text-weight-bold text-positive">2. Item a Instalar (Reposição)</div>
          <q-select
            v-model="form.new_item_id"
            :options="availableItemOptions"
            label="Selecione o Item do Estoque *"
            emit-value
            map-options
            outlined
            dense
            use-input
            @filter="filterAvailableItems"
            :loading="partStore.isItemsLoading"
            :rules="[(val) => !!val || 'Selecione a peça de reposição']"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">
                  Estoque indisponível para este tipo de peça.
                </q-item-section>
              </q-item>
            </template>
          </q-select>
        </q-card-section>

        <q-card-actions align="right" class="q-pa-md">
          <q-btn flat label="Cancelar" v-close-popup />
          <q-btn
            type="submit"
            unelevated
            color="primary"
            label="Confirmar Troca"
            :loading="isLoading"
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { usePartStore } from 'stores/part-store';
import { useMaintenanceStore } from 'stores/maintenance-store';
import type { VehicleComponent } from 'src/models/vehicle-component-models';
import type { MaintenanceRequest, ReplaceComponentPayload } from 'src/models/maintenance-models';
import { InventoryItemStatus } from 'src/models/inventory-item-models';

const props = defineProps<{
  modelValue: boolean;
  maintenanceRequest: MaintenanceRequest | null;
  componentToReplace: VehicleComponent | null;
}>();

const emit = defineEmits(['update:modelValue', 'replacement-done']);

const $q = useQuasar();
const partStore = usePartStore();
const maintenanceStore = useMaintenanceStore();
const isLoading = ref(false);

const form = ref<{
  new_item_id: number | null;
  old_item_status: InventoryItemStatus;
  notes: string;
}>({
  new_item_id: null,
  old_item_status: InventoryItemStatus.FIM_DE_VIDA,
  notes: '',
});

const oldItemStatusOptions = [
  { label: 'Descarte (Sucata)', value: InventoryItemStatus.FIM_DE_VIDA },
  { label: 'Enviar p/ Reparo (Manutenção)', value: InventoryItemStatus.EM_MANUTENCAO },
  { label: 'Devolver ao Estoque (Bom Estado)', value: InventoryItemStatus.DISPONIVEL },
];

const availableItemOptions = ref<{ label: string; value: number }[]>([]);

async function loadAvailableItems(partId: number | undefined) {
  if (!partId) return;
  await partStore.fetchAvailableItems(partId);
  filterAvailableItems('');
}

function filterAvailableItems(val: string, update?: (callbackFn: () => void) => void) {
  const needle = val.toLowerCase();
  const options = partStore.availableItems
    .filter(item =>
        item.status === InventoryItemStatus.DISPONIVEL && (
        !val || 
        String(item.item_identifier).includes(needle)
      )
    )
    .map((item) => ({
      label: `Serial: ${item.item_identifier}`,
      value: item.id,
    }));

  if (update) {
    update(() => availableItemOptions.value = options);
  } else {
    availableItemOptions.value = options;
  }
}

async function handleSubmit() {
  if (!props.maintenanceRequest || !props.componentToReplace?.id || !form.value.new_item_id) {
    $q.notify({ type: 'negative', message: 'Dados incompletos.' });
    return;
  }

  isLoading.value = true;

  const payload: ReplaceComponentPayload = {
    notes: form.value.notes,
    old_item_status: form.value.old_item_status,
    component_to_remove_id: props.componentToReplace.id,
    new_item_id: form.value.new_item_id,
  };

  const success = await maintenanceStore.replaceComponent(
    props.maintenanceRequest.id,
    payload
  );

  if (success) {
    emit('replacement-done');
    emit('update:modelValue', false);
  }
  isLoading.value = false;
}

watch(() => props.modelValue, (isOpening) => {
    if (isOpening && props.componentToReplace) {
      form.value = {
        new_item_id: null,
        old_item_status: InventoryItemStatus.FIM_DE_VIDA,
        notes: '',
      };
      void loadAvailableItems(props.componentToReplace.part?.id);
    }
});
</script>
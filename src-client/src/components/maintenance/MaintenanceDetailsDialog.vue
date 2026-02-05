<template>
  <q-dialog
    :model-value="modelValue"
    @update:model-value="(val) => emit('update:modelValue', val)"
  >
    <q-card style="width: 800px; max-width: 90vw" class="rounded-borders" v-if="request">
      <q-card-section class="bg-primary text-white">
        <div class="text-h6">
          OS #{{ request.id }}: {{ request.vehicle?.brand }} {{ request.vehicle?.model }}
        </div>
        <div class="text-subtitle2">
          Solicitante: {{ request.reporter?.full_name || 'N/A' }}
          <q-badge color="orange" text-color="black" class="q-ml-sm">
             {{ request.maintenance_type || 'CORRETIVA' }}
          </q-badge>
        </div>
      </q-card-section>

      <q-card-section v-if="industrialData" class="bg-teal-1 q-py-sm">
        <div class="row q-col-gutter-sm items-center">
           <div class="col-auto"><q-icon name="payments" color="teal-9" size="sm" /></div>
           <div class="col text-teal-10 text-weight-bold text-uppercase" style="font-size: 11px">Resumo Financeiro Industrial</div>
           <div class="col-auto text-h6 text-teal-10 text-weight-bolder">R$ {{ totalGeralIndustrial.toFixed(2) }}</div>
        </div>
      </q-card-section>

      <q-card-section v-if="authStore.canEditMaintenance && !isClosed" class="q-pb-none">
        <div class="text-weight-medium q-mb-sm text-grey-8">Fluxo de Aprovação</div>
        <div class="row q-gutter-sm">
          <q-btn
            @click="() => handleUpdateStatus(MaintenanceStatus.APROVADA)"
            color="primary" label="Aprovar OS" dense unelevated icon="thumb_up"
          />
          <q-btn
            @click="() => handleUpdateStatus(MaintenanceStatus.EM_ANDAMENTO)"
            color="info" label="Iniciar Execução" dense unelevated icon="engineering"
          />
          <q-btn
            @click="() => handleUpdateStatus(MaintenanceStatus.CONCLUIDA)"
            color="positive" label="Finalizar OS" dense unelevated icon="check_circle"
          />
          <q-btn
            @click="() => handleUpdateStatus(MaintenanceStatus.REJEITADA)"
            color="negative" label="Cancelar" dense unelevated icon="block"
          />
        </div>
      </q-card-section>

      <q-tabs
        v-model="tab"
        dense
        class="text-grey q-mt-md"
        active-color="primary"
        indicator-color="primary"
        align="justify"
        narrow-indicator
      >
        <q-tab name="details" label="Detalhes da OS" icon="description" />
        <q-tab name="components" label="Peças Utilizadas" icon="extension" />
        <q-tab name="services" label="Custos e Serviços" icon="handyman" />
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="tab" animated>
        
        <q-tab-panel name="details">
          <q-scroll-area style="height: 400px">
            <q-card-section>
              <q-list bordered separator class="rounded-borders">
                <q-item>
                  <q-item-section>
                    <q-item-label caption>Equipamento</q-item-label>
                    <q-item-label class="text-weight-bold">
                      {{ request.vehicle?.brand }} {{ request.vehicle?.model }} 
                      (Tag: {{ request.vehicle?.license_plate || request.vehicle?.identifier }})
                    </q-item-label>
                  </q-item-section>
                </q-item>
                <q-item>
                  <q-item-section>
                    <q-item-label caption>Especialidade</q-item-label>
                    <q-item-label>{{ request.category }}</q-item-label>
                  </q-item-section>
                </q-item>
                <q-item>
                  <q-item-section>
                    <q-item-label caption>Descrição da Falha / Serviço</q-item-label>
                    <q-item-label class="text-body2 bg-grey-1 q-pa-sm rounded-borders" style="white-space: pre-wrap">
                      {{ request.problem_description }}
                    </q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-card-section>

            <q-card-section v-if="industrialData">
               <div class="text-subtitle1 q-mb-sm text-primary">Detalhamento de Custos (Industrial)</div>
               <div class="row q-col-gutter-sm">
                  <div class="col-6 col-md-3" v-for="c in industrialCostBuckets" :key="c.label">
                     <div class="bg-grey-2 q-pa-sm rounded-borders text-center">
                        <div class="text-caption text-grey-7">{{ c.label }}</div>
                        <div class="text-subtitle2 text-weight-bold">R$ {{ c.value.toFixed(2) }}</div>
                     </div>
                  </div>
               </div>
            </q-card-section>

            <q-card-section v-if="request.part_changes && request.part_changes.length > 0">
              <div class="text-subtitle1 q-mb-sm text-primary">Movimentações de Estoque</div>
              <q-timeline color="secondary" dense>
                <q-timeline-entry
                  v-for="log in request.part_changes"
                  :key="log.id"
                  :subtitle="new Date(log.timestamp).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })"
                  :title="`Técnico: ${log.user.full_name}`"
                  icon="inventory_2"
                >
                  <div :style="log.is_reverted ? 'text-decoration: line-through; opacity: 0.7;' : ''">
                    <div v-if="log.component_removed">
                      <q-badge color="negative" class="q-mr-xs">REMOVIDO</q-badge>
                      <strong>{{ log.component_removed.part?.name || 'Item Desconhecido' }}</strong>
                      (Serial: {{ log.component_removed.inventory_transaction?.item?.item_identifier || 'N/A' }})
                    </div>
                    <div v-else>
                         <q-badge color="info" class="q-mr-xs">INSTALAÇÃO</q-badge>
                         Instalação de item novo (sem troca)
                    </div>

                    <div class="q-mt-xs">
                      <q-badge color="positive" class="q-mr-xs">INSTALADO</q-badge>
                      <strong>{{ log.component_installed?.part?.name || 'Item Desconhecido' }}</strong>
                      (Serial: {{ log.component_installed?.inventory_transaction?.item?.item_identifier || 'N/A' }})
                    </div>
                    
                    <div v-if="log.notes" class="text-caption text-grey-7 q-mt-sm bg-grey-2 q-pa-xs">
                      <strong>Obs:</strong> {{ log.notes }}
                    </div>
                  </div>

                  <div class="q-mt-sm" v-if="authStore.canEditMaintenance && !isClosed">
                    <q-badge v-if="log.is_reverted" color="grey-7" label="Estorno Realizado" icon="undo" />
                    <q-btn
                      v-else
                      label="Estornar Movimentação"
                      color="negative"
                      flat
                      dense
                      size="sm"
                      icon="undo"
                      @click="onRevert(log)"
                      :loading="maintenanceStore.isLoading"
                    >
                        <q-tooltip>Devolve a peça nova ao estoque e restaura a antiga</q-tooltip>
                    </q-btn>
                  </div>
                </q-timeline-entry>
              </q-timeline>
            </q-card-section>

            <q-card-section>
              <div class="text-subtitle1 q-mb-sm text-primary">Diário de Bordo</div>
              <div v-if="request.comments.length === 0" class="text-caption text-grey">Nenhum comentário registrado.</div>
              <q-chat-message
                v-for="comment in request.comments"
                :key="comment.id"
                :name="comment.user?.full_name || 'Sistema'"
                :sent="comment.user?.id === authStore.user?.id"
                text-color="white"
                :bg-color="comment.user?.id === authStore.user?.id ? 'primary' : 'grey-7'"
              >
                <div style="white-space: pre-wrap">{{ comment.comment_text }}</div>
              </q-chat-message>
            </q-card-section>
          </q-scroll-area>
        </q-tab-panel>

        <q-tab-panel name="components">
          <div class="row justify-end q-mb-md">
            <q-btn
              label="Requisitar Peça do Estoque"
              icon="add_shopping_cart"
              color="positive"
              unelevated
              @click="isInstallDialogOpen = true"
              :disable="!authStore.canEditMaintenance || isClosed"
            />
          </div>

          <q-table
            title="Peças/Componentes Vinculados"
            :rows="componentStore.components"
            :columns="componentColumns"
            row-key="id"
            :loading="componentStore.isLoading"
            no-data-label="Nenhuma peça vinculada a esta máquina."
            flat
            bordered
            dense
            style="height: 400px"
            virtual-scroll
          >
            <template v-slot:body-cell-component_and_item="props">
              <q-td :props="props">
                <div class="text-weight-bold text-primary">
                  {{ props.row.part?.name || 'N/A' }}
                </div>
                <div class="text-caption text-grey-8">
                  Serial/Lote: {{ props.row.inventory_transaction?.item?.item_identifier || 'N/A' }}
                </div>
              </q-td>
            </template>

            <template v-slot:body-cell-actions="props">
              <q-td :props="props">
                <q-btn
                  label="Trocar (Defeito/Preventiva)"
                  color="warning"
                  text-color="black"
                  unelevated
                  size="sm"
                  @click="openReplaceDialog(props.row)"
                  :disable="!authStore.canEditMaintenance || isClosed"
                />
              </q-td>
            </template>
          </q-table>
        </q-tab-panel>

        <q-tab-panel name="services">
            <div class="row q-col-gutter-md">
                <div class="col-12 col-md-7">
                    <div class="text-h6 q-mb-md">Itens de Custo</div>
                    
                    <q-list bordered separator v-if="allServices.length > 0">
  <q-item v-for="service in allServices" :key="service.id">
    <q-item-section avatar>
      <q-icon name="engineering" color="grey-7" />
    </q-item-section>
    <q-item-section>
      <q-item-label>{{ service.description }}</q-item-label>
      <q-item-label caption>Executor: {{ service.provider_name || 'Equipe Interna' }}</q-item-label>
    </q-item-section>
    <q-item-section side>
      <div class="text-weight-bold text-primary">
        R$ {{ service.cost.toFixed(2) }}
      </div>
    </q-item-section>
  </q-item>
  
  <q-separator />
  
  <q-item class="bg-grey-1">
    <q-item-section>
      <q-item-label class="text-weight-bold">Investimento Total na O.S.</q-item-label>
    </q-item-section>
    <q-item-section side>
      <div class="text-h6 text-weight-bold text-positive">
        R$ {{ grandTotalCalculated.toFixed(2) }}
      </div>
    </q-item-section>
  </q-item>
</q-list>

                    <div v-else-if="industrialData" class="text-center text-grey q-pa-lg border-dashed">
                        Os detalhes dos itens estão no arquivo permanente. <br>
                        Confira o resumo financeiro industrial na aba detalhes.
                    </div>

                    <div v-else class="text-center text-grey q-pa-lg border-dashed">
                        Nenhum serviço externo ou custo extra lançado.
                    </div>

                    
                </div>

                <div class="col-12 col-md-5" v-if="!isClosed && authStore.canEditMaintenance">
                    <q-card flat bordered class="bg-grey-1">
                        <q-card-section>
                            <div class="text-subtitle1 text-weight-bold q-mb-sm">Lançar Custo Adicional</div>
                            <q-form @submit="handleAddService">
                                <q-input 
                                    v-model="serviceForm.description" 
                                    label="Descrição (Ex: Reparo Motor)" 
                                    filled dense class="q-mb-sm bg-white" 
                                    :rules="[val => !!val || 'Obrigatório']"
                                />
                                <q-input 
                                    v-model="serviceForm.provider_name" 
                                    label="Fornecedor / Técnico" 
                                    filled dense class="q-mb-sm bg-white" 
                                />
                                <q-input 
                                    v-model.number="serviceForm.cost" 
                                    label="Valor (R$)" 
                                    type="number" 
                                    prefix="R$" 
                                    filled dense class="q-mb-md bg-white" 
                                    step="0.01"
                                    :rules="[val => val >= 0 || 'Valor inválido']"
                                />
                                <q-btn 
                                    label="Adicionar Custo" 
                                    type="submit" 
                                    color="primary" 
                                    unelevated 
                                    class="full-width" 
                                    :loading="isSubmittingService"
                                />
                            </q-form>
                        </q-card-section>
                    </q-card>
                </div>
            </div>
        </q-tab-panel>
      </q-tab-panels>

      <q-separator />

      <q-card-section v-if="tab === 'details' && !isClosed" class="bg-grey-1">
        <q-input
          v-model="newCommentText"
          outlined
          bg-color="white"
          placeholder="Adicionar nota ou atualização..."
          dense
          autogrow
          @keydown.enter.prevent="postComment"
        >
          <template v-slot:after>
            <q-btn
              @click="postComment"
              round
              dense
              flat
              icon="send"
              color="primary"
              :disable="!newCommentText.trim()"
            />
          </template>
        </q-input>
      </q-card-section>

      <q-card-section v-if="isClosed" class="text-center text-grey-7 q-pa-lg">
        <q-icon name="lock" size="2em" />
        <div v-if="request.updated_at">
          Ordem de Manutenção encerrada em {{ new Date(request.updated_at).toLocaleDateString('pt-BR') }}.
        </div>
      </q-card-section>
    </q-card>

    <ReplaceComponentDialog
      v-model="isReplaceDialogOpen"
      :maintenance-request="request"
      :component-to-replace="selectedComponent"
      @replacement-done="handleReplacementDone"
    />
    
    <InstallComponentDialog
      v-model="isInstallDialogOpen"
      :maintenance-request="request"
      @installation-done="handleReplacementDone" 
    />

    <FinishMaintenanceDialog
      v-model="showFinishDialog"
      :request="request"
      @confirm="onFinishConfirmed"
    />

  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useQuasar, type QTableColumn } from 'quasar';
import { useMaintenanceStore } from 'stores/maintenance-store';
import { useAuthStore } from 'stores/auth-store';
import { useVehicleComponentStore } from 'stores/vehicle-component-store';
import {
  MaintenanceStatus,
  type MaintenanceRequest,
  type MaintenanceRequestUpdate,
  type MaintenanceCommentCreate,
  type MaintenancePartChangePublic,
} from 'src/models/maintenance-models';
import type { VehicleComponent } from 'src/models/vehicle-component-models';

import ReplaceComponentDialog from './ReplaceComponentDialog.vue';
import InstallComponentDialog from './InstallComponentDialog.vue';
import FinishMaintenanceDialog from './FinishMaintenanceDialog.vue';

const props = defineProps<{ 
  modelValue: boolean;
  request: MaintenanceRequest | null;
}>();
const emit = defineEmits(['update:modelValue']);
const allServices = computed(() => {
  // Se não for uma OS Industrial, retorna a lista padrão
  if (!industrialData.value) return props.request?.services || [];

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const list: any[] = [];

  // Mapeia as linhas de Mão de Obra
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  industrialData.value.labor_rows?.forEach((row: any, i: number) => {
    list.push({
      id: `mo-${i}`,
      description: `[M.O.] ${row.description} (Qtd: ${row.qty})`,
      provider_name: row.responsible,
      cost: (Number(row.qty) || 0) * (Number(row.unit_value) || 0)
    });
  });

  // Mapeia as linhas de Material
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  industrialData.value.material_rows?.forEach((row: any, i: number) => {
    list.push({
      id: `mat-${i}`,
      description: `[MAT] ${row.description} (Qtd: ${row.qty})`,
      provider_name: row.responsible,
      cost: (Number(row.qty) || 0) * (Number(row.unit_value) || 0)
    });
  });

  // Mapeia as linhas de Terceiros
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  industrialData.value.third_party_rows?.forEach((row: any, i: number) => {
    list.push({
      id: `ter-${i}`,
      description: `[TER] ${row.description} (Qtd: ${row.qty})`,
      provider_name: row.responsible,
      cost: (Number(row.qty) || 0) * (Number(row.unit_value) || 0)
    });
  });

  // Adiciona o custo "Outros" se existir e for maior que zero
  if (Number(industrialData.value.others_total) > 0) {
    list.push({
      id: 'others',
      description: 'OUTROS CUSTOS / DIVERSOS',
      provider_name: 'N/A',
      cost: Number(industrialData.value.others_total)
    });
  }

  return list;
});
const $q = useQuasar();
const maintenanceStore = useMaintenanceStore();
const authStore = useAuthStore();
const componentStore = useVehicleComponentStore();

const newCommentText = ref('');
const tab = ref('details');

const isReplaceDialogOpen = ref(false);
const isInstallDialogOpen = ref(false);
const showFinishDialog = ref(false);

const selectedComponent = ref<VehicleComponent | null>(null);

// --- LÓGICA DE CUSTOS INDUSTRIAIS ---
const industrialData = computed(() => {
  if (!props.request?.manager_notes) return null;
  try {
    const meta = JSON.parse(props.request.manager_notes);
    // Verifica se tem as chaves da manutenção industrial
    if (meta.labor_total !== undefined || meta.material_total !== undefined) return meta;
    return null;
  } catch { return null; }
});

const totalGeralIndustrial = computed(() => {
  if (!industrialData.value) return 0;
  return (Number(industrialData.value.labor_total) || 0) +
         (Number(industrialData.value.material_total) || 0) +
         (Number(industrialData.value.services_total) || 0) +
         (Number(industrialData.value.others_total) || 0);
});

const industrialCostBuckets = computed(() => {
  if (!industrialData.value) return [];
  return [
    { label: 'Mão de Obra', value: Number(industrialData.value.labor_total) || 0 },
    { label: 'Materiais', value: Number(industrialData.value.material_total) || 0 },
    { label: 'Terceiros', value: Number(industrialData.value.services_total) || 0 },
    { label: 'Outros', value: Number(industrialData.value.others_total) || 0 },
  ];
});

// Lógica de Serviços
const serviceForm = ref({ description: '', provider_name: '', cost: 0 });
const isSubmittingService = ref(false);

const grandTotalCalculated = computed(() => {
    // Soma serviços da lista + o total industrial (se houver)
    const listSum = props.request?.services?.reduce((sum, s) => sum + (s.cost || 0), 0) || 0;
    return industrialData.value ? totalGeralIndustrial.value : listSum;
});


async function handleAddService() {
    if (!props.request) return;
    isSubmittingService.value = true;
    const success = await maintenanceStore.addServiceItem(props.request.id, {
        description: serviceForm.value.description,
        provider_name: serviceForm.value.provider_name,
        cost: serviceForm.value.cost,
        item_type: 'THIRD_PARTY'
    });
    if (success) serviceForm.value = { description: '', provider_name: '', cost: 0 };
    isSubmittingService.value = false;
}

const componentColumns: QTableColumn<VehicleComponent>[] = [
  { name: 'component_and_item', label: 'Componente / Serial', field: () => '', align: 'left', sortable: true },
  { name: 'installation_date', label: 'Instalado em', field: 'installation_date', format: (val) => new Date(val).toLocaleDateString('pt-BR'), align: 'left', sortable: true },
  { name: 'actions', label: 'Ações', field: () => '', align: 'center' },
];

const isClosed = computed(() => 
  props.request?.status === MaintenanceStatus.CONCLUIDA ||
  props.request?.status === MaintenanceStatus.REJEITADA
);

async function postComment() {
  if (!props.request || !newCommentText.value.trim()) return;
  const payload: MaintenanceCommentCreate = { comment_text: newCommentText.value };
  await maintenanceStore.addComment(props.request.id, payload);
  newCommentText.value = '';
}

function openReplaceDialog(component: VehicleComponent) {
  selectedComponent.value = component;
  isReplaceDialogOpen.value = true;
}

function handleReplacementDone() {
  if (props.request?.vehicle?.id) {
    void componentStore.fetchComponents(props.request.vehicle.id);
  }
}

function onRevert(log: MaintenancePartChangePublic) {
  if (!props.request || !log.component_installed) return;
  const partName = log.component_installed.part?.name || 'N/A';
  const itemIdentifier = log.component_installed.inventory_transaction?.item?.item_identifier || 'N/A';

  $q.dialog({
    title: 'Estornar Movimentação',
    message: `Confirma o estorno da peça <strong>'${partName}'</strong> (Cód: ${itemIdentifier})?`,
    html: true,
    cancel: 'Cancelar',
    ok: { label: 'Confirmar Estorno', color: 'negative' },
    persistent: false,
  }).onOk(() => {
    void (async () => {
       if(!props.request) return;
       const success = await maintenanceStore.revertPartChange(props.request.id, log.id);
       if (success) handleReplacementDone();
    })();
  });
}

function handleUpdateStatus(newStatus: MaintenanceStatus) {
  if (!props.request) return;
  if (newStatus === MaintenanceStatus.CONCLUIDA) {
    if (props.request.maintenance_type === 'PREVENTIVA') {
        showFinishDialog.value = true;
    } else {
        void performDirectUpdate({ status: newStatus });
    }
  } else if (newStatus === MaintenanceStatus.REJEITADA) {
    $q.dialog({
      title: 'Motivo do Cancelamento',
      message: 'Justifique o cancelamento desta OS:',
      prompt: { model: '', type: 'textarea' },
      cancel: true
    }).onOk((data: string) => {
       void performDirectUpdate({ status: newStatus, manager_notes: data });
    });
  } else {
    void performDirectUpdate({ status: newStatus, manager_notes: props.request.manager_notes });
  }
}

const performDirectUpdate = async (payload: MaintenanceRequestUpdate) => {
    if (!props.request) return;
    await maintenanceStore.updateRequest(props.request.id, payload);
    if (payload.status === MaintenanceStatus.CONCLUIDA || payload.status === MaintenanceStatus.REJEITADA) {
      emit('update:modelValue', false);
    }
};

async function onFinishConfirmed(payload: MaintenanceRequestUpdate) {
    if (!props.request) return;
    await maintenanceStore.updateRequest(props.request.id, payload);
    emit('update:modelValue', false);
}

watch(() => tab.value, (newTab) => {
    if (newTab === 'components' && props.request?.vehicle?.id) {
      if (componentStore.currentVehicleId !== props.request.vehicle.id) {
        void componentStore.fetchComponents(props.request.vehicle.id);
      }
    }
});

watch(() => props.request?.id, (newId, oldId) => {
    if (newId !== oldId) {
      tab.value = 'details';
      if (props.request?.vehicle.id) {
        void componentStore.fetchComponents(props.request.vehicle.id);
      }
    }
}, { immediate: true });
</script>

<style scoped>
.border-dashed { border: 1px dashed #ccc; border-radius: 4px; }
</style>
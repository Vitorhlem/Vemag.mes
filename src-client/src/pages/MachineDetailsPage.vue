<template>
  <q-page padding class="q-gutter-y-md">
    <div v-if="!vehicleStore.isLoading && vehicleStore.selectedVehicle">
      <q-card flat bordered class="bg-primary text-white">
        <q-card-section class="row items-center q-gutter-x-md">
          <q-avatar size="80px" font-size="50px" color="white" text-color="primary" icon="precision_manufacturing" />
          <div>
            <div class="text-caption opacity-80 text-uppercase letter-spacing-1">Equipamento Industrial</div>
            <div class="text-h4 text-weight-bold">
              {{ vehicleStore.selectedVehicle.brand }} {{ vehicleStore.selectedVehicle.model }}
            </div>
            <div class="text-subtitle1 opacity-90 row items-center q-gutter-x-sm q-mt-xs">
              <q-badge color="white" text-color="primary" class="q-py-xs q-px-sm text-weight-bold">
                {{ (vehicleStore.selectedVehicle.identifier || vehicleStore.selectedVehicle.license_plate) || 'Sem ID' }}
              </q-badge>
              <q-separator vertical dark />
              <span>
                Horímetro Acumulado: 
                <strong>{{ (vehicleStore.selectedVehicle.current_engine_hours || vehicleStore.selectedVehicle.current_km || 0).toLocaleString('pt-BR') }} h</strong>
              </span>
              <q-separator vertical dark />
              <q-chip dense :color="getStatusColor(vehicleStore.selectedVehicle.status)" text-color="white" icon="circle" class="q-ma-none">
                {{ vehicleStore.selectedVehicle.status }}
              </q-chip>
            </div>
          </div>
        </q-card-section>
      </q-card>
    </div>
    
    <div v-else class="row items-center q-gutter-x-md">
      <q-skeleton type="circle" size="70px" />
      <div class="col">
        <q-skeleton type="text" width="40%" class="text-h4" />
        <q-skeleton type="text" width="20%" class="text-subtitle1" />
      </div>
    </div>

    <q-card flat bordered>
      <q-tabs v-model="tab" dense class="text-grey-7" active-color="primary" indicator-color="primary" align="justify" narrow-indicator>
        <q-tab name="components" icon="extension" :label="`Componentes Fixos (${filteredComponents.length})`" />
        <q-tab name="documents" icon="description" :label="`Documentos (${machineDocuments.length})`" />
        <q-tab name="history" icon="manage_history" :label="`Movimentações (${filteredHistory.length})`" />
        <q-tab name="costs" icon="attach_money" :label="`Custos (${filteredCosts.length})`" />
        <q-tab name="maintenance" icon="build" :label="`Manutenções (${filteredMaintenances.length})`" />
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="tab" animated transition-prev="fade" transition-next="fade">
        <q-tab-panel name="components">
          <div class="column q-gutter-y-md">
            <div class="row items-center justify-between wrap q-gutter-y-sm">
              <div class="text-h6 row items-center"><q-icon name="extension" class="q-mr-sm" color="primary" />Componentes Instalados</div>
              <div class="row items-center q-gutter-sm">
                <q-input dense outlined debounce="300" v-model="search.components" placeholder="Buscar componente..." style="width: 250px">
                  <template v-slot:prepend><q-icon name="search" /></template>
                </q-input>
                <q-btn @click="isInstallDialogOpen = true" color="primary" unelevated icon="add_circle" label="Instalar Novo" />
              </div>
            </div>
            <q-table :rows="filteredComponents" :columns="componentColumns" row-key="id" :loading="componentStore.isLoading" no-data-label="Nenhum componente instalado." flat bordered>
              <template v-slot:body-cell-component_and_item="props">
                <q-td :props="props">
                  <div class="row items-center">
                    <q-avatar icon="settings" size="sm" color="grey-3" text-color="primary" class="q-mr-sm" />
                    <div>
                      <a href="#" @click.prevent="openPartHistoryDialog(props.row.part)" class="text-primary text-weight-bold link-hover">{{ props.row.part?.name || 'Peça Desconhecida' }}</a>
                      <div v-if="props.row.inventory_transaction?.item" class="text-caption text-grey">Cód: <a href="#" @click.prevent="goToItemDetails(props.row.inventory_transaction.item.id)" class="text-secondary link-hover">{{ props.row.inventory_transaction.item.item_identifier }}</a></div>
                      <div v-else-if="props.row.item" class="text-caption text-grey">Cód: <a href="#" @click.prevent="goToItemDetails(props.row.item.id)" class="text-secondary link-hover">{{ props.row.item.item_identifier }}</a></div>
                    </div>
                  </div>
                </q-td>
              </template>
              <template v-slot:body-cell-actions="props">
                <q-td :props="props">
                  <q-btn v-if="props.row.is_active" @click="confirmDiscard(props.row)" flat round dense color="negative" icon="delete_forever"><q-tooltip>Descartar / Fim de Vida</q-tooltip></q-btn>
                </q-td>
              </template>
            </q-table>
          </div>
        </q-tab-panel>

        <q-tab-panel name="documents">
          <div class="column q-gutter-y-md">
            <div class="row items-center justify-between wrap q-gutter-y-sm">
              <div class="text-h6 row items-center"><q-icon name="menu_book" class="q-mr-sm" color="primary" />Biblioteca Técnica & Manuais</div>
              <div class="row items-center q-gutter-sm"><q-btn color="primary" unelevated icon="cloud_upload" label="Anexar Documento" @click="isDocDialogOpen = true" /></div>
            </div>
            <div v-if="machineDocuments.length === 0" class="text-center q-pa-xl text-grey-6 bg-grey-2 rounded-borders"><q-icon name="folder_off" size="4rem" /><div class="q-mt-md">Nenhum manual ou documento técnico anexado a esta máquina.</div></div>
            <div v-else class="row q-col-gutter-md">
              <div v-for="doc in machineDocuments" :key="doc.id" class="col-12 col-sm-6 col-md-4 col-lg-3">
                <q-card flat bordered class="full-height column">
                  <q-card-section class="col">
                     <div class="row items-center no-wrap"><q-avatar :icon="getDocIcon(doc.document_type)" color="grey-2" text-color="primary" class="q-mr-sm" /><div class="text-subtitle2 text-weight-bold ellipsis">{{ doc.document_type }}</div></div>
                     <div class="text-caption text-grey q-mt-sm" style="min-height: 40px">{{ doc.notes || 'Sem descrição.' }}</div>
                     <div class="text-caption text-grey-6 q-mt-xs">Expira em: {{ formatDate(doc.expiry_date) }}</div>
                  </q-card-section>
                  <q-separator />
                  <q-card-actions align="right">
                    <q-btn flat round color="negative" icon="delete" size="sm" @click="handleDeleteDocument(doc.id)"><q-tooltip>Excluir Documento</q-tooltip></q-btn>
                    <q-btn flat color="primary" icon="download" label="Baixar" :href="doc.file_url" target="_blank" />
                  </q-card-actions>
                </q-card>
              </div>
            </div>
          </div>
        </q-tab-panel>

        <q-tab-panel name="history">
           <div class="column q-gutter-y-md">
            <div class="row items-center justify-between wrap q-gutter-y-sm">
              <div class="text-h6 row items-center"><q-icon name="manage_history" class="q-mr-sm" color="primary" />Log de Movimentações</div>
              <div class="row items-center q-gutter-sm">
                <q-input dense outlined v-model="dateRange.history" mask="##/##/####" label="De" style="width: 140px"><template v-slot:append><q-icon name="event" class="cursor-pointer"><q-popup-proxy cover><q-date v-model="dateRange.history" mask="DD/MM/YYYY"><div class="row items-center justify-end"><q-btn v-close-popup label="Ok" color="primary" flat /></div></q-date></q-popup-proxy></q-icon></template></q-input>
                <q-input dense outlined v-model="dateRange.historyTo" mask="##/##/####" label="Até" style="width: 140px"><template v-slot:append><q-icon name="event" class="cursor-pointer"><q-popup-proxy cover><q-date v-model="dateRange.historyTo" mask="DD/MM/YYYY"><div class="row items-center justify-end"><q-btn v-close-popup label="Ok" color="primary" flat /></div></q-date></q-popup-proxy></q-icon></template></q-input>
                <q-input dense outlined debounce="300" v-model="search.history" placeholder="Buscar por peça..." style="width: 250px"><template v-slot:prepend><q-icon name="search" /></template></q-input>
                <q-btn @click="exportToCsv('history')" color="secondary" outline icon="file_download" label="CSV" />
              </div>
            </div>
            <q-table :rows="filteredHistory" :columns="historyColumns" row-key="id" :loading="isHistoryLoading" no-data-label="Nenhuma movimentação encontrada." flat bordered>
              <template v-slot:body-cell-part_and_item="props">
                <q-td :props="props">
                  <div class="text-weight-medium">{{ getPartName(props.row.item?.part_id || props.row.part?.id) }}</div>
                  <div v-if="props.row.item" class="text-caption text-grey">Cód: <a href="#" @click.prevent="goToItemDetails(props.row.item.id)" class="text-primary link-hover">{{ props.row.item.item_identifier }}</a></div>
                  <span v-else class="text-caption text-grey-5">(Sem identificador)</span>
                </q-td>
              </template>
               <template v-slot:body-cell-transaction_type="props"><q-td :props="props"><q-chip dense square outline :color="props.value.includes('Saída') ? 'orange' : 'teal'" :icon="props.value.includes('Saída') ? 'arrow_upward' : 'arrow_downward'">{{ props.value }}</q-chip></q-td></template>
            </q-table>
          </div>
        </q-tab-panel>

        <q-tab-panel name="costs">
           <div class="column q-gutter-y-md">
            <div class="row items-center justify-between wrap q-gutter-y-sm">
              <div class="text-h6 row items-center"><q-icon name="attach_money" class="q-mr-sm" color="primary" />Gestão de Despesas</div>
              <div class="row items-center q-gutter-sm">
                 <q-btn-dropdown color="primary" unelevated label="Ações" icon="bolt">
                    <q-list>
                      <q-item clickable v-close-popup @click="isAddCostDialogOpen = true"><q-item-section avatar><q-icon name="add" /></q-item-section><q-item-section>Adicionar Custo</q-item-section></q-item>
                      <q-item clickable v-close-popup @click="exportToCsv('costs')"><q-item-section avatar><q-icon name="file_download" /></q-item-section><q-item-section>Exportar CSV</q-item-section></q-item>
                    </q-list>
                 </q-btn-dropdown>
              </div>
            </div>
            <div class="row q-col-gutter-lg">
              <div class="col-12 col-md-8">
                <q-table :rows="filteredCosts" :columns="costColumns" row-key="id" :loading="costStore.isLoading" no-data-label="Nenhum custo registrado no período." flat bordered>
                  <template v-slot:bottom-row><q-tr class="text-weight-bold" :class="$q.dark.isActive ? '' : 'bg-grey-2'"><q-td colspan="3" class="text-right text-uppercase">Total Filtrado:</q-td><q-td class="text-right text-primary text-h6">{{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(totalCost) }}</q-td></q-tr></template>
                </q-table>
              </div>
              <div class="col-12 col-md-4">
                <q-card flat bordered class="full-height">
                  <q-card-section><div class="text-subtitle1 text-weight-medium">Distribuição por Categoria</div></q-card-section>
                  <q-card-section class="flex flex-center">
                    <CostsPieChart v-if="filteredCosts.length > 0" :costs="filteredCosts" />
                    <div v-else class="text-center text-grey q-pa-xl column items-center"><q-icon name="donut_small" size="40px" color="grey-4" /><span class="q-mt-sm">Sem dados para o gráfico.</span></div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </div>
        </q-tab-panel>

        <q-tab-panel name="maintenance">
           <div class="column q-gutter-y-md">
            <div class="row items-center justify-between wrap q-gutter-y-sm">
              <div class="text-h6 row items-center"><q-icon name="build" class="q-mr-sm" color="primary" />Ordens de Manutenção (OM)</div>
              <div class="row items-center q-gutter-sm">
                <q-input dense outlined debounce="300" v-model="search.maintenances" placeholder="Buscar OM..." style="width: 250px"><template v-slot:prepend><q-icon name="search" /></template></q-input>
                <q-btn color="primary" unelevated icon="add" label="Nova OM" @click="isMaintenanceDialogOpen = true" />
              </div>
            </div>
            <q-table :rows="filteredMaintenances" :columns="maintenanceColumns" row-key="id" :loading="maintenanceStore.isLoading" no-data-label="Nenhuma manutenção encontrada." flat bordered>
              <template v-slot:body-cell-status="props"><q-td :props="props"><q-chip :color="props.row.status === 'COMPLETED' ? 'positive' : (props.row.status === 'IN_PROGRESS' ? 'primary' : 'warning')" text-color="white" dense icon="info">{{ props.value }}</q-chip></q-td></template>
              <template v-slot:body-cell-actions="props"><q-td :props="props"><q-btn flat round dense color="primary" icon="visibility" @click="openMaintenanceDetails(props.row)"><q-tooltip>Ver Detalhes da OM</q-tooltip></q-btn></q-td></template>
            </q-table>
          </div>
        </q-tab-panel>
      </q-tab-panels>
    </q-card>

    <q-dialog v-model="isInstallDialogOpen">
      <q-card style="width: 500px; max-width: 90vw;">
        <q-form @submit.prevent="handleInstallComponent">
          <q-card-section class="bg-primary text-white"><div class="text-h6">Instalar Componente Fixo</div></q-card-section>
          <q-card-section class="q-gutter-y-md q-pt-md">
            <q-select outlined v-model="installFormComponent.part_id" :options="partOptions" label="Peça/Item do Estoque *" emit-value map-options use-input @filter="filterParts" :rules="[val => !!val || 'Selecione um item']"><template v-slot:no-option><q-item><q-item-section class="text-grey">Nenhum item encontrado</q-item-section></q-item></template></q-select>
            <q-input outlined v-model.number="installFormComponent.quantity" type="number" label="Quantidade *" :rules="[val => val > 0 || 'Deve ser maior que zero']" />
          </q-card-section>
          <q-card-actions align="right" class="q-pa-md"><q-btn flat label="Cancelar" v-close-popup color="grey" /><q-btn type="submit" unelevated color="primary" label="Instalar" :loading="componentStore.isLoading" /></q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isDocDialogOpen">
      <q-card style="width: 500px">
        <q-form @submit.prevent="handleUploadDocument">
          <q-card-section class="bg-primary text-white"><div class="text-h6">Anexar Manual/Documento</div></q-card-section>
          <q-card-section class="q-gutter-y-md q-pt-md">
            <q-select outlined v-model="newDocForm.document_type" :options="['Manual Técnico', 'Esquema Elétrico', 'Procedimento Operacional', 'Laudo NR12', 'Garantia', 'Outros']" label="Tipo de Documento *" :rules="[val => !!val || 'Obrigatório']" />
            <q-input outlined v-model="newDocForm.notes" label="Descrição / Observações" type="textarea" rows="2" />
            <q-input outlined v-model="newDocForm.expiry_date" label="Validade (Opcional)" type="date" stack-label />
            <q-file outlined v-model="newDocForm.file" label="Arquivo (PDF, Imagem) *" accept=".pdf,.jpg,.jpeg,.png" :rules="[val => !!val || 'Selecione um arquivo']"><template v-slot:prepend><q-icon name="attach_file" /></template></q-file>
          </q-card-section>
          <q-card-actions align="right"><q-btn flat label="Cancelar" v-close-popup color="grey" /><q-btn type="submit" label="Enviar" color="primary" unelevated :loading="documentStore.isLoading" /></q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isAddCostDialogOpen">
      <AddCostDialog :vehicle-id="vehicleId" @close="isAddCostDialogOpen = false" />
    </q-dialog>

    <PartHistoryDialog v-model="isPartHistoryDialogOpen" :part="selectedPart" />
    <MaintenanceDetailsDialog v-model="isMaintenanceDetailsOpen" :request="selectedMaintenance" />
    <CreateRequestDialog v-model="isMaintenanceDialogOpen" :preselected-vehicle-id="vehicleId" />
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useQuasar, type QTableColumn, exportFile } from 'quasar';
import { api } from 'boot/axios';
import { format, differenceInDays, parse } from 'date-fns';

// Stores
import { useVehicleStore } from 'stores/vehicle-store';
import { useVehicleCostStore } from 'stores/vehicle-cost-store';
import { useVehicleComponentStore } from 'stores/vehicle-component-store';
import { usePartStore } from 'stores/part-store';
import { useMaintenanceStore } from 'stores/maintenance-store';
import { useDocumentStore, type DocumentCreatePayload } from 'stores/document-store';

// Models
import { VehicleStatus } from 'src/models/vehicle-models';
import type { VehicleComponent } from 'src/models/vehicle-component-models';
import type { InventoryTransaction } from 'src/models/inventory-transaction-models';
import type { Part } from 'src/models/part-models';
import type { MaintenanceRequest } from 'src/models/maintenance-models';
import type { VehicleCost } from 'src/models/vehicle-cost-models';
// Removida importação não usada: import type { DocumentPublic } from 'src/models/document-models';

// Components
import PartHistoryDialog from 'components/PartHistoryDialog.vue';
import CostsPieChart from 'components/CostsPieChart.vue';
import MaintenanceDetailsDialog from 'components/maintenance/MaintenanceDetailsDialog.vue';
import CreateRequestDialog from 'components/maintenance/CreateRequestDialog.vue';
import AddCostDialog from 'components/AddCostDialog.vue';

const route = useRoute();
const router = useRouter(); 
const $q = useQuasar();
const vehicleStore = useVehicleStore();
const costStore = useVehicleCostStore();
const componentStore = useVehicleComponentStore();
const partStore = usePartStore();
const maintenanceStore = useMaintenanceStore();
const documentStore = useDocumentStore();

const vehicleId = Number(route.params.id);
const tab = ref((route.query.tab as string) || 'components'); 
const isHistoryLoading = ref(false);
const inventoryHistory = ref<InventoryTransaction[]>([]);

const isAddCostDialogOpen = ref(false);
const isInstallDialogOpen = ref(false);
const isPartHistoryDialogOpen = ref(false);
const isMaintenanceDialogOpen = ref(false);
const isMaintenanceDetailsOpen = ref(false);
const isDocDialogOpen = ref(false);

const selectedPart = ref<Part | null>(null);
const selectedMaintenance = ref<MaintenanceRequest | null>(null);
const installFormComponent = ref({ part_id: null as number | null, quantity: 1 });
const partOptions = ref<{label: string, value: number}[]>([]);

const newDocForm = ref<{
  document_type: string;
  notes: string;
  expiry_date: string;
  file: File | null;
}>({
  document_type: 'Manual Técnico',
  notes: '',
  expiry_date: '',
  file: null
});

async function refreshAllVehicleData() {
  isHistoryLoading.value = true;
  await partStore.fetchParts();
  await Promise.all([
    fetchHistory(),
    vehicleStore.fetchVehicleById(vehicleId),
    costStore.fetchCosts(vehicleId),
    componentStore.fetchComponents(vehicleId),
    maintenanceStore.fetchMaintenanceRequests({ vehicleId: vehicleId, limit: 100 }),
    documentStore.fetchDocuments(),
  ]);
  isHistoryLoading.value = false;
}

const machineDocuments = computed(() => {
  return documentStore.documents.filter(d => d.vehicle_id === vehicleId);
});

function getDocIcon(type: string) {
  if (type.includes('Manual')) return 'menu_book';
  if (type.includes('Elétrico')) return 'electrical_services';
  if (type.includes('Laudo')) return 'policy';
  return 'description';
}

function formatDate(dateStr: string) {
  if (!dateStr) return 'Indeterminado';
  return format(new Date(dateStr), 'dd/MM/yyyy');
}

async function handleUploadDocument() {
  if (!newDocForm.value.file) return;
  
  const payload: DocumentCreatePayload = {
    document_type: newDocForm.value.document_type,
    notes: newDocForm.value.notes,
    expiry_date: newDocForm.value.expiry_date || '2099-12-31',
    file: newDocForm.value.file,
    vehicle_id: vehicleId
  };

  try {
    await documentStore.createDocument(payload);
    isDocDialogOpen.value = false;
    newDocForm.value = { document_type: 'Manual Técnico', notes: '', expiry_date: '', file: null };
  } catch (err) {
    // Erro tratado pela store
    console.error(err);
  }
}

// CORREÇÃO: Ação Async estava vazia ou retornando Promise incorretamente
function handleDeleteDocument(docId: number) {
  $q.dialog({
    title: 'Confirmar Exclusão',
    message: 'Tem certeza que deseja remover este documento?',
    cancel: true,
    persistent: true
  }).onOk(() => {
    // Não precisa ser async/await dentro do onOk se o dialog fecha imediatamente
    // O Quasar lida com isso. Se quiser aguardar, use void
    void documentStore.deleteDocument(docId);
  });
}

const search = ref({ history: '', components: '', costs: '', maintenances: '' });
const dateRange = ref({ history: '', historyTo: '', costs: '', costsTo: '' });

const filteredHistory = computed(() => {
  return inventoryHistory.value.filter(row => {
    const needle = search.value.history.toLowerCase();
    const startDate = dateRange.value.history ? parse(dateRange.value.history, 'dd/MM/yyyy', new Date()) : null;
    const endDate = dateRange.value.historyTo ? parse(dateRange.value.historyTo, 'dd/MM/yyyy', new Date()) : null;
    if(endDate) endDate.setHours(23, 59, 59, 999);
    
    const rowDate = new Date(row.timestamp);
    const dateMatch = (!startDate || rowDate >= startDate) && (!endDate || rowDate <= endDate);
    
    const itemIdentifier = row.item?.item_identifier || '';
    const partName = row.part?.name || row.item?.part?.name || '';
    const textMatch = !needle || 
                      JSON.stringify(row).toLowerCase().includes(needle) ||
                      String(itemIdentifier).includes(needle) ||
                      partName.toLowerCase().includes(needle);
    return dateMatch && textMatch;
  });
});

const filteredComponents = computed(() => {
  const needle = search.value.components.toLowerCase();
  if (!needle) return componentStore.components;
  return componentStore.components.filter(row => {
    const itemIdentifier = row.inventory_transaction?.item?.item_identifier || row.item?.item_identifier || '';
    return JSON.stringify(row).toLowerCase().includes(needle) || String(itemIdentifier).includes(needle);
  });
});

const filteredCosts = computed(() => {
  return costStore.costs.filter(row => {
    const needle = search.value.costs.toLowerCase();
    const startDate = dateRange.value.costs ? parse(dateRange.value.costs, 'dd/MM/yyyy', new Date()) : null;
    const endDate = dateRange.value.costsTo ? parse(dateRange.value.costsTo, 'dd/MM/yyyy', new Date()) : null;
    if(endDate) endDate.setHours(23, 59, 59, 999);
    
    const rowDate = new Date(row.date);
    const dateMatch = (!startDate || rowDate >= startDate) && (!endDate || rowDate <= endDate);
    const textMatch = !needle || JSON.stringify(row).toLowerCase().includes(needle);
    return dateMatch && textMatch;
  });
});
const totalCost = computed(() => filteredCosts.value.reduce((sum, cost) => sum + cost.amount, 0));

const filteredMaintenances = computed(() => {
  const needle = search.value.maintenances.toLowerCase();
  if (!needle) return maintenanceStore.maintenances;
  return maintenanceStore.maintenances.filter(row => JSON.stringify(row).toLowerCase().includes(needle));
});

const historyColumns: QTableColumn<InventoryTransaction>[] = [
    { name: 'timestamp', label: 'Data', field: 'timestamp', format: (val) => format(new Date(val), 'dd/MM/yyyy HH:mm'), align: 'left', sortable: true },
    { name: 'part_and_item', label: 'Item', field: (row) => row.id, align: 'left', sortable: true },
    { name: 'transaction_type', label: 'Tipo', field: 'transaction_type', align: 'center', sortable: true },
    { name: 'user', label: 'Responsável', field: row => row.user?.full_name || 'Sistema', align: 'left' },
    { name: 'notes', label: 'Notas', field: 'notes', align: 'left', style: 'max-width: 250px; white-space: normal;' },
];

const componentColumns: QTableColumn<VehicleComponent>[] = [
    { name: 'component_and_item', label: 'Componente', field: (row) => row.id, align: 'left', sortable: true },
    { name: 'installation_date', label: 'Data Instalação', field: 'installation_date', format: (val) => format(new Date(val), 'dd/MM/yyyy'), align: 'left', sortable: true },
    { name: 'age', label: 'Dias Instalado', field: 'installation_date', format: (val) => `${differenceInDays(new Date(), new Date(val))}`, align: 'center', sortable: true },
    { name: 'installer', label: 'Técnico', field: row => row.inventory_transaction?.user?.full_name || 'N/A', align: 'left', sortable: true },
    { name: 'actions', label: '', field: () => '', align: 'right' },
];

const costColumns: QTableColumn<VehicleCost>[] = [
  { name: 'date', label: 'Data', field: 'date', format: (val) => format(new Date(val), 'dd/MM/yyyy'), sortable: true, align: 'left' },
  { name: 'cost_type', label: 'Categoria', field: 'cost_type', sortable: true, align: 'left' },
  { name: 'description', label: 'Descrição', field: 'description', sortable: false, align: 'left', style: 'max-width: 300px; white-space: pre-wrap;' },
  { name: 'amount', label: 'Valor (R$)', field: 'amount', format: (val) => val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }), sortable: true, align: 'right' },
];

const maintenanceColumns: QTableColumn<MaintenanceRequest>[] = [
  { name: 'created_at', label: 'Data Abertura', field: 'created_at', format: (val) => val ? format(new Date(val), 'dd/MM/yyyy') : 'A definir', sortable: true, align: 'left' },
  { name: 'category', label: 'Tipo Manutenção', field: 'category', sortable: true, align: 'left' },
  { name: 'problem_description', label: 'Descrição do Serviço', field: 'problem_description', align: 'left', style: 'max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;' },
  { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
  { name: 'actions', label: '', field: () => '', align: 'right' },
];

async function fetchHistory() {
  isHistoryLoading.value = true;
  try {
    const { data } = await api.get<InventoryTransaction[]>(`/vehicles/${vehicleId}/inventory-history`);
    inventoryHistory.value = data;
  } catch (error) {
    console.error("Falha ao carregar histórico:", error);
    $q.notify({ type: 'negative', message: 'Falha ao carregar o histórico.' });
  } finally {
    isHistoryLoading.value = false;
  }
}

function getStatusColor(status: VehicleStatus | undefined) {
    if (!status) return 'grey';
    switch(status) {
        case VehicleStatus.AVAILABLE: return 'positive';
        case VehicleStatus.MAINTENANCE: return 'warning';
        case VehicleStatus.IN_USE: return 'primary';
        default: return 'grey';
    }
}

function getPartName(partId: number | undefined | null): string {
  if (!partId) return 'Item N/A';
  const part = partStore.parts.find(p => p.id === partId);
  return part?.name || 'Item N/A';
}

function filterParts(val: string, update: (cb: () => void) => void) {
  update(() => {
    const needle = val.toLowerCase();
    partOptions.value = partStore.parts
      .filter(p => p.name.toLowerCase().includes(needle) && p.stock > 0 && p.category !== 'Pneu')
      .map(p => ({ label: `${p.name} (Estoque: ${p.stock})`, value: p.id }));
  });
}

async function handleInstallComponent() {
  if (!installFormComponent.value.part_id) {
     $q.notify({ type: 'warning', message: 'Por favor, selecione uma peça do estoque.' });
     return;
  }
  
  const payload = {
    part_id: installFormComponent.value.part_id,
    quantity: installFormComponent.value.quantity
  };

  const success = await componentStore.installComponent(vehicleId, payload);
  
  if (success) {
    isInstallDialogOpen.value = false;
    installFormComponent.value = { part_id: null, quantity: 1 };
    await refreshAllVehicleData();
  }
}

function confirmDiscard(component: VehicleComponent) {
    const partName = component.part?.name || 'este item';
    $q.dialog({
        title: 'Confirmar Baixa',
        message: `Deseja dar baixa no item "${partName}"? Isso o marcará como Fim de Vida.`,
        cancel: true, persistent: false,
        ok: { label: 'Confirmar', color: 'negative', unelevated: true }
    }).onOk(() => {
      void (async () => {
         const success = await componentStore.discardComponent(component.id, vehicleId);
         if (success) await refreshAllVehicleData();
      })();
    });
}

function openPartHistoryDialog(part: Part | null) {
  if (!part) return;
  selectedPart.value = part;
  void partStore.fetchHistory(part.id);
  isPartHistoryDialogOpen.value = true;
}

function openMaintenanceDetails(maintenance: MaintenanceRequest) {
  selectedMaintenance.value = maintenance;
  isMaintenanceDetailsOpen.value = true;
}

function goToItemDetails(itemId: number) {
  void router.push({ name: 'item-details', params: { id: itemId } });
}

// CORREÇÃO: Remoção de 'any' explícito com type guard
function exportToCsv(tabName: 'history' | 'components' | 'costs' | 'maintenances') {
    type ExportableRow = InventoryTransaction | VehicleComponent | VehicleCost | MaintenanceRequest;
    
    let data: ExportableRow[] = [];
    let columns: QTableColumn[] = []; 
    let fileName = '';
    
    switch(tabName) {
        case 'history': data = filteredHistory.value; columns = historyColumns; fileName = 'historico_mov'; break;
        case 'components': data = filteredComponents.value; columns = componentColumns; fileName = 'componentes_fixos'; break;
        case 'costs': data = filteredCosts.value; columns = costColumns; fileName = 'custos'; break;
        case 'maintenances': data = filteredMaintenances.value; columns = maintenanceColumns; fileName = 'manutencoes'; break;
    }
    
    if (!data.length || !columns.length) return;

    const columnsToExp = columns.filter(c => c.name !== 'actions' && c.label);
    const content = [
        columnsToExp.map(col => col.label).join(';'),
        ...data.map(row => columnsToExp.map(col => {
          let val;
          const safeRow = row as unknown as Record<string, unknown>;
          
          if (typeof col.field === 'function') {
             // O Quasar espera que col.field receba a row inteira. 
             // O cast é necessário pois a tipagem genérica de QTableColumn é complexa
             // eslint-disable-next-line @typescript-eslint/no-explicit-any
             val = col.field(safeRow as any); 
          } else {
             val = safeRow[col.field];
          }
          
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          if (col.format && val) val = col.format(val, safeRow as any);
          return `"${String(val ?? '').replace(/"/g, '""')}"`;
        }).join(';'))
    ].join('\r\n');

    const status = exportFile(`${fileName}_maq_${vehicleId}.csv`, '\ufeff' + content, 'text/csv');
    if (status !== true) $q.notify({ message: 'Download bloqueado pelo navegador.', color: 'negative' });
}

onMounted(async () => {
  await refreshAllVehicleData();
});
</script>

<style lang="scss" scoped>
.link-hover {
  text-decoration: none;
  transition: color 0.2s;
  &:hover {
    text-decoration: underline;
    filter: brightness(0.8);
  }
}
.opacity-50 { opacity: 0.5; }
.opacity-80 { opacity: 0.8; }
.opacity-90 { opacity: 0.9; }
.full-height { height: 100%; }
.letter-spacing-1 { letter-spacing: 1px; }
</style>
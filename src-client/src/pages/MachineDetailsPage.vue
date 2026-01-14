<template>
  <q-page padding class="q-gutter-y-md bg-grey-1">
    
    <div class="row items-center q-mb-sm">
      <q-btn flat round icon="arrow_back" color="grey-8" @click="router.back()" />
      <div class="q-ml-sm">
        <div class="text-h5 text-weight-bold text-dark">{{ vehicleStore.selectedVehicle?.brand }} {{ vehicleStore.selectedVehicle?.model }}</div>
        <div class="text-caption text-grey-7 text-uppercase letter-spacing-1">Monitoramento de Ativo Industrial</div>
      </div>
      <q-space />
      <div class="text-caption text-grey-6 q-mr-sm mobile-hide">Atualizado: {{ lastUpdateStr }}</div>
      <q-btn icon="refresh" label="Atualizar" flat color="primary" @click="() => refreshAllVehicleData()" :loading="isHistoryLoading" />
    </div>

    <div v-if="!vehicleStore.isLoading && vehicleStore.selectedVehicle" class="row q-col-gutter-md">
      
      <div class="col-12 col-md-4">
        <q-card class="dashboard-card text-center relative-position overflow-hidden full-height column">
           <div class="absolute-top full-width" :class="statusColorClass" style="height: 8px;"></div>
           
           <q-card-section class="q-pt-lg col-grow flex flex-center column">
              <q-avatar size="100px" font-size="50px" :color="statusColor" text-color="white" :icon="statusIcon" class="shadow-3 q-mb-md" />
              
              <div class="text-h4 text-weight-bolder">{{ translatedStatus }}</div>
              
              <div v-if="currentReason" class="text-subtitle1 text-weight-bold text-negative bg-red-1 q-pa-xs rounded-borders inline-block q-mt-sm animate-blink">
                 {{ currentReason }}
              </div>
              <div v-else class="text-subtitle1 text-grey-6 q-mt-sm">
                 {{ statusDescription }}
              </div>
           </q-card-section>

           <q-separator inset />

           <q-card-section>
              <div class="row justify-center q-gutter-x-lg text-left">
                 <div>
                    <div class="text-caption text-uppercase text-grey">Operador Atual</div>
                    <div class="text-weight-bold row items-center">
                       <q-icon name="badge" class="q-mr-xs text-primary"/> 
                       {{ lastLog?.operator_name || 'Nenhum' }}
                    </div>
                 </div>
                 <div>
                    <div class="text-caption text-uppercase text-grey">Horímetro Total</div>
                    <div class="text-weight-bold">
                       {{ (vehicleStore.selectedVehicle.current_engine_hours || 0).toLocaleString('pt-BR') }} h
                    </div>
                 </div>
              </div>
           </q-card-section>
        </q-card>
      </div>

      <div class="col-12 col-md-8">
        <q-card class="dashboard-card full-height column">
          <q-card-section class="bg-grey-2 border-bottom-light q-py-sm">
             <div class="text-subtitle1 text-weight-bold flex items-center">
                <q-icon name="history" class="q-mr-sm"/> Últimos Eventos
             </div>
          </q-card-section>

          <q-card-section class="scroll col">
             <q-timeline color="secondary" layout="dense">
                <q-timeline-entry 
                   v-for="log in productionStore.machineHistory.slice(0, 5)" 
                   :key="log.id"
                   :subtitle="formatDateFull(log.timestamp)"
                   :color="getEventColor(log.event_type, log.new_status)"
                   :icon="getEventIcon(log.event_type, log.new_status)"
                >
                   <template v-slot:title>
                      <div class="text-subtitle2 text-weight-bold">{{ formatEventType(log.event_type) }}</div>
                   </template>
                   <div class="text-caption text-grey-8">
                      <span v-if="log.operator_name"><strong>{{ log.operator_name }}</strong>: </span>
                      <span v-if="log.reason" class="text-weight-bold">{{ log.reason }}</span>
                      <span v-else-if="log.new_status">Status alterado para {{ log.new_status }}</span>
                      <span v-else>{{ log.details || 'Evento registrado' }}</span>
                   </div>
                </q-timeline-entry>
                
                <div v-if="productionStore.machineHistory.length === 0" class="text-center text-grey q-py-md">
                   Nenhum evento recente.
                </div>
             </q-timeline>
          </q-card-section>

          <q-separator />
          <q-card-actions align="center" class="bg-grey-1">
             <q-btn 
                flat 
                color="primary" 
                class="full-width" 
                label="Ver Histórico Completo e Filtros" 
                icon="manage_search" 
                @click="isHistoryDialogOpen = true" 
             />
          </q-card-actions>
        </q-card>
      </div>
    </div>

    <q-card flat bordered class="bg-white">
      <q-tabs v-model="tab" dense class="text-grey-7" active-color="primary" indicator-color="primary" align="justify" narrow-indicator>
        <q-tab name="components" icon="extension" :label="`Peças (${filteredComponents.length})`" />
        <q-tab name="documents" icon="description" :label="`Docs (${machineDocuments.length})`" />
        <q-tab name="costs" icon="attach_money" label="Custos" />
        <q-tab name="maintenance" icon="build" label="Manutenção" />
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
                      <div class="text-weight-bold">{{ props.row.part?.name || 'Peça Desconhecida' }}</div>
                      <div v-if="props.row.item" class="text-caption text-grey">S/N: {{ props.row.item.item_identifier }}</div>
                    </div>
                  </div>
                </q-td>
              </template>
              <template v-slot:body-cell-actions="props">
                <q-td :props="props">
                  <q-btn v-if="props.row.is_active" @click="confirmDiscard(props.row)" flat round dense color="negative" icon="delete_forever"><q-tooltip>Descartar</q-tooltip></q-btn>
                </q-td>
              </template>
            </q-table>
          </div>
        </q-tab-panel>

        <q-tab-panel name="documents">
          <div class="column q-gutter-y-md">
            <div class="row items-center justify-between wrap q-gutter-y-sm">
              <div class="text-h6 row items-center"><q-icon name="menu_book" class="q-mr-sm" color="primary" />Manuais & Documentos</div>
              <q-btn color="primary" unelevated icon="cloud_upload" label="Anexar Documento" @click="isDocDialogOpen = true" />
            </div>
            <div v-if="machineDocuments.length === 0" class="text-center q-pa-xl text-grey-6 bg-grey-2 rounded-borders">
                <q-icon name="folder_off" size="4rem" />
                <div class="q-mt-md">Nenhum documento técnico encontrado.</div>
            </div>
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
                    <q-btn flat round color="negative" icon="delete" size="sm" @click="handleDeleteDocument(doc.id)"><q-tooltip>Excluir</q-tooltip></q-btn>
                    <q-btn flat color="primary" icon="download" label="Baixar" :href="doc.file_url" target="_blank" />
                  </q-card-actions>
                </q-card>
              </div>
            </div>
          </div>
        </q-tab-panel>

        <q-tab-panel name="costs">
           <div class="column q-gutter-y-md">
            <div class="row items-center justify-between wrap q-gutter-y-sm">
              <div class="text-h6 row items-center"><q-icon name="attach_money" class="q-mr-sm" color="primary" />Gestão de Despesas</div>
              <q-btn color="primary" unelevated label="Adicionar Custo" icon="add" @click="isAddCostDialogOpen = true" />
            </div>
            <div class="row q-col-gutter-lg">
              <div class="col-12 col-md-8">
                <q-table :rows="filteredCosts" :columns="costColumns" row-key="id" :loading="costStore.isLoading" flat bordered>
                  <template v-slot:bottom-row><q-tr class="text-weight-bold bg-grey-2"><q-td colspan="3" class="text-right text-uppercase">Total:</q-td><q-td class="text-right text-primary text-h6">{{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(totalCost) }}</q-td></q-tr></template>
                </q-table>
              </div>
              <div class="col-12 col-md-4">
                <q-card flat bordered class="full-height">
                  <q-card-section class="flex flex-center">
                    <CostsPieChart v-if="filteredCosts.length > 0" :costs="filteredCosts" />
                    <div v-else class="text-center text-grey q-pa-xl column items-center"><q-icon name="donut_small" size="40px" color="grey-4" /><span class="q-mt-sm">Sem dados.</span></div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
          </div>
        </q-tab-panel>

        <q-tab-panel name="maintenance">
           <div class="column q-gutter-y-md">
            <div class="row items-center justify-between wrap q-gutter-y-sm">
              <div class="text-h6 row items-center"><q-icon name="build" class="q-mr-sm" color="primary" />Ordens de Manutenção</div>
              <q-btn color="primary" unelevated icon="add" label="Nova OM" @click="isMaintenanceDialogOpen = true" />
            </div>
            <q-table :rows="filteredMaintenances" :columns="maintenanceColumns" row-key="id" :loading="maintenanceStore.isLoading" flat bordered>
              <template v-slot:body-cell-status="props"><q-td :props="props"><q-chip :color="props.row.status === 'COMPLETED' ? 'positive' : 'warning'" text-color="white" dense icon="info">{{ props.value }}</q-chip></q-td></template>
              <template v-slot:body-cell-actions="props"><q-td :props="props"><q-btn flat round dense color="primary" icon="visibility" @click="openMaintenanceDetails(props.row)"><q-tooltip>Ver Detalhes</q-tooltip></q-btn></q-td></template>
            </q-table>
          </div>
        </q-tab-panel>

      </q-tab-panels>
    </q-card>

    <q-dialog v-model="isHistoryDialogOpen" full-width full-height>
      <q-card>
        <q-toolbar class="bg-primary text-white">
          <q-toolbar-title>Histórico Detalhado de Produção</q-toolbar-title>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-toolbar>
        <q-card-section class="full-height q-pa-none">
           <ProductionHistoryTable :machine-id="vehicleId" />
        </q-card-section>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isInstallDialogOpen"><q-card style="width: 500px;"><q-form @submit.prevent="handleInstallComponent"><q-card-section class="bg-primary text-white"><div class="text-h6">Instalar Componente</div></q-card-section><q-card-section class="q-gutter-y-md q-pt-md"><q-select outlined v-model="installFormComponent.part_id" :options="partOptions" label="Item do Estoque *" emit-value map-options use-input @filter="filterParts" /><q-input outlined v-model.number="installFormComponent.quantity" type="number" label="Quantidade *" /></q-card-section><q-card-actions align="right"><q-btn flat label="Cancelar" v-close-popup /><q-btn type="submit" unelevated color="primary" label="Instalar" /></q-card-actions></q-form></q-card></q-dialog>
    <q-dialog v-model="isDocDialogOpen"><q-card style="width: 500px"><q-form @submit.prevent="handleUploadDocument"><q-card-section class="bg-primary text-white"><div class="text-h6">Anexar Documento</div></q-card-section><q-card-section class="q-gutter-y-md q-pt-md"><q-select outlined v-model="newDocForm.document_type" :options="['Manual', 'Elétrico', 'Garantia']" label="Tipo *" /><q-input outlined v-model="newDocForm.notes" label="Descrição" /><q-file outlined v-model="newDocForm.file" label="Arquivo *" /></q-card-section><q-card-actions align="right"><q-btn flat label="Cancelar" v-close-popup /><q-btn type="submit" label="Enviar" color="primary" unelevated /></q-card-actions></q-form></q-card></q-dialog>
    <q-dialog v-model="isAddCostDialogOpen"><AddCostDialog :vehicle-id="vehicleId" @close="isAddCostDialogOpen = false" /></q-dialog>
    <PartHistoryDialog v-model="isPartHistoryDialogOpen" :part="selectedPart" />
    <MaintenanceDetailsDialog v-model="isMaintenanceDetailsOpen" :request="selectedMaintenance" />
    <CreateRequestDialog v-model="isMaintenanceDialogOpen" :preselected-vehicle-id="vehicleId" />

  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { type QTableColumn } from 'quasar';
import { format } from 'date-fns';

import { useVehicleStore } from 'stores/vehicle-store';
import { useVehicleCostStore } from 'stores/vehicle-cost-store';
import { useVehicleComponentStore } from 'stores/vehicle-component-store';
import { usePartStore } from 'stores/part-store';
import { useMaintenanceStore } from 'stores/maintenance-store';
import { useDocumentStore, type DocumentCreatePayload } from 'stores/document-store';
import { useProductionStore } from 'stores/production-store';

import type { VehicleComponent } from 'src/models/vehicle-component-models';
import type { Part } from 'src/models/part-models';
import type { MaintenanceRequest } from 'src/models/maintenance-models';
import type { VehicleCost } from 'src/models/vehicle-cost-models';

import PartHistoryDialog from 'components/PartHistoryDialog.vue';
import CostsPieChart from 'components/CostsPieChart.vue';
import MaintenanceDetailsDialog from 'components/maintenance/MaintenanceDetailsDialog.vue';
import CreateRequestDialog from 'components/maintenance/CreateRequestDialog.vue';
import AddCostDialog from 'components/AddCostDialog.vue';
import ProductionHistoryTable from 'components/production/ProductionHistoryTable.vue'; 

const route = useRoute();
const router = useRouter(); 

const vehicleStore = useVehicleStore();
const costStore = useVehicleCostStore();
const componentStore = useVehicleComponentStore();
const partStore = usePartStore();
const maintenanceStore = useMaintenanceStore();
const documentStore = useDocumentStore();
const productionStore = useProductionStore();

const vehicleId = Number(route.params.id);
const tab = ref('components'); 
const isHistoryLoading = ref(false);
const isHistoryDialogOpen = ref(false);
const lastUpdateStr = ref('');
let refreshInterval: ReturnType<typeof setInterval>;

// --- LÓGICA DE MONITORAMENTO ROBUSTA ---

const statusRaw = computed(() => {
   // 1. Pega status do veículo (ex: "Em uso" ou "IN_USE")
   let s = String(vehicleStore.selectedVehicle?.status || '').trim();
   
   // 2. Se vier vazio/nulo, usa o último evento da timeline como fallback
   if ((!s || s === 'null' || s === 'undefined' || s === 'OFFLINE') && productionStore.machineHistory.length > 0) {
       const lastLog = productionStore.machineHistory[0];
       // Mapeia termos do evento para termos de exibição
       if (lastLog?.new_status === 'RUNNING') s = 'Em uso';
       else if (lastLog?.new_status === 'STOPPED') s = 'Disponível';
       else if (lastLog?.new_status === 'SETUP') s = 'Em manutenção';
       else s = lastLog?.new_status || '';
   }
   return s;
});

const translatedStatus = computed(() => {
   const s = statusRaw.value;
   // Aceita Inglês (IN_USE) e Português (Em uso)
   if (['Em uso', 'IN_USE', 'RUNNING', 'ON_TRIP'].includes(s)) return 'EM PRODUÇÃO';
   if (['Em manutenção', 'MAINTENANCE', 'SETUP'].includes(s)) return 'EM MANUTENÇÃO'; 
   if (['Disponível', 'AVAILABLE', 'IDLE', 'STOPPED'].includes(s)) return 'PARADA / DISPONÍVEL';
   return 'OFFLINE';
});

const statusColor = computed(() => {
   const s = statusRaw.value;
   if (['Em uso', 'IN_USE', 'RUNNING', 'ON_TRIP'].includes(s)) return 'positive';
   if (['Em manutenção', 'MAINTENANCE', 'SETUP'].includes(s)) return 'negative';
   if (['Disponível', 'AVAILABLE', 'IDLE', 'STOPPED'].includes(s)) return 'warning';
   return 'grey';
});

const statusColorClass = computed(() => `bg-${statusColor.value}`);

const statusIcon = computed(() => {
   const s = statusRaw.value;
   if (['Em uso', 'IN_USE', 'RUNNING'].includes(s)) return 'settings_suggest';
   if (['Em manutenção', 'MAINTENANCE', 'SETUP'].includes(s)) return 'build';
   if (['Disponível', 'AVAILABLE', 'IDLE', 'STOPPED'].includes(s)) return 'hourglass_empty';
   return 'power_off';
});

const statusDescription = computed(() => {
    const s = translatedStatus.value;
    if (s === 'EM PRODUÇÃO') return 'Máquina operando normalmente';
    if (s === 'PARADA / DISPONÍVEL') return 'Aguardando início de O.S.';
    if (s === 'EM MANUTENÇÃO') return 'Intervenção técnica ou Setup';
    return 'Status desconhecido';
});

const lastLog = computed(() => productionStore.machineHistory[0]);
const currentReason = computed(() => {
   const log = lastLog.value;
   if (!log) return null;
   const s = translatedStatus.value;
   // Se estiver parada ou manutenção, mostra motivo
   if ((s === 'EM MANUTENÇÃO' || s === 'PARADA / DISPONÍVEL') && log.reason) {
      return log.reason;
   }
   return null;
});

// --- TIMELINE HELPERS ---
function formatDateFull(dateStr: string) { return new Date(dateStr).toLocaleString('pt-BR'); }

function formatEventType(type: string) {
   const map: Record<string, string> = { 'STATUS_CHANGE': 'Status', 'LOGIN': 'Acesso', 'LOGOUT': 'Saída', 'COUNT': 'Produção', 'ANDON_OPEN': 'Andon' };
   return map[type] || type;
}

function getEventColor(type: string, status?: string) {
   if (type === 'ANDON_OPEN') return 'purple';
   if (status === 'STOPPED' || status === 'MAINTENANCE') return 'negative';
   if (status === 'RUNNING' || status === 'IN_USE') return 'positive';
   if (status === 'SETUP') return 'orange';
   return 'grey';
}

function getEventIcon(type: string, status?: string) {
   if (type === 'ANDON_OPEN') return 'campaign';
   if (status === 'STOPPED') return 'block';
   if (status === 'RUNNING') return 'play_circle';
   if (type === 'COUNT') return 'add_circle';
   return 'circle';
}

// --- DATA FETCHING ---
async function refreshAllVehicleData() {
  isHistoryLoading.value = true;
  await partStore.fetchParts();
  
  await Promise.all([
    vehicleStore.fetchVehicleById(vehicleId),
    productionStore.fetchMachineHistory(vehicleId, { limit: 5 }), // Busca apenas 5 para o resumo
    costStore.fetchCosts(vehicleId),
    componentStore.fetchComponents(vehicleId),
    maintenanceStore.fetchMaintenanceRequests({ vehicleId: vehicleId, limit: 50 }),
    documentStore.fetchDocuments(),
  ]);
  
  lastUpdateStr.value = new Date().toLocaleTimeString();
  isHistoryLoading.value = false;
}

// --- TABELAS & AÇÕES ---
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
const newDocForm = ref<{ document_type: string; notes: string; expiry_date: string; file: File | null; }>({ document_type: 'Manual Técnico', notes: '', expiry_date: '', file: null });
const search = ref({ components: '' });

const machineDocuments = computed(() => documentStore.documents.filter(d => d.vehicle_id === vehicleId));
const filteredComponents = computed(() => {
  const needle = search.value.components.toLowerCase();
  if (!needle) return componentStore.components;
  return componentStore.components.filter(row => JSON.stringify(row).toLowerCase().includes(needle));
});
const filteredCosts = computed(() => costStore.costs);
const totalCost = computed(() => filteredCosts.value.reduce((sum, cost) => sum + cost.amount, 0));
const filteredMaintenances = computed(() => maintenanceStore.maintenances);

const componentColumns: QTableColumn<VehicleComponent>[] = [
    { name: 'component_and_item', label: 'Componente', field: (row) => row.id, align: 'left', sortable: true },
    { name: 'installation_date', label: 'Data', field: 'installation_date', format: (val) => format(new Date(val), 'dd/MM/yyyy'), align: 'left' },
    { name: 'actions', label: '', field: () => '', align: 'right' },
];
const costColumns: QTableColumn<VehicleCost>[] = [
  { name: 'date', label: 'Data', field: 'date', format: (val) => format(new Date(val), 'dd/MM/yyyy'), align: 'left' },
  { name: 'cost_type', label: 'Categoria', field: 'cost_type', align: 'left' },
  { name: 'amount', label: 'Valor', field: 'amount', format: (val) => `R$ ${val}`, align: 'right' },
];
const maintenanceColumns: QTableColumn<MaintenanceRequest>[] = [
  { name: 'created_at', label: 'Data', field: 'created_at', format: (val) => val ? format(new Date(val), 'dd/MM/yyyy') : '-', align: 'left' },
  { name: 'status', label: 'Status', field: 'status', align: 'center' },
  { name: 'actions', label: '', field: () => '', align: 'right' },
];

function getDocIcon(type: string) { return type.includes('Manual') ? 'menu_book' : 'description'; }
function formatDate(dateStr: string) { return dateStr ? format(new Date(dateStr), 'dd/MM/yyyy') : '-'; }
function filterParts(val: string, update: (cb: () => void) => void) {
  update(() => {
    const needle = val.toLowerCase();
    partOptions.value = partStore.parts.filter(p => p.name.toLowerCase().includes(needle)).map(p => ({ label: p.name, value: p.id }));
  });
}

async function handleInstallComponent() { 
    if(!installFormComponent.value.part_id) return;
    await componentStore.installComponent(vehicleId, { part_id: installFormComponent.value.part_id, quantity: installFormComponent.value.quantity });
    isInstallDialogOpen.value = false; 
    await refreshAllVehicleData();
}

async function handleUploadDocument() { 
    if(!newDocForm.value.file) return;
    const payload: DocumentCreatePayload = {
        vehicle_id: vehicleId,
        document_type: newDocForm.value.document_type,
        notes: newDocForm.value.notes,
        expiry_date: newDocForm.value.expiry_date,
        file: newDocForm.value.file
    };
    await documentStore.createDocument(payload);
    isDocDialogOpen.value = false; 
}

function handleDeleteDocument(id: number) { void documentStore.deleteDocument(id); }

function confirmDiscard(row: VehicleComponent) { 
    void (async () => {
       await componentStore.discardComponent(row.id, vehicleId);
       await refreshAllVehicleData();
    })();
}

function openMaintenanceDetails(m: MaintenanceRequest) { 
    selectedMaintenance.value = m; 
    isMaintenanceDetailsOpen.value = true; 
}

onMounted(() => {
   void refreshAllVehicleData();
   refreshInterval = setInterval(() => void refreshAllVehicleData(), 5000);
});

onUnmounted(() => {
   clearInterval(refreshInterval);
});
</script>

<style lang="scss" scoped>
.dashboard-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: white;
}
.letter-spacing-1 { letter-spacing: 1px; }
.border-bottom-light { border-bottom: 1px solid #f1f5f9; }
.animate-blink { animation: blink 2s infinite; }
@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
</style>
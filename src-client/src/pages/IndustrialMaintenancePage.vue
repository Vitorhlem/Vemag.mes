<template>
  <q-page class="q-pa-md bg-industrial-layout">
    
    <div class="row items-center justify-between q-mb-lg animate-fade print-hide">
      <div class="row items-center">
        <div class="logo-container q-mr-lg shadow-2">
          <img src="/vemagdark.png" class="logo-img">
        </div>
        <div>
          <div class="text-h4 text-weight-bolder text-dark">Gestão de Engenharia</div>
          <div class="text-subtitle1 text-grey-7">Centro de Controle de Manutenção (MES)</div>
        </div>
      </div>
      
      <q-btn 
        push 
        color="teal-7" 
        icon="add" 
        label="Nova Ordem de Serviço" 
        @click="newOS"
      />
    </div>

    <div class="row q-col-gutter-md q-mb-lg animate-fade print-hide">
      <div class="col-12 col-md-4">
        <q-card class="kpi-card border-left-teal">
          <q-card-section class="row items-center no-wrap">
            <q-avatar color="teal-1" text-color="teal-9" icon="assignment_turned_in" />
            <div class="q-ml-md">
              <div class="text-caption text-grey-7 text-uppercase">Concluídas</div>
              <div class="text-h5 text-weight-bolder">{{ countConcluidas }}</div>
            </div>
          </q-card-section>
        </q-card>
      </div>
      <div class="col-12 col-md-4">
        <q-card class="kpi-card border-left-amber">
          <q-card-section class="row items-center no-wrap">
            <q-avatar color="amber-1" text-color="amber-9" icon="edit_note" />
            <div class="q-ml-md">
              <div class="text-caption text-grey-7 text-uppercase">Rascunhos</div>
              <div class="text-h5 text-weight-bolder">{{ countRascunhos }}</div>
            </div>
          </q-card-section>
        </q-card>
      </div>
      <div class="col-12 col-md-4">
        <q-card class="kpi-card border-left-teal">
          <q-card-section class="row items-center no-wrap">
            <q-avatar color="teal-1" text-color="teal-9" icon="attach_money" />
            <div class="q-ml-md">
              <div class="text-caption text-grey-7 text-uppercase">Custo Mensal</div>
              <div class="text-h5 text-weight-bolder">R$ {{ totalMonthCost.toFixed(0) }}</div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <q-card class="shadow-1 animate-fade-up print-hide">
      <q-tabs v-model="activeTab" class="text-teal-9 bg-grey-2" active-color="primary" align="left">
        <q-tab name="concluida" label="Arquivo Permanente" />
        <q-tab name="rascunho" label="Rascunhos" />
      </q-tabs>

      <q-tab-panels v-model="activeTab" animated>
        <q-tab-panel :name="activeTab" class="q-pa-none">
          <q-table
            :rows="filteredOrders"
            :columns="columns"
            row-key="id"
            :filter="search"
            :loading="isLoading"
            flat
            bordered
          >
            <template v-slot:top-right>
              <q-input borderless dense debounce="300" v-model="search" placeholder="Pesquisar..." class="bg-grey-2 q-px-md rounded-borders">
                <template v-slot:append><q-icon name="search" /></template>
              </q-input>
            </template>
            <template v-slot:body-cell-actions="props">
              <q-td :props="props" auto-width>
                <q-btn flat round color="teal" icon="visibility" size="sm" @click="openEdit(props.row)" />
              </q-td>
            </template>
          </q-table>
        </q-tab-panel>
      </q-tab-panels>
    </q-card>

    <q-dialog v-model="showForm" persistent maximized transition-show="slide-up">
      <q-card class="bg-grey-4">
        <q-toolbar class="bg-dark text-white print-hide">
          <q-btn flat round icon="close" v-close-popup />
          <q-toolbar-title>OS Industrial #{{ form.id || 'Nova' }}</q-toolbar-title>
          <q-btn flat icon="delete" label="Excluir" @click="confirmDelete" v-if="form.id && !isReadOnly" />
          <q-btn outline color="white" icon="print" label="Imprimir" @click="printDocument" class="q-ml-sm" />
          <q-btn unelevated color="teal-7" icon="save" label="Salvar" @click="submitOS('RASCUNHO')" v-if="!isReadOnly" class="q-ml-sm" />
          <q-btn unelevated color="positive" icon="check" label="Finalizar" @click="submitOS('CONCLUIDA')" v-if="!isReadOnly" class="q-ml-sm" />
        </q-toolbar>

        <q-card-section class="flex flex-center q-pa-none scroll bg-grey-5">
          <div class="a4-sheet shadow-24 bg-white q-pa-md printable-area">
            
            <div class="row items-center q-mb-md">
              <div class="col-4">
                <img src="/vemagdark.png" style="height: 60px">
              </div>
              <div class="col-4 text-center">
                <div class="text-h6 text-weight-bolder" style="line-height: 1.2">ORDEM DE SERVIÇO</div>
                <div class="text-caption text-weight-bold">MANUTENÇÃO INDUSTRIAL</div>
              </div>
              <div class="col-4 text-right">
                <div class="text-h6 text-teal text-weight-bold">Nº: {{ form.id || 'SISTEMA' }}</div>
              </div>
            </div>

            <q-separator color="dark" size="1.5px" class="q-mb-md" />

            <div class="row q-col-gutter-sm q-mb-md">
              <div class="col-6">
                <q-select outlined dense v-model="form.vehicle_id" :options="vehicleOptions" label="Equipamento" emit-value map-options :readonly="isReadOnly" />
              </div>
              <div class="col-6">
                <q-input outlined dense v-model="form.cost_center" label="Centro de Custo" :readonly="isReadOnly" />
              </div>
              <div class="col-4">
                <q-input outlined dense v-model="form.stopped_at" label="Data/Hora Parada" stack-label type="datetime-local" :readonly="isReadOnly" />
              </div>
              <div class="col-4">
                <q-input outlined dense v-model="form.returned_at" label="Data/Hora Retorno" stack-label type="datetime-local" :readonly="isReadOnly" />
              </div>
              <div class="col-4">
                <q-select outlined dense v-model="form.maintenance_type" :options="typeOptions" label="Tipo" :readonly="isReadOnly" />
              </div>
              <div class="col-12">
                <q-input outlined dense v-model="form.responsible" label="Responsável" :readonly="isReadOnly" />
              </div>
            </div>

            <div v-for="table in tableConfigs" :key="table.key" class="q-mb-md">
              <div class="section-title">{{ table.label }}</div>
              <q-markup-table flat bordered dense class="os-table">
                <thead class="bg-grey-3">
                  <tr>
                    <th class="text-left" style="width: 15%">Data</th>
                    <th class="text-left">Descrição</th>
                    <th class="text-center" style="width: 8%">Qtd</th>
                    <th class="text-left" style="width: 20%">Responsável</th>
                    <th class="print-hide" style="width: 40px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in form[table.rows]" :key="i">
                    <td><q-input v-model="row.date" borderless dense type="date" :readonly="isReadOnly" /></td>
                    <td><q-input v-model="row.description" borderless dense :readonly="isReadOnly" /></td>
                    <td><q-input v-model.number="row.qty" borderless dense type="number" class="text-center" :readonly="isReadOnly" /></td>
                    <td><q-input v-model="row.responsible" borderless dense :readonly="isReadOnly" /></td>
                    <td class="print-hide">
                      <q-btn flat round icon="close" color="red" size="xs" @click="form[table.rows].splice(i, 1)" v-if="!isReadOnly" />
                    </td>
                  </tr>
                </tbody>
              </q-markup-table>
              <q-btn 
                v-if="!isReadOnly"
                flat color="teal" 
                icon="add" 
                :label="'ADICIONAR ' + table.short" 
                class="print-hide q-mt-xs text-weight-bold" 
                size="sm"
                @click="addRow(table.key)" 
              />
            </div>

            <div class="section-title">SERVIÇOS EXECUTADOS / OBSERVAÇÕES</div>
            <q-input 
              v-model="form.executed_services" 
              type="textarea" 
              outlined 
              rows="4" 
              class="q-mb-md" 
              :readonly="isReadOnly" 
            />

            <div class="totals-box row items-center q-pa-md q-mb-xl">
              <div class="col row q-col-gutter-sm">
                <div class="col-3">
                  <q-input outlined dense v-model.number="form.labor_total" label="Mão de Obra" prefix="R$" :readonly="isReadOnly" />
                </div>
                <div class="col-3">
                  <q-input outlined dense v-model.number="form.material_total" label="Material" prefix="R$" :readonly="isReadOnly" />
                </div>
                <div class="col-3">
                  <q-input outlined dense v-model.number="form.services_total" label="Serviços" prefix="R$" :readonly="isReadOnly" />
                </div>
                <div class="col-3">
                  <q-input outlined dense v-model.number="form.others_total" label="Outros" prefix="R$" :readonly="isReadOnly" />
                </div>
              </div>
              <div class="col-auto q-pl-xl text-right">
                <div class="text-overline text-weight-bold text-dark">TOTAL GERAL</div>
                <div class="text-h4 text-weight-bolder text-teal">R$ {{ grandTotal.toFixed(2) }}</div>
              </div>
            </div>

            <div class="row justify-around q-mt-xl text-center">
              <div class="col-5">
                <div class="signature-font">{{ form.elaborated_by || '...' }}</div>
                <div class="signature-line"></div>
                <q-input v-model="form.elaborated_by" outlined dense label="Elaborador" class="print-hide q-mt-sm" :readonly="isReadOnly" />
                <div class="text-caption text-weight-bold q-mt-xs">Elaborador</div>
              </div>
              <div class="col-5">
                <div class="signature-font">{{ form.supervisor || '...' }}</div>
                <div class="signature-line"></div>
                <q-input v-model="form.supervisor" outlined dense label="Supervisor" class="print-hide q-mt-sm" :readonly="isReadOnly" />
                <div class="text-caption text-weight-bold q-mt-xs">Supervisor</div>
              </div>
            </div>

          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useQuasar, date } from 'quasar';
import { api } from 'boot/axios';
import { useMaintenanceStore } from 'stores/maintenance-store';
import { useProductionStore } from 'stores/production-store';
import { useAuthStore } from 'stores/auth-store';

const $q = useQuasar();
const maintenanceStore = useMaintenanceStore();
const productionStore = useProductionStore();
const authStore = useAuthStore();

// Tabela do Dashboard
const columns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true, align: 'left' },
  { name: 'vehicle', label: 'Equipamento', field: row => row.vehicle?.identifier, sortable: true, align: 'left' },
  { name: 'date', label: 'Data', field: row => date.formatDate(row.created_at, 'DD/MM/YYYY'), sortable: true, align: 'left' },
  { name: 'status', label: 'Status', field: 'status', align: 'center' },
  { name: 'actions', label: 'Ações', align: 'right' }
];

const activeTab = ref('concluida');
const showForm = ref(false);
const search = ref('');
const isLoading = ref(false);
const typeOptions = ['Mecânica', 'Elétrica', 'Pneumática', 'Hidráulica'];

const tableConfigs = [
  { key: 'labor', label: 'MÃO DE OBRA UTILIZADA', rows: 'labor_rows', short: 'MO' },
  { key: 'material', label: 'MATERIAL UTILIZADO', rows: 'material_rows', short: 'MATERIAL' },
  { key: 'third', label: 'SERVIÇOS DE TERCEIROS', rows: 'third_party_rows', short: 'TERCEIRO' }
];

const initialForm = () => ({
  id: null, vehicle_id: null, cost_center: '', stopped_at: '', returned_at: '',
  responsible: authStore.user?.full_name || '', maintenance_type: 'Mecânica', executed_services: '',
  elaborated_by: authStore.user?.full_name || '', supervisor: '', status: 'RASCUNHO',
  labor_rows: [], material_rows: [], third_party_rows: [],
  labor_total: 0, material_total: 0, services_total: 0, others_total: 0
});

const form = ref(initialForm());

const isReadOnly = computed(() => form.value.status === 'CONCLUIDA');
const filteredOrders = computed(() => maintenanceStore.maintenances.filter(m => m.status === activeTab.value.toUpperCase()));
const countConcluidas = computed(() => maintenanceStore.maintenances.filter(m => m.status === 'CONCLUIDA').length);
const countRascunhos = computed(() => maintenanceStore.maintenances.filter(m => m.status === 'RASCUNHO').length);
const totalMonthCost = computed(() => maintenanceStore.maintenances.filter(m => m.status === 'CONCLUIDA').reduce((acc, m) => acc + (m.total_cost || 0), 0));
const vehicleOptions = computed(() => productionStore.machinesList.map(m => ({ value: m.id, label: `${m.identifier} - ${m.brand}` })));
const grandTotal = computed(() => (Number(form.value.labor_total)||0) + (Number(form.value.material_total)||0) + (Number(form.value.services_total)||0) + (Number(form.value.others_total)||0));

// Ações
function addRow(type: string) {
  const row = { date: date.formatDate(Date.now(), 'YYYY-MM-DD'), description: '', qty: 1, responsible: authStore.user?.full_name || '' };
  if (type === 'labor') form.value.labor_rows.push(row);
  else if (type === 'material') form.value.material_rows.push(row);
  else if (type === 'third') form.value.third_party_rows.push(row);
}

function newOS() { form.value = initialForm(); showForm.value = true; }

function openEdit(os: any) {
  let meta: any = {};
  try { meta = JSON.parse(os.manager_notes || '{}'); } catch (e) {}
  form.value = {
    ...initialForm(),
    id: os.id,
    vehicle_id: os.vehicle_id,
    cost_center: os.cost_center,
    status: os.status,
    stopped_at: os.stopped_at?.substring(0, 16),
    returned_at: os.returned_at?.substring(0, 16),
    maintenance_type: os.maintenance_type,
    executed_services: os.problem_description,
    labor_total: meta.labor_total || 0,
    material_total: meta.material_total || 0,
    services_total: meta.services_total || 0,
    others_total: meta.others_total || 0,
    labor_rows: os.services?.filter((s:any) => s.item_type === 'LABOR').map((s:any) => ({ date: s.created_at?.split('T')[0], description: s.description, qty: s.quantity, responsible: s.responsible })) || []
    // ... mapear demais linhas conforme sua lógica de API
  };
  showForm.value = true;
}

async function submitOS(status: string) {
  $q.loading.show();
  form.value.status = status;
  const success = await maintenanceStore.createIndustrialOS({ ...form.value, manager_notes: JSON.stringify({ 
    labor_total: form.value.labor_total, material_total: form.value.material_total, 
    services_total: form.value.services_total, others_total: form.value.others_total,
    elaborated_by: form.value.elaborated_by, supervisor: form.value.supervisor
  })});
  if (success) { showForm.value = false; await refreshData(); }
  $q.loading.hide();
}

async function confirmDelete() {
  $q.dialog({ title: 'Excluir', message: 'Deseja apagar esta OS?', cancel: true }).onOk(async () => {
    await api.delete(`/maintenance/industrial-os/${form.value.id}`);
    showForm.value = false; await refreshData();
  });
}

const printDocument = () => window.print();
const refreshData = async () => { isLoading.value = true; await maintenanceStore.fetchMaintenanceRequests(); isLoading.value = false; };
onMounted(async () => { await Promise.all([maintenanceStore.fetchMaintenanceRequests(), productionStore.fetchAvailableMachines()]); });
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=Mrs+Saint+Delafield&display=swap');

.bg-industrial-layout { background: #e0e4e8; min-height: 100vh; }

/* KPI ESTILO */
.kpi-card { border-radius: 8px; border: 1px solid #ddd; }
.border-left-teal { border-left: 6px solid #00897b; }
.border-left-amber { border-left: 6px solid #ffb300; }

/* FORMULÁRIO A4 ESTILO IMAGEM */
.a4-sheet { 
  width: 210mm; 
  min-height: 297mm; 
  margin: 20px auto; 
  color: #263238;
}

.section-title { 
  background: #263238; 
  color: white; 
  padding: 4px 10px; 
  font-weight: bold; 
  font-size: 11px; 
  margin-top: 10px;
}

.os-table {
  border: 1px solid #263238;
  thead th { font-size: 10px; font-weight: bold; text-transform: uppercase; color: #444; }
  tbody td { padding: 0 4px !important; }
}

.totals-box {
  background: #f4f6f7;
  border-left: 8px solid #00897b;
  border-radius: 4px;
}

.signature-font { 
  font-family: 'Mrs Saint Delafield', cursive; 
  font-size: 3.5rem; 
  color: #1a237e; 
  height: 50px; 
  display: flex; 
  align-items: flex-end; 
  justify-content: center;
}

.signature-line { border-top: 1.5px solid #263238; width: 100%; margin-top: 5px; }

/* REGRAS DE IMPRESSÃO */
@media print {
  body * { visibility: hidden; }
  .printable-area, .printable-area * { visibility: visible; }
  .printable-area { position: absolute; left: 0; top: 0; width: 100% !important; margin: 0 !important; padding: 5mm !important; }
  .print-hide { display: none !important; }
  .bg-grey-4, .bg-grey-5 { background: white !important; }
  .a4-sheet { box-shadow: none !important; border: none !important; }
}
.logo-container {
  background: white;
  padding: 10px;
  border-radius: 12px;
  /* Adicione as regras abaixo para a imagem dentro do container */
  .logo-img {
    max-height: 60px; /* Define uma altura máxima */
    width: auto;      /* Mantém a proporção da imagem */
    max-width: 100%;  /* Garante que não ultrapasse o container */
  }
}
</style>
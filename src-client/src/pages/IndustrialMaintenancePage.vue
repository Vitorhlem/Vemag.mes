<template>
  <q-page class="q-pa-md bg-industrial-layout">
    
    <div class="row items-center justify-between q-mb-lg animate-fade print-hide">
      <div class="row items-center">
        <div class="logo-container q-mr-lg shadow-2">
          <img src="/vemagdark.png" class="logo-img">
        </div>
        <div>
          <div class="text-h4 text-weight-bolder text-dark">Gestão de Manutenção</div>
          <div class="text-subtitle1 text-grey-7">Centro de Controle de Manutenção (MES)</div>
        </div>
      </div>
      
      <q-btn 
        push 
        color="teal-7" 
        icon="add" 
        label="Nova Ordem de Manutenção" 
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
          <q-toolbar-title>OM Industrial #{{ form.id || 'Nova' }}</q-toolbar-title>    
          <q-btn flat icon="delete" label="Excluir" @click="confirmDelete" v-if="form.id && !isReadOnly" />
          <q-btn flat color="white" icon="picture_as_pdf" label="Salvar PDF" class="q-ml-sm" @click="saveAsPDF" />
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
                <div class="text-h6 text-weight-bolder" style="line-height: 1.2">ORDEM DE MANUTENÇÃO</div>
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
                    <th class="text-right" style="width: 12%">Vl. Unit</th>
                    <th class="text-left" style="width: 20%">Responsável</th>
                    <th class="print-hide" style="width: 40px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, i) in form[table.rows]" :key="i">
                    <td><q-input v-model="row.date" borderless dense type="date" :readonly="isReadOnly" /></td>
                    <td><q-input v-model="row.description" borderless dense :readonly="isReadOnly" /></td>
                    <td><q-input v-model.number="row.qty" borderless dense type="number" class="text-center" :readonly="isReadOnly" /></td>
                    <td><q-input v-model.number="row.unit_value" borderless dense type="number" prefix="R$" class="text-right" :readonly="isReadOnly" /></td>
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
                  <q-input outlined dense v-model.number="form.labor_total" label="Mão de Obra" prefix="R$" readonly />
                </div>
                <div class="col-3">
                  <q-input outlined dense v-model.number="form.material_total" label="Material" prefix="R$" readonly />
                </div>
                <div class="col-3">
                  <q-input outlined dense v-model.number="form.services_total" label="Serviços" prefix="R$" readonly />
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
                <div class="signature-font text-no-wrap">{{ form.elaborated_by || '...' }}</div>
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
import html2pdf from 'html2pdf.js';
import { ref, computed, onMounted, watch } from 'vue';
import { useQuasar, date } from 'quasar';
import { api } from 'boot/axios';
import { useMaintenanceStore } from 'stores/maintenance-store';
import { useProductionStore } from 'stores/production-store';
import { useAuthStore } from 'stores/auth-store';
import { MaintenanceStatus } from 'src/models/maintenance-models'; // Verifique se o import existe
const $q = useQuasar();
const maintenanceStore = useMaintenanceStore();
const productionStore = useProductionStore();
const authStore = useAuthStore();

const columns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true, align: 'left' },
  { name: 'vehicle', label: 'Equipamento', field: row => row.vehicle?.identifier, sortable: true, align: 'left' },
  { name: 'date', label: 'Data', field: row => date.formatDate(row.created_at, 'DD/MM/YYYY'), sortable: true, align: 'left' },
  { name: 'status', label: 'Status', field: 'status', align: 'center' },
  { name: 'actions', label: 'Ações', align: 'right' }
];

const saveAsPDF = () => {
  const element = document.querySelector('.printable-area');
  const opt = {
    margin: 0,
    filename: `OM_Industrial_${form.value.id || 'Nova'}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 3, useCORS: true, letterRendering: true },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  };
  // eslint-disable-next-line @typescript-eslint/no-floating-promises
  html2pdf().set(opt).from(element).save();
};

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
  id: null, 
  vehicle_id: null, 
  cost_center: '', 
  stopped_at: '', 
  returned_at: '',
  responsible: '',
  maintenance_type: 'Mecânica', 
  executed_services: '',
  elaborated_by: authStore.user?.full_name || '', 
  supervisor: '', 
  status: 'RASCUNHO',
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  labor_rows: [] as any[], 
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  material_rows: [] as any[], 
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  third_party_rows: [] as any[],
  labor_total: 0, 
  material_total: 0, 
  services_total: 0, 
  others_total: 0
});

const form = ref(initialForm());

const isReadOnly = computed(() => String(form.value.status) === String(MaintenanceStatus.CONCLUIDA));
const filteredOrders = computed(() => maintenanceStore.maintenances.filter(m => String(m.status) === activeTab.value.toUpperCase()));

const countConcluidas = computed(() => maintenanceStore.maintenances.filter(m => m.status === MaintenanceStatus.CONCLUIDA).length);
const countRascunhos = computed(() => maintenanceStore.maintenances.filter(m => m.status === MaintenanceStatus.RASCUNHO).length);

const totalMonthCost = computed(() => {
  return maintenanceStore.maintenances
    .filter(m => m.status === MaintenanceStatus.CONCLUIDA)
    .reduce((acc, m) => {
      let cost = m.total_cost;
      if (!cost && m.manager_notes) {
        try {
          const meta = JSON.parse(m.manager_notes);
          cost = (Number(meta.labor_total) || 0) + (Number(meta.material_total) || 0) + (Number(meta.services_total) || 0) + (Number(meta.others_total) || 0);
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (e) { cost = 0; }
      }
      return acc + (Number(cost) || 0);
    }, 0);
});

const vehicleOptions = computed(() => productionStore.machinesList.map(m => ({ value: m.id, label: `${m.identifier} - ${m.brand}` })));
const grandTotal = computed(() => (Number(form.value.labor_total)||0) + (Number(form.value.material_total)||0) + (Number(form.value.services_total)||0) + (Number(form.value.others_total)||0));

// --- CÁLCULO AUTOMÁTICO DE TOTAIS ---
watch(() => form.value.labor_rows, (rows) => {
  form.value.labor_total = rows.reduce((acc, row) => acc + ((Number(row.qty) || 0) * (Number(row.unit_value) || 0)), 0);
}, { deep: true });

watch(() => form.value.material_rows, (rows) => {
  form.value.material_total = rows.reduce((acc, row) => acc + ((Number(row.qty) || 0) * (Number(row.unit_value) || 0)), 0);
}, { deep: true });

watch(() => form.value.third_party_rows, (rows) => {
  form.value.services_total = rows.reduce((acc, row) => acc + ((Number(row.qty) || 0) * (Number(row.unit_value) || 0)), 0);
}, { deep: true });

function addRow(type: string) {
  const row = { 
    date: date.formatDate(Date.now(), 'YYYY-MM-DD'), 
    description: '', 
    qty: 1, 
    unit_value: 0, 
    responsible: authStore.user?.full_name || '' 
  };
  if (type === 'labor') form.value.labor_rows.push(row);
  else if (type === 'material') form.value.material_rows.push(row);
  else if (type === 'third') form.value.third_party_rows.push(row);
}

function newOS() { form.value = initialForm(); showForm.value = true; }
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function openEdit(os: any) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let meta: any = {};
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  try { meta = os.manager_notes ? JSON.parse(os.manager_notes) : {}; } catch (e) { meta = {}; }

  form.value = {
    ...initialForm(),
    id: os.id,
    vehicle_id: os.vehicle_id,
    cost_center: os.cost_center || '',
    responsible: os.responsible || meta.responsible || '', 
    supervisor: os.supervisor || meta.supervisor || '',
    elaborated_by: meta.elaborated_by || '',
    status: os.status,
    stopped_at: os.stopped_at ? os.stopped_at.substring(0, 16) : '',
    returned_at: os.returned_at ? os.returned_at.substring(0, 16) : '',
    maintenance_type: os.category || os.maintenance_type || 'Mecânica',
    executed_services: os.problem_description || '',
    labor_total: meta.labor_total || 0,
    material_total: meta.material_total || 0,
    services_total: meta.services_total || 0,
    others_total: meta.others_total || 0,
    labor_rows: meta.labor_rows || [],
    material_rows: meta.material_rows || [],
    third_party_rows: meta.third_party_rows || []
  };
  showForm.value = true;
}

async function submitOS(status: string) {
  $q.loading.show({ message: 'Salvando O.M. Industrial...' });
  form.value.status = status;

  const payload = {
    ...form.value,
    category: form.value.maintenance_type, // FIX: Para aparecer no Card
    executed_services: form.value.executed_services,
    manager_notes: JSON.stringify({
      labor_total: form.value.labor_total,
      material_total: form.value.material_total,
      services_total: form.value.services_total,
      others_total: form.value.others_total,
      labor_rows: form.value.labor_rows,
      material_rows: form.value.material_rows,
      third_party_rows: form.value.third_party_rows,
      elaborated_by: form.value.elaborated_by,
      supervisor: form.value.supervisor,
      category: form.value.maintenance_type,
      responsible: form.value.responsible
    })
  };

  const success = await maintenanceStore.createIndustrialOS(payload);
  if (success) { 
    showForm.value = false; 
    await refreshData(); 
    $q.notify({ type: 'positive', message: 'Ordem de Manutenção salva com sucesso!' });
  }
  $q.loading.hide();
}

function confirmDelete() { // Removido o 'async' daqui
  $q.dialog({ title: 'Excluir', message: 'Deseja apagar esta OM?', cancel: true }).onOk(() => {
    // Adicionado void para indicar que sabemos que a função interna é uma promessa flutuante
    void (async () => {
      await api.delete(`/maintenance/industrial-os/${form.value.id}`);
      showForm.value = false; 
      await refreshData();
    })();
  });
}

const printDocument = () => window.print();
const refreshData = async () => { isLoading.value = true; await maintenanceStore.fetchMaintenanceRequests(); isLoading.value = false; };
onMounted(async () => { await Promise.all([maintenanceStore.fetchMaintenanceRequests(), productionStore.fetchAvailableMachines()]); });
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=Mrs+Saint+Delafield&display=swap');

:deep(.q-panel), :deep(.q-tab-panel), :deep(.q-page), :deep(html), :deep(body) {
  overflow: hidden !important;
  height: 100vh;
}

.bg-industrial-layout { 
  background: #e0e4e8; 
  height: 100vh;
  overflow: hidden; 
}

.a4-sheet { 
  width: 210mm; 
  max-height: 296mm; 
  min-height: 296mm;
  margin: 0 auto; 
  padding: 12mm !important;
  color: #263238;
  position: relative;
  box-sizing: border-box;
  overflow: hidden; 
  display: block;
}

.section-title { 
  background: #37474f;
  color: white; 
  padding: 6px 12px; 
  font-weight: bold; 
  font-size: 10px; 
  margin-top: 15px;
  text-transform: uppercase;
}

.os-table {
  border: 1px solid #cfd8dc;
  thead th { 
    font-size: 9px; 
    font-weight: bold; 
    text-transform: capitalize; 
    color: #263238;
    background-color: #f5f5f5 !important;
  }
  tbody td { padding: 0 4px !important; border-bottom: 1px solid #eceff1; }
}

.totals-box {
  background: #f1f3f4;
  border-left: 6px solid #00897b;
  border-radius: 4px;
  margin-top: 20px;
}

.signature-font { 
  font-family: 'Mrs Saint Delafield', cursive; 
  font-size: 2.8rem;
  color: #1a237e; 
  height: 50px; 
  display: flex; 
  align-items: flex-end; 
  justify-content: center;
  line-height: 1;
  white-space: nowrap;
}

.signature-line { border-top: 1.2px solid #263238; width: 100%; }

.logo-container {
  background: white;
  padding: 8px;
  border-radius: 8px;
  .logo-img { max-height: 50px; width: auto; }
}

@media print {
  @page { size: A4; margin: 0; }
  body * { visibility: hidden; }
  .printable-area, .printable-area * { visibility: visible; }
  .printable-area { position: fixed; left: 0; top: 0; width: 210mm !important; height: 297mm !important; margin: 0 !important; padding: 10mm !important; }
  .print-hide { display: none !important; }
}
</style>
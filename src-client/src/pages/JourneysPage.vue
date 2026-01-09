<template>
  <q-page padding>

    <div v-if="isDemo" class="q-mb-lg animate-fade">
      <q-banner class="rounded-borders border-left-primary bg-grey-2">
        <template v-slot:avatar>
          <q-icon name="history_edu" color="primary" />
        </template>
        <div class="text-subtitle1 text-weight-bold">Registro de Operações Ilimitado</div>
        <div class="text-body2 text-grey-8">
          No modo Demo, o histórico detalhado exibe as <strong>5 últimas Ordens de Produção</strong>. O restante é arquivado com segurança.
        </div>
        <template v-slot:action>
          <q-btn flat label="Liberar Histórico Completo" color="primary" @click="showComparisonDialog = true" />
        </template>
      </q-banner>
    </div>

    <div class="flex items-center justify-between q-mb-md">
      <div>
        <h1 class="text-h5 text-weight-bold q-my-none flex items-center">
          <q-icon name="fact_check" class="q-mr-sm text-primary" />
          {{ terminologyStore.journeyPageTitle }}
        </h1>
        <div class="text-caption text-grey-7">Controle de turnos e apontamento de horas</div>
      </div>
      
      <div class="flex items-center q-gutter-x-sm">
         <q-btn 
          v-if="!journeyStore.currentUserActiveJourney" 
          @click="openStartDialog" 
          color="primary" 
          icon="add_task" 
          :label="terminologyStore.startJourneyButtonLabel" 
          unelevated 
        />
      </div>
    </div>

    <q-card v-if="journeyStore.currentUserActiveJourney" class="bg-grey-10 text-white q-mb-lg border-l-success shadow-2" flat bordered>
      <q-card-section>
        <div class="row items-center">
          <q-avatar color="positive" text-color="white" icon="settings_motion" class="q-mr-md" />
          <div>
            <div class="text-subtitle2 text-uppercase text-grey-5">Status Atual</div>
            <div class="text-h5 text-weight-bold">Produção em Andamento</div>
            <div class="text-subtitle1 text-grey-4 q-mt-xs" v-if="journeyStore.currentUserActiveJourney.vehicle">
              <q-icon name="precision_manufacturing" class="q-mr-xs" />
              {{ journeyStore.currentUserActiveJourney.vehicle.brand }} {{ journeyStore.currentUserActiveJourney.vehicle.model }}
              <span class="text-grey-6 text-caption q-ml-sm">({{ journeyStore.currentUserActiveJourney.vehicle.license_plate || 'Sem Tag' }})</span>
            </div>
          </div>
        </div>
      </q-card-section>
      
      <q-separator dark />
      
      <q-card-section class="row q-col-gutter-md">
          <div class="col-6 col-md-3">
              <div class="text-caption text-grey-5">Início</div>
              <div class="text-weight-medium">{{ formatDate(journeyStore.currentUserActiveJourney.start_time) }}</div>
          </div>
          <div class="col-6 col-md-3">
              <div class="text-caption text-grey-5">Horímetro Inicial</div>
              <div class="text-weight-medium">{{ (journeyStore.currentUserActiveJourney.start_engine_hours || 0).toFixed(1) }} h</div>
          </div>
      </q-card-section>

      <q-card-actions align="right" class="bg-grey-9">
        <q-btn 
            @click="openEndDialog()" 
            color="positive" 
            icon="stop_circle"
            label="Finalizar Turno / Apontar" 
            unelevated 
        />
      </q-card-actions>
    </q-card>
    
    <q-card flat bordered>
      <q-table
        :title="terminologyStore.journeyHistoryTitle"
        :rows="journeyStore.journeys"
        :columns="columns"
        row-key="id"
        :loading="journeyStore.isLoading"
        no-data-label="Nenhuma ordem de produção encontrada"
        :pagination="{ rowsPerPage: 10 }"
        :row-class="getRowClass"
        flat
      >
        <template v-slot:body-cell-status="props">
            <q-td :props="props">
                <q-badge :color="props.row.is_active ? 'positive' : 'grey-7'">
                    {{ props.row.is_active ? 'EM OPERAÇÃO' : 'FINALIZADO' }}
                </q-badge>
            </q-td>
        </template>

        <template v-slot:body-cell-actions="props">
          <q-td :props="props">
            <div v-if="!isRowBlurred(props.rowIndex)">
              <q-btn 
                v-if="props.row.is_active" 
                @click="openEndDialog(props.row)" 
                flat round dense 
                icon="stop_circle" 
                color="positive" 
                title="Finalizar Turno" 
              />
              <q-btn 
                v-if="authStore.isManager" 
                @click="promptToDeleteJourney(props.row)" 
                flat round dense 
                icon="delete" 
                color="negative" 
                title="Excluir Registro" 
              />
            </div>
            <div v-else>
              <q-icon name="lock" color="grey-5" />
            </div>
          </q-td>
        </template>
      </q-table>
    </q-card>
    
    <q-dialog v-model="showComparisonDialog">
      <q-card style="width: 700px; max-width: 95vw;">
        <q-card-section class="bg-primary text-white q-py-lg">
          <div class="text-h5 text-weight-bold text-center">Histórico Vitalício</div>
          <div class="text-subtitle1 text-center text-blue-2">Auditoria completa de produção</div>
        </q-card-section>

        <q-card-section class="q-pa-none">
          <q-markup-table flat separator="horizontal">
            <thead>
              <tr class=" text-uppercase text-grey-7">
                <th class="text-left text-white q-pa-md">Funcionalidade</th>
                <th class="text-center text-weight-bold text-amber-10 q-pa-md">Plano Demo</th>
                <th class="text-center text-weight-bold q-pa-md text-primary">Plano PRO</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="text-weight-medium q-pa-md"><q-icon name="history" color="grey" size="xs" /> Histórico Visível</td>
                <td class="text-center text-amber-10">Últimos 5 registros</td>
                <td class="text-center text-primary text-weight-bold"><q-icon name="check_circle" /> Completo e Vitalício</td>
              </tr>
              <tr>
                <td class="text-weight-medium q-pa-md"><q-icon name="precision_manufacturing" color="grey" size="xs" /> Ordens Simultâneas</td>
                <td class="text-center text-amber-10">Limitado</td>
                <td class="text-center text-primary text-weight-bold"><q-icon name="check_circle" /> Ilimitado</td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card-section>

        <q-card-actions align="center" class="q-pa-lg ">
          <div class="text-center full-width">
            <q-btn color="primary" label="Falar com Consultor" size="lg" unelevated icon="whatsapp" class="full-width" />
            <q-btn flat color="grey" label="Continuar no Demo" class="q-mt-sm" v-close-popup />
          </div>
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isStartDialogOpen">
      <q-card style="width: 500px; max-width: 90vw;">
        <q-card-section class="bg-primary text-white">
            <div class="text-h6">Iniciar Ordem de Produção</div>
            <div class="text-caption">Selecione a máquina para iniciar o apontamento</div>
        </q-card-section>
        
        <q-form @submit.prevent="handleStartJourney">
          <q-card-section class="q-gutter-y-md">
            <q-select 
                outlined 
                v-model="startForm.vehicle_id" 
                :options="vehicleOptions" 
                label="Máquina / Equipamento *" 
                emit-value map-options 
                :rules="[val => !!val || 'Selecione uma máquina']" 
            >
                <template v-slot:prepend><q-icon name="precision_manufacturing" /></template>
            </q-select>
            
            <q-select 
                v-if="isAgroOrIndustry" 
                outlined 
                v-model="startForm.implement_id" 
                :options="implementOptions" 
                label="Ferramenta/Molde Acoplado (Opcional)" 
                emit-value map-options clearable 
                :loading="implementStore.isLoading" 
            >
                <template v-slot:prepend><q-icon name="handyman" /></template>
            </q-select>
            
            <q-input 
                outlined 
                v-model.number="startForm.start_engine_hours" 
                type="number" 
                label="Horímetro Inicial (h) *" 
                hint="Leitura atual do relógio da máquina"
                :rules="[val => val !== null && val !== undefined && val >= 0 || 'Valor deve ser positivo']" 
            >
                <template v-slot:prepend><q-icon name="timer" /></template>
            </q-input>
            
            <q-input 
                outlined 
                v-model="startForm.trip_description" 
                label="Observações / Nº da OP (Opcional)" 
                type="textarea"
                autogrow
            />
            
            <div v-if="!isFixedMachineContext">
                <q-separator class="q-my-md" />
                <div class="text-subtitle2 text-grey-8">Deslocamento (Opcional)</div>
                <q-input outlined v-model="startForm.destination_city" label="Cidade Destino" dense />
            </div>

          </q-card-section>
          
          <q-card-actions align="right" class="bg-grey-1">
              <q-btn flat label="Cancelar" v-close-popup color="grey-7" />
              <q-btn type="submit" unelevated color="primary" label="Iniciar Produção" :loading="isSubmitting" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

    <q-dialog v-model="isEndDialogOpen">
      <q-card style="width: 400px; max-width: 90vw;">
        <q-card-section class="bg-positive text-white">
            <div class="text-h6">Finalizar Turno</div>
        </q-card-section>
        
        <q-form @submit.prevent="handleEndJourney">
          <q-card-section class="q-pt-md">
            <div class="text-subtitle1 q-mb-md text-grey-8">
                Apontamento Final:
            </div>
            
            <q-input 
                v-if="isAgroOrIndustry" 
                autofocus outlined 
                v-model.number="endForm.end_engine_hours" 
                type="number" 
                label="Horímetro Final (h) *" 
                :rules="[
                    val => val !== null && val !== undefined || 'Campo obrigatório',
                    val => val >= (editingJourney?.start_engine_hours || 0) || 'O valor final deve ser maior que o inicial'
                ]" 
            >
                <template v-slot:prepend><q-icon name="timer_off" /></template>
            </q-input>
            
            <q-input 
                v-else 
                autofocus outlined 
                v-model.number="endForm.end_mileage" 
                type="number" 
                label="KM Final *" 
            />
            
            <div class="q-mt-sm bg-blue-1 q-pa-sm rounded-borders text-caption text-primary" v-if="calculatedProduction > 0">
                <strong>Produção Calculada:</strong> {{ calculatedProduction.toFixed(1) }} Horas
            </div>

          </q-card-section>
          
          <q-card-actions align="right">
              <q-btn flat label="Cancelar" v-close-popup />
              <q-btn type="submit" unelevated color="positive" label="Confirmar Apontamento" :loading="isSubmitting" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useQuasar, type QTableColumn } from 'quasar';
import { isAxiosError } from 'axios';
import { useAuthStore } from 'stores/auth-store';
import { useTerminologyStore } from 'stores/terminology-store';
import { useJourneyStore } from 'stores/journey-store';
import { useVehicleStore } from 'stores/vehicle-store';
import { useImplementStore } from 'stores/implement-store';
import { useDemoStore } from 'stores/demo-store';
import { JourneyType, type Journey, type JourneyCreate, type JourneyUpdate } from 'src/models/journey-models';

const $q = useQuasar();
const authStore = useAuthStore();
const terminologyStore = useTerminologyStore();
const journeyStore = useJourneyStore();
const vehicleStore = useVehicleStore();
const implementStore = useImplementStore();
const demoStore = useDemoStore();

const isDemo = computed(() => authStore.user?.role === 'cliente_demo');
const showComparisonDialog = ref(false);

// --- CORREÇÃO: Usando 'agronegocio' OU 'servicos' para ativar modo horas ---
const isAgroOrIndustry = computed(() => 
    authStore.userSector === 'agronegocio' || authStore.userSector === 'servicos'
);

// --- CORREÇÃO: Máquina fixa é contexto de 'servicos' ---
const isFixedMachineContext = computed(() => 
    authStore.userSector === 'servicos'
);

function isRowBlurred(rowIndex: number) {
  if (!isDemo.value) return false;
  return rowIndex >= 5; 
}

function getRowClass(row: Journey, rowIndex: number) {
  if (isRowBlurred(rowIndex)) return 'demo-blur';
  return '';
}

const isSubmitting = ref(false);
const isStartDialogOpen = ref(false);
const isEndDialogOpen = ref(false);
const editingJourney = ref<Journey | null>(null);
const startForm = ref<Partial<JourneyCreate>>({});
const endForm = ref<Partial<JourneyUpdate>>({});

const vehicleOptions = computed(() => 
    vehicleStore.availableVehicles.map(v => ({ 
        label: `${v.brand} ${v.model} (Tag: ${v.license_plate || v.identifier})`, 
        value: v.id 
    }))
);

const implementOptions = computed(() => 
    implementStore.availableImplements.map(i => ({ 
        label: `${i.name} (${i.brand})`, 
        value: i.id 
    }))
);

const calculatedProduction = computed(() => {
    if(!editingJourney.value || endForm.value.end_engine_hours === undefined) return 0;
    const start = editingJourney.value.start_engine_hours || 0;
    return (endForm.value.end_engine_hours || 0) - start;
});

const columns = computed<QTableColumn[]>(() => {
  const cols: QTableColumn[] = [
    { name: 'status', label: 'Status', field: (row: Journey) => row.is_active, align: 'left', sortable: true },
    { name: 'vehicle', label: 'Máquina', field: (row: Journey) => `${row.vehicle?.brand || ''} ${row.vehicle?.model || ''}`, align: 'left', sortable: true },
    { name: 'driver', label: 'Operador', field: (row: Journey) => row.driver?.full_name || 'N/A', align: 'left', sortable: true },
    { name: 'startTime', label: 'Início', field: 'start_time', align: 'center', format: (val: string) => new Date(val).toLocaleString('pt-BR'), sortable: true },
    { name: 'endTime', label: 'Fim', field: 'end_time', align: 'center', format: (val: string | null) => val ? new Date(val).toLocaleString('pt-BR') : 'Em andamento', sortable: true },
    { name: 'distance', label: 'Horas Produtivas', align: 'center', field: (row: Journey) => {
        // Cálculo correto para exibição
        if (row.end_engine_hours != null && row.start_engine_hours != null) {
            return (row.end_engine_hours - row.start_engine_hours).toFixed(1) + ' h';
        }
        return '---';
      }, sortable: true
    },
  ];

  if (isAgroOrIndustry.value) {
    cols.push({ name: 'implement', label: 'Ferramenta/Molde', align: 'left', field: (row: Journey) => row.implement ? `${row.implement.name}` : '-', sortable: true });
  }

  if (authStore.isManager) {
    cols.push({ name: 'actions', label: 'Ações', field: 'actions', align: 'right' });
  }
  return cols;
});

watch(() => startForm.value.vehicle_id, (newVehicleId) => {
  if (!newVehicleId) return;
  const selectedVehicle = vehicleStore.availableVehicles.find(v => v.id === newVehicleId);
  if (selectedVehicle) {
    startForm.value.start_engine_hours = selectedVehicle.current_engine_hours ?? 0;
    startForm.value.start_mileage = selectedVehicle.current_km ?? 0;
  }
});

async function openStartDialog() {
  await vehicleStore.fetchAllVehicles();
  startForm.value = { 
    vehicle_id: null, 
    trip_type: JourneyType.FREE_ROAM, 
    trip_description: '', 
    implement_id: null,
    start_engine_hours: 0
  };
  isStartDialogOpen.value = true;
}

function openEndDialog(journey?: Journey) {
  const journeyToEnd = journey || journeyStore.currentUserActiveJourney;
  if (!journeyToEnd) return;
  
  editingJourney.value = journeyToEnd;
  endForm.value = {};
  
  const currentVal = journeyToEnd.start_engine_hours ?? 0;
  endForm.value.end_engine_hours = currentVal;
  
  isEndDialogOpen.value = true;
}

async function handleStartJourney() {
  isSubmitting.value = true;
  try {
    if (!startForm.value.trip_type) startForm.value.trip_type = JourneyType.FREE_ROAM;
    await journeyStore.startJourney(startForm.value as JourneyCreate);
    $q.notify({ type: 'positive', message: 'Ordem de Produção iniciada!' });
    isStartDialogOpen.value = false;
    await journeyStore.fetchAllJourneys(); 
  } catch (error) {
    let message = 'Erro ao iniciar.';
    if (isAxiosError(error) && error.response?.data?.detail) { message = error.response.data.detail as string; }
    $q.notify({ type: 'negative', message });
  } finally {
    isSubmitting.value = false;
  }
}

async function handleEndJourney() {
  if (!editingJourney.value) return;
  isSubmitting.value = true;
  try {
    await journeyStore.endJourney(editingJourney.value.id, endForm.value);
    $q.notify({ type: 'positive', message: 'Turno finalizado com sucesso.' });
    isEndDialogOpen.value = false;
    await journeyStore.fetchAllJourneys();
    await vehicleStore.fetchAllVehicles(); 
    if (isDemo.value) { void demoStore.fetchDemoStats(true); }
  } catch (error) {
    let message = 'Erro ao finalizar.';
    if (isAxiosError(error) && error.response?.data?.detail) { message = error.response.data.detail as string; }
    $q.notify({ type: 'negative', message });
  } finally {
    isSubmitting.value = false;
    editingJourney.value = null;
  }
}

function promptToDeleteJourney(journey: Journey) {
  $q.dialog({
    title: 'Confirmar Exclusão', 
    message: 'Tem certeza que deseja excluir este registro?',
    cancel: true, persistent: false,
    ok: { label: 'Excluir', color: 'negative', unelevated: true },
  }).onOk(() => { 
    void (async () => { 
        await journeyStore.deleteJourney(journey.id);
        if (isDemo.value) { await demoStore.fetchDemoStats(true); }
    })();
  });
}

function formatDate(val: string) {
    return new Date(val).toLocaleString('pt-BR');
}

onMounted(() => {
  void journeyStore.fetchAllJourneys();
  if (isDemo.value) {
    void demoStore.fetchDemoStats();
  }
});
</script>

<style scoped>
.border-l-success { border-left: 5px solid var(--q-positive); }
.border-left-primary { border-left: 4px solid var(--q-primary); }
:deep(.demo-blur) { filter: blur(4px); opacity: 0.6; pointer-events: none; user-select: none; }
</style>
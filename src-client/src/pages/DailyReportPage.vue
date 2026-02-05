<template>
  <q-page class="q-pa-md bg-grey-1">
    
    <div class="row items-center justify-between q-mb-md">
      <div>
        <div class="text-h4 text-weight-bold text-blue-grey-9">Relatório Consolidado</div>
        <div class="text-subtitle1 text-grey-7">Snapshot Diário de Performance (Imutável)</div>
      </div>
      
      <div class="row q-gutter-md items-center">
        <q-input outlined dense v-model="selectedDate" label="Data de Referência" bg-color="white" style="width: 160px" readonly>
          <template v-slot:append>
            <q-icon name="event" class="cursor-pointer">
              <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                <q-date v-model="selectedDate" mask="YYYY-MM-DD" @update:model-value="loadData">
                  <div class="row items-center justify-end"><q-btn v-close-popup label="Ok" color="primary" flat /></div>
                </q-date>
              </q-popup-proxy>
            </q-icon>
          </template>
        </q-input>

        <q-btn push color="indigo" icon="published_with_changes" label="Recalcular Dia" :loading="mesStore.isLoading" @click="confirmClosing">
            <q-tooltip>Forçar fechamento e atualizar dados</q-tooltip>
        </q-btn>
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-lg">
        <div class="col-12 col-md-3">
            <q-card class="shadow-1 bg-white text-grey-9 border-left-primary">
                <q-card-section>
                    <div class="text-caption text-uppercase text-grey-6">Eficiência Média (Pessoas)</div>
                    <div class="text-h4 text-weight-bolder">{{ kpiEmployeeEfficiency }}%</div>
                </q-card-section>
            </q-card>
        </div>
        <div class="col-12 col-md-3">
            <q-card class="shadow-1 bg-white text-grey-9 border-left-orange">
                <q-card-section>
                    <div class="text-caption text-uppercase text-grey-6">Disponibilidade Frota</div>
                    <div class="text-h4 text-weight-bolder">{{ kpiFleetAvailability }}%</div>
                </q-card-section>
            </q-card>
        </div>
        <div class="col-12 col-md-3">
            <q-card class="shadow-1 bg-white text-grey-9 border-left-green">
                <q-card-section>
                    <div class="text-caption text-uppercase text-grey-6">Horas Produzidas (Total)</div>
                    <div class="text-h4 text-weight-bolder">{{ kpiTotalProduction }}h</div>
                </q-card-section>
            </q-card>
        </div>
        <div class="col-12 col-md-3">
            <q-card class="shadow-1 bg-white text-grey-9 border-left-red">
                <q-card-section>
                    <div class="text-caption text-uppercase text-grey-6">Horas Manutenção</div>
                    <div class="text-h4 text-weight-bolder">{{ kpiTotalMaintenance }}h</div>
                </q-card-section>
            </q-card>
        </div>
    </div>

    <q-card class="shadow-2 bg-white">
        <q-tabs
          v-model="activeTab"
          dense
          class="text-grey"
          active-color="primary"
          indicator-color="primary"
          align="justify"
          narrow-indicator
        >
          <q-tab name="employees" icon="badge" label="Visão Operadores" />
          <q-tab name="vehicles" icon="precision_manufacturing" label="Visão Máquinas" />
        </q-tabs>

        <q-separator />

        <q-tab-panels v-model="activeTab" animated>
          
          <q-tab-panel name="employees" class="q-pa-none">
            <q-table
                :rows="mesStore.dailyEmployeeHistory"
                :columns="empColumns"
                row-key="id"
                flat
                :pagination="{ rowsPerPage: 15 }"
            >
                <template v-slot:body-cell-efficiency="props">
                    <q-td :props="props" style="width: 150px">
                        <q-linear-progress :value="props.value / 100" :color="getColor(props.value)" size="14px" rounded>
                            <div class="absolute-full flex flex-center text-white text-caption text-weight-bold">{{ props.value }}%</div>
                        </q-linear-progress>
                    </q-td>
                </template>
                <template v-slot:body-cell-top_reasons="props">
                    <q-td :props="props">
                        <q-badge v-for="(r, i) in props.value" :key="i" color="grey-3" text-color="black" class="q-mr-xs">
                            {{ r.label }} ({{ r.count }})
                        </q-badge>
                    </q-td>
                </template>
            </q-table>
          </q-tab-panel>

          <q-tab-panel name="vehicles" class="q-pa-none">
            <q-table
                :rows="mesStore.dailyVehicleHistory"
                :columns="vehColumns"
                row-key="id"
                flat
                :pagination="{ rowsPerPage: 15 }"
            >
                <template v-slot:body-cell-availability="props">
                    <q-td :props="props" class="text-weight-bold" :class="getColorText(props.value)">
                        {{ props.value }}%
                    </q-td>
                </template>
                <template v-slot:body-cell-top_reasons="props">
                    <q-td :props="props">
                        <q-badge v-for="(r, i) in props.value" :key="i" color="red-1" text-color="red-9" class="q-mr-xs">
                            {{ r.label }}
                        </q-badge>
                    </q-td>
                </template>
            </q-table>
          </q-tab-panel>

        </q-tab-panels>
    </q-card>

  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { date, useQuasar } from 'quasar';
import { useMesStore } from 'stores/mes-store';

const $q = useQuasar();
const mesStore = useMesStore();
const activeTab = ref('employees');
const selectedDate = ref(date.formatDate(new Date(), 'YYYY-MM-DD'));

// --- COLUNAS ---
const empColumns = [
  { name: 'employee_name', label: 'Colaborador', field: 'employee_name', align: 'left', sortable: true },
  { name: 'total_hours', label: 'Hrs Totais', field: 'total_hours', format: (v: number) => v.toFixed(1) },
  { name: 'productive_hours', label: 'Hrs Prod.', field: 'productive_hours', classes: 'text-green-9 text-weight-bold' },
  { name: 'unproductive_hours', label: 'Hrs Parada', field: 'unproductive_hours', classes: 'text-red-9' },
  { name: 'efficiency', label: 'Eficiência', field: 'efficiency', align: 'left' },
  { name: 'top_reasons', label: 'Ofensores', field: 'top_reasons', align: 'left' },
];

const vehColumns = [
  { name: 'vehicle_name', label: 'Equipamento', field: 'vehicle_name', align: 'left', sortable: true },
  { name: 'running_hours', label: 'Hrs Rodando', field: 'running_hours', classes: 'text-green-9 text-weight-bold' },
  { name: 'maintenance_hours', label: 'Hrs Manut.', field: 'maintenance_hours', classes: 'text-red-9' },
  { name: 'idle_hours', label: 'Hrs Ocioso', field: 'idle_hours', classes: 'text-orange-9' },
  { name: 'availability', label: 'Disponibilidade', field: 'availability' },
  { name: 'utilization', label: 'Utilização', field: 'utilization', format: (v: number) => v + '%' },
  { name: 'top_reasons', label: 'Principais Paradas', field: 'top_reasons', align: 'left' },
];

// --- KPIs COMPUTADOS ---
const kpiEmployeeEfficiency = computed(() => {
    const list = mesStore.dailyEmployeeHistory;
    if (!list.length) return 0;
    const avg = list.reduce((acc, curr) => acc + curr.efficiency, 0) / list.length;
    return Math.round(avg);
});

const kpiFleetAvailability = computed(() => {
    const list = mesStore.dailyVehicleHistory;
    if (!list.length) return 0;
    const avg = list.reduce((acc, curr) => acc + curr.availability, 0) / list.length;
    return Math.round(avg);
});

const kpiTotalProduction = computed(() => {
    const total = mesStore.dailyVehicleHistory.reduce((acc, curr) => acc + curr.running_hours, 0);
    return total.toFixed(1);
});

const kpiTotalMaintenance = computed(() => {
    const total = mesStore.dailyVehicleHistory.reduce((acc, curr) => acc + curr.maintenance_hours, 0);
    return total.toFixed(1);
});

// --- ACTIONS ---
function loadData() {
    // eslint-disable-next-line @typescript-eslint/no-floating-promises
    mesStore.fetchDailyHistory(selectedDate.value);
}

function confirmClosing() {
    $q.dialog({
        title: 'Recalcular Dia',
        message: 'Isso irá processar todos os logs do dia selecionado e atualizar o histórico. Confirmar?',
        cancel: true,
        persistent: true
    // eslint-disable-next-line @typescript-eslint/no-misused-promises
    }).onOk(async () => {
        await mesStore.forceDailyClosing(selectedDate.value);
        $q.notify({ type: 'positive', message: 'Dados recalculados com sucesso!' });
    });
}

function getColor(val: number) {
    if (val >= 90) return 'positive';
    if (val >= 70) return 'primary';
    if (val >= 50) return 'warning';
    return 'negative';
}

function getColorText(val: number) {
    if (val >= 90) return 'text-positive';
    if (val >= 70) return 'text-primary';
    return 'text-negative';
}

onMounted(() => {
    loadData();
});
</script>

<style scoped>
.border-left-primary { border-left: 5px solid #1976D2; }
.border-left-green { border-left: 5px solid #21BA45; }
.border-left-orange { border-left: 5px solid #F2C037; }
.border-left-red { border-left: 5px solid #C10015; }
</style>
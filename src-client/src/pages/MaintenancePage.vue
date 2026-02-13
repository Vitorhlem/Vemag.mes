<template>
  <q-page class="q-pa-md q-pa-lg-xl dashboard-bg">
    
    <div class="row items-center justify-between q-mb-lg q-col-gutter-y-md animate-fade-down">
      <div class="col-12 col-md-auto">
        <h1 class="text-h4 text-weight-bolder q-my-none text-gradient-trucar flex items-center gap-sm">
          <q-icon name="engineering" size="md" class="text-primary" />
          Gestão de Manutenção (PCM)
        </h1>
        <div class="text-subtitle2 text-teal-9 opacity-80 q-mt-xs">
          Controle de Ordens de Manutenção (OM), Preventivas e Paradas
        </div>
      </div>

      <div class="col-12 col-md-auto">
        <div class="d-inline-block relative-position">
          <q-btn 
            color="primary" 
            icon="add_task" 
            label="Nova Ordem de Manutenção" 
            size="md"
            unelevated 
            class="shadow-green btn-rounded"
            @click="openCreateRequestDialog"
            :disable="isLimitReached"
          />
          <q-tooltip 
            v-if="isLimitReached" 
            class="bg-negative text-body2 shadow-4" 
            anchor="bottom middle" 
            self="top middle"
            :offset="[10, 10]"
          >
            <div class="row items-center no-wrap">
                <q-icon name="lock" size="sm" class="q-mr-sm" />
                <div>
                    <div class="text-weight-bold">Limite Atingido</div>
                    <div class="text-caption">O plano Demo permite até {{ demoUsageLimitLabel }} OM/mês.</div>
                    <div class="text-caption q-mt-xs text-yellow-2 cursor-pointer" @click="showComparisonDialog = true">Clique para aumentar</div>
                </div>
            </div>
          </q-tooltip>
        </div>
      </div>
    </div>

    <div v-if="isDemo" class="q-mb-xl animate-fade">
      <q-card flat class="demo-card-gradient shadow-green">
        <q-card-section class="q-pa-md">
          <div class="row items-center justify-between">
            <div class="col-grow row items-center q-gutter-x-md">
              <q-circular-progress
                show-value
                font-size="14px"
                :value="usagePercentage"
                size="60px"
                :thickness="0.22"
                :color="usageColor"
                track-color="white-10"
                class="text-white q-my-xs"
              >
                {{ usagePercentage }}%
              </q-circular-progress>
              
              <div>
                <div class="text-subtitle2 text-uppercase text-white opacity-80">Ordens de Manutenção (Mês)</div>
                <div class="text-h4 text-white text-weight-bold">
                  {{ demoUsageCount }} <span class="text-h6 text-white opacity-70">/ {{ demoUsageLimitLabel }}</span>
                </div>
              </div>
            </div>
            
            <div class="col-auto">
               <q-btn flat dense color="white" icon="info" round>
                 <q-tooltip>Você utilizou {{ usagePercentage }}% da sua franquia de OM mensais.</q-tooltip>
               </q-btn>
            </div>
          </div>
          <q-linear-progress :value="usagePercentage / 100" class="q-mt-md rounded-borders" color="white" track-color="white-10" />
        </q-card-section>
      </q-card>
    </div>

    <div class="row q-col-gutter-md q-mb-lg">
      <div class="col-12 col-md-4">
        <q-card flat class="full-height glass-card shadow-sm border-left-orange">
          <q-card-section class="row items-center">
            <div class="col">
              <div class="text-caption text-teal-9 text-uppercase text-weight-bold">Backlog (Pendentes)</div>
              <div class="text-h4 text-weight-bold text-orange-8">{{ totalOpen }}</div>
            </div>
            <div class="col-auto">
              <q-avatar color="orange-1" text-color="orange-9" icon="assignment_late" size="lg" font-size="28px" class="glass-badge-status" />
            </div>
          </q-card-section>
        </q-card>
      </div>
      <div class="col-12 col-md-4">
        <q-card flat class="full-height glass-card shadow-sm border-left-blue">
          <q-card-section class="row items-center">
            <div class="col">
              <div class="text-caption text-teal-9 text-uppercase text-weight-bold">Em Execução</div>
              <div class="text-h4 text-weight-bold text-blue-8">{{ totalInProgress }}</div>
            </div>
            <div class="col-auto">
              <q-avatar color="blue-1" text-color="blue-9" icon="miscellaneous_services" size="lg" font-size="28px" class="glass-badge-status" />
            </div>
          </q-card-section>
        </q-card>
      </div>
      <div class="col-12 col-md-4">
        <q-card flat class="full-height glass-card shadow-sm border-left-green">
          <q-card-section class="row items-center">
            <div class="col">
              <div class="text-caption text-teal-9 text-uppercase text-weight-bold">OM Encerradas</div>
              <div class="text-h4 text-weight-bold text-green-8">{{ totalCompleted }}</div>
            </div>
            <div class="col-auto">
              <q-avatar color="green-1" text-color="green-9" icon="fact_check" size="lg" font-size="28px" class="glass-badge-status" />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <q-card flat class="glass-card shadow-sm overflow-hidden">
      <q-card-section class="q-pb-none">
        <div class="row items-center justify-between q-mb-md">
            <q-tabs 
                v-model="tab" 
                dense 
                class="text-teal-8 tab-text-color" 
                active-color="primary" 
                indicator-color="primary" 
                align="left" 
                narrow-indicator
            >
                <q-tab name="open" label="Backlog de Manutenção" icon="format_list_bulleted" />
                <q-tab name="closed" label="Histórico de Intervenções" icon="manage_history" />
            </q-tabs>

            <q-input
                outlined
                dense
                debounce="300"
                v-model="searchTerm"
                placeholder="Buscar OM, Máquina ou Técnico..."
                class="search-input glass-input"
                hide-bottom-space
            >
                <template v-slot:prepend><q-icon name="search" class="text-teal-9" /></template>
            </q-input>
        </div>
        <q-separator class="opacity-10" />
      </q-card-section>

      <q-card-section class="q-pa-none">
        <q-tab-panels v-model="tab" animated class="bg-transparent">
          
          <q-tab-panel name="open" class="q-pa-md">
            <div v-if="maintenanceStore.isLoading" class="row q-col-gutter-md">
              <div v-for="n in 4" :key="n" class="col-xs-12 col-sm-6 col-md-4 col-lg-3">
                  <q-card flat class="glass-card"><q-skeleton height="180px" square class="bg-teal-1 opacity-20" /></q-card>
              </div>
            </div>
            
            <div v-else-if="openRequests.length > 0" class="row q-col-gutter-md">
              <div v-for="req in openRequests" :key="req.id" class="col-xs-12 col-sm-6 col-md-4 col-lg-3">
                <MaintenanceRequestCard :request="req" @click="openDetailsDialog(req)" />
              </div>
            </div>
            
            <div v-else class="text-center q-pa-xl">
              <div class="bg-teal-1 q-pa-md rounded-borders inline-block q-mb-md glass-badge">
                  <q-icon name="check_circle" size="4em" color="teal-5" />
              </div>
              <div class="text-h6 text-teal-10">Operação Normal</div>
              <p class="text-teal-9 opacity-70">Nenhuma ordem de Manutenção pendente no momento.</p>
            </div>
          </q-tab-panel>

          <q-tab-panel name="closed" class="q-pa-none">
            <div v-if="closedRequests.length === 0 && !maintenanceStore.isLoading" class="text-center q-pa-xl">
              <q-icon name="history" size="4em" color="teal-2" />
              <p class="q-mt-md text-teal-9 opacity-50">Nenhum histórico de manutenção encontrado.</p>
            </div>
            
            <q-list v-else separator class="glass-table">
              <q-item 
                v-for="req in closedRequests" 
                :key="req.id" 
                clickable 
                v-ripple 
                @click="openDetailsDialog(req)"
                class="q-py-md hover-bg-teal-faded"
              >
                <q-item-section avatar>
                    <q-avatar :color="getStatusColor(req.status)" text-color="white" icon="build" size="md" font-size="18px" class="shadow-1" />
                </q-item-section>
                
                <q-item-section>
                  <q-item-label class="text-weight-bold text-teal-10">
                      <q-icon name="precision_manufacturing" size="xs" class="q-mr-xs text-teal-7"/>
                      {{ req.vehicle?.brand }} {{ req.vehicle?.model }}
                  </q-item-label>
                  <q-item-label caption>
                      <span class="text-teal-9 text-weight-medium">Tag: {{ req.vehicle?.license_plate || req.vehicle?.identifier || 'N/A' }}</span> 
                      &bull; <span class="text-primary text-weight-bold">{{ req.category || 'Geral' }}</span>
                      &bull; <span class="text-grey-7">{{ req.problem_description }}</span>
                  </q-item-label>
                </q-item-section>
                
                <q-item-section side>
                  <div class="column items-end">
                      <q-badge :color="getStatusColor(req.status)" :label="translateStatus(req.status)" class="q-mb-xs glass-badge-status" />
                      <span class="text-caption text-teal-8 font-mono" v-if="req.created_at">
                          {{ new Date(req.created_at).toLocaleDateString() }}
                      </span>
                  </div>
                </q-item-section>
              </q-item>
            </q-list>
          </q-tab-panel>
        </q-tab-panels>
      </q-card-section>
    </q-card>

    <MaintenanceDetailsDialog 
      v-model="isDetailsDialogOpen" 
      :request="selectedRequest" 
    />
    
    <CreateRequestDialog 
      v-model="isCreateDialogOpen" 
      @request-created="refreshData" 
    />

    <q-dialog v-model="showComparisonDialog">
      <q-card class="glass-card overflow-hidden" style="width: 750px; max-width: 95vw;">
        <q-card-section class="text-white q-py-lg text-center relative-position overflow-hidden" style="background: linear-gradient(135deg, #00665e, #70c0b0);">
          <div class="absolute-full bg-white opacity-10" style="transform: skewY(-5deg) scale(1.5);"></div>
          <q-icon name="domain" size="4em" class="q-mb-sm" />
          <div class="text-h4 text-weight-bold relative-position">Gestão de Ativos Profissional</div>
          <div class="text-subtitle1 text-teal-1 relative-position">Eleve o nível do seu PCM com o Plano PRO</div>
        </q-card-section>

        <q-card-section class="q-pa-none">
          <q-markup-table flat class="bg-transparent glass-table">
            <thead>
              <tr class="bg-teal-gradient-faded text-teal-9">
                <th class="text-left q-pa-md text-uppercase text-caption text-weight-bold">Funcionalidade</th>
                <th class="text-center text-weight-bold q-pa-md bg-orange-1 text-orange-9 border-left">Plano Demo</th>
                <th class="text-center text-weight-bold q-pa-md text-primary bg-teal-1">Plano PRO</th>
              </tr>
            </thead>
            <tbody class="text-teal-10">
              <tr>
                <td class="text-weight-medium q-pa-md"><q-icon name="build" color="teal-4" size="xs" /> Ordens de Manutenção (Mês)</td>
                <td class="text-center bg-orange-1 text-orange-10">{{ demoUsageLimitLabel }}</td>
                <td class="text-center text-primary text-weight-bold bg-teal-1"><q-icon name="check_circle" /> Ilimitado</td>
              </tr>
              <tr>
                <td class="text-weight-medium q-pa-md"><q-icon name="update" color="teal-4" size="xs" /> Planejamento (PMP)</td>
                <td class="text-center bg-orange-1 text-orange-10">Manual</td>
                <td class="text-center text-primary text-weight-bold bg-teal-1"><q-icon name="check_circle" /> Automatizado</td>
              </tr>
              <tr>
                <td class="text-weight-medium q-pa-md"><q-icon name="inventory_2" color="teal-4" size="xs" /> Gestão de Almoxarifado</td>
                <td class="text-center bg-orange-1 text-orange-10">Básico</td>
                <td class="text-center text-primary text-weight-bold bg-teal-1">Integrado à OM</td>
              </tr>
            </tbody>
          </q-markup-table>
        </q-card-section>

        <q-card-actions align="center" class="q-pa-lg bg-teal-gradient-faded-full">
          <div class="column items-center full-width q-gutter-y-md">
            <div class="text-h6 text-weight-bold text-teal-10">Quer reduzir o tempo de máquina parada?</div>
            <q-btn color="positive" label="Falar com Engenheiro de Vendas" size="lg" unelevated icon="whatsapp" class="full-width shadow-green" />
            <q-btn flat color="teal-8" label="Continuar no Demo" v-close-popup class="text-teal-9" />
          </div>
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { setCssVar } from 'quasar';
import { useMaintenanceStore } from 'stores/maintenance-store';
import { useAuthStore } from 'stores/auth-store';
import { useDemoStore } from 'stores/demo-store';
import { MaintenanceStatus, type MaintenanceRequest } from 'src/models/maintenance-models';
import CreateRequestDialog from 'components/maintenance/CreateRequestDialog.vue';
import MaintenanceDetailsDialog from 'components/maintenance/MaintenanceDetailsDialog.vue';
import MaintenanceRequestCard from 'components/maintenance/MaintenanceRequestCard.vue';

const maintenanceStore = useMaintenanceStore();
const authStore = useAuthStore();
const demoStore = useDemoStore();

const isDemo = computed(() => authStore.user?.role === 'cliente_demo');
const showComparisonDialog = ref(false);

const demoUsageCount = computed(() => demoStore.stats?.maintenance_count ?? 0);
const demoUsageLimit = computed(() => 5);
const demoUsageLimitLabel = computed(() => demoUsageLimit.value.toString());

const isLimitReached = computed(() => {
  if (!isDemo.value) return false;
  return demoUsageCount.value >= demoUsageLimit.value;
});

const usagePercentage = computed(() => {
  if (!isDemo.value || demoUsageLimit.value <= 0) return 0;
  const pct = Math.round((demoUsageCount.value / demoUsageLimit.value) * 100);
  return Math.min(pct, 100);
});

const usageColor = computed(() => {
  if (usagePercentage.value >= 100) return 'red-4';
  if (usagePercentage.value >= 80) return 'orange-4';
  return 'white';
});

const searchTerm = ref('');
const tab = ref('open');
const isCreateDialogOpen = ref(false);
const isDetailsDialogOpen = ref(false);
const selectedRequest = ref<MaintenanceRequest | null>(null);

const openRequests = computed(() => maintenanceStore.maintenances.filter(r => r.status !== MaintenanceStatus.CONCLUIDA && r.status !== MaintenanceStatus.REJEITADA));
const closedRequests = computed(() => maintenanceStore.maintenances.filter(r => r.status === MaintenanceStatus.CONCLUIDA || r.status === MaintenanceStatus.REJEITADA));

const totalOpen = computed(() => openRequests.value.length);
const totalInProgress = computed(() => maintenanceStore.maintenances.filter(r => r.status === MaintenanceStatus.EM_ANDAMENTO).length);
const totalCompleted = computed(() => closedRequests.value.length);

function openCreateRequestDialog() {
  if (isLimitReached.value) {
      showComparisonDialog.value = true;
      return;
  }
  isCreateDialogOpen.value = true;
}

function openDetailsDialog(request: MaintenanceRequest) {
  selectedRequest.value = request;
  isDetailsDialogOpen.value = true;
}

function refreshData() {
    isCreateDialogOpen.value = false;
    void maintenanceStore.fetchMaintenanceRequests();
    if (authStore.isDemo) {
        void demoStore.fetchDemoStats(true);
    }
}

function getStatusColor(status: MaintenanceStatus): string {
  const colorMap: Record<MaintenanceStatus, string> = {
    [MaintenanceStatus.PENDENTE]: 'orange',
    [MaintenanceStatus.APROVADA]: 'teal-9',
    [MaintenanceStatus.REJEITADA]: 'negative',
    [MaintenanceStatus.EM_ANDAMENTO]: 'info',
    [MaintenanceStatus.CONCLUIDA]: 'positive',
  };
  return colorMap[status] || 'grey';
}

function translateStatus(status: MaintenanceStatus): string {
    const map: Record<MaintenanceStatus, string> = {
        [MaintenanceStatus.PENDENTE]: 'Pendente',
        [MaintenanceStatus.APROVADA]: 'Aprovada',
        [MaintenanceStatus.REJEITADA]: 'Cancelada',
        [MaintenanceStatus.EM_ANDAMENTO]: 'Em Execução',
        [MaintenanceStatus.CONCLUIDA]: 'Encerrada'
    };
    return map[status] || status;
}

watch(searchTerm, (newValue) => {
  void maintenanceStore.fetchMaintenanceRequests({ search: newValue });
});

onMounted(() => {
  setCssVar('primary', '#00665e');
  void maintenanceStore.fetchMaintenanceRequests();
  if (authStore.isDemo) {
      void demoStore.fetchDemoStats(true);
  }
});
</script>

<style scoped lang="scss">
/* Estilização Trucar PCM */
.dashboard-bg { 
  background-color: #f0f4f4;
  min-height: 100vh;
  transition: background-color 0.3s;
}

.text-gradient-trucar {
  background: linear-gradient(to right, #00665e, #70c0b0);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Glassmorphism Puro */
.glass-card {
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid rgba(18, 140, 126, 0.1);
  border-radius: 12px;
}

.glass-input {
  background: rgba(255, 255, 255, 0.5) !important;
  backdrop-filter: blur(8px);
  border-radius: 4px;
}

.glass-badge {
  background: rgba(18, 140, 126, 0.1) !important;
  color: #00665e !important;
  border: 1px solid rgba(18, 140, 126, 0.2);
}

.glass-badge-status {
  backdrop-filter: blur(4px);
  border: 1px solid rgba(0,0,0,0.05);
}

.glass-table {
  background: transparent !important;
  :deep(.q-item) { border-bottom: 1px solid rgba(18, 140, 126, 0.05); }
}

/* Demo Card com Gradiente Trucar */
.demo-card-gradient {
  background: linear-gradient(135deg, #00665e 0%, #0a4f47 100%);
  border: none;
  border-radius: 16px;
}

.border-left-orange { border-left: 6px solid #fb8c00; }
.border-left-blue { border-left: 6px solid #1976d2; }
.border-left-green { border-left: 6px solid #43a047; }

.search-input {
  width: 300px;
  @media (max-width: 599px) { width: 100%; }
}

.white-10 { background: rgba(255, 255, 255, 0.1) !important; }
.shadow-green { box-shadow: 0 4px 14px 0 rgba(18, 140, 126, 0.2); }
.btn-rounded { border-radius: 8px; }
.font-mono { font-family: 'JetBrains Mono', monospace; }

.hover-bg-teal-faded:hover {
  background-color: rgba(112, 192, 176, 0.1);
  transition: background-color 0.2s;
}

.bg-teal-gradient-faded { background: linear-gradient(135deg, rgba(112, 192, 176, 0.1) 0%, transparent 100%); }
.bg-teal-gradient-faded-full { background: linear-gradient(90deg, rgba(112, 192, 176, 0.05) 0%, rgba(255,255,255,0.4) 100%); }

.animate-fade-down { animation: fadeDown 0.8s ease-out forwards; }
.animate-fade { animation: fadeIn 0.4s ease-in-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }

/* =========================================
   DARK MODE OVERRIDES (DARK FOREST)
   ========================================= */
.body--dark {
  .dashboard-bg { 
    background-color: #05100e !important; 
  }

  /* Glass Components */
  .glass-card {
    background: rgba(5, 20, 18, 0.7) !important;
    border-color: rgba(18, 140, 126, 0.2);
    color: #e0f2f1;
  }

  .glass-input {
    background: rgba(18, 140, 126, 0.1) !important;
    :deep(.q-field__native), :deep(.q-field__label) {
        color: #b2dfdb !important;
    }
    :deep(.q-icon) {
        color: #80cbc4 !important;
    }
  }

  /* Text Colors */
  .text-teal-9 { color: #80cbc4 !important; }
  .text-teal-10 { color: #ffffff !important; }
  .text-teal-8 { color: #b2dfdb !important; }
  .text-grey-7 { color: #b0bec5 !important; }
  .text-grey-6 { color: #90a4ae !important; }

  /* KPI Cards Text Adjustments for Dark Mode */
  .text-orange-8 { color: #ffcc80 !important; } /* Lighter Orange */
  .text-blue-8 { color: #90caf9 !important; }   /* Lighter Blue */
  .text-green-8 { color: #a5d6a7 !important; }  /* Lighter Green */

  /* KPI Icon Backgrounds (Darker tint) */
  .bg-orange-1 { background-color: rgba(251, 140, 0, 0.15) !important; }
  .bg-blue-1 { background-color: rgba(25, 118, 210, 0.15) !important; }
  .bg-green-1 { background-color: rgba(67, 160, 71, 0.15) !important; }
  .bg-teal-1 { background-color: rgba(18, 140, 126, 0.15) !important; }

  /* Tab Text Color */
  .tab-text-color {
    color: #80cbc4 !important;
  }

  /* List Hover */
  .hover-bg-teal-faded:hover {
    background-color: rgba(18, 140, 126, 0.15) !important;
  }

  /* Table Comparison in Dialog */
  .glass-table {
    :deep(thead tr) { background: rgba(18, 140, 126, 0.2); }
    :deep(tbody tr td) { color: #e0f2f1; }
  }
  .bg-orange-1 { background-color: rgba(255, 152, 0, 0.1) !important; }
  .text-orange-9, .text-orange-10 { color: #ffb74d !important; }
  
  /* Footer Gradient */
  .bg-teal-gradient-faded-full {
    background: linear-gradient(90deg, rgba(18, 140, 126, 0.1) 0%, rgba(0,0,0,0.2) 100%);
  }
}
</style>
<template>
  <q-page class="dashboard-bg q-pa-md q-pa-lg-xl">
    
    <div class="row items-center justify-between q-mb-xl animate-fade-down">
      <div class="col-12 col-md-auto">
        <div class="row items-center q-gutter-x-sm">
          <q-icon name="factory" size="2em" class="text-primary opacity-80" />
          <div>
            <div class="text-caption text-uppercase text-teal-9 text-weight-bold letter-spacing-2">
              Visão Geral da Planta
            </div>
            <h1 class="text-h4 text-weight-900 q-my-none text-gradient">
              Painel de Controle
            </h1>
          </div>
        </div>
        <div class="text-subtitle1 text-grey-7 q-mt-sm flex items-center">
          <span>Bem-vindo de volta, <strong>{{ authStore.user?.full_name?.split(' ')[0] }}</strong>.</span>
          <q-badge color="teal-1" text-color="teal-9" class="q-ml-md q-px-sm glass-badge">
            <span class="dot-indicator bg-teal-5 q-mr-xs"></span> Sistema Online
          </q-badge>
        </div>
      </div>

      <div class="col-12 col-md-auto q-mt-md q-md-mt-none">
        <div class="row q-gutter-sm">
           <q-btn 
             flat
             color="teal-10" 
             icon="refresh" 
             label="Atualizar Dados" 
             class="btn-hover-effect glass-btn text-teal-9"
             @click="() => refreshData()" 
             :loading="dashboardStore.isLoading || vehicleStore.isLoading"
           />
           <q-btn-dropdown 
             color="primary" 
             icon="add" 
             label="Ações Rápidas" 
             unelevated 
             class="shadow-4 btn-rounded q-px-lg shadow-green"
             content-class="glass-menu shadow-10"
           >
            <q-list class="q-py-md" style="min-width: 240px">
              <div class="text-caption q-px-md q-mb-sm text-teal-9 text-uppercase text-weight-bold">Cadastro</div>
              <q-item clickable v-close-popup @click="() => router.push('/vehicles')" class="item-hover">
                <q-item-section avatar><div class="icon-box bg-teal-1 text-teal-9"><q-icon name="precision_manufacturing" size="20px"/></div></q-item-section>
                <q-item-section>
                   <q-item-label class="text-weight-bold text-teal-10">Nova Máquina</q-item-label>
                   <q-item-label caption class="text-grey-7">Cadastrar ativo</q-item-label>
                </q-item-section>
              </q-item>
              <q-separator spaced class="q-mx-md opacity-10" />
              <div class="text-caption q-px-md q-mb-sm text-teal-9 text-uppercase text-weight-bold">Operação</div>
              <q-item clickable v-close-popup @click="() => router.push('/factory/kiosk')" class="item-hover">
                <q-item-section avatar><div class="icon-box bg-cyan-1 text-cyan-9"><q-icon name="monitor" size="20px"/></div></q-item-section>
                <q-item-section>
                   <q-item-label class="text-weight-bold text-teal-10">Modo Kiosk</q-item-label>
                   <q-item-label caption class="text-grey-7">Tela do operador</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>
      </div>
    </div>

    <div v-if="dashboardStore.isLoading && !realTimeStats" class="row q-col-gutter-md animate-pulse">
       <div class="col-12 col-md-2" v-for="n in 6" :key="n"><q-skeleton type="rect" height="100px" class="rounded-xl" /></div>
    </div>

    <div v-else class="fade-in-up">
      <div class="row q-col-gutter-md q-mb-lg">
        <div class="col-12 col-sm-6 col-md-4 col-lg-2">
          <StatCard label="Ativos Totais" :value="realTimeStats.total" icon="domain" color="blue-grey-10" to="/vehicles" class="full-height glass-card shadow-card hover-scale" />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-2">
          <StatCard label="Em Produção" :value="realTimeStats.running" icon="precision_manufacturing" color="positive" class="full-height glass-card shadow-card hover-scale" />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-2">
          <StatCard label="Em Setup" :value="realTimeStats.setup" icon="settings_suggest" color="purple-9" class="full-height glass-card shadow-card hover-scale" />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-2">
          <StatCard label="Pausadas" :value="realTimeStats.stopped" icon="pause_circle" color="orange-9" class="full-height glass-card shadow-card hover-scale" />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-2">
          <StatCard label="Manutenção" :value="realTimeStats.maintenance" icon="engineering" color="red-10" class="full-height glass-card shadow-card hover-scale" />
        </div>
        <div class="col-12 col-sm-6 col-md-4 col-lg-2">
          <StatCard label="Disponíveis" :value="realTimeStats.idle" icon="check_circle" color="teal-7" class="full-height glass-card shadow-card hover-scale" />
        </div>
      </div>

      <div class="text-h6 text-weight-bold text-teal-10 q-mb-md flex items-center">
        <q-icon name="insights" class="q-mr-sm text-teal-6" /> Performance da Planta (Média Real)
      </div>
      
      <div class="row q-col-gutter-md q-mb-xl">
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Disponibilidade" 
             :value="realTimeStats.availabilityRate"
             unit="%" 
             icon="bolt" 
             color="cyan-8" 
             class="metric-clean glass-card"
             :formatter="(v: number) => `${v.toFixed(1)}%`" 
           />
         </div>
         
         <div class="col-12 col-sm-6 col-lg-3">
           <MetricCard 
             title="Taxa de Utilização" 
             :value="realTimeStats.utilizationRate" 
             unit="%" 
             icon="pie_chart" 
             color="teal" 
             class="metric-clean glass-card"
             :formatter="(v: number) => `${v.toFixed(1)}%`" 
           />
         </div>
      </div>

      <div class="row q-col-gutter-lg">
        
        <div class="col-12 col-lg-8 column q-gutter-y-lg">
          
          <div class="dashboard-card glass-card shadow-1 q-pa-none overflow-hidden relative-position">
             <div class="absolute-full flex flex-center z-top" style="background: rgba(255,255,255,0.7); backdrop-filter: blur(2px);">
                <q-badge color="grey-9" padding="md" class="text-h6 shadow-2">
                   <q-icon name="pause_circle" class="q-mr-sm" /> MÓDULO INATIVO TEMPORARIAMENTE
                </q-badge>
             </div>
             <div class="card-header q-pa-md border-bottom-light">
                <div class="text-h6 text-weight-bold text-teal-10">Custos Industriais</div>
                <div class="text-caption text-grey-6">Análise de gastos por categoria</div>
             </div>
             <div class="q-pa-md opacity-20" style="height: 350px;"></div>
          </div>

          <div class="dashboard-card glass-card shadow-1 q-pa-none overflow-hidden relative-position">
             <div class="absolute-full flex flex-center z-top" style="background: rgba(255,255,255,0.7); backdrop-filter: blur(2px);">
                <q-badge color="grey-9" padding="md" class="text-h6 shadow-2">
                   <q-icon name="pause_circle" class="q-mr-sm" /> MÓDULO INATIVO TEMPORARIAMENTE
                </q-badge>
             </div>
             <div class="card-header q-pa-md border-bottom-light bg-teal-gradient-faded">
                <div class="text-subtitle1 text-weight-bold text-teal-10">Agenda de Manutenção</div>
                <div class="text-caption text-grey-6">Próximas intervenções programadas</div>
             </div>
             <div class="q-pa-md opacity-20" style="height: 200px;"></div>
          </div>
        </div>

        <div class="col-12 col-lg-4 column">
          <div class="dashboard-card glass-card shadow-1 overflow-hidden full-height">
             <div class="q-pa-md border-bottom-light">
                <div class="text-subtitle1 text-weight-bold text-teal-10">Utilização dos ativos</div>
                <div class="text-caption text-grey-6">Distribuição atual dos ativos</div>
             </div>
             <div class="q-pa-md flex flex-center" style="min-height: 400px">
                <ApexChart 
                    v-if="realTimeStats.total > 0" 
                    type="donut" 
                    height="350" 
                    :options="fleetStatusChart.options" 
                    :series="fleetStatusChart.series" 
                />
                <div v-else class="text-center text-teal-5">
                   <q-icon name="pie_chart" size="4em" color="teal-1" />
                   <div class="text-caption q-mt-sm">Carregando dados...</div>
                </div>
             </div>
          </div>
        </div>

      </div>
    </div>
    
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { setCssVar, useQuasar } from 'quasar'; // Adicionado useQuasar
import { useDashboardStore } from 'stores/dashboard-store';
import { useAuthStore } from 'stores/auth-store';
import { useVehicleStore } from 'stores/vehicle-store'; 
import ApexChart from 'vue3-apexcharts';
import StatCard from 'components/StatCard.vue';
import MetricCard from 'components/MetricCard.vue'; 





const dashboardStore = useDashboardStore();
const authStore = useAuthStore();
const vehicleStore = useVehicleStore(); 
const router = useRouter();
const $q = useQuasar(); // Para detectar modo escuro nos gráficos



// --- CORES REATIVAS PARA GRÁFICOS (DARK MODE) ---
const chartTextColor = computed(() => $q.dark.isActive ? '#cbd5e1' : '#64748b');

const realTimeStats = computed(() => {
  const allMachines = vehicleStore.vehicles;
  // Normaliza o status para evitar erros de maiúsculo/minúsculo ou espaços
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const getStatus = (m: any) => String(m.status || '').trim().toUpperCase();

  const total = allMachines.length;
  
  // Contagem por Categoria
  const running = allMachines.filter(m => 
    ['EM USO', 'PRODUÇÃO AUTÔNOMA', 'EM OPERAÇÃO', 'RUNNING'].includes(getStatus(m))
  ).length;
  
  const setup = allMachines.filter(m => getStatus(m) === 'SETUP').length;
  const maintenance = allMachines.filter(m => 
    ['EM MANUTENÇÃO', 'MANUTENÇÃO', 'MAINTENANCE'].includes(getStatus(m))
  ).length;
  const stopped = allMachines.filter(m => 
    ['PARADA', 'PAUSADA', 'STOPPED'].includes(getStatus(m))
  ).length;
  const idle = allMachines.filter(m => 
    ['DISPONÍVEL', 'OCIOSIDADE', 'AVAILABLE', 'IDLE'].includes(getStatus(m))
  ).length;

  // DISPONIBILIDADE: (Produzindo + Disponível) / (Total - Setup)
  // Máquinas em Setup são "paradas planejadas", por isso saem da conta
  const baseAvailable = total - setup;
  const currentAvailable = running + idle;
  const availabilityRate = baseAvailable > 0 ? (currentAvailable / baseAvailable) * 100 : 0;

  // TAXA DE UTILIZAÇÃO: (Somente o que está produzindo agora) / Total
  const utilizationRate = total > 0 ? (running / total) * 100 : 0;

  return { 
    total, running, setup, maintenance, stopped, idle, 
    utilizationRate, availabilityRate 
  };
});



const fleetStatusChart = computed(() => {
    const s = realTimeStats.value;
    // A ORDEM AQUI DEVE SER A MESMA DAS LABELS ABAIXO
    const series = [s.running, s.setup, s.stopped, s.maintenance, s.idle];
    
    return {
        series,
        options: {
            labels: ['Produzindo', 'Em Setup', 'Pausada', 'Manutenção', 'Disponível'],
            colors: ['#128c7e', '#9c27b0', '#ff9800', '#ef4444', '#78909c'], 
            chart: { type: 'donut', fontFamily: 'Inter, sans-serif', background: 'transparent' },
            theme: { mode: $q.dark.isActive ? 'dark' : 'light' },
            legend: { position: 'bottom', labels: { colors: chartTextColor.value } },
            dataLabels: { enabled: false },
            plotOptions: { 
                donut: { 
                    size: '75%', 
                    labels: { 
                        show: true, 
                        total: { 
                            show: true, 
                            label: 'Ativos', 
                            color: $q.dark.isActive ? '#ffffff' : '#128c7e',
                            formatter: () => s.total 
                        } 
                    } 
                } 
            },
            stroke: { show: true, width: 2, colors: [$q.dark.isActive ? '#1e1e1e' : '#fff'] }
        }
    };
});
async function refreshData() {
    await Promise.all([
        dashboardStore.fetchManagerDashboard('last_30_days'),
        vehicleStore.fetchAllVehicles({ page: 1, rowsPerPage: 100 })
    ]);
}


onMounted(() => {
    setCssVar('primary', '#128c7e');
    if (authStore.isManager) {
        void refreshData();
    }
});
</script>

<style scoped lang="scss">
// Variáveis Trucar
$trucar-green: #128c7e;
$trucar-mint: #70c0b0;
$shadow-green: 0 4px 14px 0 rgba(18, 140, 126, 0.39);

.dashboard-bg { 
  background-color: #f0f4f4; // Fundo padrão claro
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

/* --- Glassmorphism --- */
.glass-card {
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid rgba(18, 140, 126, 0.1);
  transition: background-color 0.3s, border-color 0.3s;
}

.glass-badge {
  background: rgba(18, 140, 126, 0.1) !important;
  backdrop-filter: blur(4px);
}

.glass-btn {
  background: rgba(18, 140, 126, 0.05);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(18, 140, 126, 0.1);
}

.glass-menu {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(10px);
}

/* --- Tipografia --- */
.text-weight-900 { font-weight: 900; }
.text-gradient {
  background: linear-gradient(to right, $trucar-green, $trucar-mint);
  -webkit-background-clip: text;
  background-clip: text; /* Correção para compatibilidade */
  -webkit-text-fill-color: transparent;
}
.letter-spacing-2 { letter-spacing: 2px; }

/* --- Cartões e Sombras --- */
.dashboard-card { 
  border-radius: 16px; 
}
.shadow-card {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
.shadow-green { box-shadow: $shadow-green; }

/* --- Bordas e Separadores --- */
.border-bottom-light { border-bottom: 1px solid rgba(18, 140, 126, 0.1); }
.border-top-critical { border-top: 4px solid var(--q-negative); }

/* --- Efeitos de Hover --- */
.hover-scale { 
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  &:hover { 
    transform: translateY(-4px); 
    box-shadow: 0 10px 25px -5px rgba(18, 140, 126, 0.2);
    border-color: $trucar-green;
  } 
}
.btn-hover-effect:hover { background: rgba(18, 140, 126, 0.1); color: $trucar-green; }
.item-hover:hover { 
  background-color: rgba(112, 192, 176, 0.1); 
  .text-weight-bold { color: $trucar-green; } 
}

/* --- Elementos Decorativos --- */
.icon-box {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
}
.icon-box-sm {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
}
.dot-indicator {
  width: 8px; height: 8px; border-radius: 50%; display: inline-block;
}
.rounded-xl { border-radius: 16px; }
.rounded-circle { border-radius: 50%; }
.btn-rounded { border-radius: 8px; }

/* --- Backgrounds Específicos --- */
.bg-teal-gradient-faded {
  background: linear-gradient(90deg, rgba(112, 192, 176, 0.1) 0%, transparent 100%);
}
.hover\:bg-teal-5-faded:hover { background-color: rgba(112, 192, 176, 0.1); }
.hover\:bg-red-1-faded:hover { background-color: rgba(239, 68, 68, 0.05); }

/* --- Animations --- */
.fade-in-up { animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.animate-pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
.animate-fade-down { animation: fadeDown 0.8s ease-out forwards; }

@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }

.empty-state-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 20px;
  min-height: 250px;
  width: 100%;
}
.empty-state-list .q-icon {
  margin-left: auto;
  margin-right: auto;
  display: block;
}

.empty-state-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    height: 100%;
    min-height: 300px;
}

/* =========================================
   DARK MODE OVERRIDES (DARK FOREST)
   ========================================= */
.body--dark {
  // Fundo Floresta Negra
  .dashboard-bg { 
    background-color: #05100e !important; 
  }

  // Cards Escuros Translúcidos
  .glass-card {
    background: rgba(5, 20, 18, 0.7) !important;
    border-color: rgba(18, 140, 126, 0.2);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
  }
  
  .glass-menu {
    background: rgba(10, 25, 23, 0.95) !important;
    border: 1px solid rgba(18, 140, 126, 0.3);
  }

  .alert-header-bg {
    background: rgba(255, 255, 255, 0.05) !important;
  }

  // Textos
  .text-teal-9 { color: #80cbc4 !important; }  // Teal claro
  .text-teal-10 { color: #e0f2f1 !important; } // Quase branco
  .text-grey-7 { color: #94a3b8 !important; }  // Cinza médio
  .text-grey-6 { color: #64748b !important; }
  .text-grey-9 { color: #e2e8f0 !important; } // Títulos de alerta

  // Ícones e Box
  .icon-box, .icon-box-sm {
    background-color: rgba(18, 140, 126, 0.15) !important;
    .q-icon { color: #4db6ac !important; }
  }
  // Cores específicas dos boxes de ação rápida
  .bg-cyan-1 { background-color: rgba(34, 211, 238, 0.1) !important; }
  .text-cyan-9 { color: #22d3ee !important; }
  .bg-orange-1 { background-color: rgba(251, 146, 60, 0.1) !important; }
  .text-orange-9 { color: #fb923c !important; }

  // Hover em Listas
  .item-hover:hover {
    background-color: rgba(18, 140, 126, 0.15);
  }
  .hover\:bg-teal-5-faded:hover {
     background-color: rgba(18, 140, 126, 0.15) !important;
  }
  .hover\:bg-red-1-faded:hover {
     background-color: rgba(239, 68, 68, 0.1) !important;
  }

  // Badges e Elementos de UI
  .glass-badge {
    background: rgba(18, 140, 126, 0.2) !important;
    color: #80cbc4 !important;
  }
  .bg-teal-1 { background-color: rgba(18, 140, 126, 0.15) !important; }
  
  // Separadores
  .border-bottom-light { border-bottom-color: rgba(255, 255, 255, 0.05); }
}
</style>
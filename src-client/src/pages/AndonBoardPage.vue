<template>
  <q-layout view="hHh lpR fFf" class="bg-black text-white font-inter overflow-hidden">
    
    <q-header class="bg-transparent q-py-md q-px-lg">
      <div class="row items-center justify-between">
        <div class="row items-center">
           <q-icon name="monitor_heart" color="red-5" size="32px" class="q-mr-md" :class="{'animate-pulse': hasCriticalCalls}" />
           <div class="text-h5 text-weight-bold tracking-widest text-grey-5">ANDON LIVE</div>
        </div>
        <div class="text-h4 text-weight-bold font-mono">{{ currentTime }}</div>
      </div>
    </q-header>

    <q-page-container>
      <q-page class="q-pa-lg">
        
        <div v-if="isLoading && calls.length === 0" class="absolute-full flex flex-center">
           <q-spinner-dots size="4em" color="grey-7" />
        </div>

        <div v-else class="row q-col-gutter-lg">
          
          <div 
            v-for="call in sortedCalls" 
            :key="call.id" 
            class="col-12 col-md-6 col-lg-4 col-xl-3"
          >
            <q-card 
              class="andon-tile column justify-between no-shadow relative-position fade-enter-active"
              :class="getTileColor(call)"
            >
              <q-card-section class="col column justify-center items-center text-center q-py-xl">
                 <div class="text-h1 text-weight-bolder font-mono lh-none" :class="{'blink-slow': isCritical(call)}">
                    {{ getElapsedTime(call) }}
                 </div>
                 <div class="text-subtitle2 text-uppercase opacity-60 q-mb-md">TEMPO DECORRIDO</div>

                 <div class="text-h4 text-weight-bolder leading-tight line-clamp-2 q-px-md">
                    {{ call.machine_name }}
                 </div>
                 <div class="text-caption opacity-60 q-mt-sm">{{ call.machine_sector }}</div>
              </q-card-section>

              <q-card-section class="row items-center justify-between bg-black-10 q-py-sm text-subtitle1">
                 <div class="row items-center">
                    <q-icon :name="getSectorIcon(call.sector)" class="q-mr-sm" size="20px" />
                    <span class="text-weight-bold">{{ call.sector }}</span>
                 </div>
                 
                 <div v-if="call.status === 'IN_PROGRESS'" class="row items-center text-caption bg-white text-dark q-px-sm rounded-borders">
                    <q-icon name="engineering" class="q-mr-xs" /> {{ call.accepted_by_name || 'Técnico' }}
                 </div>
                 <div v-else class="text-caption opacity-80 uppercase font-mono">
                    {{ call.reason }}
                 </div>
              </q-card-section>
            </q-card>
          </div>

          <div v-if="!isLoading && calls.length === 0" class="absolute-full flex flex-center column">
             <div class="text-h1 text-grey-9 text-weight-bolder">ALL CLEAR</div>
             <div class="text-h5 text-grey-8 q-mt-md">Produção Normal</div>
          </div>

        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { date } from 'quasar';
import { AndonService, AndonStatus } from 'src/services/andon-service';
import type { AndonCall } from 'src/services/andon-service';


// --- State ---
const calls = ref<AndonCall[]>([]);
const now = ref(new Date());
const isLoading = ref(true);
let updateTimer: ReturnType<typeof setInterval>;
let clockTimer: ReturnType<typeof setInterval>;

// --- Computed ---
const currentTime = computed(() => date.formatDate(now.value, 'HH:mm'));

const sortedCalls = computed(() => {
    return [...calls.value].sort((a, b) => new Date(a.opened_at).getTime() - new Date(b.opened_at).getTime());
});

const hasCriticalCalls = computed(() => calls.value.some(c => isCritical(c)));

// --- API Logic ---
async function fetchCalls() {
    try {
        calls.value = await AndonService.getActiveCalls();
    } catch (e) {
        console.error("Erro ao buscar Andon", e);
        // Não mostrar notificação de erro para não poluir a TV se a rede piscar
    } finally {
        isLoading.value = false;
    }
}

// --- Helpers de Tempo e Estilo ---
function getMinutesElapsed(call: AndonCall): number {
    const start = new Date(call.opened_at).getTime();
    const current = now.value.getTime();
    return Math.max(0, (current - start) / 1000 / 60);
}

function getElapsedTime(call: AndonCall): string {
    const diff = Math.max(0, Math.floor((now.value.getTime() - new Date(call.opened_at).getTime()) / 1000));
    const h = Math.floor(diff / 3600);
    const m = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
    // Se passar de 1 hora, mostra H:MM, senão mostra MM:SS para dar senso de urgência
    if (h > 0) return `${h}:${m}`;
    
    const s = (diff % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
}

function isCritical(call: AndonCall): boolean {
    return call.status === AndonStatus.OPEN && getMinutesElapsed(call) > 10;
}

function getTileColor(call: AndonCall) {
    if (call.status === AndonStatus.IN_PROGRESS) return 'bg-blue-9';
    
    const mins = getMinutesElapsed(call);
    if (mins > 10) return 'bg-deep-purple-10'; // Crítico
    if (mins > 5) return 'bg-red-9'; // Atenção
    return 'bg-orange-9'; // Novo
}

function getSectorIcon(sector: string) {
    const map: Record<string, string> = {
        'Manutenção': 'build', 'Qualidade': 'verified',
        'Logística': 'forklift', 'Gerente': 'priority_high',
        'Segurança': 'health_and_safety', 'PCP': 'schedule'
    };
    return map[sector] || 'notifications';
}

// --- Ciclo de Vida ---
onMounted(() => {
    void fetchCalls(); // Busca imediata
    
    // Polling a cada 3 segundos (Tempo real)
    updateTimer = setInterval(() => { void fetchCalls(); }, 3000);
    
    // Timer do relógio local para atualizar cronômetros visualmente a cada segundo
    clockTimer = setInterval(() => { now.value = new Date(); }, 1000);
});

onUnmounted(() => {
    clearInterval(updateTimer);
    clearInterval(clockTimer);
});
</script>

<style scoped>
.font-inter { font-family: 'Roboto', sans-serif; }
.font-mono { font-family: 'Courier New', monospace; letter-spacing: -2px; }

.andon-tile {
    height: 320px;
    border-radius: 4px;
    transition: all 0.3s ease;
}

.bg-black-10 { background-color: rgba(0,0,0,0.2); }
.lh-none { line-height: 1; }
.tracking-widest { letter-spacing: 4px; }
.opacity-60 { opacity: 0.6; }
.opacity-80 { opacity: 0.8; }

.line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.blink-slow { animation: fade 2s infinite alternate; }
.animate-pulse { animation: pulse 1.5s infinite; }

@keyframes fade { from { opacity: 1; } to { opacity: 0.7; } }
@keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }

/* Animação de entrada dos cards */
.fade-enter-active { animation: fadeInUp 0.5s; }
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
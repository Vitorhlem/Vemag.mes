<template>
  <q-layout view="hHh lpR fFf" class="app-bg text-white font-industry overflow-hidden window-height">
    
    <q-header class="header-glass q-py-md q-px-xl">
      <div class="row items-center justify-between">
        <div class="row items-center q-gutter-x-lg">
          <div class="logo-box relative-position flex flex-center">
              <div class="absolute-full bg-red-5 opacity-20 rounded-borders animate-ping" v-if="hasCriticalCalls"></div>
              <q-icon name="hub" color="white" size="32px" />
          </div>
          <div>
            <div class="text-h5 text-weight-bolder tracking-wide text-uppercase">Andon<span class="text-primary">Live</span></div>
            <div class="row items-center q-gutter-x-sm">
                <div class="status-dot animate-pulse"></div>
                <div class="text-caption text-grey-5 text-uppercase tracking-widest" style="font-size: 10px">Monitoramento Ativo</div>
            </div>
          </div>
        </div>

        <div class="row items-center q-gutter-x-xl">
           <div class="metric-group text-right">
              <div class="label">Paradas Ativas</div>
              <div class="value text-red-4">{{ calls.length }}</div>
           </div>
           <div class="separator-vertical"></div>
           <div class="metric-group text-right">
              <div class="label">Hora Local</div>
              <div class="value text-white font-digital">{{ currentTime }}</div>
           </div>
        </div>
      </div>
    </q-header>

    <q-page-container class="full-height relative-position z-10">
      <q-page class="q-pa-lg full-height column">
        
        <div v-if="isLoading && calls.length === 0" class="col flex flex-center">
           <div class="column items-center">
              <q-spinner-dots size="4em" color="primary" />
              <div class="text-subtitle1 text-grey-6 q-mt-md tracking-wide">Sincronizando dados da fábrica...</div>
           </div>
        </div>

        <div v-else class="col relative-position">
          <transition-group 
            appear
            enter-active-class="animated fadeInUp"
            leave-active-class="animated fadeOut"
            tag="div" 
            class="row q-col-gutter-md full-height content-start"
          >
            
            <div 
              v-for="call in sortedCalls" 
              :key="call.id" 
              class="col-12 col-md-6 col-lg-4 col-xl-3"
            >
              <q-card 
                class="andon-card column justify-between cursor-pointer" 
                :class="getCardStyle(call)"
                @click="openActionDialog(call)"
              >
                <div class="absolute-full hover-overlay"></div>

                <div class="row items-start justify-between q-mb-md relative-position z-10">
                    <div class="column col">
                        <q-badge 
                            :color="getSectorColor(call.sector)" 
                            class="q-mb-xs self-start text-weight-bold q-px-sm q-py-xs shadow-2"
                            rounded
                        >
                            {{ call.sector }}
                        </q-badge>
                        <div class="text-h5 text-weight-900 text-uppercase leading-tight ellipsis-2-lines q-pr-sm">
                            {{ call.machine_name || 'Máquina ' + call.machine_id }}
                        </div>
                    </div>
                    <div class="timer-box" :class="{'critical-pulse': isCritical(call)}">
                        {{ getElapsedTime(call) }}
                    </div>
                </div>

                <div class="col column justify-center q-py-sm relative-position z-10">
                    <div class="text-subtitle1 text-grey-3 font-weight-medium ellipsis-2-lines">
                        {{ call.reason || 'Sem motivo detalhado' }}
                    </div>
                    <div class="text-caption text-grey-5 q-mt-xs">
                        Aberto em: {{ formatStartTime(call) }}
                    </div>
                </div>

                <div class="card-footer row items-center justify-between q-mt-md relative-position z-10">
                    <div class="row items-center">
                        <q-avatar size="24px" color="grey-8" text-color="white" class="q-mr-sm font-weight-bold">
                            {{ (call.operator_name || 'U').charAt(0) }}
                        </q-avatar>
                        <div class="text-caption text-grey-4 ellipsis" style="max-width: 100px">
                            {{ call.operator_name || 'Operador' }}
                        </div>
                    </div>

                    <div v-if="call.status === 'IN_PROGRESS'" class="status-pill text-blue">
                        <q-avatar size="18px" color="blue-9" text-color="white" class="q-mr-xs font-weight-bold">
                            {{ (call.accepted_by_name || 'T').charAt(0) }}
                        </q-avatar>
                        <div class="ellipsis" style="max-width: 90px">
                            {{ call.accepted_by_name || 'Atendendo' }}
                        </div>
                    </div>
                    <div v-else class="status-pill text-orange">
                        <q-icon name="touch_app" size="14px" class="q-mr-xs animate-bounce" /> AGUARDANDO
                    </div>
                </div>

                <div class="progress-line">
                    <div class="bar" :style="{width: '100%'}" :class="getBarColor(call)"></div>
                </div>

              </q-card>
            </div>

          </transition-group>

          <div v-if="!isLoading && calls.length === 0" class="absolute-full flex flex-center column">
              <div class="empty-state-glow">
                 <q-icon name="check" size="80px" color="green-4" />
              </div>
              <div class="text-h2 text-weight-900 text-white text-uppercase tracking-widest q-mt-xl text-shadow">All Systems Go</div>
              <div class="text-h6 text-grey-6 font-light q-mt-sm">Produção Operando Normalmente</div>
          </div>

        </div>
      </q-page>
    </q-page-container>
    
    <div class="bg-grid absolute-full"></div>

    <q-dialog v-model="isDialogOpen" backdrop-filter="blur(4px)">
        <q-card class="bg-grey-9 text-white shadow-24" style="width: 500px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1)">
            
            <q-card-section class="row items-center justify-between q-pb-none">
                <div class="text-h6 text-weight-bold text-uppercase text-grey-4">Gerenciar Chamado #{{ selectedCall?.id }}</div>
                <q-btn icon="close" flat round dense v-close-popup />
            </q-card-section>

            <q-card-section class="q-pt-md">
                <div class="text-h4 text-weight-bolder leading-tight q-mb-sm">
                    {{ selectedCall?.machine_name }}
                </div>
                <q-chip :color="getSectorColor(selectedCall?.sector || '')" text-color="white" icon="label">
                    {{ selectedCall?.sector }}
                </q-chip>
                
                <div class="bg-grey-8 rounded-borders q-pa-md q-mt-md">
                    <div class="text-caption text-uppercase text-grey-5 q-mb-xs">Motivo Relatado</div>
                    <div class="text-body1">{{ selectedCall?.reason }}</div>
                    <div class="text-caption text-grey-5 q-mt-sm">
                        Solicitante: <span class="text-white">{{ selectedCall?.operator_name || 'Desconhecido' }}</span>
                    </div>
                </div>

                <div v-if="selectedCall?.status === 'IN_PROGRESS'" class="q-mt-md row items-center text-blue-4 bg-blue-10 q-pa-sm rounded-borders">
                    <q-icon name="engineering" size="24px" class="q-mr-sm" />
                    <div>
                        <div class="text-weight-bold">Em Atendimento por:</div>
                        <div>{{ selectedCall?.accepted_by_name || 'Técnico' }}</div>
                    </div>
                </div>
            </q-card-section>

            <q-separator color="grey-8" />

            <q-card-actions align="right" class="q-pa-md q-gutter-md">
                
                <q-btn 
                    v-if="selectedCall?.status === 'OPEN'"
                    push 
                    color="primary" 
                    size="lg" 
                    class="full-width"
                    icon="handyman"
                    label="ASSUMIR CHAMADO"
                    :loading="isProcessing"
                    @click="takeCall"
                />

                <div v-if="selectedCall?.status === 'IN_PROGRESS'" class="full-width column q-gutter-y-md">
                    <q-btn 
                        push 
                        color="positive" 
                        size="lg" 
                        class="full-width"
                        icon="check_circle"
                        label="FINALIZAR CHAMADO"
                        :loading="isProcessing"
                        @click="resolveCall"
                    />
                </div>

            </q-card-actions>
        </q-card>
    </q-dialog>

  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { date, useQuasar } from 'quasar';
import { AndonService } from 'src/services/andon-service';
import { useAuthStore } from 'stores/auth-store'; // Importante para validar usuário

interface AndonCall {
    id: number;
    machine_id: number;
    machine_name?: string;
    sector: string;
    reason?: string;
    status: string;
    opened_at?: string;
    created_at?: string;
    operator_name?: string;
    accepted_by_name?: string;
}

const $q = useQuasar();
const authStore = useAuthStore(); // Para saber quem está clicando
const calls = ref<AndonCall[]>([]);
const now = ref(new Date());
const isLoading = ref(true);
const isDialogOpen = ref(false);
const selectedCall = ref<AndonCall | null>(null);
const isProcessing = ref(false);

let updateTimer: any;
let clockTimer: any;

const currentTime = computed(() => date.formatDate(now.value, 'HH:mm:ss'));

const sortedCalls = computed(() => {
    return [...calls.value].sort((a, b) => {
        const startA = new Date(a.opened_at || a.created_at || now.value).getTime();
        const startB = new Date(b.opened_at || b.created_at || now.value).getTime();
        return startA - startB; 
    });
});

const hasCriticalCalls = computed(() => calls.value.some(c => isCritical(c)));

// --- API ---
async function fetchCalls() {
    try {
        const data = await AndonService.getActiveCalls();
        if (Array.isArray(data)) {
            calls.value = data;
        }
    } catch (e) {
        console.error("Erro Andon:", e);
    } finally {
        isLoading.value = false;
    }
}

// --- INTERATIVIDADE ---

function openActionDialog(call: AndonCall) {
    // Só abre o modal se tiver usuário logado capaz de atuar
    // Se for uma TV sem usuário, pode bloquear ou pedir PIN (aqui assume logado)
    selectedCall.value = call;
    isDialogOpen.value = true;
}

async function takeCall() {
    if (!selectedCall.value) return;
    
    // Validação simples de Auth
    if (!authStore.user) {
        $q.notify({ type: 'warning', message: 'Você precisa estar logado para assumir chamados.' });
        return;
    }

    isProcessing.value = true;
    try {
        await AndonService.acceptCall(selectedCall.value.id);
        $q.notify({ type: 'positive', message: 'Chamado assumido! Bom trabalho.' });
        isDialogOpen.value = false;
        fetchCalls(); // Atualiza lista imediatamente
    } catch (error) {
        $q.notify({ type: 'negative', message: 'Erro ao assumir chamado.' });
    } finally {
        isProcessing.value = false;
    }
}

async function resolveCall() {
    if (!selectedCall.value) return;
    isProcessing.value = true;
    try {
        await AndonService.resolveCall(selectedCall.value.id);
        $q.notify({ type: 'positive', message: 'Chamado finalizado com sucesso!' });
        isDialogOpen.value = false;
        fetchCalls(); // Atualiza lista
    } catch (error) {
        $q.notify({ type: 'negative', message: 'Erro ao finalizar chamado.' });
    } finally {
        isProcessing.value = false;
    }
}

// --- Helpers Visuais ---
function getMinutesElapsed(call: AndonCall): number {
    const startStr = call.opened_at || call.created_at;
    if (!startStr) return 0;
    return Math.max(0, (now.value.getTime() - new Date(startStr).getTime()) / 1000 / 60);
}

function getElapsedTime(call: AndonCall): string {
    const startStr = call.opened_at || call.created_at;
    if (!startStr) return "00:00";
    
    const diff = Math.max(0, Math.floor((now.value.getTime() - new Date(startStr).getTime()) / 1000));
    const h = Math.floor(diff / 3600);
    const m = Math.floor((diff % 3600) / 60).toString().padStart(2, '0');
    const s = (diff % 60).toString().padStart(2, '0');
    return h > 0 ? `${h}:${m}:${s}` : `${m}:${s}`;
}

function formatStartTime(call: AndonCall) {
    const d = new Date(call.opened_at || call.created_at || now.value);
    return date.formatDate(d, 'HH:mm');
}

function isCritical(call: AndonCall): boolean {
    return (call.status !== 'IN_PROGRESS') && getMinutesElapsed(call) > 15;
}

function getCardStyle(call: AndonCall) {
    if (call.status === 'IN_PROGRESS') return 'card-blue';
    const mins = getMinutesElapsed(call);
    if (mins > 15) return 'card-purple critical-border';
    if (mins > 5) return 'card-red';
    return 'card-orange';
}

function getBarColor(call: AndonCall) {
    if (call.status === 'IN_PROGRESS') return 'bg-blue-5';
    const mins = getMinutesElapsed(call);
    if (mins > 15) return 'bg-purple-5';
    if (mins > 5) return 'bg-red-5';
    return 'bg-orange-5';
}

function getSectorColor(sector: string) {
    if (!sector) return 'grey';
    const s = sector.toUpperCase();
    if (s.includes('MANUT')) return 'brown-5';
    if (s.includes('QUALID')) return 'teal-5';
    if (s.includes('LOGIS')) return 'indigo-5';
    if (s.includes('PCP')) return 'deep-purple-5';
    if (s.includes('ELETR')) return 'orange-8';
    return 'blue-grey-8';
}

onMounted(() => {
    fetchCalls();
    updateTimer = setInterval(fetchCalls, 5000);
    clockTimer = setInterval(() => { now.value = new Date(); }, 1000);
});

onUnmounted(() => {
    clearInterval(updateTimer);
    clearInterval(clockTimer);
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&family=JetBrains+Mono:wght@500;700&display=swap');

.app-bg { background-color: #0f172a; font-family: 'Inter', sans-serif; }
.bg-grid {
    background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    z-index: 0; pointer-events: none;
}

.header-glass {
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-box {
    width: 48px; height: 48px;
    background: linear-gradient(135deg, #334155, #1e293b);
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.metric-group .label { font-size: 10px; text-transform: uppercase; color: #94a3b8; font-weight: 600; letter-spacing: 1px; }
.metric-group .value { font-size: 24px; font-weight: 700; line-height: 1.1; }
.metric-group .font-digital { font-family: 'JetBrains Mono', monospace; letter-spacing: -1px; }
.separator-vertical { width: 1px; height: 30px; background: rgba(255,255,255,0.15); }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background-color: #4ade80; box-shadow: 0 0 8px #4ade80; }

/* CARD STYLES */
.andon-card {
    height: 240px;
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
    overflow: hidden;
    position: relative;
}
.andon-card:hover { transform: translateY(-4px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4); border-color: rgba(255,255,255,0.2); }
.hover-overlay { background: radial-gradient(circle at center, rgba(255,255,255,0.05) 0%, transparent 70%); opacity: 0; transition: opacity 0.3s; }
.andon-card:hover .hover-overlay { opacity: 1; }

.card-orange { border-left: 4px solid #f97316; box-shadow: inset 10px 0 30px -15px rgba(249, 115, 22, 0.2); }
.card-red { border-left: 4px solid #ef4444; box-shadow: inset 10px 0 30px -15px rgba(239, 68, 68, 0.3); }
.card-purple { border-left: 4px solid #a855f7; box-shadow: inset 10px 0 30px -15px rgba(168, 85, 247, 0.3); }
.card-blue { border-left: 4px solid #3b82f6; box-shadow: inset 10px 0 30px -15px rgba(59, 130, 246, 0.2); }

.timer-box {
    font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 700;
    color: #e2e8f0; background: rgba(0, 0, 0, 0.3); padding: 4px 12px; border-radius: 8px;
    letter-spacing: -1px; border: 1px solid rgba(255,255,255,0.05);
}
.critical-pulse { color: #fca5a5; animation: text-pulse 1s infinite alternate; border-color: rgba(239, 68, 68, 0.4); }

.card-footer { border-top: 1px solid rgba(255, 255, 255, 0.05); padding-top: 12px; }
.status-pill {
    font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 4px 8px;
    border-radius: 6px; background: rgba(255,255,255,0.05); display: flex; align-items: center;
}

.progress-line { position: absolute; bottom: 0; left: 0; width: 100%; height: 3px; background: rgba(0,0,0,0.3); }
.progress-line .bar { height: 100%; animation: load 60s linear; }

.empty-state-glow {
    width: 160px; height: 160px; border-radius: 50%;
    background: radial-gradient(circle, rgba(74, 222, 128, 0.2) 0%, rgba(0,0,0,0) 70%);
    display: flex; justify-content: center; align-items: center;
    border: 1px solid rgba(74, 222, 128, 0.1); box-shadow: 0 0 40px rgba(74, 222, 128, 0.1);
}

.animate-pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
.animate-ping { animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite; }
.animate-bounce { animation: bounce 2s infinite; }

@keyframes text-pulse { from { opacity: 1; text-shadow: 0 0 10px rgba(239,68,68,0.5); } to { opacity: 0.6; text-shadow: none; } }
@keyframes load { from { width: 0; } to { width: 100%; } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
@keyframes ping { 75%, 100% { transform: scale(2); opacity: 0; } }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }

.font-weight-medium { font-weight: 500; }
.opacity-20 { opacity: 0.2; }
</style>
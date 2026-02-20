<template>
  <q-page class="q-pa-md bg-grey-2">
    <div v-if="isTvMode" class="row items-center justify-between q-mb-lg bg-dark text-white q-pa-md rounded-borders shadow-2">
      <div class="row items-center">
        <q-icon name="hub" size="md" color="primary" class="q-mr-sm" />
        <div>
          <div class="text-h5 text-weight-bolder">Andon<span class="text-primary">Live</span></div>
          <div class="text-caption text-grey-5 uppercase tracking-widest">Monitoramento de Chão de Fábrica</div>
        </div>
      </div>
      <div class="row q-gutter-x-md text-center">
        <div class="q-px-md">
          <div class="text-caption text-grey-5">PARADAS ATIVAS</div>
          <div class="text-h5 text-weight-bold text-negative">{{ calls.length }}</div>
        </div>
        <q-separator vertical dark inset />
        <div class="q-px-md">
          <div class="text-caption text-grey-5">HORA ATUAL</div>
          <div class="text-h5 text-weight-bold">{{ currentTime }}</div>
        </div>
      </div>
    </div>

    <div class="row q-col-gutter-md q-mb-lg">
      <div class="col-12 col-md-4">
        <q-card class="kpi-card border-left-negative">
          <q-card-section class="row items-center no-wrap">
            <q-avatar color="red-1" text-color="negative" icon="warning" />
            <div class="q-ml-md">
              <div class="text-caption text-grey-7 text-uppercase">Aguardando Técnico</div>
              <div class="text-h5 text-weight-bolder text-negative">{{ pendingCallsCount }}</div>
            </div>
          </q-card-section>
        </q-card>
      </div>
      <div class="col-12 col-md-4">
        <q-card class="kpi-card border-left-primary">
          <q-card-section class="row items-center no-wrap">
            <q-avatar color="blue-1" text-color="primary" icon="engineering" />
            <div class="q-ml-md">
              <div class="text-caption text-grey-7 text-uppercase">Em Atendimento</div>
              <div class="text-h5 text-weight-bolder text-primary">{{ inProgressCallsCount }}</div>
            </div>
          </q-card-section>
        </q-card>
      </div>
      <div class="col-12 col-md-4">
        <q-card class="kpi-card border-left-teal">
          <q-card-section class="row items-center no-wrap">
            <q-avatar color="teal-1" text-color="teal-9" icon="timer" />
            <div class="q-ml-md">
              <div class="text-caption text-grey-7 text-uppercase">Tempo Médio de Resposta</div>
              <div class="text-h5 text-weight-bolder text-teal-9">{{ avgResponseTime }} min</div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <div v-if="isLoading && calls.length === 0" class="flex flex-center q-pa-xl">
      <q-spinner-dots size="4em" color="primary" />
    </div>

    <div v-else>
      <transition-group appear enter-active-class="animated fadeIn" leave-active-class="animated fadeOut" tag="div" class="row q-col-gutter-md">
        <div v-for="call in sortedCalls" :key="call.id" class="col-12 col-sm-6 col-md-4 col-xl-3">
          <q-card 
            class="andon-card-pro cursor-pointer transition-all" 
            :class="getCardClass(call)"
            @click="openActionDialog(call)"
          >
            <q-card-section class="q-pb-none">
              <div class="row justify-between items-start">
                <q-badge :color="getSectorColor(call.sector)" class="text-weight-bold q-mb-xs">
                  {{ call.sector }}
                </q-badge>
                <div class="text-h6 font-mono text-weight-bold" :class="isCritical(call) ? 'text-negative animate-flash' : 'text-grey-9'">
                  {{ getElapsedTime(call) }}
                </div>
              </div>
              <div class="text-h5 text-weight-bolder text-dark q-mt-xs">
                {{ call.machine_name || 'Máquina ' + call.machine_id }}
              </div>
            </q-card-section>

            <q-card-section class="q-py-md">
              <div class="text-subtitle1 text-grey-8 text-weight-medium line-clamp-2" style="min-height: 3em">
                {{ call.reason || 'Parada não especificada' }}
              </div>
              <div class="text-caption text-grey-6 q-mt-sm">
                Início: {{ formatStartTime(call) }}
              </div>
            </q-card-section>

            <q-separator inset color="grey-3" />

            <q-card-section class="row items-center justify-between">
              <div class="row items-center">
                <q-avatar size="24px" color="grey-3" text-color="grey-8" class="q-mr-xs">
                  <q-icon name="person" size="16px" />
                </q-avatar>
                <span class="text-caption text-weight-medium text-grey-8">{{ call.operator_name || 'Op. Padrão' }}</span>
              </div>

              <q-chip 
                v-if="call.status === 'IN_PROGRESS'" 
                outline color="primary" size="sm" icon="engineering"
              >
                {{ call.accepted_by_name || 'Técnico' }}
              </q-chip>
              <q-chip v-else color="orange-1" text-color="orange-9" size="sm" icon="priority_high" class="text-weight-bold">
                AGUARDANDO
              </q-chip>
            </q-card-section>

            <q-linear-progress 
              :value="1" 
              :color="isCritical(call) ? 'negative' : (call.status === 'IN_PROGRESS' ? 'primary' : 'orange')" 
              size="4px" 
            />
          </q-card>
        </div>
      </transition-group>

      <div v-if="!isLoading && calls.length === 0" class="flex flex-center column q-pa-xl bg-white rounded-borders shadow-1 q-mt-md">
        <q-icon name="check_circle" size="80px" color="teal-4" />
        <div class="text-h4 text-weight-bold text-grey-9 q-mt-md">Sem Paradas Ativas</div>
        <div class="text-subtitle1 text-grey-6">A linha de produção está operando normalmente.</div>
      </div>
    </div>

    <q-dialog v-model="isDialogOpen">
      <q-card style="width: 450px; border-radius: 12px">
        <q-card-section class="bg-primary text-white row items-center">
          <div class="text-h6">Gerenciar Chamado Andon</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section class="q-pa-lg text-center">
          <div class="text-overline text-primary uppercase">Equipamento</div>
          <div class="text-h4 text-weight-bolder">{{ selectedCall?.machine_name }}</div>
          <q-chip outline color="grey-8" class="q-mt-sm">{{ selectedCall?.sector }}</q-chip>
          
          <div class="bg-grey-2 q-pa-md q-mt-lg rounded-borders text-left">
            <div class="text-caption text-grey-7 uppercase text-weight-bold">Motivo da Parada</div>
            <div class="text-body1 text-grey-9">{{ selectedCall?.reason }}</div>
          </div>
        </q-card-section>

        <q-separator />

        <q-card-actions align="center" class="q-pa-md">
          <q-btn 
            v-if="selectedCall?.status === 'OPEN'"
            label="ASSUMIR ATENDIMENTO" 
            color="primary" icon="handyman" class="full-width q-py-sm"
            unelevated :loading="isProcessing" @click="takeCall"
          />
          <q-btn 
            v-if="selectedCall?.status === 'IN_PROGRESS'"
            label="FINALIZAR E LIBERAR MÁQUINA" 
            color="positive" icon="check_circle" class="full-width q-py-sm"
            unelevated :loading="isProcessing" @click="resolveCall"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { date, useQuasar } from 'quasar';
import { AndonService } from 'src/services/andon-service';
import { useAuthStore } from 'src/stores/auth-store';

const authStore = useAuthStore();
const route = useRoute();
const $q = useQuasar();

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const calls = ref<any[]>([]);
const now = ref(new Date());
const isLoading = ref(true);
const isDialogOpen = ref(false);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const selectedCall = ref<any>(null);
const isProcessing = ref(false);
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let clockTimer: any;
let socket: WebSocket | null = null;

const isTvMode = computed(() => route.name === 'andon-full');
const currentTime = computed(() => date.formatDate(now.value, 'HH:mm:ss'));
const pendingCallsCount = computed(() => calls.value.filter(c => c.status === 'OPEN').length);
const inProgressCallsCount = computed(() => calls.value.filter(c => c.status === 'IN_PROGRESS').length);
const avgResponseTime = computed(() => calls.value.length === 0 ? 0 : 8);

const sortedCalls = computed(() => {
  return [...calls.value].sort((a, b) => {
    const priorityA = a.status === 'OPEN' ? 2 : 1;
    const priorityB = b.status === 'OPEN' ? 2 : 1;
    if (priorityA !== priorityB) return priorityB - priorityA;
    return new Date(a.opened_at || a.created_at).getTime() - new Date(b.opened_at || b.created_at).getTime();
  });
});

// Tempo Real via WebSocket
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const orgId = authStore.user?.organization_id;
  
  if (!orgId) return;

  // Garanta que a URL está batendo com a rota do FastAPI
  const wsUrl = `${protocol}//${host}/api/v1/andon/ws/${orgId}`;
  console.log("📡 Conectando ao Andon via:", wsUrl);

  socket = new WebSocket(wsUrl);

  socket.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);
      console.log("📥 Mensagem recebida no Andon:", message);

      // 🔔 Independente do tipo (NEW_CALL ou UPDATE_CALL),
      // nós recarregamos a lista oficial do servidor.
      if (message.type === 'NEW_CALL' || message.type === 'UPDATE_CALL') {
        
        // 1. Recarrega os dados do banco (Garante 100% de sincronia)
        void fetchCalls(); 
        
        // 2. Notificação e Som (Apenas para novos chamados)
        if (message.type === 'NEW_CALL') {
          $q.notify({ 
            icon: 'campaign', 
            color: 'negative', 
            message: `NOVO CHAMADO: ${message.data?.machine_name || 'Equipamento'}`,
            position: 'top',
            padding: '20px',
            classes: 'text-h6' // Deixa o aviso maior para a TV
          });
          playAndonAlert();
        }
      }
    } catch (e) {
      console.error("Erro ao processar mensagem do rádio", e);
    }
  };

  socket.onclose = () => {
    console.warn("⚠️ WebSocket Andon desconectado. Tentando reconectar...");
    setTimeout(connectWebSocket, 5000);
  };
  
  socket.onerror = (err) => {
    console.error("❌ Erro no WebSocket do Andon:", err);
  };
}
async function fetchCalls() {
  try {
    const data = await AndonService.getActiveCalls();
    calls.value = Array.isArray(data) ? data : [];
  } catch (e) {
    console.error("Erro Andon:", e);
  } finally {
    isLoading.value = false;
  }
}

async function takeCall() {
  if (!selectedCall.value) return;
  isProcessing.value = true;
  try {
    await AndonService.acceptCall(selectedCall.value.id);
    $q.notify({ type: 'positive', message: 'Atendimento iniciado!' });
    isDialogOpen.value = false;
    void fetchCalls();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Erro ao assumir chamado.' });
  } finally { isProcessing.value = false; }
}

async function resolveCall() {
  if (!selectedCall.value) return;
  isProcessing.value = true;
  try {
    await AndonService.resolveCall(selectedCall.value.id);
    $q.notify({ type: 'positive', message: 'Máquina liberada!' });
    isDialogOpen.value = false;
    void fetchCalls();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Erro ao finalizar.' });
  } finally { isProcessing.value = false; }
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getElapsedTime(call: any): string {
  const start = new Date(call.opened_at || call.created_at);
  const diff = Math.max(0, Math.floor((now.value.getTime() - start.getTime()) / 1000));
  const m = Math.floor(diff / 60).toString().padStart(2, '0');
  const s = (diff % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function isCritical(call: any): boolean {
  if (call.status === 'IN_PROGRESS') return false;
  const start = new Date(call.opened_at || call.created_at);
  return (now.value.getTime() - start.getTime()) / 1000 / 60 > 10;
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getCardClass(call: any) {
  if (call.status === 'IN_PROGRESS') return 'border-top-primary';
  if (isCritical(call)) return 'border-top-negative shadow-critical';
  return 'border-top-warning';
}

function getSectorColor(sector: string) {
  const s = sector?.toUpperCase() || '';
  if (s.includes('MANUT')) return 'orange-9';
  if (s.includes('QUAL')) return 'teal-7';
  if (s.includes('PCP')) return 'indigo-7';
  return 'blue-grey-6';
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function formatStartTime(call: any) {
  return date.formatDate(call.opened_at || call.created_at, 'HH:mm');
}
function playAndonAlert() {
  const audio = new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg');
  audio.play().catch(() => console.log('Áudio bloqueado pelo navegador até o primeiro clique do usuário.'));
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function openActionDialog(call: any) {
  selectedCall.value = call;
  isDialogOpen.value = true;
}

onMounted(() => {
  void fetchCalls();
  connectWebSocket();
  clockTimer = setInterval(() => { now.value = new Date(); }, 1000);
});

onUnmounted(() => {
  if (socket) socket.close();
  clearInterval(clockTimer);
});
</script>

<style scoped lang="scss">
.andon-card-pro {
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  transition: transform 0.2s, box-shadow 0.2s;
  background: white;
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.1);
  }
}
.border-top-primary { border-top: 5px solid var(--q-primary); }
.border-top-negative { border-top: 5px solid var(--q-negative); }
.border-top-warning { border-top: 5px solid var(--q-warning); }
.kpi-card { border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.border-left-negative { border-left: 4px solid var(--q-negative); }
.border-left-primary { border-left: 4px solid var(--q-primary); }
.border-left-teal { border-left: 4px solid #009688; }
.shadow-critical { box-shadow: 0 0 15px rgba(211, 47, 47, 0.2); }
.animate-flash { animation: flash 1.5s infinite; }
@keyframes flash { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.font-mono { font-family: 'JetBrains Mono', monospace; }
</style>
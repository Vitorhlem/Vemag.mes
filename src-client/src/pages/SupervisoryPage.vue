<template>
  <q-page class="q-pa-md bg-grey-1 column">
    
    <div class="row items-center q-mb-md">
      <div class="column">
        <h1 class="text-h5 text-weight-bold text-teal-9 q-ma-none flex items-center">
          <q-icon name="schema" size="md" class="q-mr-sm" /> 
          Supervisório Digital (Planta)
        </h1>
        <p class="text-caption text-grey-6 q-ma-none">Visão em tempo real da alocação de máquinas.</p>
      </div>

      <q-space />

      <q-btn
        :color="isEditMode ? 'orange-9' : 'teal-8'"
        :icon="isEditMode ? 'lock_open' : 'lock'"
        :label="isEditMode ? 'Finalizar Edição' : 'Editar Layout'"
        :outline="!isEditMode"
        class="shadow-2 q-px-md font-weight-bold transition-all"
        @click="toggleEditMode"
      >
        <q-tooltip v-if="!isEditMode">Destravar para arrastar máquinas</q-tooltip>
      </q-btn>
    </div>

    <div 
      class="blueprint-container shadow-4 rounded-borders relative-position overflow-hidden col-grow"
      ref="mapAreaRef"
      @dragover.prevent
      @drop="onDrop"
    >
      <div 
        v-if="unplacedMachines.length > 0 && isEditMode"
        class="unplaced-dock shadow-2 bg-white q-pa-sm"
      >
        <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">Máquinas não alocadas (Arraste p/ o mapa):</div>
        <div class="row q-gutter-sm">
          <div 
            v-for="machine in unplacedMachines" 
            :key="machine.id"
            class="machine-card dock-card"
            draggable="true"
            @dragstart="onDragStart($event, machine)"
          >
            <div class="machine-id">{{ machine.id }}</div>
            <div class="machine-model text-truncate">{{ machine.model }}</div>
          </div>
        </div>
      </div>

      <transition-group name="fade">
        <div 
          v-for="machine in placedMachines" 
          :key="machine.id"
          class="machine-card map-card shadow-5"
          :class="[
             getStatusColorClass(machine.status), 
             { 'edit-mode-active': isEditMode, 'pulse-effect': isRunning(machine.status) }
          ]"
          :style="{
            left: `${machine.layout_x}%`,
            top: `${machine.layout_y}%`,
          }"
          :draggable="isEditMode"
          @dragstart="onDragStart($event, machine)"
          @click="goToMachineDetails(machine.id)"
        >
          <div class="card-header row items-center justify-between no-wrap">
            <div class="machine-id-badge shadow-1">{{ machine.id }}</div>
            <q-btn v-if="isEditMode" round dense flat icon="close" size="xs" class="remove-btn" @click.stop="removeMachineFromMap(machine)" />
          </div>

          <div class="card-body column items-center justify-center">
            <q-icon :name="getMachineIcon(machine.category)" size="sm" class="q-mb-xs opacity-80" />
            <div class="machine-model text-weight-bolder text-center" style="line-height: 1.1;">{{ machine.model }}</div>
            <div class="machine-brand text-caption" style="font-size: 0.65rem;">{{ machine.brand }}</div>
          </div>

          <div class="card-footer text-center q-pt-xs">
            <span class="status-label text-weight-bold text-uppercase">{{ formatStatus(machine.status) }}</span>
          </div>
        </div>
      </transition-group>

    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useProductionStore } from 'stores/production-store';
import type { Machine } from 'stores/production-store';

const router = useRouter();
const $q = useQuasar();
const store = useProductionStore();

const mapAreaRef = ref<HTMLElement | null>(null);
const isEditMode = ref(false);

// Variável global simples para o Drag'n'Drop
let draggedMachine: Machine | null = null;

// =========================================================================
// COMPUTADOS E FILTROS
// =========================================================================

// Máquinas que JÁ TEM x e y definidos
const placedMachines = computed(() => {
  return store.machinesList.filter(m => m.layout_x != null && m.layout_y != null);
});

// Máquinas que AINDA NÃO TEM x e y definidos
const unplacedMachines = computed(() => {
  return store.machinesList.filter(m => m.layout_x == null || m.layout_y == null);
});

// =========================================================================
// LÓGICA DE DRAG AND DROP (O Segredo Matemático)
// =========================================================================

function toggleEditMode() {
  isEditMode.value = !isEditMode.value;
  if (!isEditMode.value) {
    $q.notify({ type: 'positive', message: 'Layout Travado e Salvo com Sucesso!', icon: 'lock' });
  } else {
    $q.notify({ type: 'info', message: 'Modo de Edição Ativado. Arraste as máquinas.', icon: 'open_with' });
  }
}

function onDragStart(event: DragEvent, machine: Machine) {
  if (!isEditMode.value) {
    event.preventDefault(); // Impede arrastar se estiver travado
    return;
  }
  draggedMachine = machine;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    // Truque: Imagem fantasma transparente para ficar mais limpo
    const emptyImage = new Image();
    emptyImage.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
    event.dataTransfer.setDragImage(emptyImage, 0, 0);
  }
}

async function onDrop(event: DragEvent) {
  if (!isEditMode.value || !draggedMachine || !mapAreaRef.value) return;

  const mapRect = mapAreaRef.value.getBoundingClientRect();
  
  // Calcula a posição do mouse em relação ao canto esquerdo superior do mapa (em Pixels)
  let rawX = event.clientX - mapRect.left;
  let rawY = event.clientY - mapRect.top;

  // Centraliza o mouse no meio do Card (O card tem aprox 110x110px)
  rawX = rawX - 55; 
  rawY = rawY - 55;

  // Matemática Mágica: Converte os Pixels para Porcentagem (0 a 100%)
  let percentX = (rawX / mapRect.width) * 100;
  let percentY = (rawY / mapRect.height) * 100;

  // Travas de borda para a máquina não sair voando para fora do monitor
  if (percentX < 0) percentX = 0;
  if (percentX > 90) percentX = 90;
  if (percentY < 0) percentY = 0;
  if (percentY > 85) percentY = 85;

  // Chama a função da store (que vai bater no backend via Axios)
  await store.saveMachineLayout(draggedMachine.id, Number(percentX.toFixed(2)), Number(percentY.toFixed(2)));
  
  draggedMachine = null;
}

async function removeMachineFromMap(machine: Machine) {
  await store.saveMachineLayout(machine.id, null as any, null as any);
  $q.notify({ type: 'warning', message: `${machine.model} voltou para a doca.`, timeout: 1000 });
}

// =========================================================================
// INTERAÇÃO E VISUAL
// =========================================================================

function goToMachineDetails(machineId: number) {
  if (isEditMode.value) return; // No modo edição, o clique é bloqueado para não irritar ao arrastar
  router.push(`/employees?machine=${machineId}`);
}

function formatStatus(raw: string | undefined): string {
  if (!raw) return 'DESCONHECIDO';
  const s = raw.toUpperCase();
  
  // Mapeamento corrigido (Agora com "USO" em português)
  if (s.includes('AUTÔNOM') || s.includes('AUTONOMOUS')) return 'AUTÔNOMO';
  if (s.includes('USO') || s.includes('RUNNING') || s.includes('OPERAÇÃO') || s.includes('PRODUCING')) return 'OPERAÇÃO';
  if (s.includes('MANUTEN') || s.includes('MAINTENANCE') || s.includes('BROKEN')) return 'MANUTENÇÃO';
  if (s.includes('SETUP') || s.includes('PREPARA')) return 'SETUP';
  
  // Paradas e Ociosidade
  if (s.includes('OCIOS') || s.includes('DISPON') || s.includes('AVAILABLE') || s.includes('IDLE')) return 'OCIOSO';
  if (s.includes('PARADA') || s.includes('PAUS') || s.includes('STOPPED')) return 'PARADA';
  
  return 'DESCONHECIDO';
}

function getStatusColorClass(raw: string | undefined): string {
  const status = formatStatus(raw);
  
  switch(status) {
    case 'OPERAÇÃO': return 'status-green';
    case 'AUTÔNOMO': return 'status-blue';
    case 'SETUP': return 'status-purple';
    
    // 🚀 CORREÇÃO: Ocioso/Disponível agora usa a classe cinza!
    case 'OCIOSO': return 'status-grey'; 
    
    case 'PARADA': return 'status-orange'; // Laranja fica apenas para Pausa/Parada com OP ativa
    case 'MANUTENÇÃO': return 'status-red';
    default: return 'status-grey'; // Se não reconhecer o status, fica cinza neutro
  }
}



function isRunning(raw: string | undefined): boolean {
  return formatStatus(raw) === 'PRODUZINDO';
}

function getMachineIcon(category: string | undefined): string {
  const cat = String(category || '').toLowerCase();
  if (cat.includes('cnc') || cat.includes('torno')) return 'precision_manufacturing';
  if (cat.includes('solda') || cat.includes('weld')) return 'whatshot';
  if (cat.includes('prensa')) return 'compress';
  if (cat.includes('corte') || cat.includes('laser')) return 'content_cut';
  return 'settings_suggest';
}

let ws: WebSocket | null = null;
let reconnectTimer: NodeJS.Timeout | null = null;

function connectWebSocket() {
  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
  const wsBase = apiBase.replace(/^http/, 'ws').replace('/api/v1', '');
  
  // Cria um ID diferente da EmployeesPage para não dar conflito se você abrir as duas abas
  const plantId = 98000 + Math.floor(Math.random() * 999);
  const wsUrl = `${wsBase}/ws/${plantId}`; 
  
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
      console.log('🟢 [PLANTA] Supervisório conectado ao tempo real!');
      if (reconnectTimer) clearTimeout(reconnectTimer);
  };

  ws.onmessage = (event) => {
      try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'MACHINE_STATE_CHANGED') {
              console.log(`⚡ [PLANTA] Máquina ${data.machine_id} mudou! Atualizando mapa...`);
              
              // MÁGICA: Acha o card da máquina no mapa e pinta a borda instantaneamente!
              const machineIndex = store.machinesList.findIndex(m => m.id === Number(data.machine_id));
              if (machineIndex !== -1) {
                  store.machinesList[machineIndex].status = data.machine_status_db || data.new_status;
              } else {
                  // Prevenção de erro: Se a máquina não estiver no mapa, busca tudo do servidor
                  store.fetchAvailableMachines();
              }
          }
      } catch (error) {
          console.error('Erro ao ler o WebSocket no Supervisório:', error);
      }
  };

  ws.onclose = () => {
      console.warn('🟡 [PLANTA] Conexão perdida. Tentando reconectar...');
      reconnectTimer = setTimeout(connectWebSocket, 5000);
  };
}

// =========================================================================
// CICLO DE VIDA 
// =========================================================================
onMounted(async () => {
  $q.loading.show();
  await store.fetchAvailableMachines();
  $q.loading.hide();

  // Liga a escuta em tempo real em vez do relógio bobo!
  connectWebSocket();
});

onUnmounted(() => {
  // Desliga tudo quando sair da página do Mapa
  if (ws) {
      ws.onclose = null;
      ws.close();
  }
  if (reconnectTimer) {
      clearTimeout(reconnectTimer);
  }
});
</script>

<style lang="scss" scoped>
/* -------------------------------------------------------------------------
   MALHA (PAPEL MILIMETRADO DE ENGENHARIA)
   ------------------------------------------------------------------------- */
.blueprint-container {
  background-color: #f8fafc;
  /* Cria uma grade usando Gradientes (Mágica do CSS) */
  background-image: 
    linear-gradient(rgba(18, 140, 126, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(18, 140, 126, 0.05) 1px, transparent 1px),
    linear-gradient(rgba(18, 140, 126, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(18, 140, 126, 0.1) 1px, transparent 1px);
  background-size: 20px 20px, 20px 20px, 100px 100px, 100px 100px;
  background-position: -1px -1px, -1px -1px, -1px -1px, -1px -1px;
  
  border: 2px solid rgba(18, 140, 126, 0.2);
  min-height: 600px;
}

/* -------------------------------------------------------------------------
   ESTACIONAMENTO DE MÁQUINAS (DOCK)
   ------------------------------------------------------------------------- */
.unplaced-dock {
  position: absolute;
  bottom: 20px;
  left: 20px;
  border-radius: 8px;
  border: 1px dashed rgba(0,0,0,0.2);
  z-index: 10;
  max-width: 60%;
  overflow-x: auto;
}

.dock-card {
  width: 80px;
  height: 40px;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  cursor: grab;
  
  .machine-id { font-size: 10px; font-weight: bold; color: #666; }
  .machine-model { font-size: 11px; max-width: 70px; }
}

/* -------------------------------------------------------------------------
   O CARD DA MÁQUINA (DIGITAL TWIN)
   ------------------------------------------------------------------------- */
.machine-card {
  user-select: none; /* Evita que o texto seja selecionado ao arrastar */
}

.map-card {
  position: absolute;
  width: 125px; /* Um pouco mais largo para ajudar com nomes longos */
  min-height: 115px; /* Em vez de altura fixa, usamos altura mínima */
  height: fit-content; /* Cresce automaticamente se o texto for gigante */
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(5px);
  border-radius: 12px;
  border: 3px solid #ccc;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  z-index: 2;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-5px) scale(1.05);
    z-index: 5; 
  }
}
.edit-mode-active {
  cursor: grab !important;
  &:active { cursor: grabbing !important; }
}

.card-header {
  padding: 4px 6px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  
  .machine-id-badge {
    background: #333; color: white;
    font-size: 10px; font-weight: 800;
    padding: 2px 6px; border-radius: 12px;
  }
  
  .remove-btn { color: #f44336; margin-top: -2px; margin-right: -2px; }
}

.card-body {
  flex-grow: 1;
  padding: 5px;
  color: #334e4b;

  .machine-model {
    font-size: 0.70rem; /* Fonte levemente menor para encaixar melhor */
    display: -webkit-box;
    -webkit-line-clamp: 3; /* Limite máximo de 3 linhas */
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.2;
    margin-top: 2px;
  }
}

.card-footer {
  /* Removemos o fundo cinza claro para usar as cores sólidas */
  border-top: 1px solid rgba(0,0,0,0.05);
  padding: 5px;
  border-bottom-left-radius: 9px;
  border-bottom-right-radius: 9px;
  
  .status-label { 
    font-size: 0.6rem; 
    letter-spacing: 0.5px; 
    color: white; /* Letra branca para dar contraste com os fundos coloridos */
  }
}
/* -------------------------------------------------------------------------
   CORES DE STATUS (A Borda e a Sombra)
   ------------------------------------------------------------------------- */
.status-green {
  border-color: #4CAF50;
  .card-footer { background-color: #4CAF50; }
}
.status-blue {
  border-color: #2196F3;
  .card-footer { background-color: #2196F3; }
}
.status-purple {
  border-color: #9C27B0;
  .card-footer { background-color: #9C27B0; }
}
.status-orange {
  border-color: #FF9800;
  .card-footer { background-color: #FF9800; }
}
.status-red {
  border-color: #F44336;
  .card-footer { background-color: #F44336; }
}
.status-brown {
  border-color: #4E342E; /* Usando o equivalente HEX ao brown-8 do Quasar */
  .card-footer { background-color: #4E342E; }
}

/* -------------------------------------------------------------------------
   EFEITO DE PULSO (MÁQUINA TRABALHANDO)
   ------------------------------------------------------------------------- */
.pulse-effect {
  animation: machine-pulse 2s infinite;
}
.status-grey {
  border-color: #9E9E9E;
  .card-footer { background-color: #9E9E9E; }
}
@keyframes machine-pulse {
  0% { box-shadow: 0 0 0 0 rgba(18, 140, 126, 0.4); }
  70% { box-shadow: 0 0 0 15px rgba(18, 140, 126, 0); }
  100% { box-shadow: 0 0 0 0 rgba(18, 140, 126, 0); }
}

/* Utilitários */
.opacity-80 { opacity: 0.8; }
.text-truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Animação Vue Transition Group */
.fade-enter-active, .fade-leave-active { transition: opacity 0.5s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
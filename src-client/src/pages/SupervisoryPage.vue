<template>
  <q-page class="q-pa-none overflow-hidden bg-grey-1" style="min-height: calc(100vh - 50px) !important; height: calc(100vh - 50px) !important;">
    
    <div 
      class="viewport-container absolute-full bg-grey-1"
      ref="viewportRef"
      @mousedown="startPan" 
      @mousemove="onPan" 
      @mouseup="endPan" 
      @mouseleave="endPan"
      @wheel.prevent="onWheel"
      @dragover.prevent
      @drop="onDrop"
      :style="{ cursor: isPanning ? 'grabbing' : (isEditMode ? 'grab' : 'default') }"
    >
      <div class="absolute-top-left q-pa-md" style="z-index: 100;">
        <q-btn
          :color="isEditMode ? 'orange-9' : 'teal-8'"
          :icon="isEditMode ? 'lock_open' : 'lock'"
          :label="isEditMode ? 'Finalizar Edição' : 'Editar Layout'"
          :outline="!isEditMode"
          class="shadow-4 font-weight-bold transition-all bg-white"
          @click="toggleEditMode"
        >
          <q-tooltip v-if="!isEditMode">Destravar para arrastar máquinas</q-tooltip>
        </q-btn>
      </div>

      <div class="zoom-controls-panel shadow-4 bg-white rounded-borders q-pa-xs">
        <q-btn flat round dense icon="add" color="teal-9" @click="zoomIn">
          <q-tooltip>Aproximar</q-tooltip>
        </q-btn>
        <q-separator />
        <q-btn flat round dense icon="remove" color="teal-9" @click="zoomOut">
          <q-tooltip>Afastar</q-tooltip>
        </q-btn>
        <q-separator />
        <q-btn flat round dense icon="filter_center_focus" color="primary" @click="resetView">
          <q-tooltip>Centralizar Mapa</q-tooltip>
        </q-btn>
      </div>

      <div 
        class="blueprint-canvas"
        ref="mapAreaRef"
        :style="{ 
          transform: `translate(${panX}px, ${panY}px) scale(${scale})`,
          width: '4000px', 
          height: '4000px'
        }"
      >
        <transition-group name="fade">
          <div 
            v-for="machine in placedMachines" 
            :key="machine.id"
            class="machine-card map-card shadow-5"
            :class="[
               getStatusColorClass(machine.status), 
               { 'edit-mode-active': isEditMode, 'pulse-effect': isRunning(machine.status) }
            ]"
            :style="{ left: `${machine.layout_x}%`, top: `${machine.layout_y}%` }"
            :draggable="isEditMode"
            @dragstart.stop="onDragStart($event, machine)"
            @click="goToMachineDetails(machine.id)"
          >
            <div class="card-header absolute-top row items-center justify-between no-wrap">
              <div class="machine-id-badge shadow-2">{{ machine.id }}</div>
              <q-btn v-if="isEditMode" round dense flat icon="close" size="xs" class="remove-btn shadow-2" @click.stop="removeMachineFromMap(machine)" />
            </div>

            <div class="card-body">
              <div v-if="machine.photo_url" class="machine-bg-layer" :style="{ backgroundImage: `url(${getImageUrl(machine.photo_url)})` }"></div>
              <div v-if="machine.photo_url" class="machine-gradient-overlay"></div>

              <div class="card-content-layer column items-center">
                <q-icon v-if="!machine.photo_url" :name="getMachineIcon(machine.category)" size="32px" class="q-mb-sm opacity-60 text-teal-8" />
                <div class="machine-model text-weight-bolder text-center full-width" :class="machine.photo_url ? 'text-white' : 'text-teal-10'">
                  {{ machine.model }}
                </div>
                <div class="machine-brand text-caption text-center full-width" :class="machine.photo_url ? 'text-grey-4' : 'text-grey-7'">
                  {{ machine.brand }}
                </div>
              </div>
            </div>

            <div class="card-footer text-center q-pt-xs">
              <span class="status-label text-weight-bold text-uppercase">{{ formatStatus(machine.status) }}</span>
            </div>
          </div>
        </transition-group>
      </div> <div 
        v-if="unplacedMachines.length > 0 && isEditMode"
        class="unplaced-dock shadow-4 bg-white q-pa-sm"
      >
        <div class="text-caption text-weight-bold text-grey-8 q-mb-xs">Máquinas na Doca (Arraste):</div>
        <div class="row q-gutter-sm">
          <div 
            v-for="machine in unplacedMachines" 
            :key="machine.id"
            class="machine-card dock-card text-center"
            draggable="true"
            @dragstart="onDragStart($event, machine)"
          >
            <q-avatar v-if="machine.photo_url" rounded size="26px" class="q-mb-xs shadow-1">
              <img :src="getImageUrl(machine.photo_url)" style="object-fit: cover;" />
            </q-avatar>
            <div v-else class="machine-id">{{ machine.id }}</div>
            <div class="machine-model text-truncate full-width q-px-xs" style="font-size: 0.6rem;">{{ machine.model }}</div>
          </div>
        </div>
      </div>

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
const isPanning = ref(false);
const panX = ref(0);
const panY = ref(0);
const scale = ref(0.85); 
let startMouseX = 0;
let startMouseY = 0;
const mapAreaRef = ref<HTMLElement | null>(null);
const isEditMode = ref(false);

const viewportRef = ref<HTMLElement | null>(null);

function centerMap() {

  const centerCanvasX = 2000;
  const centerCanvasY = 2000;

  const viewWidth = viewportRef.value ? viewportRef.value.clientWidth : window.innerWidth;
  const viewHeight = viewportRef.value ? viewportRef.value.clientHeight : window.innerHeight;

  panX.value = (viewWidth / 2) - (centerCanvasX * scale.value);
  panY.value = (viewHeight / 2) - (centerCanvasY * scale.value);
}

let draggedMachine: Machine | null = null;

function zoomIn() { scale.value = Math.min(scale.value + 0.1, 2.5); }
function zoomOut() { scale.value = Math.max(scale.value - 0.1, 0.3); }
function resetView() { 
  scale.value = 0.85; 
  centerMap(); 
}

const placedMachines = computed(() => {
  return store.machinesList.filter(m => m.layout_x != null && m.layout_y != null);
});

const unplacedMachines = computed(() => {
  return store.machinesList.filter(m => m.layout_x == null || m.layout_y == null);
});


function onWheel(event: WheelEvent) {

  if (event.deltaY > 0) zoomOut();
  else zoomIn();
}

function startPan(event: MouseEvent) {
  if ((event.target as HTMLElement).closest('.machine-card') || 
      (event.target as HTMLElement).closest('.unplaced-dock') ||
      (event.target as HTMLElement).closest('.zoom-controls-panel') ||
      (event.target as HTMLElement).closest('.q-btn')) return;
  
  isPanning.value = true;
  startMouseX = event.clientX - panX.value;
  startMouseY = event.clientY - panY.value;
}

function onPan(event: MouseEvent) {
  if (!isPanning.value) return;
  panX.value = event.clientX - startMouseX;
  panY.value = event.clientY - startMouseY;
}

function endPan() {
  isPanning.value = false;
}

function getImageUrl(url: string | null | undefined) { 
  if (!url) return ''; 
  

  const fixedUrl = url.replace(/\\/g, '/');

  if (fixedUrl.startsWith('http')) return fixedUrl; 

  const cleanUrl = fixedUrl.startsWith('/') ? fixedUrl : `/${fixedUrl}`;

  const host = window.location.hostname;
  return `http://${host}:8000${cleanUrl}`; 
}
function toggleEditMode() {
  isEditMode.value = !isEditMode.value;
  if (!isEditMode.value) {
    $q.notify({ type: 'positive', message: 'Layout Travado e Salvo com Sucesso!', icon: 'lock' });
  } else {
    $q.notify({ type: 'info', message: 'Modo de Edição Ativado. Arraste as máquinas.', icon: 'open_with' });
  }
}

let dragOffsetX = 0;
let dragOffsetY = 0;

function onDragStart(event: DragEvent, machine: Machine) {
  if (!isEditMode.value) {
    event.preventDefault(); 
    return;
  }
  draggedMachine = machine;


  const target = (event.target as HTMLElement).closest('.machine-card');
  if (target && event.clientX) {
     const rect = target.getBoundingClientRect();

     dragOffsetX = (event.clientX - rect.left) / scale.value;
     dragOffsetY = (event.clientY - rect.top) / scale.value;
  } else {
     dragOffsetX = 70;
     dragOffsetY = 65;
  }

  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    const emptyImage = new Image();
    emptyImage.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
    event.dataTransfer.setDragImage(emptyImage, 0, 0);
  }
}

async function onDrop(event: DragEvent) {
  if (!isEditMode.value || !draggedMachine || !mapAreaRef.value) return;

  const canvasRect = mapAreaRef.value.getBoundingClientRect();
  

  let rawX = (event.clientX - canvasRect.left) / scale.value;
  let rawY = (event.clientY - canvasRect.top) / scale.value;

  rawX -= dragOffsetX;
  rawY -= dragOffsetY;


  let percentX = (rawX / 4000) * 100;
  let percentY = (rawY / 4000) * 100;


  percentX = Math.max(0, Math.min(percentX, 98));
  percentY = Math.max(0, Math.min(percentY, 98));

  await store.saveMachineLayout(draggedMachine.id, Number(percentX.toFixed(3)), Number(percentY.toFixed(3)));
  draggedMachine = null;
}
async function removeMachineFromMap(machine: Machine) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  await store.saveMachineLayout(machine.id, null as any, null as any);
  $q.notify({ type: 'warning', message: `${machine.model} voltou para a doca.`, timeout: 1000 });
}



function goToMachineDetails(machineId: number) {
  if (isEditMode.value) return; 
  void router.push(`/employees?machine=${machineId}`);
}

function formatStatus(raw: string | undefined): string {
  if (!raw) return 'DESCONHECIDO';
  const s = raw.toUpperCase();
  

  if (s.includes('AUTÔNOM') || s.includes('AUTONOMOUS')) return 'AUTÔNOMO';
  if (s.includes('USO') || s.includes('RUNNING') || s.includes('OPERAÇÃO') || s.includes('PRODUCING')) return 'OPERAÇÃO';
  if (s.includes('MANUTEN') || s.includes('MAINTENANCE') || s.includes('BROKEN')) return 'MANUTENÇÃO';
  if (s.includes('SETUP') || s.includes('PREPARA')) return 'SETUP';
  
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

    case 'OCIOSO': return 'status-grey'; 
    
    case 'PARADA': return 'status-orange'; 
    case 'MANUTENÇÃO': return 'status-red';
    default: return 'status-grey'; 
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
              
              const machineIndex = store.machinesList.findIndex(m => m.id === Number(data.machine_id));
              if (machineIndex !== -1) {
                  store.machinesList[machineIndex].status = data.machine_status_db || data.new_status;
              } else {
                  void store.fetchAvailableMachines();
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


onMounted(async () => {
  $q.loading.show();
  await store.fetchAvailableMachines();
  $q.loading.hide();


  connectWebSocket();
});

onUnmounted(() => {

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

.zoom-controls-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(18, 140, 126, 0.2);
}

.viewport-container {
  background-color: #f8fafc;
  
  border: none !important;
  outline: none !important;
  margin: 0;
  padding: 0;
}

.blueprint-canvas {
  position: absolute;
  top: 0;
  left: 0;
  transform-origin: top left;
  
  background-image: 
    linear-gradient(rgba(18, 140, 126, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(18, 140, 126, 0.05) 1px, transparent 1px),
    linear-gradient(rgba(18, 140, 126, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(18, 140, 126, 0.1) 1px, transparent 1px);
  background-size: 20px 20px, 20px 20px, 100px 100px, 100px 100px;
  
  transition: transform 0.05s linear; 
}


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
  height: 80px;
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


.machine-card {
  user-select: none; 
}

.map-card {
  position: absolute;
  width: 160px; 
  min-height: 200px; 
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(5px);
  border-radius: 12px;
  border: 3px solid #ccc;
  transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s;
  display: flex;
  flex-direction: column;
  z-index: 2;
  cursor: pointer;
  overflow: hidden;
  
  &:hover {
    transform: translateY(-5px) scale(1.03);
    box-shadow: 0 12px 24px rgba(0,0,0,0.2) !important;
    z-index: 5; 
    
    .machine-bg-layer {
      transform: scale(1.15); 
    }
  }
}

.edit-mode-active {
  cursor: grab !important;
  &:active { cursor: grabbing !important; }
}


.card-header {
  z-index: 10;
  padding: 6px;
  
  .machine-id-badge {
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(4px);
    color: #fff;
    font-size: 11px;
    font-weight: 900;
    padding: 3px 8px;
    border-radius: 6px;
  }
  
  .remove-btn { 
    background-color: #e53935;
    color: white;
  }
}


.card-body {
  flex-grow: 1;
  position: relative; 
  display: flex;
  flex-direction: column;
}

.machine-bg-layer {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.9; 
  z-index: 0;
  transition: transform 0.5s ease;
}


.machine-gradient-overlay {
  position: absolute;
  bottom: 0; left: 0; width: 100%; height: 75%;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.85) 0%, rgba(0, 0, 0, 0.5) 50%, transparent 100%);
  z-index: 1;
}


.card-content-layer {
  position: relative;
  z-index: 2; 
  flex-grow: 1;
  padding: 8px 6px;
  justify-content: flex-end; 
  
  .machine-model {
    font-size: 0.8rem;
    line-height: 1.1;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-shadow: 0px 1px 3px rgba(0,0,0,0.8); 
  }
  
  .machine-brand {
    font-size: 0.65rem;
    margin-top: 2px;
  }
}

.card-footer {
  border-top: 1px solid rgba(0,0,0,0.05);
  padding: 5px;
  position: relative;
  z-index: 10; 
  
  .status-label { 
    font-size: 0.65rem; 
    letter-spacing: 0.5px; 
    color: white; 
  }
}


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
  border-color: #4E342E; 
  .card-footer { background-color: #4E342E; }
}
.status-grey {
  border-color: #9E9E9E;
  .card-footer { background-color: #9E9E9E; }
}


.pulse-effect {
  animation: machine-pulse 2s infinite;
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
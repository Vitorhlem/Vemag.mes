/* eslint-disable @typescript-eslint/no-explicit-any */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { Notify, Loading } from 'quasar';
import { api } from 'boot/axios';

// --- INTERFACES ---
export interface Machine {
  id: number;
  brand: string;
  model: string;
  license_plate?: string;
  status?: string; 
  category?: string;
  current_driver_id?: number;
}

export interface OperationStep {
  seq: number;
  resource: string;
  name: string;
  description: string;
  timeEst: number;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'PAUSED';
}

export interface ProductionOrder {
  id: number;
  code: string;
  client?: string;
  product?: string;
  deliveryDate?: string;
  part_name: string;
  part_image_url: string;
  technical_drawing_url?: string; // <--- NOVO CAMPO PARA O DESENHO
  target_quantity: number;
  produced_quantity: number;
  scrap_quantity: number;
  status: 'PENDING' | 'SETUP' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'STOPPED' | 'IDLE' | 'MAINTENANCE' | 'AVAILABLE';
  steps?: OperationStep[];
  operations: Record<string, unknown>[]; 
}

export interface ProductionLog {
  id: number;
  event_type: string;
  timestamp: string;
  new_status?: string;
  reason?: string;
  details?: string;
  operator_name?: string;
}

export interface Operator {
  id: number;
  full_name: string;
  email: string;
  employee_id?: string;
  role?: string;
}

export const useProductionStore = defineStore('production', () => {
  
  // --- ESTADO ---
  const machinesList = ref<Machine[]>([]);
  const machineId = ref<number | null>(null);
  const currentMachine = ref<Machine | null>(null);
  const machineName = ref<string>('Não Configurado');
  const machineSector = ref<string>('-');

  const currentOperator = ref<Operator | null>(null);
  const currentOperatorBadge = ref<string | null>(null);
  
  const activeOrder = ref<ProductionOrder | null>(null);
  const currentStepIndex = ref<number>(-1);
  const machineHistory = ref<ProductionLog[]>([]);

  // --- DADOS MOCKADOS (Baseado na O.P. 3940/0 Real) ---
  const MOCK_OP_STEPS: OperationStep[] = [
      { 
        seq: 10, 
        resource: '2.13', 
        name: 'SUPORTE TÉCNICO DA QUALIDADE', 
        timeEst: 0.5, 
        status: 'PENDING', 
        description: `SUPORTE PARA MANGUEIRA DE DRENAGEM - DESENHO - 300232C-000-DW-5837-0002 - REV.0

1. MATÉRIA-PRIMA FORNECIMENTO VEMAG.
2. REALIZAR INSPEÇÃO DE RECEBIMENTO DA MATÉRIA-PRIMA.
3. REGISTRAR NÚMERO DA (O.P.).` 
      },
      { 
        seq: 20, 
        resource: '3.01', 
        name: 'OXICORTE', 
        timeEst: 2.0, 
        status: 'PENDING', 
        description: `1. OXICORTAR AS PEÇAS DE ACORDO COM AS ESPECÍFICAS ESPESSURAS DAS CHAPAS E PROGRAMA CNC.
2. IDENTIFICAR AS PEÇAS COM O NÚMERO DA (O.P.).` 
      },
      { 
        seq: 30, 
        resource: '3.05', 
        name: 'REBARBAÇÃO DE CALDEIRARIA', 
        timeEst: 0.5, 
        status: 'PENDING', 
        description: `1. REMOVER CAREPAS E REBARBAS DO OXICORTE.
2. DAR ACABAMENTO EM TODO O CONTORNO DAS PEÇAS ATRAVÉS DE ESMERILHAMENTOS.
3. MANTER O AUTO CONTROLE E A IDENTIFICAÇÕES DAS PEÇAS.` 
      },
      { 
        seq: 40, 
        resource: '4.10', 
        name: 'TRAÇAGEM', 
        timeEst: 1.0, 
        status: 'PENDING', 
        description: `(EXECUTAR AS TRAÇAGENS DAS COORDENADAS NAS CHAPAS OXICORTADAS, CONFORME OS RESPECTIVOS DESENHOS "DE")

NOTAS:
01- QUANTIDADES CONFORME DESENHO "DE"

ITENS POS. 4 - CHAPA OLHAL #5/8" x 40 mm x 50 mm x R20 mm - DESENHO - DE-1481.01.001
- (1x) TRAÇAR FURO PASSANTE (Ø15 mm)

ITENS POS. 1 - CHAPA #1/2" x 100 mm x 250 mm - DESENHO - DE-1481.01.002
- (4x) TRAÇAR FURO PASSANTE (Ø11 mm)

ITENS POS. 2 - CHAPA #3/4" x 670 mm x 930 mm - DESENHO - DE-1481.01.003
- (4x) TRAÇAR ROSCA PASSANTES (M10 x 1,5)

(MANTER AS IDENTIFICAÇÕES DAS PEÇAS).` 
      },
      { 
        seq: 50, 
        resource: '4.06', 
        name: 'RADIAL P', 
        timeEst: 2.0, 
        status: 'PENDING', 
        description: `(EXECUTAR AS FURAÇÕES DOS RESPECTIVOS ITENS ABAIXO, SEGUINDO AS MARCAÇÕES DAS TRAÇAGENS, CONFORME OS RESPECTIVOS DESENHOS "DE")

NOTAS:
01- QUANTIDADES CONFORME DESENHO "DE"` 
      }
  ];

  // --- GETTERS ---
  const isKioskConfigured = computed(() => !!machineId.value);
  const isShiftActive = computed(() => !!currentOperatorBadge.value);
  const hasActiveOrder = computed(() => !!activeOrder.value);
  
  const isRunning = computed(() => {
    return activeOrder.value?.status === 'RUNNING';
  });

  const currentActiveStep = computed(() => {
    if (!activeOrder.value?.steps || currentStepIndex.value === -1) return null;
    return activeOrder.value.steps[currentStepIndex.value];
  });
  
  const isMachineBroken = computed(() => {
      const rawStatus = currentMachine.value?.status || '';
      const status = String(rawStatus).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      return status.includes('maintenance') || status.includes('broken') || status.includes('manutencao') || status.includes('manutenção');
  });

  // --- ACTIONS ---

  function _setMachineData(data: Machine) {
    currentMachine.value = data;
    machineId.value = data.id;
    machineName.value = `${data.brand} ${data.model}`;
    machineSector.value = data.category || 'Geral';
  }

  async function loadKioskConfig() {
    const savedId = localStorage.getItem('TRU_MACHINE_ID');
    if (savedId) {
      machineId.value = Number(savedId);
      try {
        const { data } = await api.get<Machine>(`/vehicles/${savedId}`);
        _setMachineData(data);
        checkActiveSession();
      } catch { console.warn('Máquina offline.'); }
    }
  }

  function checkActiveSession() {
      const savedOp = localStorage.getItem('TRU_CURRENT_OPERATOR');
      if (savedOp) {
          try {
              const op = JSON.parse(savedOp);
              currentOperator.value = op;
              currentOperatorBadge.value = op.email;
          } catch { localStorage.removeItem('TRU_CURRENT_OPERATOR'); }
      }
  }

  async function fetchAvailableMachines() {
    try {
      const { data } = await api.get<Machine[]>('/production/machines', { params: { limit: 100 } });
      machinesList.value = data;
    } catch (error) { console.error(error); Notify.create({ type: 'negative', message: 'Erro ao buscar máquinas.' }); }
  }

  async function configureKiosk(id: number) {
    try {
      const { data } = await api.get<Machine>(`/vehicles/${id}`);
      _setMachineData(data);
      localStorage.setItem('TRU_MACHINE_ID', String(data.id));
      Notify.create({ type: 'positive', message: 'Terminal Configurado!' });
    } catch { Notify.create({ type: 'negative', message: 'Erro ao configurar terminal.' }); }
  }

  async function setMachineStatus(status: string) {
    if (currentMachine.value) {
        const label = status === 'MAINTENANCE' ? "Em manutenção" : (status === 'AVAILABLE' ? "Disponível" : status);
        currentMachine.value = { ...currentMachine.value, status: label };
    }
    try { await api.post('/production/machine/status', { machine_id: machineId.value, status: status }); } catch (error) { console.error('Erro status', error); }
  }

  async function fetchMachineHistory(id: number, params: { skip?: number, limit?: number, event_type?: string | null | undefined } = {}) {
    try {
      const q = new URLSearchParams();
      if (params.skip) q.append('skip', String(params.skip));
      if (params.limit) q.append('limit', String(params.limit));
      if (params.event_type) q.append('event_type', params.event_type);
      const { data } = await api.get<ProductionLog[]>(`/production/history/${id}?${q.toString()}`);
      machineHistory.value = data;
      return data;
    } catch (error) { console.error('Erro history', error); return []; }
  }

  async function loginOperator(scannedCode: string) {
    if (!machineId.value) return;
    Loading.show({ message: 'Validando...' });
    try {
      const { data: users } = await api.get('/users/', { params: { limit: 1000 } });
      const cleanCode = scannedCode.trim();
      const cleanCodeNoZeros = cleanCode.replace(/^0+/, '');
      
      const operator = users.find((u: any) => {
        if (u.employee_id && String(u.employee_id).trim() === cleanCode) return true;
        if (String(u.id) === cleanCode || String(u.id) === cleanCodeNoZeros) return true;
        if (u.email && u.email.toLowerCase() === cleanCode.toLowerCase()) return true;
        return false;
      });

      if (!operator) {
        Notify.create({ type: 'negative', message: `Crachá ${cleanCode} não encontrado.` });
        return;
      }

      await api.post('/production/event', {
        machine_id: machineId.value,
        operator_badge: operator.email,
        event_type: 'LOGIN',
        new_status: 'IDLE',
        reason: 'Início de Turno'
      });

      currentOperator.value = operator;
      currentOperatorBadge.value = operator.email;
      localStorage.setItem('TRU_CURRENT_OPERATOR', JSON.stringify(operator));
      
      if (!isMachineBroken.value && currentMachine.value) {
          currentMachine.value = { ...currentMachine.value, status: 'Disponível' };
      }
      
      Notify.create({ type: 'positive', message: `Olá, ${operator.full_name.split(' ')[0]}!` });

    } catch (error) { console.error(error); Notify.create({ type: 'negative', message: 'Erro login.' }); } finally { Loading.hide(); }
  }

  async function logoutOperator(overrideStatus?: string) {
    if (!machineId.value || !currentOperatorBadge.value) return;
    let statusToSend = 'AVAILABLE';
    let visualStatus = 'Disponível';
    if (overrideStatus === 'MAINTENANCE' || isMachineBroken.value) {
        statusToSend = 'MAINTENANCE';
        visualStatus = 'Em manutenção';
    }
    try {
      await api.post('/production/event', {
        machine_id: machineId.value,
        operator_badge: currentOperatorBadge.value,
        event_type: 'LOGOUT',
        new_status: statusToSend, 
        reason: 'Logoff'
      });
      if (currentMachine.value) {
          currentMachine.value = { ...currentMachine.value, status: visualStatus };
      }
    } catch (error) { console.error('Erro ao deslogar:', error); }
    currentOperator.value = null;
    currentOperatorBadge.value = null;
    activeOrder.value = null;
    currentStepIndex.value = -1;
    localStorage.removeItem('TRU_CURRENT_OPERATOR');
  }

  async function loadOrderFromQr(qrCode: string) {
    if (isMachineBroken.value) { Notify.create({ type: 'negative', message: 'Máquina em manutenção.' }); return; }
    try {
      Loading.show({ message: 'Carregando O.P...' });
      
      // TENTA BUSCAR DADOS REAIS
      let data: ProductionOrder;
      try {
          const res = await api.get<ProductionOrder>(`/production/orders/${qrCode}`);
          data = res.data;
      } catch {
          // SE FALHAR (para teste), usa o mock local com os dados da imagem
          console.warn("API falhou, usando mock local");
          data = {
              id: 999, code: qrCode, client: 'Technip Brasil', product: 'DEWATERING HOSE',
              deliveryDate: '15/10/2025', part_name: 'Suporte', 
              part_image_url: 'https://placehold.co/600x400/png',
              technical_drawing_url: 'https://placehold.co/800x600/008C7A/FFFFFF/png?text=DESENHO+TECNICO+VEMAG', // Mock da imagem
              target_quantity: 50, produced_quantity: 0, scrap_quantity: 0, 
              status: 'PENDING', operations: [], steps: []
          } as ProductionOrder;
      }
      
      if (!data.status) data.status = 'PENDING';
      
      // Carrega os steps detalhados se vier vazio
      if (!data.steps || data.steps.length === 0) {
          data.steps = JSON.parse(JSON.stringify(MOCK_OP_STEPS));
      }

      activeOrder.value = { ...data };
      currentStepIndex.value = 0;
      
      if (currentOperatorBadge.value && machineId.value) {
         await api.post('/production/session/start', {
            machine_id: machineId.value, operator_badge: currentOperatorBadge.value, order_code: qrCode
         });
      }
      Notify.create({ type: 'positive', message: 'O.P. Carregada!' });
    } catch { 
      Notify.create({ type: 'negative', message: 'Erro crítico ao carregar.' }); 
      activeOrder.value = null;
    } finally { Loading.hide(); }
  }

  async function startProduction() { 
      if (activeOrder.value) activeOrder.value = { ...activeOrder.value, status: 'RUNNING' };
      if (currentMachine.value) currentMachine.value = { ...currentMachine.value, status: 'Em uso' };
      await sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' }); 
  }

  async function pauseProduction(reason: string) { 
      if (activeOrder.value) activeOrder.value = { ...activeOrder.value, status: 'PAUSED' };
      if (currentMachine.value) currentMachine.value = { ...currentMachine.value, status: 'Parada' };
      await sendEvent('STATUS_CHANGE', { new_status: 'STOPPED', reason }); 
  }

  async function enterSetup() {
      if (activeOrder.value) activeOrder.value = { ...activeOrder.value, status: 'SETUP' };
      if (currentMachine.value) currentMachine.value = { ...currentMachine.value, status: 'Em manutenção' };
      await sendEvent('STATUS_CHANGE', { new_status: 'SETUP', reason: 'Setup Iniciado' });
  }

  function addProduction(qty: number, isScrap = false) {
    if (!activeOrder.value) return;
    const newGood = (activeOrder.value.produced_quantity || 0) + (isScrap ? 0 : qty);
    const newScrap = (activeOrder.value.scrap_quantity || 0) + (isScrap ? qty : 0);
    activeOrder.value = { ...activeOrder.value, produced_quantity: newGood, scrap_quantity: newScrap };
    void sendEvent('COUNT', { quantity_good: isScrap ? 0 : qty, quantity_scrap: isScrap ? qty : 0 });
  }

  function startStep(index: number) {
    if (activeOrder.value?.steps && activeOrder.value.steps[index]) {
      activeOrder.value.steps.forEach(s => { if (s.status === 'IN_PROGRESS') s.status = 'PAUSED'; });
      activeOrder.value.steps[index].status = 'IN_PROGRESS';
      currentStepIndex.value = index;
      if (currentMachine.value) currentMachine.value = { ...currentMachine.value, status: 'Em uso' };
      void sendEvent('STEP_START', { step: activeOrder.value.steps[index].name, new_status: 'RUNNING' });
    }
  }

  function pauseStep(reason: string) {
    if (activeOrder.value?.steps && currentStepIndex.value > -1) {
        const step = activeOrder.value.steps[currentStepIndex.value];
        if (step) {
            step.status = 'PAUSED';
            if (currentMachine.value) currentMachine.value = { ...currentMachine.value, status: 'Parada' };
            void sendEvent('STEP_PAUSE', { step: step.name, reason: reason, new_status: 'STOPPED' });
        }
    }
  }

  function finishStep(index: number) {
    if (activeOrder.value?.steps && activeOrder.value.steps[index]) {
      activeOrder.value.steps[index].status = 'COMPLETED';
      void sendEvent('STEP_COMPLETE', { step: activeOrder.value.steps[index].name });
      const nextIndex = activeOrder.value.steps.findIndex(s => s.status === 'PENDING');
      if (nextIndex !== -1) {
          currentStepIndex.value = nextIndex;
          Notify.create({ type: 'positive', message: 'Etapa concluída!' });
      } else {
          currentStepIndex.value = -1;
          if (currentMachine.value) currentMachine.value = { ...currentMachine.value, status: 'Disponível' };
          Notify.create({ type: 'positive', message: 'Roteiro Finalizado!' });
      }
    }
  }

  async function finishSession() {
    if (!machineId.value || !currentOperatorBadge.value) return;
    try {
      Loading.show();
      await api.post('/production/session/stop', { machine_id: machineId.value, operator_badge: currentOperatorBadge.value });
      activeOrder.value = null; 
      Notify.create({ type: 'positive', message: 'Sessão Finalizada.' });
    } catch { Notify.create({ type: 'negative', message: 'Erro ao finalizar.' }); } finally { Loading.hide(); }
  }

  async function createMaintenanceOrder(notes: string) {
      if (!machineId.value) return;
      try {
          Loading.show();
          const payload = { vehicle_id: machineId.value, problem_description: `Kiosk: ${notes}`, category: 'Mecânica', maintenance_type: 'CORRETIVA' };
          await api.post('/maintenance/requests', payload);
          if(currentMachine.value) currentMachine.value = { ...currentMachine.value, status: 'Em manutenção' };
          Notify.create({ type: 'positive', icon: 'build_circle', message: 'O.M. Criada!' });
      } catch (error: any) { 
          console.error(error);
          Notify.create({ type: 'negative', message: 'Erro O.M.' }); 
      } finally { Loading.hide(); }
  }

  async function sendEvent(type: string, payload: Record<string, unknown> = {}) {
    if (!machineId.value || !currentOperatorBadge.value) return;
    try { await api.post('/production/event', { machine_id: machineId.value, operator_badge: currentOperatorBadge.value, order_code: activeOrder.value?.code, event_type: type, ...payload }); } catch (e) { console.error('Falha sync', e); }
  }

  function triggerAndon(sector: string, notes = '') {
    if (!machineId.value || !currentOperatorBadge.value) return;
    void api.post('/production/andon', { machine_id: machineId.value, operator_badge: currentOperatorBadge.value, sector: sector, notes: notes });
    Notify.create({ type: 'warning', icon: 'campaign', message: `Chamado: ${sector}` });
  }

  return {
    machinesList, machineId, currentMachine, machineName, machineSector,
    currentOperator, currentOperatorBadge, activeOrder, machineHistory,
    currentStepIndex, currentActiveStep,
    isKioskConfigured, isShiftActive, isMachineBroken, isRunning, hasActiveOrder,
    loadKioskConfig, _setMachineData, setMachineStatus,
    fetchAvailableMachines, configureKiosk, fetchMachineHistory,
    loginOperator, logoutOperator, loadOrderFromQr, finishSession,
    createMaintenanceOrder, sendEvent, triggerAndon,
    startStep, pauseStep, finishStep, 
    startProduction, pauseProduction, enterSetup, addProduction 
  };
});
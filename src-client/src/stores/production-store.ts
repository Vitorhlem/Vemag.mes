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

// Interface para o Operador
export interface Operator {
  id: number;
  full_name: string;
  email: string;
  employee_id?: string; // <--- CAMPO IMPORTANTE DO CRACHÁ
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

  // --- DADOS MOCKADOS ---
  const MOCK_OP_STEPS: OperationStep[] = [
      { seq: 10, resource: '2.13', name: 'SUPORTE TÉCNICO', timeEst: 0.5, status: 'PENDING', description: 'Inspeção de recebimento.' },
      { seq: 20, resource: '3.01', name: 'OXICORTE', timeEst: 2.0, status: 'PENDING', description: 'Corte conforme programa CNC.' },
      { seq: 30, resource: '3.05', name: 'CALDEIRARIA', timeEst: 0.5, status: 'PENDING', description: 'Acabamento.' },
      { seq: 40, resource: '4.10', name: 'TRAÇAGEM', timeEst: 1.0, status: 'PENDING', description: 'Traçagem de coordenadas.' },
      { seq: 50, resource: '4.06', name: 'FURAÇÃO RADIAL', timeEst: 2.0, status: 'PENDING', description: 'Execução de furos.' }
  ];

  // --- GETTERS ---
  const isKioskConfigured = computed(() => !!machineId.value);
  const isShiftActive = computed(() => !!currentOperatorBadge.value);
  const hasActiveOrder = computed(() => !!activeOrder.value);
  
  const isRunning = computed(() => {
    return activeOrder.value?.steps?.some(s => s.status === 'IN_PROGRESS') ?? false;
  });

  const currentActiveStep = computed(() => {
    if (!activeOrder.value?.steps || currentStepIndex.value === -1) return null;
    return activeOrder.value.steps[currentStepIndex.value];
  });
  
  const isMachineBroken = computed(() => {
      const rawStatus = currentMachine.value?.status || '';
      const status = String(rawStatus)
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
      
      return status.includes('maintenance') || 
             status.includes('broken') || 
             status.includes('manutencao') || 
             status.includes('manutenção');
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
        // Tenta restaurar sessão do operador se houver
        checkActiveSession();
      } catch {
        console.warn('Máquina salva offline ou removida.');
      }
    }
  }

  // Restaura sessão do localStorage
  function checkActiveSession() {
      const savedOp = localStorage.getItem('TRU_CURRENT_OPERATOR');
      if (savedOp) {
          try {
              const op = JSON.parse(savedOp);
              currentOperator.value = op;
              currentOperatorBadge.value = op.email;
              console.log('Sessão restaurada:', op.full_name);
          } catch {
              localStorage.removeItem('TRU_CURRENT_OPERATOR');
          }
      }
  }

  async function fetchAvailableMachines() {
    try {
      const { data } = await api.get<Machine[]>('/production/machines', { 
          params: { limit: 100 } 
      });
      machinesList.value = data;
    } catch (error) {
      console.error(error);
      Notify.create({ type: 'negative', message: 'Erro ao buscar lista de máquinas.' });
    }
  }

  async function configureKiosk(id: number) {
    try {
      const { data } = await api.get<Machine>(`/vehicles/${id}`);
      _setMachineData(data);
      localStorage.setItem('TRU_MACHINE_ID', String(data.id));
      Notify.create({ type: 'positive', message: 'Terminal Configurado!' });
    } catch {
      Notify.create({ type: 'negative', message: 'Erro ao configurar terminal.' });
    }
  }

  async function setMachineStatus(status: string) {
    if (currentMachine.value) {
        if (status === 'MAINTENANCE') currentMachine.value.status = "Em manutenção"; 
        else if (status === 'AVAILABLE') currentMachine.value.status = "Disponível";
        else currentMachine.value.status = status;
    }
    
    try {
       await api.post('/production/machine/status', {
           machine_id: machineId.value,
           status: status
       });
    } catch (error) { console.error('Erro ao salvar status', error); }
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
    } catch (error) {
      console.error('Erro history', error);
      return [];
    }
  }

  // --- LOGIN DO OPERADOR (CORRIGIDO PARA LER O CAMPO employee_id) ---
  async function loginOperator(scannedCode: string) {
    if (!machineId.value) return;
    
    Loading.show({ message: 'Validando Operador...' });
    try {
      const { data: users } = await api.get('/users/', { params: { limit: 1000 } });
      
      const cleanCode = scannedCode.trim();
      const cleanCodeNoZeros = cleanCode.replace(/^0+/, ''); // Remove zeros à esquerda (ex: "0010" -> "10")
      
      console.log(`[LOGIN] Buscando crachá: "${cleanCode}"`);
      
      const operator = users.find((u: any) => {
        // 1. Verifica pelo campo employee_id (Matrícula/Crachá) - Prioridade Máxima
        if (u.employee_id && String(u.employee_id).trim() === cleanCode) {
            return true;
        }
        
        // 2. Fallback: Verifica pelo ID numérico do banco
        if (String(u.id) === cleanCode || String(u.id) === cleanCodeNoZeros) {
            return true;
        }
        
        // 3. Fallback: Verifica por email
        if (u.email && u.email.toLowerCase() === cleanCode.toLowerCase()) return true;
        
        return false;
      });

      if (!operator) {
        Notify.create({ 
            type: 'negative', 
            message: `Crachá ${cleanCode} não encontrado.`,
            caption: 'Verifique se a matrícula (employee_id) está cadastrada.'
        });
        return;
      }

      await api.post('/production/event', {
        machine_id: machineId.value,
        operator_badge: operator.email, // Backend usa email para identificar
        event_type: 'LOGIN',
        new_status: 'IDLE',
        reason: 'Início de Turno'
      });

      currentOperator.value = operator;
      currentOperatorBadge.value = operator.email;
      
      // Persiste sessão
      localStorage.setItem('TRU_CURRENT_OPERATOR', JSON.stringify(operator));
      
      if (!isMachineBroken.value && currentMachine.value) {
          currentMachine.value.status = 'Disponível';
      }
      
      Notify.create({ 
        type: 'positive', 
        message: `Bem-vindo, ${operator.full_name.split(' ')[0]}!` 
      });

    } catch (error) {
      console.error(error);
      Notify.create({ type: 'negative', message: 'Erro de conexão no login.' });
    } finally {
      Loading.hide();
    }
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
          currentMachine.value.status = visualStatus;
      }
      
    } catch (error) { console.error('Erro ao deslogar:', error); }
    
    currentOperator.value = null;
    currentOperatorBadge.value = null;
    activeOrder.value = null;
    currentStepIndex.value = -1;
    localStorage.removeItem('TRU_CURRENT_OPERATOR'); // Limpa persistência
  }

  async function loadOrderFromQr(qrCode: string) {
    if (isMachineBroken.value) {
        Notify.create({ type: 'negative', message: 'Máquina em manutenção. Necessário liberar.' });
        return;
    }

    try {
      Loading.show({ message: 'Carregando O.P...' });
      
      const mockData: ProductionOrder = {
          id: 999,
          code: qrCode,
          client: 'Technip Brasil Engenharia',
          product: 'DEWATERING HOSE SUPPORT',
          deliveryDate: '15/10/2025',
          part_name: 'Suporte',
          part_image_url: '',
          target_quantity: 50,
          produced_quantity: 0,
          scrap_quantity: 0,
          status: 'PENDING',
          operations: [],
          steps: JSON.parse(JSON.stringify(MOCK_OP_STEPS))
      };

      activeOrder.value = mockData;
      currentStepIndex.value = 0;
      
      if (currentOperatorBadge.value && machineId.value) {
         await api.post('/production/session/start', {
            machine_id: machineId.value,
            operator_badge: currentOperatorBadge.value,
            order_code: qrCode
         });
      }
      Notify.create({ type: 'positive', message: 'O.P. Carregada com Roteiro!' });
    } catch { 
      Notify.create({ type: 'negative', message: 'Erro ao carregar O.P.' });
    } finally {
      Loading.hide();
    }
  }

  function startStep(index: number) {
    if (activeOrder.value?.steps && activeOrder.value.steps[index]) {
      activeOrder.value.steps.forEach(s => {
        if (s.status === 'IN_PROGRESS') s.status = 'PAUSED';
      });
      
      activeOrder.value.steps[index].status = 'IN_PROGRESS';
      currentStepIndex.value = index;
      
      if (currentMachine.value) currentMachine.value.status = 'Em uso';
      
      void sendEvent('STEP_START', { step: activeOrder.value.steps[index].name, new_status: 'RUNNING' });
    }
  }

  function pauseStep(reason: string) {
    // Verificação robusta para garantir que activeOrder e steps existem
    if (activeOrder.value?.steps && currentStepIndex.value > -1) {
      const step = activeOrder.value.steps[currentStepIndex.value];
      
      if (step) {
        step.status = 'PAUSED';
        if (currentMachine.value) currentMachine.value.status = 'Parada';
        
        // Logs para Debug
        console.log(`[STORE] Passo pausado: ${step.name}. Motivo: ${reason}`);
        
        void sendEvent('STEP_PAUSE', { 
            step: step.name, 
            reason: reason, 
            new_status: 'STOPPED' 
        });
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
          Notify.create({ type: 'positive', message: 'Etapa concluída! Próxima liberada.' });
      } else {
          currentStepIndex.value = -1;
          if (currentMachine.value) currentMachine.value.status = 'Disponível';
          Notify.create({ type: 'positive', message: 'Roteiro de Produção Finalizado!' });
      }
    }
  }

  async function finishSession() {
    if (!machineId.value || !currentOperatorBadge.value) return;
    try {
      Loading.show();
      await api.post('/production/session/stop', {
        machine_id: machineId.value,
        operator_badge: currentOperatorBadge.value
      });
      Notify.create({ type: 'positive', message: 'Sessão Finalizada.' });
      activeOrder.value = null;
    } catch { 
      Notify.create({ type: 'negative', message: 'Erro ao finalizar.' });
    } finally {
      Loading.hide();
    }
  }

  async function createMaintenanceOrder(notes: string) {
      if (!machineId.value) return;
      try {
          Loading.show();
          const payload = {
              vehicle_id: machineId.value,
              problem_description: `Abertura via Kiosk: ${notes}`,
              category: 'Mecânica', 
              maintenance_type: 'CORRETIVA'
          };
          
          await api.post('/maintenance/requests', payload);
          
          if(currentMachine.value) currentMachine.value.status = 'Em manutenção';
          
          Notify.create({ 
              type: 'positive', 
              icon: 'build_circle',
              message: 'Ordem de Manutenção Criada!',
              caption: 'A equipe foi notificada.' 
          });
      } catch (error: any) { 
          console.error('Erro ao criar O.M.:', error.response?.data);
          let msg = 'Erro ao processar dados.';
          const detail = error.response?.data?.detail;
          if (Array.isArray(detail)) {
              msg = `Campo inválido: ${detail[0]?.loc?.[1]} - ${detail[0]?.msg}`;
          }
          Notify.create({ type: 'negative', message: msg });
      } finally {
          Loading.hide();
      }
  }

  async function sendEvent(type: string, payload: Record<string, unknown> = {}) {
    if (!machineId.value || !currentOperatorBadge.value) return;
    try {
      await api.post('/production/event', {
        machine_id: machineId.value,
        operator_badge: currentOperatorBadge.value,
        order_code: activeOrder.value?.code,
        event_type: type,
        ...payload
      });
    } catch (e) { console.error('Falha de sync', e); }
  }

  function triggerAndon(sector: string, notes = '') {
    if (!machineId.value || !currentOperatorBadge.value) return;
    void api.post('/production/andon', {
        machine_id: machineId.value,
        operator_badge: currentOperatorBadge.value,
        sector: sector,
        notes: notes
    });
    Notify.create({ type: 'warning', icon: 'campaign', message: `Chamado para ${sector}` });
  }

  async function startProduction() { await sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' }); }
  async function pauseProduction(reason: string) { await sendEvent('STATUS_CHANGE', { new_status: 'STOPPED', reason }); }
  
  function addProduction(qty: number, isScrap = false) {
    if (!activeOrder.value) return;
    if (isScrap) activeOrder.value.scrap_quantity += qty;
    else activeOrder.value.produced_quantity += qty;
    void sendEvent('COUNT', { quantity_good: isScrap ? 0 : qty, quantity_scrap: isScrap ? qty : 0 });
  }

  return {
    machinesList, machineId, currentMachine, machineName, machineSector,
    currentOperator, currentOperatorBadge, activeOrder, machineHistory,
    currentStepIndex, currentActiveStep,
    isKioskConfigured, isShiftActive, isMachineBroken, isRunning, hasActiveOrder,
    loadKioskConfig, _setMachineData, setMachineStatus,
    fetchAvailableMachines, configureKiosk, fetchMachineHistory,
    loginOperator, logoutOperator, loadOrderFromQr, finishSession,
    startStep, pauseStep, finishStep, createMaintenanceOrder,
    sendEvent, triggerAndon,
    startProduction, pauseProduction, addProduction
  };
});
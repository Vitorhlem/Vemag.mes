/* eslint-disable @typescript-eslint/no-explicit-any */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { Notify, Loading } from 'quasar';
import { api } from 'boot/axios';
import {AndonService} from 'src/services/andon-service'; 
import type { AndonCallCreate } from 'src/services/andon-service';
import { findBestStepIndex } from 'src/data/sap-operations'; 
import { db } from 'src/db/offline-db';

// --- INTERFACES ---
export interface Machine {
  id: number;
  brand: string;
  model: string;
  identifier?: string;
  status?: string; 
  category?: string;
  current_operator_id?: number;
  sap_resource_code?: string;
  layout_x?: number;
  photo_url?: string; 
  layout_y?: number;
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
  
  // --- CAMPOS NOVOS ---
  custom_ref?: string;    // DocNum ou Nome do Cliente
  op_number?: string;     // Número original da OP/OS
  part_code?: string;     // Código do item (ItemCode)
  drawing?: string;       // URL ou código do desenho
  // --------------------
  planned_qty?: number; 
  uom?: string;
  client?: string;
  product?: string;
  is_service?: boolean; 
  deliveryDate?: string;
  part_name: string;
  part_image_url: string;
  technical_drawing_url?: string;
  target_quantity: number;
  status: string;
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
  const machineId = ref<number | null>(Number(sessionStorage.getItem('TRU_MACHINE_ID')) || null);
  const machineResource = ref<string>('');
  const currentMachine = ref<Machine | null>(null);
  const machineName = ref<string>('Não Configurado');
  const machineSector = ref<string>('-');
  const activeOperator = ref({
    name: '',
    badge: ''
  });
  const isInSetup = computed(() => {
      if (activeOrder.value?.status === 'SETUP') return true;
      return activeOrder.value?.status === 'SETUP'; 
  });
  const currentOperator = ref<Operator | null>(null);
  const currentOperatorBadge = ref<string | null>(null);
  
  const activeOrder = ref<ProductionOrder | null>(null);
  const currentStepIndex = ref<number>(-1);
  const machineHistory = ref<ProductionLog[]>([]);



  // --- GETTERS ---
  const isKioskConfigured = computed(() => !!machineId.value);
  const isShiftActive = computed(() => !!currentOperatorBadge.value);
  const hasActiveOrder = computed(() => !!activeOrder.value);
  
  const isRunning = computed(() => {
    return activeOrder.value?.status === 'RUNNING';
  });

  const currentActiveStep = computed(() => {
    if (!activeOrder.value?.steps || currentStepIndex.value === -1) return null;
    return activeOrder.value?.steps?.[currentStepIndex.value] || null;
  });
  
  const isMachineBroken = computed(() => {
      const rawStatus = currentMachine.value?.status || '';
      const status = String(rawStatus).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      return status.includes('maintenance') || status.includes('broken') || status.includes('manutencao') || status.includes('manutenção');
  });

  // --- ACTIONS ---

  async function identifyOperator(badge: string) {
    try {
      const response = await api.get(`/users/by-badge/${badge}`);
      const user = response.data;
      

      activeOperator.value = {
        name: user.full_name,
        badge: user.employee_id
      };
      
      return user;
    } catch (error) {
      console.error('Erro ao identificar operador:', error);
      throw error;
    }
  }


  function clearOperator() {
    activeOperator.value = { name: '', badge: '' };
  }

  function _setMachineData(data: Machine) {
    currentMachine.value = data;
    machineId.value = data.id;
    machineName.value = `${data.brand} ${data.model}`;
    machineSector.value = data.category || 'Geral';
    machineResource.value = data.sap_resource_code || '4.02.01'; 
    
    console.log(`[STORE] Máquina Configurada: ${machineName.value} | Recurso SAP: ${machineResource.value}`);
  }
  async function fetchActiveSession() {
    if (!this.machineId) return;

    try {
        const { data } = await api.get(`/production/session/active/${this.machineId}`);
        
        if (data && data.order) {
            console.log("🟢 [STORE] Sessão ativa recuperada do banco:", data.order.code);
            this.activeOrder = data.order;
            this.currentStepIndex = data.current_step_index;
            this.isShiftActive = true; 
        }
    } catch (error: any) {
        if (error.response && error.response.status === 404) {
            console.log('ℹ️ Nenhuma sessão ativa encontrada (Máquina disponível).');
            this.activeOrder = null;
            this.isShiftActive = false;
            return; 
        }
        
        console.error('Erro ao buscar sessão ativa:', error);
    }
}

async function loadKioskConfig() {
    const savedId = sessionStorage.getItem('TRU_MACHINE_ID');
    if (savedId) {
        machineId.value = Number(savedId);
        try {
            const { data } = await api.get<Machine>(`/machines/${savedId}`);
            _setMachineData(data);
                        await fetchActiveSession(); 
            
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

  async function configureKiosk(id: number) {
    try {
      const { data } = await api.get<Machine>(`/machines/${id}`);
      _setMachineData(data);
      
      sessionStorage.setItem('TRU_MACHINE_ID', String(data.id)); 
      
      Notify.create({ type: 'positive', message: 'Terminal Configurado (Sessão)!' });
    } catch { 
      Notify.create({ type: 'negative', message: 'Erro ao configurar terminal.' }); 
    }
}

 async function setMachineStatus(status: string, reason?: string) {
  if (!machineId.value) return;

  const statusPayload = { 
    machine_id: machineId.value, 
    status: status,
    reason: reason || null, // 👈 ENVIANDO O MOTIVO AQUI!
    timestamp: new Date().toISOString() 
  };

  try {
    await api.post('/production/machine/status', statusPayload);
  } catch (error: any) {
    if (!error.response || error.code === 'ECONNABORTED') {
      await db.sync_queue.add({
        type: 'STATUS_UPDATE',
        payload: statusPayload,
        timestamp: statusPayload.timestamp,
        status: 'pending'
      });
    }
  } finally {
    if (currentMachine.value) {
      const s = status.toUpperCase();
      const map: Record<string, string> = {
        'RUNNING': 'Em uso', 'IN_USE': 'Em uso', 'EM USO': 'Em uso', 'PRODUCING': 'Em uso',
        'AVAILABLE': 'Disponível', 'IDLE': 'Disponível', 'DISPONIVEL': 'Disponível',
        'MAINTENANCE': 'Manutenção', 'SETUP': 'Setup', 'OCIOSO': 'Ociosidade', 'OCIOSIDADE': 'Ociosidade',
        'IN_USE_AUTONOMOUS': 'Produção Autônoma', 'PRODUÇÃO AUTÔNOMA': 'Produção Autônoma'
      };
      currentMachine.value.status = map[s] || status;
    }
  }
}
async function loginOperator(scannedCode: string) {
    if (!machineId.value) return;
    Loading.show({ message: 'Vinculando Operador...' });
    
    try {
      const { data: operator } = await api.get(`/production/operator/${scannedCode}`);

      currentOperator.value = operator;
      currentOperatorBadge.value = operator.employee_id;
      localStorage.setItem('TRU_CURRENT_OPERATOR', JSON.stringify(operator));
      const machineIsWorking = activeOrder.value && 
                               (['RUNNING', 'IN_USE'].includes(activeOrder.value.status));

      if (machineIsWorking) {
          console.log("⚡ [KPI] Máquina rodando. Convertendo Autônoma -> Humana.");
          
          await sendEvent('STATUS_CHANGE', { 
              new_status: 'RUNNING', 
              reason: 'Operador assumiu máquina em movimento' 
          }, operator.employee_id);

          await setMachineStatus('RUNNING');
      } else {
          await setMachineStatus('AVAILABLE');
      }

      Notify.create({ type: 'positive', message: `Olá, ${operator.full_name.split(' ')[0]}!` });

    } catch (error: any) { 
      console.error('Erro no login:', error); 
      Notify.create({ type: 'negative', message: 'Falha ao processar crachá.' }); 
    } finally { 
      Loading.hide(); 
    }
}
  async function sendEvent(type: string, payload: Record<string, unknown> = {}, badgeOverride?: string) {
  const badge = badgeOverride || currentOperatorBadge.value;

  if (!machineId.value || !badge) {
    console.warn(`[MES] Evento ${type} bloqueado: Sem identificação de máquina ou operador.`);
    return;
  }
  
  const eventPayload = { 
    machine_id: machineId.value, 
    operator_badge: badge, 
    order_code: activeOrder.value?.code || null, 
    event_type: type, 
    timestamp: new Date().toISOString(),
    ...payload 
  };

  try { 

    await api.post('/production/event', eventPayload); 
  } catch (error: any) { 
    if (!error.response || error.code === 'ECONNABORTED') {
      await db.sync_queue.add({
        type: 'EVENT',
        payload: eventPayload,
        timestamp: eventPayload.timestamp,
        status: 'pending'
      });
      console.warn(`[OFFLINE] Evento ${type} armazenado para sincronização posterior.`);
    } else {
      console.error('Erro ao registrar evento no servidor:', error);
    }
  }
}

  async function logoutOperator(overrideStatus?: string, keepActiveOrder = false, customReason?: string) {
    if (!machineId.value) return;
    

    if (!currentOperatorBadge.value) {
        currentOperator.value = null;
        if (!keepActiveOrder) {
            activeOrder.value = null;
            currentStepIndex.value = -1;
        }
        return;
    }

    const statusMap: Record<string, string> = {
        'AVAILABLE': 'Disponível',
        'IN_USE': 'Em uso',
        'IN_USE_AUTONOMOUS': 'Produção Autônoma',
        'SETUP': 'Setup',
        'MAINTENANCE': 'Em manutenção',
        'STOPPED': 'Parada',
        'OCIOSO': 'Ociosidade'
    };

    let targetStatus = overrideStatus || 'AVAILABLE';

    if (isMachineBroken.value) {
        targetStatus = 'MAINTENANCE';
    } else if (keepActiveOrder && !overrideStatus) {
        targetStatus = 'IN_USE_AUTONOMOUS';
    }

    const reasonText = customReason || (keepActiveOrder ? 'Troca de Turno' : 'Saída');

    try {
        await api.post('/production/event', {
            machine_id: machineId.value,
            operator_badge: currentOperatorBadge.value,
            event_type: 'LOGOUT',
            new_status: targetStatus, 
            reason: reasonText 
        });

        if (!overrideStatus) {
            await setMachineStatus(targetStatus);
        }

        if (currentMachine.value) {
            currentMachine.value.status = statusMap[targetStatus] || 'Disponível';
        }

    } catch (error) { 
        console.error('Erro ao deslogar:', error); 
    }

    currentOperator.value = null;
    currentOperatorBadge.value = null;
    localStorage.removeItem('TRU_CURRENT_OPERATOR');

    if (!keepActiveOrder) {
        activeOrder.value = null;
        currentStepIndex.value = -1;
        localStorage.removeItem('TRU_ACTIVE_ORDER');
        localStorage.removeItem('TRU_CURRENT_STEP');
    } else {
        console.log("🔄 Mantendo O.P. ativa para o próximo turno.");
    }
  }

  async function executeShiftChange(keepRunning: boolean) {
    if (!currentOperatorBadge.value) return;

    try {
        if (keepRunning) {

            await setMachineStatus('IN_USE_AUTONOMOUS');
            

            await logoutOperator('IN_USE_AUTONOMOUS', true); 
            
            Notify.create({ 
                type: 'positive', 
                message: 'Turno encerrado. Máquina em modo autônomo.', 
                icon: 'autorenew' 
            });

        } else {

            await setMachineStatus('OCIOSO');

            await logoutOperator('OCIOSO', true); 
            
            Notify.create({ 
                type: 'info', 
                message: 'Turno encerrado. Máquina parada.', 
                icon: 'pause' 
            });
        }

        return true;

    } catch (error) {
        console.error("Erro na Troca de Turno:", error);
        Notify.create({ type: 'negative', message: 'Erro ao registrar troca.' });
        return false;
    }
}

  async function fetchMachine(id?: number) {
    const targetId = id || machineId.value;
    
    if (!targetId) return;

    try {
        const { data } = await api.get(`/machines/${targetId}`);
        
        currentMachine.value = data;

        if (data.sap_resource_code) machineResource.value = data.sap_resource_code;
        if (data.model) machineName.value = data.model;
    } catch (error) {
        console.error('Erro ao buscar dados da máquina:', error);
    }
}

  let orderSocket: WebSocket | null = null;

  async function processReceivedOrder(data: any, originalQrCode?: string) {
    try {
      const safeCode = data.op_number || data.code || originalQrCode;
      const isServiceOrder = data.type === 'Service' || String(safeCode).startsWith('OS-') || data.is_service;

      activeOrder.value = { 
        ...data, 
        code: String(safeCode),      
        is_service: isServiceOrder,  
        status: data.status || 'SETUP' 
      };

      const bestIndex = findBestStepIndex(machineResource.value, activeOrder.value.steps || []);
      currentStepIndex.value = bestIndex;

      if (currentOperatorBadge.value && machineId.value) {
          const currentStep = activeOrder.value.steps?.[currentStepIndex.value];
          const stageStr = currentStep ? String(currentStep.seq) : '010';

          await api.post('/production/session/start', {
            machine_id: machineId.value, 
            operator_badge: currentOperatorBadge.value, 
            op_number: String(safeCode),
            step_seq: stageStr
          });
          
          isInSetup.value = true;
          if (activeOrder.value) activeOrder.value.status = 'SETUP';
      }

      await db.orders_cache.put({ code: String(safeCode), data: data, last_updated: new Date().toISOString() });
    } catch (e: any) { 
      console.error(e);
      Notify.create({ type: 'negative', message: 'Erro ao processar roteiro da O.P.' }); 
      activeOrder.value = null;
    }
  }

  async function requestOrderFromSAP(qrCode: string): Promise<any> {
    if (isMachineBroken.value) { 
      Notify.create({ type: 'negative', message: 'Máquina em manutenção.' }); 
      return null; 
    }

    if (!window.navigator.onLine) {
        const cached = await db.orders_cache.get(qrCode);
        if (cached) {
            await processReceivedOrder(cached.data, qrCode);
        }
        return cached ? cached.data : null;
    }

    return new Promise((resolve, reject) => {
        const apiBase = import.meta.env.VITE_API_URL || 'http://192.168.0.22:8000/api/v1';// 👈 Porta 8000 do novo ambiente
        const wsBase = apiBase.replace(/^http/, 'ws').replace('/api/v1', '');
        const wsUrl = `${wsBase}/ws/${machineId.value}`; 

        if (orderSocket) {
            orderSocket.close();
        }
        
        orderSocket = new WebSocket(wsUrl);

        orderSocket.onopen = () => {
            console.log(`📡 Escutando Celery via WebSocket (Máquina ${machineId.value})...`);
            Loading.show({ message: 'Buscando O.P.s no SAP...' });

            api.get(`/production/orders/${qrCode}?machine_id=${machineId.value}`).catch(e => {
                Loading.hide();
                if (orderSocket) orderSocket.close();
                Notify.create({ type: 'negative', message: 'Erro ao acionar o SAP.' }); 
                reject(e instanceof Error ? e : new Error(String(e)));
            });
        };

        orderSocket.onmessage = async (event) => {
            try {
                const msg = JSON.parse(event.data);
                
                if (msg.type === 'SAP_OPEN_ORDERS' || msg.type === 'SAP_ORDER_DATA') {
                    console.log('✅ OPs recebidas do Celery!');
                    Loading.hide();
                    
                    if (qrCode === 'open') {
                        if (orderSocket) orderSocket.close();
                        resolve(msg.data); 
                        return;
                    }

                    const orderData = Array.isArray(msg.data) 
                      ? msg.data.find((o: any) => String(o.op_number) === String(qrCode) || String(o.code) === String(qrCode)) || msg.data[0] 
                      : msg.data;

                    if (orderData) {
                        await processReceivedOrder(orderData, qrCode);
                        resolve(orderData);
                    } else {
                        Notify.create({ type: 'warning', message: 'O.P. não encontrada no SAP.' });
                        resolve(null);
                    }

                    if (orderSocket) orderSocket.close();
                }
            } catch (e) {
                console.error('Erro ao processar mensagem WS:', e);
            }
        };

        orderSocket.onerror = () => {
            Loading.hide();
            Notify.create({ type: 'negative', message: 'Falha na conexão em tempo real.' });
            reject(new Error("Erro de conexão WebSocket com o Celery"));
        };
    });
  }


  async function startProduction() { 
      if (activeOrder.value) activeOrder.value = { ...activeOrder.value, status: 'RUNNING' };
    
      
      await sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' }); 
      
  }

  async function pauseProduction(reason: string) { 
      if (activeOrder.value) activeOrder.value = { ...activeOrder.value, status: 'PAUSED' };
      
      await sendEvent('STATUS_CHANGE', { new_status: 'STOPPED', reason }); 
      
      await setMachineStatus('STOPPED'); 
  }

  

async function toggleSetup() {
    if (!machineId.value || !currentOperatorBadge.value) return;

    if (isInSetup.value) {
        isInSetup.value = false;
        if (activeOrder.value) activeOrder.value.status = 'PENDING';
    } else {
        isInSetup.value = true;
        if (activeOrder.value) activeOrder.value.status = 'SETUP';
        await sendEvent('STATUS_CHANGE', { new_status: 'SETUP', reason: 'Início de Setup' });
    }
}


  function startStep(index: number) {
    if (activeOrder.value?.steps && activeOrder.value.steps[index]) {
      activeOrder.value.steps.forEach(s => { if (s.status === 'IN_PROGRESS') s.status = 'PAUSED'; });
      activeOrder.value.steps[index].status = 'IN_PROGRESS';
      currentStepIndex.value = index;
      void sendEvent('STEP_START', { step: activeOrder.value.steps[index].name, new_status: 'RUNNING' });
    }
  }

  function pauseStep(reason: string) {
    if (activeOrder.value?.steps && currentStepIndex.value > -1) {
        const step = activeOrder.value.steps[currentStepIndex.value];
        if (step) {
            step.status = 'PAUSED';
            void sendEvent('STEP_PAUSE', { step: step.name, reason: reason, new_status: 'STOPPED' });
        }
    }
  }

  function setImprovisedStep(sapOp: any) {
    if (!activeOrder.value) return;

    const newStep: OperationStep = {
      seq: Number(sapOp.code),
      resource: sapOp.code, 
      name: sapOp.description,
      description: `ETAPA IMPROVISADA/IMPREVISTA: Execução realizada no recurso ${machineName.value} conforme necessidade de fábrica.`,
      timeEst: 0,
      status: 'PENDING'
    };

    if (!activeOrder.value.steps) activeOrder.value.steps = [];
    activeOrder.value.steps.push(newStep);
    
    currentStepIndex.value = activeOrder.value.steps.length - 1;
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
          Notify.create({ type: 'positive', message: 'Roteiro Finalizado!' });
      }
    }
  }
  
  async function finishSession() {
    if (!machineId.value || !currentOperatorBadge.value) return;
    try {
      Loading.show();
      await api.post('/production/session/stop', { machine_id: machineId.value, operator_badge: currentOperatorBadge.value, reason: "FINALIZAR ETAPA" });
      activeOrder.value = null; 
      if (currentMachine.value && !isMachineBroken.value) {
          currentMachine.value = { ...currentMachine.value, status: 'Disponível' };
      }
      Notify.create({ type: 'positive', message: 'O.P. Finalizada. Dados salvos.' });
    } catch { Notify.create({ type: 'negative', message: 'Erro ao finalizar.' }); } finally { Loading.hide(); }
  }

  async function createMaintenanceOrder(notes: string) {
      if (!machineId.value) return;
      try {
          Loading.show();
          const payload = { machine_id: machineId.value, problem_description: `Kiosk: ${notes}`, category: 'Mecânica', maintenance_type: 'CORRETIVA' };
          await api.post('/maintenance/requests', payload);

          await setMachineStatus('MAINTENANCE');
          
          Notify.create({ type: 'positive', icon: 'build_circle', message: 'O.M. Criada!' });
      } catch (error: any) { 
          console.error(error);
          Notify.create({ type: 'negative', message: 'Erro ao criar O.M.' }); 
      } finally { Loading.hide(); }
  }

  async function triggerAndon(sector: string, note?: string) {
    if (!machineId.value) {
        Notify.create({ type: 'warning', message: 'Máquina não identificada para o chamado.' });
        return;
    }

    try {
        Loading.show({ 
            message: `Chamando equipe de ${sector}...`,
            backgroundColor: 'red-10',
            customClass: 'text-weight-bold'
        });
        
        const payload: AndonCallCreate = {
            machine_id: machineId.value,
            sector: sector,
            reason: note || 'Solicitação via Tablet',
            description: `Operador: ${currentOperator.value?.full_name || 'Anônimo'}`
        };

        await AndonService.createCall(payload);
        
        Notify.create({ 
            type: 'positive', 
            icon: 'campaign',
            message: `Chamado enviado para ${sector}! A equipe foi notificada.`,
            timeout: 5000,
            position: 'top'
        });

    } catch (error) {
        console.error("Erro ao abrir Andon:", error);
        Notify.create({ type: 'negative', message: 'Erro de conexão ao enviar chamado.' });
    } finally {
        Loading.hide();
    }
  }

  async function saveMachineLayout(machineId: number, x: number, y: number) {
      try {
          await api.post('/production/machine/layout', {
              machine_id: machineId,
              layout_x: x,
              layout_y: y
          });
          
          const index = machinesList.value.findIndex(m => m.id === machineId);
          if (index !== -1) {
              machinesList.value[index].layout_x = x;
              machinesList.value[index].layout_y = y;
          }
      } catch (error) {
          console.error("Erro ao salvar layout:", error);
          Notify.create({ type: 'negative', message: 'Erro ao salvar posição da máquina.' });
      }
  }

  return {
    machinesList, machineId, currentMachine, machineName, machineSector,
    currentOperator, currentOperatorBadge, activeOrder, machineHistory,
    currentStepIndex, currentActiveStep,
    isKioskConfigured, isShiftActive, isMachineBroken, isRunning, hasActiveOrder,
    loadKioskConfig, _setMachineData, setMachineStatus,
    fetchAvailableMachines, configureKiosk, fetchMachineHistory,
    loginOperator, logoutOperator, requestOrderFromSAP, processReceivedOrder, finishSession,
    createMaintenanceOrder, sendEvent, triggerAndon,
    startStep, pauseStep, finishStep, startProduction, pauseProduction, isInSetup, toggleSetup, activeOperator, identifyOperator, clearOperator,
    machineResource, setImprovisedStep, fetchMachine, executeShiftChange, saveMachineLayout
  };
});
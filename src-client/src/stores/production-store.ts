/* eslint-disable @typescript-eslint/no-explicit-any */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { Notify, Loading } from 'quasar';
import { api } from 'boot/axios';
import {AndonService} from 'src/services/andon-service'; // Importe o novo serviço
import type { AndonCallCreate } from 'src/services/andon-service';
import { findBestStepIndex } from 'src/data/sap-operations'; // <--- IMPORT NOVO
import { db } from 'src/db/offline-db';

// --- INTERFACES ---
export interface Machine {
  id: number;
  brand: string;
  model: string;
  license_plate?: string;
  status?: string; 
  category?: string;
  current_driver_id?: number;
  sap_resource_code?: string; // <--- CAMPO IMPORTANTE ADICIONADO
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
  is_service?: boolean; // <-- ADICIONE ESTA LINHA
  deliveryDate?: string;
  part_name: string;
  part_image_url: string;
  technical_drawing_url?: string;
  target_quantity: number;
  produced_quantity: number;
  scrap_quantity: number;
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
      // Chama a rota nova que criamos no backend
      const response = await api.get(`/users/by-badge/${badge}`);
      const user = response.data;
      
      // Salva na memória TEMPORÁRIA (não muda o login do admin)
      activeOperator.value = {
        name: user.full_name,
        badge: user.employee_id
      };
      
      return user; // Retorna para a tela exibir msg de boas vindas
    } catch (error) {
      console.error('Erro ao identificar operador:', error);
      throw error;
    }
  }

  // Ação para limpar (logout do operador)
  function clearOperator() {
    activeOperator.value = { name: '', badge: '' };
  }

  function _setMachineData(data: Machine) {
    currentMachine.value = data;
    machineId.value = data.id;
    machineName.value = `${data.brand} ${data.model}`;
    machineSector.value = data.category || 'Geral';
    
    // AQUI ESTÁ A CORREÇÃO:
    // Pega o 'sap_resource_code' do banco de dados (ex: '4.12.01')
    // Se não tiver, usa um fallback seguro ou mantém vazio para forçar erro/aviso
    machineResource.value = data.sap_resource_code || '4.02.01'; 
    
    console.log(`[STORE] Máquina Configurada: ${machineName.value} | Recurso SAP: ${machineResource.value}`);
  }
  async function fetchActiveSession() {
    // [CORREÇÃO] Use 'this.machineId' em vez de 'machineId.value'
    if (!this.machineId) return;

    try {
        const { data } = await api.get(`/production/session/active/${this.machineId}`);
        
        if (data && data.order) {
            console.log("🟢 [STORE] Sessão ativa recuperada do banco:", data.order.code);
            // [CORREÇÃO] Use 'this.' para atribuir ao estado
            this.activeOrder = data.order;
            this.currentStepIndex = data.current_step_index;
            this.isShiftActive = true; // Garante que o turno fique ativo
        }
    } catch (error: any) {
        // [CORREÇÃO] Tratamento do 404 (Não é erro, é apenas "Sem sessão")
        if (error.response && error.response.status === 404) {
            console.log('ℹ️ Nenhuma sessão ativa encontrada (Máquina disponível).');
            this.activeOrder = null;
            this.isShiftActive = false;
            return; 
        }
        
        console.error('Erro ao buscar sessão ativa:', error);
    }
}

// 2. Atualize o loadKioskConfig para chamar essa recuperação
async function loadKioskConfig() {
    const savedId = sessionStorage.getItem('TRU_MACHINE_ID');
    if (savedId) {
        machineId.value = Number(savedId);
        try {
            const { data } = await api.get<Machine>(`/vehicles/${savedId}`);
            _setMachineData(data);
            
            // NOVIDADE: Busca no banco se existe uma ordem rodando ANTES do login
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
      const { data } = await api.get<Machine>(`/vehicles/${id}`);
      _setMachineData(data);
      
      // MUDANÇA AQUI: sessionStorage isola por aba
      sessionStorage.setItem('TRU_MACHINE_ID', String(data.id)); 
      // localStorage.setItem('TRU_MACHINE_ID', String(data.id)); // REMOVA ISSO SE EXISTIR
      
      Notify.create({ type: 'positive', message: 'Terminal Configurado (Sessão)!' });
    } catch { 
      Notify.create({ type: 'negative', message: 'Erro ao configurar terminal.' }); 
    }
}

  async function setMachineStatus(status: string) {
  if (!machineId.value) return;

  const statusPayload = { 
    machine_id: machineId.value, 
    status: status,
    timestamp: new Date().toISOString() 
  };

  try {
    // Tenta avisar o servidor em tempo real
    await api.post('/production/machine/status', statusPayload);
  } catch (error: any) {
    // 1. INTERCEPTAÇÃO OFFLINE: Agenda a mudança de status para o sync
    if (!error.response || error.code === 'ECONNABORTED') {
      await db.sync_queue.add({
        type: 'STATUS_UPDATE',
        payload: statusPayload,
        timestamp: statusPayload.timestamp,
        status: 'pending'
      });
      console.warn(`[OFFLINE] Mudança de status (${status}) agendada.`);
    }
  } finally {
    // 2. ATUALIZAÇÃO LOCAL (UI): Independente da rede, o operador vê a mudança na tela
    if (currentMachine.value) {
      const s = status.toUpperCase();
      
      if (['RUNNING', 'IN_USE', 'EM USO', 'PRODUCING'].includes(s)) {
        currentMachine.value.status = 'Em uso';
      } 
      else if (['AVAILABLE', 'IDLE', 'DISPONIVEL', 'STOPPED'].includes(s)) {
        currentMachine.value.status = 'Disponível';
      } 
      else if (['MAINTENANCE', 'BROKEN', 'SETUP', 'MANUTENÇÃO'].includes(s)) {
        currentMachine.value.status = 'Manutenção';
      } 
      else if (['PAUSED', 'PARADA', 'PAUSA'].includes(s)) {
        currentMachine.value.status = 'Em Pausa'; 
      }
      else {
        currentMachine.value.status = status;
      }
    }
  }
}
async function loginOperator(scannedCode: string) {
    if (!machineId.value) return;
    Loading.show({ message: 'Vinculando Operador...' });
    
    try {
      const { data: operator } = await api.get(`/production/operator/${scannedCode}`);

      // 1. Atualiza a memória local IMEDIATAMENTE
      currentOperator.value = operator;
      currentOperatorBadge.value = operator.employee_id;
      localStorage.setItem('TRU_CURRENT_OPERATOR', JSON.stringify(operator));

      // 2. SEMPRE envia o evento de LOGIN (Independente se a máquina roda ou não)
      // É este evento que "abre" a porta para o KPI humano.
      await sendEvent('LOGIN', { 
          new_status: activeOrder.value?.status || 'IDLE',
          reason: 'Troca de Turno / Início' 
      }, operator.employee_id);

      // 3. Se a máquina já estava rodando, enviamos o STATUS_CHANGE logo em seguida
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
  // 1. Definição do Identificador do Operador
  const badge = badgeOverride || currentOperatorBadge.value;

  if (!machineId.value || !badge) {
    console.warn(`[MES] Evento ${type} bloqueado: Sem identificação de máquina ou operador.`);
    return;
  }
  
  // 2. Montagem do Payload com Timestamp Original
  const eventPayload = { 
    machine_id: machineId.value, 
    operator_badge: badge, 
    order_code: activeOrder.value?.code || null, 
    event_type: type, 
    timestamp: new Date().toISOString(), // Garantimos que o tempo da ação seja preservado
    ...payload 
  };

  try { 
    // Tenta enviar em tempo real
    await api.post('/production/event', eventPayload); 
  } catch (error: any) { 
    // 3. INTERCEPTAÇÃO OFFLINE: Se não houver rede, guarda na fila local
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

  async function logoutOperator(overrideStatus?: string, keepActiveOrder = false) {
    if (!machineId.value) return;
    
    // Se não tiver badge (já saiu), ignora
    if (!currentOperatorBadge.value) {
        currentOperator.value = null;
        if (!keepActiveOrder) {
            activeOrder.value = null;
            currentStepIndex.value = -1;
        }
        return;
    }

    let statusToSend = 'AVAILABLE';
    let visualStatus = 'Disponível';

    // Lógica de Status
    if (overrideStatus === 'MAINTENANCE' || isMachineBroken.value) {
        statusToSend = 'MAINTENANCE';
        visualStatus = 'Em manutenção';
    } else if (keepActiveOrder && activeOrder.value?.status === 'RUNNING') {
        // MÁQUINA CONTINUA RODANDO SEM OPERADOR
        statusToSend = 'RUNNING'; 
        visualStatus = 'Em Operação (Turno)';
    }

    try {
      await api.post('/production/event', {
        machine_id: machineId.value,
        operator_badge: currentOperatorBadge.value,
        event_type: 'LOGOUT',
        new_status: statusToSend, 
        reason: 'Logoff / Troca de Turno'
      });
      await setMachineStatus(statusToSend);

      if (currentMachine.value) {
          currentMachine.value = { ...currentMachine.value, status: visualStatus };
      }
    } catch (error) { console.error('Erro ao deslogar:', error); }

    // Limpeza de Estado
    currentOperator.value = null;
    currentOperatorBadge.value = null;
    localStorage.removeItem('TRU_CURRENT_OPERATOR');

    // AQUI O PULO DO GATO:
    // Se for troca de turno rodando, NÃO limpamos a activeOrder nem o currentStep
    if (!keepActiveOrder) {
        activeOrder.value = null;
        currentStepIndex.value = -1;
    }
  }

  async function loadOrderFromQr(qrCode: string) {
  // 1. Bloqueio por Manutenção
  if (isMachineBroken.value) { 
    Notify.create({ type: 'negative', message: 'Máquina em manutenção. Não é possível iniciar O.P.' }); 
    return; 
  }

  try {
    Loading.show({ message: 'Buscando Ordem de Produção...' });
    
    let data: any;
    try {
      // TENTA ONLINE: Busca da API e atualiza o Cache
      const res = await api.get(`/production/orders/${qrCode}`);
      data = res.data;

      // ATUALIZA O CACHE LOCAL (IndexedDB) para uso futuro offline
      await db.orders_cache.put({
        code: qrCode,
        data: data,
        last_updated: new Date().toISOString()
      });
      
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (apiError) {
      // TENTA OFFLINE: Se a rede falhar, busca no banco local
      console.warn("Rede indisponível, tentando banco local...");
      const cached = await db.orders_cache.get(qrCode);
      
      if (cached) {
        data = cached.data;
        Notify.create({ 
          type: 'warning', 
          icon: 'wifi_off',
          message: 'Modo Offline Ativado: Carregando dados do cache local.',
          timeout: 4000
        });
      } else {
        // Se não tiver nem no cache, aí sim falha
        throw new Error('O.P. não encontrada no cache local. Conecte-se à rede para o primeiro carregamento.');
      }
    }

    // --- PROCESSAMENTO DOS DADOS (IDÊNTICO À SUA LÓGICA DE NEGÓCIO) ---
    if (!data.status) data.status = 'PENDING';
    
    activeOrder.value = { 
      ...activeOrder.value, 
      ...data, 
      status: data.status || 'PENDING'
    };

    const bestIndex = findBestStepIndex(machineResource.value, activeOrder.value.steps || []);

    if (bestIndex !== -1) {
      currentStepIndex.value = bestIndex;
      const stepName = activeOrder.value.steps![bestIndex].name;
      Notify.create({ 
          type: 'positive', icon: 'gps_fixed',
          message: `Etapa identificada: #${(bestIndex+1)*10} - ${stepName}`,
          timeout: 4000
      });
    } else {
      currentStepIndex.value = -1; 
    }

    // --- INÍCIO DE SESSÃO TÉCNICA ---
    if (currentOperatorBadge.value && machineId.value) {
        const currentStep = activeOrder.value.steps?.[currentStepIndex.value];
        const stageStr = currentStep ? String(currentStep.seq) : '010';

        // Tenta registrar o início no servidor (se falhar, o sistema apenas segue em modo offline)
        try {
          await api.post('/production/session/start', {
            machine_id: machineId.value, 
            operator_badge: currentOperatorBadge.value, 
            op_number: String(qrCode),
            step_seq: stageStr
          });
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        } catch (e) {
          console.log("Aviso: Sessão iniciada localmente (Sem conexão com servidor)");
        }
        
        // Registra o evento de log para o KPI de Setup (Sincronizado via Outbox se necessário)
        await sendEvent('STATUS_CHANGE', { 
            new_status: 'SETUP', 
            reason: 'Setup Inicial (Seleção de O.P.)' 
        });

        activeOrder.value.status = 'SETUP';
        await setMachineStatus('SETUP');
    }

  } catch (e: any) { 
    Notify.create({ type: 'negative', message: e.message || 'Erro crítico ao carregar O.P.' }); 
    activeOrder.value = null;
  } finally { 
    Loading.hide(); 
  }
}

  async function startProduction() { 
      if (activeOrder.value) activeOrder.value = { ...activeOrder.value, status: 'RUNNING' };

      
      // 1. Registra o Log
      await sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' }); 
      
  }

  async function pauseProduction(reason: string) { 
      if (activeOrder.value) activeOrder.value = { ...activeOrder.value, status: 'PAUSED' };
      
      // 1. Registra Log
      await sendEvent('STATUS_CHANGE', { new_status: 'STOPPED', reason }); 
      
      // 2. CORREÇÃO AQUI:
      // ANTES: await setMachineStatus('AVAILABLE'); 
      // AGORA: Envia 'STOPPED' para o backend saber que está ocupada/pausada
      await setMachineStatus('STOPPED'); 
  }

  

  async function toggleSetup() {
      if (!machineId.value || !currentOperatorBadge.value) return;

      // --- SAIR DO MODO SETUP ---
      if (isInSetup.value) {
          try {
              // 1. Registra Log de FIM (Volta para Available)
              // O backend vai calcular o tempo entre o log anterior (SETUP) e este (AVAILABLE)
              await sendEvent('STATUS_CHANGE', { 
                  new_status: 'AVAILABLE', 
                  reason: 'Fim de Setup' 
              });

              // 3. Atualiza estado local da Ordem
              if (activeOrder.value) {
                  activeOrder.value.status = 'PENDING'; 
              }

          } catch (e) {
              console.error("Erro ao sair do setup:", e);
          }
      } 
      // --- ENTRAR NO MODO SETUP ---
      else {
          try {
              if (activeOrder.value) {
                  activeOrder.value.status = 'SETUP';
              }

              // 1. Registra Log de INÍCIO
              // O campo 'reason' contendo "Setup" é crucial para o gráfico classificar como Produtivo
              await sendEvent('STATUS_CHANGE', { 
                  new_status: 'SETUP', 
                  reason: 'Início de Setup' 
              });

              // 2. Bloqueia a máquina no banco (Dashboard fica Vermelho/Manutenção)
              // Usamos MAINTENANCE porque "Setup" não existe no Enum do banco
              await setMachineStatus('MAINTENANCE'); 
              
          } catch (e) {
              console.error("Erro ao entrar em setup:", e);
          }
      }
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
      resource: sapOp.code, // Código da operação para o roteamento
      name: sapOp.description,
      description: `ETAPA IMPROVISADA/IMPREVISTA: Execução realizada no recurso ${machineName.value} conforme necessidade de fábrica.`,
      timeEst: 0,
      status: 'PENDING'
    };

    // Injeta a etapa no roteiro atual
    if (!activeOrder.value.steps) activeOrder.value.steps = [];
    activeOrder.value.steps.push(newStep);
    
    // Define como a etapa atual (última adicionada)
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
      await api.post('/production/session/stop', { machine_id: machineId.value, operator_badge: currentOperatorBadge.value });
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
          const payload = { vehicle_id: machineId.value, problem_description: `Kiosk: ${notes}`, category: 'Mecânica', maintenance_type: 'CORRETIVA' };
          await api.post('/maintenance/requests', payload);
          
          // Força status de manutenção
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
        // Feedback visual imediato
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

  return {
    machinesList, machineId, currentMachine, machineName, machineSector,
    currentOperator, currentOperatorBadge, activeOrder, machineHistory,
    currentStepIndex, currentActiveStep,
    isKioskConfigured, isShiftActive, isMachineBroken, isRunning, hasActiveOrder,
    loadKioskConfig, _setMachineData, setMachineStatus,
    fetchAvailableMachines, configureKiosk, fetchMachineHistory,
    loginOperator, logoutOperator, loadOrderFromQr, finishSession,
    createMaintenanceOrder, sendEvent, triggerAndon,
    startStep, pauseStep, finishStep, startProduction, pauseProduction, isInSetup, toggleSetup, addProduction, activeOperator, identifyOperator, clearOperator,
    machineResource, setImprovisedStep
  };
});
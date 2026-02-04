/* eslint-disable @typescript-eslint/no-explicit-any */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { Notify, Loading } from 'quasar';
import { api } from 'boot/axios';
import {AndonService} from 'src/services/andon-service'; // Importe o novo serviço
import type { AndonCallCreate } from 'src/services/andon-service';
import { findBestStepIndex } from 'src/data/sap-operations'; // <--- IMPORT NOVO

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
      // Verifica se o status local da ordem é SETUP
      if (activeOrder.value?.status === 'SETUP') return true;
      
      // Verifica se o status da máquina no banco indica manutenção/setup
      // (Lembrando que no banco salvamos "Em manutenção" para setup)
      const machStatus = (currentMachine.value?.status || '').toUpperCase();
      
      // Se estiver "Em manutenção" mas a ordem estiver rodando ou pausada, não é setup.
      // Setup é quando explicitamente colocamos a flag.
      // Simplificação: Se o último log foi SETUP, estamos em setup.
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
    if (!machineId.value) return;
    try {
        // Busca os dados da sessão/ordem que o banco diz que está ativa para esta máquina
        const { data } = await api.get(`/production/session/active/${machineId.value}`);
        if (data && data.order) {
            console.log("🟢 [STORE] Sessão ativa recuperada do banco:", data.order.code);
            activeOrder.value = data.order; // Preenche a ordem
            currentStepIndex.value = data.current_step_index;
        }
    } catch (e) {
        console.warn("⚠️ [STORE] Nenhuma sessão ativa encontrada para esta máquina.");
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

      try {
          await api.post('/production/machine/status', { machine_id: machineId.value, status: status });
          
          if (currentMachine.value) {
              const s = status.toUpperCase();
              
              if (s === 'RUNNING' || s === 'IN_USE' || s === 'EM USO') {
                  currentMachine.value.status = 'Em uso';
              } 
              else if (s === 'AVAILABLE' || s === 'IDLE' || s === 'DISPONIVEL') {
                  currentMachine.value.status = 'Disponível';
              } 
              else if (s === 'MAINTENANCE' || s === 'BROKEN') {
                  currentMachine.value.status = 'Manutenção';
              } 
              // --- ADICIONE ESTE BLOCO ---
              else if (s === 'STOPPED' || s === 'PARADA' || s === 'PAUSED') {
                  currentMachine.value.status = 'Em Pausa'; 
              }
              // ---------------------------
              else {
                  currentMachine.value.status = status;
              }
          }
      } catch (e) {
          console.error("Erro ao atualizar status da máquina:", e);
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
    // Usa o badge que veio por parâmetro OU o que está na Store
    const badge = badgeOverride || currentOperatorBadge.value;

    if (!machineId.value || !badge) {
        console.warn(`[DEBUG KIOSK] Bloqueado: Evento ${type} sem operador identificado.`);
        return;
    }
    
    const eventPayload = { 
        machine_id: machineId.value, 
        operator_badge: badge, 
        order_code: activeOrder.value?.code, 
        event_type: type, 
        ...payload 
    };

    try { 
        await api.post('/production/event', eventPayload); 
    } catch (e) { 
        console.error('Falha de sincronização MES', e); 
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
    if (isMachineBroken.value) { Notify.create({ type: 'negative', message: 'Máquina em manutenção.' }); return; }
    try {
      Loading.show({ message: 'Carregando O.P...' });
      
      let data: ProductionOrder;
      try {
          const res = await api.get<ProductionOrder>(`/production/orders/${qrCode}`);
          data = res.data;
      } catch {
          console.warn("API falhou, usando mock local");
          data = {
              id: 999, code: qrCode, client: 'Technip Brasil', product: 'DEWATERING HOSE',
              deliveryDate: '15/10/2025', part_name: 'Suporte', 
              part_image_url: 'https://placehold.co/600x400/png',
              technical_drawing_url: 'https://placehold.co/800x600/008C7A/FFFFFF/png?text=DESENHO+TECNICO+VEMAG', 
              target_quantity: 50, produced_quantity: 0, scrap_quantity: 0, 
              status: 'PENDING', operations: [], steps: []
          } as ProductionOrder;
      }
      
      if (!data.status) data.status = 'PENDING';
      
      activeOrder.value = { 
        ...activeOrder.value, // Mantém o que já tinha (Meta, Nome, Código)
        ...data,              // Adiciona o que veio da API (Roteiro, Desenho)
        status: data.status || 'PENDING'
      };
      
      // Pega o recurso da máquina configurada no Kiosk
      const myResource = machineResource.value; 

      // Chama nossa função matchmaker
      const bestIndex = findBestStepIndex(myResource, activeOrder.value.steps || []);

      if (bestIndex !== -1) {
          currentStepIndex.value = bestIndex;
          
          // Feedback visual chique
          const stepName = activeOrder.value.steps![bestIndex].name;
          Notify.create({ 
              type: 'positive', 
              icon: 'gps_fixed',
              message: `Etapa identificada para esta máquina: #${(bestIndex+1)*10} - ${stepName}`,
              timeout: 4000
          });
      } else {
          // AGORA: Se não achar, não faz nada automaticamente. 
          // A lógica de perguntar será na Página (Vue).
          currentStepIndex.value = -1; 
      }

      if (currentOperatorBadge.value && machineId.value) {
          const currentStep = activeOrder.value.steps?.[currentStepIndex.value];
          const stageStr = currentStep ? String(currentStep.seq) : '010';

          console.log("📡 [STORE] Iniciando Sessão e Log de Setup...");
          
          // 1. Inicia a sessão técnica
          await api.post('/production/session/start', {
            machine_id: machineId.value, 
            operator_badge: currentOperatorBadge.value, 
            op_number: String(qrCode),
            step_seq: stageStr
          });
          
          // 2. NOVA LINHA: Registra o evento de log para o KPI de Setup
          // Sem isso, o painel de performance não "vê" que o setup começou
          await sendEvent('STATUS_CHANGE', { 
              new_status: 'SETUP', 
              reason: 'Setup Inicial (Seleção de O.P.)' 
          });

          activeOrder.value.status = 'SETUP';
          await setMachineStatus('SETUP');
      }

    } catch (e) { 
      Notify.create({ type: 'negative', message: 'Erro crítico ao carregar.' }); 
      activeOrder.value = null;
    } finally { 
      Loading.hide(); 
    }
  }

  async function startProduction() { 
      if (activeOrder.value) activeOrder.value = { ...activeOrder.value, status: 'RUNNING' };

      
      // 1. Registra o Log
      await sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' }); 
      
      // 2. FORÇA O STATUS NO BANCO (Isso corrige o dashboard)
      await setMachineStatus('RUNNING');
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

              // 2. Libera a máquina no banco (Dashboard fica Verde/Disponível)
              await setMachineStatus('AVAILABLE');

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
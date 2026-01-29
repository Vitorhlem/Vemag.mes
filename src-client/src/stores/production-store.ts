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
  const machineId = ref<number | null>(null);
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

  // --- DADOS MOCKADOS (Baseado na O.P. 3940/0 Real) ---
  const MOCK_OP_STEPS: OperationStep[] = [
      { 
        seq: 10, 
        resource: '2.13', 
        name: 'SUPORTE TÉCNICO DA QUALIDADE', 
        timeEst: 0.5, 
        status: 'PENDING', 
        description: `SUPORTE PARA MANGUEIRA DE DRENAGEM - DESENHO - 300232C-000-DW-5837-0002 - REV.0\n\n1. MATÉRIA-PRIMA FORNECIMENTO VEMAG.\n2. REALIZAR INSPEÇÃO DE RECEBIMENTO DA MATÉRIA-PRIMA.\n3. REGISTRAR NÚMERO DA (O.P.).` 
      },
      { 
        seq: 20, 
        resource: '3.01', 
        name: 'OXICORTE', 
        timeEst: 2.0, 
        status: 'PENDING', 
        description: `1. OXICORTAR AS PEÇAS DE ACORDO COM AS ESPECÍFICAS ESPESSURAS DAS CHAPAS E PROGRAMA CNC.\n2. IDENTIFICAR AS PEÇAS COM O NÚMERO DA (O.P.).` 
      },
      { 
        seq: 30, 
        resource: '3.05', 
        name: 'REBARBAÇÃO DE CALDEIRARIA', 
        timeEst: 0.5, 
        status: 'PENDING', 
        description: `1. REMOVER CAREPAS E REBARBAS DO OXICORTE.\n2. DAR ACABAMENTO EM TODO O CONTORNO DAS PEÇAS ATRAVÉS DE ESMERILHAMENTOS.\n3. MANTER O AUTO CONTROLE E A IDENTIFICAÇÕES DAS PEÇAS.` 
      },
      { 
        seq: 40, 
        resource: '4.10', 
        name: 'TRAÇAGEM', 
        timeEst: 1.0, 
        status: 'PENDING', 
        description: `(EXECUTAR AS TRAÇAGENS DAS COORDENADAS NAS CHAPAS OXICORTADAS, CONFORME OS RESPECTIVOS DESENHOS "DE")\n\nNOTAS:\n01- QUANTIDADES CONFORME DESENHO "DE"\n\nITENS POS. 4 - CHAPA OLHAL #5/8" x 40 mm x 50 mm x R20 mm - DESENHO - DE-1481.01.001\n- (1x) TRAÇAR FURO PASSANTE (Ø15 mm)\n\nITENS POS. 1 - CHAPA #1/2" x 100 mm x 250 mm - DESENHO - DE-1481.01.002\n- (4x) TRAÇAR FURO PASSANTE (Ø11 mm)\n\nITENS POS. 2 - CHAPA #3/4" x 670 mm x 930 mm - DESENHO - DE-1481.01.003\n- (4x) TRAÇAR ROSCA PASSANTES (M10 x 1,5)\n\n(MANTER AS IDENTIFICAÇÕES DAS PEÇAS).` 
      },
      { 
        seq: 50, 
        resource: '4.06', 
        name: 'RADIAL P', 
        timeEst: 2.0, 
        status: 'PENDING', 
        description: `(EXECUTAR AS FURAÇÕES DOS RESPECTIVOS ITENS ABAIXO, SEGUINDO AS MARCAÇÕES DAS TRAÇAGENS, CONFORME OS RESPECTIVOS DESENHOS "DE")\n\nNOTAS:\n01- QUANTIDADES CONFORME DESENHO "DE"` 
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
      localStorage.setItem('TRU_MACHINE_ID', String(data.id));
      Notify.create({ type: 'positive', message: 'Terminal Configurado!' });
    } catch { Notify.create({ type: 'negative', message: 'Erro ao configurar terminal.' }); }
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
    
    console.log(`[DEBUG KIOSK] 1. Iniciando Login. Código Scaneado: "${scannedCode}"`); // LOG 1
    
    Loading.show({ message: 'Validando...' });
    
    try {
      // Chama a rota específica de identificação
      console.log(`[DEBUG KIOSK] 2. Chamando API: /production/operator/${scannedCode}`); // LOG 2
      const { data: operator } = await api.get(`/production/operator/${scannedCode}`);

      console.log('[DEBUG KIOSK] 3. Operador Retornado API:', operator); // LOG 3

      // REGISTRA O LOGIN
      const loginPayload = {
        machine_id: machineId.value,
        operator_badge: operator.employee_id, // Força uso do ID retornado
        event_type: 'LOGIN',
        new_status: 'IDLE',
        reason: 'Início de Turno'
      };
      
      console.log('[DEBUG KIOSK] 4. Enviando Evento Login:', loginPayload); // LOG 4
      await api.post('/production/event', loginPayload);
      await setMachineStatus('AVAILABLE');

      // ATUALIZA ESTADO
      currentOperator.value = operator;
      currentOperatorBadge.value = operator.employee_id; // <--- O PULO DO GATO
      
      console.log('[DEBUG KIOSK] 5. Estado Atualizado. Badge Ativo:', currentOperatorBadge.value); // LOG 5

      localStorage.setItem('TRU_CURRENT_OPERATOR', JSON.stringify(operator));
      
      if (!isMachineBroken.value && currentMachine.value) {
          currentMachine.value = { ...currentMachine.value, status: 'Disponível' };
      }
      
      Notify.create({ 
        type: 'positive', 
        message: `Bem-vindo, ${operator.full_name.split(' ')[0]}!`,
        caption: `Matrícula: ${operator.employee_id}`
      });

    } catch (error: any) { 
      console.error('[DEBUG KIOSK] ERRO:', error); 
      const msg = error.response?.data?.detail || 'Crachá não identificado.';
      Notify.create({ type: 'negative', message: msg }); 
    } finally { 
      Loading.hide(); 
    }
  }

  async function sendEvent(type: string, payload: Record<string, unknown> = {}) {
    if (!machineId.value || !currentOperatorBadge.value) {
        console.warn('[DEBUG KIOSK] Tentativa de evento sem operador ou máquina!');
        return;
    }
    
    const eventPayload = { 
        machine_id: machineId.value, 
        operator_badge: currentOperatorBadge.value, // <--- Verifica se isso é o Admin ou Operador
        order_code: activeOrder.value?.code, 
        event_type: type, 
        ...payload 
    };

    console.log(`[DEBUG KIOSK] Enviando Evento (${type}):`, eventPayload); // LOG EVENTOS

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
      
      if (!data.steps || data.steps.length === 0) {
          data.steps = JSON.parse(JSON.stringify(MOCK_OP_STEPS));
      }

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
          // Fallback: Se não achou nada, vai pro início, mas avisa
          currentStepIndex.value = 0;
          Notify.create({ 
              type: 'warning', 
              icon: 'warning',
              message: 'Atenção: Nenhuma etapa deste roteiro parece ser para esta máquina.',
              timeout: 6000
          });
      }

      if (currentOperatorBadge.value && machineId.value) {
          // Pegamos a sequência da etapa que o roteamento identificou
          const currentStep = activeOrder.value.steps?.[currentStepIndex.value];
          const stageStr = currentStep ? String(currentStep.seq) : '010';

          console.log("📡 [STORE] Iniciando Sessão Automática via loadOrder...");
          
          await api.post('/production/session/start', {
    machine_id: machineId.value, 
    operator_badge: currentOperatorBadge.value, 
    op_number: String(qrCode),
    step_seq: stageStr
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
    machineResource
  };
});
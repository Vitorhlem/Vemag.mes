/* eslint-disable @typescript-eslint/no-explicit-any */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { Notify, Loading } from 'quasar';
import { api } from 'boot/axios';

export interface Machine {
  id: number;
  brand: string;
  model: string;
  license_plate?: string;
  status?: string; 
  category?: string;
  current_driver_id?: number;
}

export interface ProductionOrder {
  id: number;
  code: string;
  part_name: string;
  part_image_url: string;
  target_quantity: number;
  produced_quantity: number;
  scrap_quantity: number;
  status: 'PENDING' | 'SETUP' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'STOPPED' | 'IDLE' | 'MAINTENANCE' | 'AVAILABLE';
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

export const useProductionStore = defineStore('production', () => {
  
  // --- ESTADO ---
  const machinesList = ref<Machine[]>([]);
  const machineId = ref<number | null>(null);
  const currentMachine = ref<Machine | null>(null);
  const machineName = ref<string>('Não Configurado');
  const machineSector = ref<string>('-');

  const currentOperatorBadge = ref<string | null>(null);
  const activeOrder = ref<ProductionOrder | null>(null);
  const machineHistory = ref<ProductionLog[]>([]);

  // --- GETTERS ---
  const isKioskConfigured = computed(() => !!machineId.value);
  const isShiftActive = computed(() => !!currentOperatorBadge.value);
  
  // === CORREÇÃO CRÍTICA DO GETTER ===
  // O banco retorna "Em manutenção". O código busca por "manutenção" ou "maintenance".
const isMachineBroken = computed(() => {
      // 1. Pega o status atual do objeto da máquina
      const rawStatus = currentMachine.value?.status || '';
      
      // 2. Normaliza para minúsculo e remove acentos para evitar erros (ex: "manutenção" vira "manutencao")
      // Isso é vital para funcionar em qualquer navegador/banco
      const status = String(rawStatus)
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");
      
      // 3. Verifica as palavras-chave (Inglês e Português)
      // O banco manda "Em manutenção", que virou "em manutencao".
      // A verificação abaixo vai encontrar "manutencao" e retornar TRUE.
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
      } catch {
        console.warn('Máquina salva offline ou removida.');
      }
    }
  }

  async function fetchAvailableMachines() {
    try {
      const { data } = await api.get<Machine[]>('/machines', { params: { limit: 100 } });
      machinesList.value = data;
    } catch {
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

  // Define Status Manualmente (ex: Quebra)
  // Envia "MAINTENANCE" (Inglês) para API -> API converte para "Em manutenção"
  async function setMachineStatus(status: string) {
    // ATUALIZAÇÃO OTIMISTA: Muda na hora para garantir a UI
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

  async function loginOperator(badge: string) {
    if (!machineId.value) return;
    try {
      Loading.show();
      await api.post('/production/event', {
        machine_id: machineId.value,
        operator_badge: badge,
        event_type: 'LOGIN',
        new_status: 'IDLE',
        reason: 'Início de Turno'
      });
      currentOperatorBadge.value = badge;
      
      // Se não estiver quebrada, vai para Disponível.
      if (!isMachineBroken.value && currentMachine.value) {
          currentMachine.value.status = 'Disponível';
      }
      Notify.create({ type: 'positive', message: 'Login Efetuado' });
    } catch {
      Notify.create({ type: 'negative', message: 'Crachá Inválido' });
      throw new Error('Login falhou');
    } finally {
      Loading.hide();
    }
  }

  // --- LOGOUT INTELIGENTE ---
  // Envia "MAINTENANCE" para API se a máquina estiver quebrada
  async function logoutOperator(overrideStatus?: string) {
    if (!machineId.value || !currentOperatorBadge.value) return;
    
    let statusToSend = 'AVAILABLE';
    let visualStatus = 'Disponível'; // Para UI imediata

    // Se forçado ou já estiver quebrada, manda MAINTENANCE
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
      
      // Atualiza localmente
      if (currentMachine.value) {
          currentMachine.value.status = visualStatus;
      }
      
    } catch (error) {
       console.error('Erro ao deslogar:', error);
    }
    currentOperatorBadge.value = null;
    activeOrder.value = null;
  }

  async function loadOrderFromQr(qrCode: string) {
    if (isMachineBroken.value) {
        Notify.create({ type: 'negative', message: 'Máquina em manutenção. Necessário liberar.' });
        return;
    }

    try {
      Loading.show();
      const { data } = await api.get<ProductionOrder>(`/production/orders/${qrCode}`);
      activeOrder.value = data;
      
      if (currentOperatorBadge.value && machineId.value) {
         await api.post('/production/session/start', {
            machine_id: machineId.value,
            operator_badge: currentOperatorBadge.value,
            order_code: data.code
         });
      }
      Notify.create({ type: 'positive', message: 'O.P. Iniciada com Sucesso' });
    } catch { 
      Notify.create({ type: 'negative', message: 'O.S. não encontrada.' });
    } finally {
      Loading.hide();
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
      Notify.create({ type: 'positive', message: 'O.P. Finalizada! Dados salvos.' });
      activeOrder.value = null;
    } catch { 
      Notify.create({ type: 'negative', message: 'Erro ao finalizar O.P.' });
    } finally {
      Loading.hide();
    }
  }

  async function createMaintenanceOrder(notes: string) {
      if (!machineId.value) return;
      try {
          Loading.show();
          
          // --- CORREÇÃO BASEADA NO SEU SCHEMA ---
          const payload = {
              vehicle_id: machineId.value,
              
              // Campo obrigatório conforme seu schema
              problem_description: `Abertura via Kiosk: ${notes}`,
              
              // Campo obrigatório (Enum). 
              // Tente 'MECANICA', 'ELETRICA' ou 'OUTROS' (deve ser maiúsculo)
              category: 'Mecânica', 
              
              // Opcional, mas vamos garantir
              maintenance_type: 'CORRETIVA'
          };

          // Não enviamos mais 'priority' nem 'status', pois seu Schema não aceita na criação.
          
          await api.post('/maintenance/requests', payload);
          
          // Atualiza visualmente para 'Em manutenção'
          if(currentMachine.value) currentMachine.value.status = 'Em manutenção';
          
          Notify.create({ 
              type: 'positive', 
              icon: 'build_circle',
              message: 'Ordem de Manutenção Aberta!',
              caption: 'A equipe de manutenção foi notificada.' 
          });
      } catch (error: any) { 
          console.error('Erro ao criar O.M.:', error.response?.data);
          
          // Tratamento de erro detalhado para você saber o que houve
          const detail = error.response?.data?.detail;
          let msg = 'Erro ao processar dados.';
          
          if (Array.isArray(detail)) {
              // Pega o primeiro erro da lista
              msg = `Campo inválido: ${detail[0]?.loc?.[1]} - ${detail[0]?.msg}`;
              
              // Dica específica para erro de categoria
              if (detail[0]?.loc?.[1] === 'category') {
                  msg += ' (Verifique se a categoria MECANICA existe no backend)';
              }
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
      // Atualiza visualmente para garantir
      if (payload.new_status === 'RUNNING' && currentMachine.value) {
         currentMachine.value.status = 'Em uso';
      }
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
    currentOperatorBadge, activeOrder, machineHistory,
    isKioskConfigured, isShiftActive, isMachineBroken,
    loadKioskConfig, _setMachineData, setMachineStatus,
    fetchAvailableMachines, configureKiosk, fetchMachineHistory,
    loginOperator, logoutOperator, loadOrderFromQr, finishSession,
    startProduction, pauseProduction, addProduction, createMaintenanceOrder,
    sendEvent, triggerAndon 
  };
});
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

  // --- ACTIONS ---

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
      const { data } = await api.get<Machine[]>('/production/machines', { params: { limit: 100 } });
      machinesList.value = data;
    } catch {
      Notify.create({ type: 'negative', message: 'Erro ao buscar máquinas.' });
    }
  }

  async function configureKiosk(id: number) {
    try {
      const { data } = await api.get<Machine>(`/vehicles/${id}`);
      _setMachineData(data);
      localStorage.setItem('TRU_MACHINE_ID', String(data.id));
      Notify.create({ type: 'positive', message: 'Terminal Vinculado!' });
    } catch {
      Notify.create({ type: 'negative', message: 'Erro ao configurar.' });
    }
  }

  function _setMachineData(data: Machine) {
    currentMachine.value = data;
    machineId.value = data.id;
    machineName.value = `${data.brand} ${data.model}`;
    machineSector.value = data.category || 'Geral';
  }

  // CORREÇÃO AQUI: Tipagem explícita para aceitar undefined/null no event_type
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
      if (currentMachine.value) currentMachine.value.status = 'IDLE';
      Notify.create({ type: 'positive', message: 'Login Efetuado' });
    } catch {
      Notify.create({ type: 'negative', message: 'Crachá Inválido' });
      throw new Error('Login falhou');
    } finally {
      Loading.hide();
    }
  }

  async function logoutOperator() {
    if (!machineId.value || !currentOperatorBadge.value) return;
    try {
      await api.post('/production/event', {
        machine_id: machineId.value,
        operator_badge: currentOperatorBadge.value,
        event_type: 'LOGOUT',
        new_status: 'AVAILABLE',
        reason: 'Logoff'
      });
    } catch (error) {
       console.error('Erro ao deslogar:', error);
    }
    currentOperatorBadge.value = null;
    activeOrder.value = null;
  }

  async function loadOrderFromQr(qrCode: string) {
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
    } catch (e) {
      Notify.create({ type: 'negative', message: 'O.S. não encontrada ou erro ao iniciar sessão.' });
      console.error(e);
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
      if (currentMachine.value) currentMachine.value.status = 'AVAILABLE';
    } catch (e) {
      Notify.create({ type: 'negative', message: 'Erro ao finalizar O.P.' });
      console.error(e);
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
      
      if (payload.new_status && typeof payload.new_status === 'string') {
         if (activeOrder.value) activeOrder.value.status = payload.new_status as ProductionOrder['status'];
         if (currentMachine.value) currentMachine.value.status = payload.new_status;
      }
    } catch (e) {
      console.error('Falha de sync', e);
    }
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

  async function startProduction() { 
    await sendEvent('STATUS_CHANGE', { new_status: 'RUNNING' }); 
  }
  
  async function pauseProduction(reason: string) { 
    await sendEvent('STATUS_CHANGE', { new_status: 'STOPPED', reason }); 
  }
  
  function addProduction(qty: number, isScrap = false) {
    if (!activeOrder.value) return;
    if (isScrap) activeOrder.value.scrap_quantity += qty;
    else activeOrder.value.produced_quantity += qty;
    
    void sendEvent('COUNT', { quantity_good: isScrap ? 0 : qty, quantity_scrap: isScrap ? qty : 0 });
  }

  return {
    machinesList, machineId, currentMachine, machineName, machineSector,
    currentOperatorBadge, activeOrder, machineHistory,
    isKioskConfigured, isShiftActive,
    loadKioskConfig, fetchAvailableMachines, configureKiosk, fetchMachineHistory,
    loginOperator, logoutOperator, loadOrderFromQr, finishSession,
    startProduction, pauseProduction, addProduction,
    sendEvent, triggerAndon 
  };
});
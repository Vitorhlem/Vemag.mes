import { defineStore } from 'pinia';
import { ref } from 'vue';
import { api } from 'boot/axios';

// --- INTERFACES (MANTIDAS) ---
export interface OEEMetrics {
  oee_percentage: number;
  availability: number;
  performance: number;
  quality: number;
  metrics: {
    total_time_min: number;
    planned_stop_min: number;
    producing_min: number;
  };
}

export interface ProductionLog {
  id: number;
  event_type: string;
  timestamp: string;
  new_status: string;
  reason: string;
  details: string;
  operator_name: string;
  operator_id?: number;    // ID do usuário no banco (para o link)
  operator_badge?: string; // Crachá (para exibição visual)
}

export interface TimelineBlock {
  status: string;
  start: string;
  end: string;
  duration_min: number;
  reason?: string | null;
  operator_name?: string | null;
  color: string;
}

export interface DailyMetric {
  id: number;
  employee_name: string;
  total_hours: number;
  productive_hours: number;
  unproductive_hours: number;
  efficiency: number;
  top_reasons: { label: string; count: number }[];
  closed_at: string;
}

export interface VehicleMetric {
  id: number;
  vehicle_name: string;
  running_hours: number;
  maintenance_hours: number;
  idle_hours: number;
  availability: number;
  utilization: number;
  top_reasons: { label: string; count: number }[];
}

export interface EmployeeStat {
  id: number;
  employee_name: string;
  total_hours: number;
  productive_hours: number;
  unproductive_hours: number;
  efficiency: number;
  top_reasons: { label: string; count: number }[];
}

export interface SessionDetail {
  id: number;
  machine_name: string;
  order_code: string;
  start_time: string;
  end_time: string | null;
  duration: string;
  efficiency: number;
}

export const useMesStore = defineStore('mes', () => {
  
  // Estados
  const oeeData = ref<OEEMetrics | null>(null);
  const rawLogs = ref<ProductionLog[]>([]);
  const timeline = ref<TimelineBlock[]>([]);
  const employeeStats = ref<EmployeeStat[]>([]);
  const userSessions = ref<SessionDetail[]>([]);
  const isLoading = ref(false);
  const dailyHistory = ref<DailyMetric[]>([]);
  const dailyEmployeeHistory = ref<DailyMetric[]>([]);
  const dailyVehicleHistory = ref<VehicleMetric[]>([]);

  // --- ACTIONS ---

  async function fetchMachineOEE(machineId: number, start: string, end: string) {
    try {
      isLoading.value = true;
      const { data } = await api.get<OEEMetrics>(`/production/stats/machine/${machineId}/oee`, {
        params: { start_date: start, end_date: end }
      });
      oeeData.value = data;
    } catch (error) {
      console.error('Erro OEE', error);
      oeeData.value = null;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchDailyTimeline(machineId: number, dateStr: string) {
    try {
      isLoading.value = true;
      // Garante que rawLogs seja limpo antes de popular
      rawLogs.value = [];
      timeline.value = [];

      const { data } = await api.get<ProductionLog[]>(`/production/history/${machineId}`, {
        params: { limit: 1000 } // Traz logs suficientes para montar o dia
      });
      
      rawLogs.value = data; // Popula a tabela de histórico
      processTimeline(data, dateStr); // Monta o Gantt
    } catch (error) {
      console.error('Erro Timeline', error);
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchEmployeeStats(start: string, end: string) {
    try {
      isLoading.value = true;
      const { data } = await api.get<EmployeeStat[]>('/production/stats/employees', {
        params: { start_date: start, end_date: end }
      });
      employeeStats.value = data;
    } catch (error) {
      console.error('Erro Stats Funcionario', error);
      employeeStats.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchDailyHistory(date: string) {
    try {
      isLoading.value = true;
      const [resEmp, resVeh] = await Promise.all([
        api.get<DailyMetric[]>('/production/reports/daily-closing/employees', { params: { target_date: date } }),
        api.get<VehicleMetric[]>('/production/reports/daily-closing/vehicles', { params: { target_date: date } })
      ]);
      
      dailyEmployeeHistory.value = resEmp.data;
      dailyVehicleHistory.value = resVeh.data;
    } catch (error) {
      console.error('Erro ao buscar histórico consolidado', error);
    } finally {
      isLoading.value = false;
    }
  }

  async function forceDailyClosing(date: string) {
    try {
      isLoading.value = true;
      await api.post('/production/closing/force', { target_date: date });
      await fetchDailyHistory(date);
      return true;
    } catch (error) {
      console.error('Erro ao processar fechamento', error);
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchUserSessions(userId: number, start: string, end: string) {
    try {
      isLoading.value = true;
      const { data } = await api.get<SessionDetail[]>(`/production/users/${userId}/sessions`, {
        params: { start_date: start, end_date: end }
      });
      userSessions.value = data;
    } catch (error) {
      console.error('Erro User Sessions', error);
      userSessions.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  // --- HELPERS (LÓGICA CORRIGIDA PARA BATER COM O COCKPIT) ---
  function processTimeline(logs: ProductionLog[], targetDate: string) {
    if (!logs || logs.length === 0) {
        timeline.value = [];
        return;
    }

    // 1. Ordena logs cronologicamente
    const sorted = [...logs].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    const blocks: TimelineBlock[] = [];
    
    // 2. Define limites exatos do dia (00:00:00 a 23:59:59)
    const dayStart = new Date(targetDate + 'T00:00:00');
    const dayEnd = new Date(targetDate + 'T23:59:59');
    
    for (let i = 0; i < sorted.length; i++) {
      const current = sorted[i];
      // O próximo evento define o fim do evento atual.
      // Se não houver próximo (é o último do array), assumimos que vai até "agora" ou fim do dia.
      const nextTimestamp = sorted[i+1]?.timestamp || new Date().toISOString(); 
      
      const startTime = new Date(current.timestamp);
      let endTime = new Date(nextTimestamp);

      // 3. CORTES DE TEMPO (BORDAS DO DIA)
      // Se o evento começou ANTES de hoje, mas terminou HOJE (ou depois), corta o início para 00:00
      if (startTime < dayStart) {
          if (endTime < dayStart) continue; // Evento totalmente no passado, ignora
          startTime.setHours(0,0,0,0); 
      }

      // Se o evento começou HOJE, mas termina AMANHÃ, corta o fim para 23:59
      if (endTime > dayEnd) {
          endTime = dayEnd; 
      }

      // Validação básica: se o corte resultou em tempo negativo ou zerado, ignora
      if (endTime <= startTime) continue;

      const durationMin = (endTime.getTime() - startTime.getTime()) / 1000 / 60;
      
      // 4. NORMALIZAÇÃO DE STATUS E CORREÇÃO DE LÓGICA
      const rawStatus = String(current.new_status || '').toUpperCase().trim();
      const rawReason = String(current.reason || '').toUpperCase().trim();
      const rawEventType = String(current.event_type || '').toUpperCase().trim();

      let finalStatusForGantt = 'OCIOSO';
      let customColor = ''; 

      // Verificação auxiliar para saber se está rodando
      const isRunning = ['RUNNING', 'EM USO', 'EM OPERAÇÃO', 'IN_USE'].includes(rawStatus);

      // --- CORREÇÃO: PRODUÇÃO AUTÔNOMA (TROCA DE TURNO) ---
      
      // CASO 1: O início do buraco (Operador Saiu mantendo a máquina rodando)
      // Verifica se é LOGOUT/SAÍDA ou se o motivo fala de Logoff/Troca
      const isAutonomousStart = isRunning && (
          rawEventType.includes('SAÍDA') || 
          rawEventType.includes('LOGOUT') ||
          rawReason.includes('LOGOFF') || 
          rawReason.includes('TROCA DE TURNO')
      );

      // CASO 2: O meio da transição (Operador Entrou, mas ainda não assumiu)
      // Pintamos o Login de AZUL também para ele não criar uma fatia verde minúscula no meio.
      // Isso une visualmente o Logoff até o "Assumir".
      const isAutonomousTransition = isRunning && (
          rawEventType.includes('ENTRADA') || 
          rawEventType.includes('LOGIN')
      );

      if (isAutonomousStart || isAutonomousTransition) {
           finalStatusForGantt = 'AUTONOMOUS';
           customColor = '#2196F3'; // Azul Material Design
      } 
      else {
          // --- LÓGICA PADRÃO ---

          // GRUPO 1: EM OPERAÇÃO (Verde)
          if (isRunning) {
             finalStatusForGantt = 'RUNNING'; 
          }
          
          // GRUPO 2: MANUTENÇÃO / SETUP (Roxo ou Vermelho)
          else if (
              ['SETUP', 'MAINTENANCE', 'EM MANUTENÇÃO', 'MANUTENÇÃO'].includes(rawStatus) ||
              rawReason.includes('SETUP') || 
              rawEventType.includes('SETUP')
          ) {
              if (rawStatus === 'SETUP' || rawReason.includes('SETUP')) {
                  finalStatusForGantt = 'SETUP';
              } else {
                  finalStatusForGantt = 'MAINTENANCE';
              }
          }

          // GRUPO 3: PARADA (Laranja)
          else if (['PAUSED', 'PARADA', 'STOPPED', 'AVAILABLE', 'DISPONÍVEL'].includes(rawStatus)) {
              finalStatusForGantt = 'PAUSED';
          }
          
          // FALLBACK
          else {
              finalStatusForGantt = 'PAUSED'; 
          }
      }

      blocks.push({
        status: finalStatusForGantt,
        start: startTime.toISOString(),
        end: endTime.toISOString(),
        duration_min: Math.round(durationMin),
        reason: current.reason || null,
        operator_name: current.operator_name || null,
        color: customColor // Passa a cor azul se for autônomo, ou vazio p/ padrão
      });
    }
    
    timeline.value = blocks;
  }

  return {
    oeeData,
    rawLogs,
    timeline,
    employeeStats,
    userSessions,
    isLoading,
    fetchMachineOEE,
    fetchDailyTimeline,
    fetchEmployeeStats,
    fetchUserSessions,
    dailyHistory,
    fetchDailyHistory,
    forceDailyClosing,
    dailyEmployeeHistory,
    dailyVehicleHistory,
  };
});
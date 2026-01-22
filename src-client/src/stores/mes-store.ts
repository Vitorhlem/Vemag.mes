import { defineStore } from 'pinia';
import { ref } from 'vue';
import { api } from 'boot/axios';

// --- INTERFACES ---
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
}

export interface TimelineBlock {
  status: string;
  start: string;
  end: string;
  duration_min: number;
  reason?: string | null; // CORREÇÃO: Aceita null
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

// Detalhe de Sessão para o Dossiê
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
  const dailyHistory = ref<DailyMetric[]>([]); // Novo State
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
      const { data } = await api.get<ProductionLog[]>(`/production/history/${machineId}`, {
        params: { limit: 1000 }
      });
      rawLogs.value = data;
      processTimeline(data, dateStr);
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
      // Busca em paralelo
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

  // [NOVO] Forçar Fechamento Manual
  async function forceDailyClosing(date: string) {
    try {
      isLoading.value = true;
      await api.post('/production/closing/force', { target_date: date });
      // Após forçar, recarrega a lista para mostrar o resultado
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

  // --- HELPERS ---
  function processTimeline(logs: ProductionLog[], targetDate: string) {
    const sorted = [...logs].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    const blocks: TimelineBlock[] = [];
    const dayStart = new Date(targetDate + 'T00:00:00');
    const dayEnd = new Date(targetDate + 'T23:59:59');
    
    for (let i = 0; i < sorted.length - 1; i++) {
        const current = sorted[i];
        const next = sorted[i+1];
        
        // CORREÇÃO: Verificação de existência
        if (!current || !next) continue;

        const startTime = new Date(current.timestamp);
        const endTime = new Date(next.timestamp);
        
        if (startTime >= dayStart && startTime <= dayEnd) {
            const durationMin = (endTime.getTime() - startTime.getTime()) / 1000 / 60;
            
            let color = 'grey-4';
            const s = (current.new_status || '').toUpperCase();
            if (['RUNNING', 'EM OPERAÇÃO', 'EM USO'].includes(s)) color = 'positive';
            else if (['STOPPED', 'PARADA', 'PAUSED'].includes(s)) color = 'negative';
            else if (['SETUP', 'MANUTENÇÃO'].includes(s)) color = 'warning';

            blocks.push({
                status: current.new_status || '?',
                start: current.timestamp,
                end: next.timestamp,
                duration_min: Math.round(durationMin),
                reason: current.reason || null, // CORREÇÃO: Passa null se undefined
                color: color
            });
        }
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
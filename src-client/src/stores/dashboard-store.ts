import { defineStore } from 'pinia';
import { api } from 'boot/axios';

export interface MachinePosition {
  id: number;
  identifier: string; 
  status: string;    
  layout_x?: number;  
  layout_y?: number;
  operator_name?: string;
}

export interface ManagerDashboardResponse {
  total_machines: number;
  active_machines: number;
  stopped_machines: number;
  average_availability: number; 
  average_oee?: number;       
  alerts_count: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  daily_production_chart: any[]; 
}

export interface OperatorDashboardResponse {
  operator_name: string;
  current_machine?: string;
  shift_hours: number;
  efficiency: number;
  produced_items: number;
}


export interface DashboardState {
  managerDashboard: ManagerDashboardResponse | null;
  operatorDashboard: OperatorDashboardResponse | null;
  machinePositions: MachinePosition[];
  isLoading: boolean;
  lastUpdated: Date | null;
}

export const useDashboardStore = defineStore('dashboard', {
  state: (): DashboardState => ({
    managerDashboard: null,
    operatorDashboard: null,
    machinePositions: [],
    isLoading: false,
    lastUpdated: null,
  }),

  actions: {
    /**
     * 
     * @param period 
     * @param silent 
     */
    async fetchManagerDashboard(period = 'today', silent = false) {
      if (!silent) this.isLoading = true;
      
      try {
        const response = await api.get<ManagerDashboardResponse>('/dashboard/manager', {
          params: { period },
        });
        this.managerDashboard = response.data;
        this.lastUpdated = new Date();
      } catch (error) {
        console.error('❌ Erro ao carregar dashboard do gestor:', error);
      } finally {
        if (!silent) this.isLoading = false;
      }
    },

    async fetchOperatorDashboard() {
      this.isLoading = true;
      try {
        const response = await api.get<OperatorDashboardResponse>('/dashboard/operator');
        this.operatorDashboard = response.data;
      } catch (error) {
        console.error('❌ Erro ao carregar dashboard do operador:', error);
      } finally {
        this.isLoading = false;
      }
    },


    async fetchMachinePositions() {
      try {
        const response = await api.get<MachinePosition[]>('/dashboard/machines/positions');
        this.machinePositions = response.data;
      } catch (error) {
        console.error('❌ Erro ao atualizar posições das máquinas:', error);
      }
    },


    clearDashboardData() {
      this.managerDashboard = null;
      this.operatorDashboard = null;
      this.machinePositions = [];
      this.isLoading = false;
      this.lastUpdated = null;
    },
  },
});
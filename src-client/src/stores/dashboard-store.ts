import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import type {
  ManagerDashboardResponse,
  DriverDashboardResponse,
  MachinePosition,
} from 'src/models/report-models';

// Definição do novo estado da store, mais completo
export interface DashboardState {
  managerDashboard: ManagerDashboardResponse | null;
  driverDashboard: DriverDashboardResponse | null;
  machinePositions: MachinePosition[];
  isLoading: boolean;
}

export const useDashboardStore = defineStore('dashboard', {
  state: (): DashboardState => ({
    managerDashboard: null,
    driverDashboard: null,
    machinePositions: [],
    isLoading: false,
  }),

  actions: {
    /**
     * Busca os dados para o dashboard do GESTOR.
     * @param period A string do período para o filtro (ex: 'last_30_days')
     * @param silent Se true, não altera o estado isLoading (para refresh silencioso)
     */
    async fetchManagerDashboard(period = 'last_30_days', silent = false) {
      if (!silent) this.isLoading = true;
      try {
        const response = await api.get<ManagerDashboardResponse>('/dashboard/manager', {
          params: { period },
        });
        this.managerDashboard = response.data;
      } catch (error) {
        console.error('Falha ao buscar dados do dashboard do gestor:', error);
        // Opcional: adicionar notificação de erro para o usuário
      } finally {
        if (!silent) this.isLoading = false;
      }
    },

    /**
     * Busca os dados para o dashboard do MOTORISTA.
     */
    async fetchDriverDashboard() {
      this.isLoading = true;
      try {
        const response = await api.get<DriverDashboardResponse>('/dashboard/driver');
        this.driverDashboard = response.data;
      } catch (error) {
        console.error('Falha ao buscar dados do dashboard do motorista:', error);
      } finally {
        this.isLoading = false;
      }
    },

    /**
     * Busca as posições dos veículos para o MAPA.
     * Esta ação é otimizada para ser chamada repetidamente (polling).
     */
    async fetchMachinePositions() {
      // Não usamos 'isLoading' aqui para permitir uma atualização silenciosa em segundo plano.
      try {
        const response = await api.get<MachinePosition[]>('/dashboard/machines/positions');
        this.machinePositions = response.data;
      } catch (error) {
        console.error('Falha ao buscar posições dos veículos:', error);
      }
    },

    /**
     * Limpa os dados do dashboard, útil ao fazer logout.
     */
    clearDashboardData() {
      this.managerDashboard = null;
      this.driverDashboard = null;
      this.machinePositions = [];
      this.isLoading = false;
    },
  },
});

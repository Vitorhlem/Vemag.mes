import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import { MachineStatus, type Machine, type MachineCreate, type MachineUpdate } from 'src/models/machine-models';
import { useAuthStore } from './auth-store';
import { useTireStore } from './tire-store';

interface FetchParams {
  page?: number;
  rowsPerPage?: number;
  search?: string;
}

interface PaginatedMachinesResponse {
  machines: Machine[];
  total_items: number;
}

const initialState = () => ({
  machines: [] as Machine[],
  selectedMachine: null as Machine | null,
  isLoading: false,
  totalItems: 0,
});



export const useMachineStore = defineStore('machine', {
  state: initialState,
  getters: {
    availableMachines: (state) =>
      state.machines.filter(v => v.status === MachineStatus.AVAILABLE),
  },

  actions: {
    async fetchAllMachines(params: FetchParams = {}) {
      this.isLoading = true;
      try {
        const queryParams = {
          page: params.page || 1,
          rowsPerPage: params.rowsPerPage || 8,
          search: params.search || '',
        };
        const response = await api.get<PaginatedMachinesResponse>('/machines/', { params: queryParams });
        this.machines = response.data.machines;
        this.totalItems = response.data.total_items;
      } catch (error) {
        console.error('Falha ao buscar veículos:', error);
        Notify.create({ type: 'negative', message: 'Falha ao buscar veículos.' });
      } finally {
        this.isLoading = false;
      }
    },
    async fetchMachineById(machineId: number) {
      this.isLoading = true;
      try {
        const response = await api.get<Machine>(`/machines/${machineId}`);
        this.selectedMachine = response.data;
      } catch (error) {
        Notify.create({ type: 'negative', message: 'Falha ao carregar dados do veículo.' });
        console.error(`Falha ao buscar veículo ${machineId}:`, error);
      } finally {
        this.isLoading = false;
      }
    },

    updateMachineInList(updatedMachine: Machine) {
      const index = this.machines.findIndex(v => v.id === updatedMachine.id);
      if (index !== -1) {
        // Substitui o objeto antigo pelo novo na lista
        this.machines[index] = updatedMachine;
      }
      // Opcional: Se o veículo atualizado for o selecionado, atualize-o também
      if (this.selectedMachine && this.selectedMachine.id === updatedMachine.id) {
        this.selectedMachine = updatedMachine;
      }
    },

    async addNewMachine(machineData: MachineCreate, initialFetchParams: FetchParams) {
      try {
        await api.post('/machines/', machineData);
        Notify.create({ type: 'positive', message: 'Item adicionado com sucesso!' });
        await this.fetchAllMachines({ ...initialFetchParams, page: 1 });

        const authStore = useAuthStore();
        if (authStore.isDemo) {
          const demoStore = useDemoStore();
          await demoStore.fetchDemoStats(true);
        }

      } catch (error) {
        Notify.create({ type: 'negative', message: 'Erro ao adicionar item.' });
        console.error('Erro ao adicionar:', error);
        throw error;
      }
    },

    async updateMachine(id: number, machineData: MachineUpdate, currentFetchParams: FetchParams) {
      try {
        await api.put(`/machines/${id}`, machineData);
        Notify.create({ type: 'positive', message: 'Item atualizado com sucesso!' });
        await this.fetchAllMachines(currentFetchParams);
      } catch (error) {
        Notify.create({ type: 'negative', message: 'Erro ao atualizar item.' });
        console.error('Erro ao atualizar:', error);
        throw error;
      }
    },

    async updateAxleConfiguration(machineId: number, axleConfig: string) {
      try {
        const response = await api.patch<Machine>(`/machines/${machineId}/axle-config`, { axle_configuration: axleConfig });
        if (this.selectedMachine && this.selectedMachine.id === machineId) {
          this.selectedMachine = response.data;
        }
        const tireStore = useTireStore();
        if (tireStore.tireLayout) {
          tireStore.tireLayout.axle_configuration = response.data.axle_configuration || null;
        }

        Notify.create({ type: 'positive', message: 'Configuração de eixos atualizada!' });
        return true;
      } catch (error) {
        Notify.create({ type: 'negative', message: 'Erro ao atualizar configuração.' });
        console.error('Erro ao atualizar configuração de eixos:', error);
        return false;
      }
    },

    async deleteMachine(id: number, currentFetchParams: FetchParams) {
      try {
        await api.delete(`/machines/${id}`);
        Notify.create({ type: 'positive', message: 'Item excluído com sucesso.' });
        await this.fetchAllMachines(currentFetchParams);

        const authStore = useAuthStore();
        if (authStore.isDemo) {
          const demoStore = useDemoStore();
          await demoStore.fetchDemoStats(true);
        }

      } catch (error) {
        Notify.create({ type: 'negative', message: 'Erro ao excluir o item.' });
        console.error('Erro ao excluir:', error);
      }
    },
  },
});


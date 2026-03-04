import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import { type IMachineCost, type ICostCreate } from 'src/models/cost-models';

interface CostsState {
  costs: IMachineCost[];
  isLoading: boolean;
}

export const useMachineCostStore = defineStore('machineCost', {
  state: (): CostsState => ({
    costs: [],
    isLoading: false,
  }),

  actions: {
    async fetchAllCosts(params?: { startDate?: Date, endDate?: Date }) {
      this.isLoading = true;
      try {
        const response = await api.get<IMachineCost[]>('/costs/', { params });
        this.costs = response.data;
      } catch (error) {
        console.error('Falha ao buscar todos os custos:', error);
        Notify.create({ type: 'negative', message: 'Não foi possível carregar os custos.' });
      } finally {
        this.isLoading = false;
      }
    },

    async fetchCostsByMachine(machineId: number) {
      this.isLoading = true;
      try {
        const response = await api.get<IMachineCost[]>(`/machines/${machineId}/costs`);
        this.costs = response.data;
      } catch (error) {
        console.error('Falha ao buscar custos da máquina:', error);
        Notify.create({ type: 'negative', message: 'Não foi possível carregar os custos do veículo.' });
      } finally {
        this.isLoading = false;
      }
    },

    async addCost(machineId: number, costData: Omit<ICostCreate, 'machine_id'>) {
      try {
        const payload = { ...costData, machine_id: machineId };
        await api.post('/machine_costs/', payload);
        
        await this.fetchCostsByMachine(machineId);
      } catch (error) {
        console.error('Erro ao adicionar custo:', error);
        Notify.create({ type: 'negative', message: 'Erro ao salvar o novo custo.' });
        throw error;
      }
    },
  },
});
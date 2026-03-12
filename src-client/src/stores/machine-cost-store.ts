import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import type { MachineCost, MachineCostCreate } from 'src/models/machine-cost-models';
import { format } from 'date-fns';

interface FetchAllCostsParams {
  startDate?: Date | null;
  endDate?: Date | null;
}

export const useMachineCostStore = defineStore('machineCost', {
  state: () => ({
    costs: [] as MachineCost[],
    isLoading: false,
  }),

  actions: {
    /**
     * @param machineId O ID do veículo cujos custos queremos carregar.
     */
    async fetchCosts(machineId: number) {
      this.isLoading = true;
      try {
        const response = await api.get<MachineCost[]>(`/machines/${machineId}/costs/`);
        this.costs = response.data;
      } catch{
        Notify.create({ type: 'negative', message: 'Falha ao carregar a lista de custos do veículo.' });
      } finally {
        this.isLoading = false;
      }
    },

    async fetchAllCosts(params: FetchAllCostsParams = {}) {
      this.isLoading = true;
      try {
        const queryParams: Record<string, string> = {};
        if (params.startDate) {
          queryParams.start_date = format(params.startDate, 'yyyy-MM-dd');
        }
        if (params.endDate) {
          queryParams.end_date = format(params.endDate, 'yyyy-MM-dd');
        }
        
        const response = await api.get<MachineCost[]>('/costs/', { params: queryParams });
        this.costs = response.data;
      } catch {
        Notify.create({ type: 'negative', message: 'Falha ao carregar a lista de custos.' });
      } finally {
        this.isLoading = false;
      }
    },

    async addCost(machineId: number, payload: MachineCostCreate): Promise<boolean> {
      try {
        await api.post(`/machines/${machineId}/costs/`, payload);

        return true;
      } catch  {
        Notify.create({ type: 'negative', message: 'Erro ao adicionar custo.' });
        return false;
      }
    },
  },
});
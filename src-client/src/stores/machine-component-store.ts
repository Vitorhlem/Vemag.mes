import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import { isAxiosError } from 'axios';
import type { MachineComponent, MachineComponentCreate } from 'src/models/machine-component-models';

export const useMachineComponentStore = defineStore('machineComponent', {
  state: () => ({
    components: [] as MachineComponent[],
    isLoading: false,
    currentMachineId: null as number | null, // <-- ADICIONE ESTA LINHA
  }),
  actions: {
    async fetchComponents(machineId: number) {
      this.isLoading = true;
      try {
        const response = await api.get<MachineComponent[]>(`/machines/${machineId}/components`);
        this.components = response.data;
        this.currentMachineId = machineId; // <-- ADICIONE ESTA LINHA
      } catch {
        Notify.create({ type: 'negative', message: 'Falha ao carregar componentes do veículo.' });
        this.currentMachineId = null; // <-- Opcional: limpar em caso de falha
      } finally {
        this.isLoading = false;
      }
    },

    async installComponent(machineId: number, payload: MachineComponentCreate): Promise<boolean> {
      this.isLoading = true;
      try {
        await api.post(`/machines/${machineId}/components`, payload);
        Notify.create({ type: 'positive', message: 'Componente instalado com sucesso!' });
        await this.fetchComponents(machineId); // Recarrega a lista
        return true;
      } catch (error) {
        const message = isAxiosError(error) ? error.response?.data?.detail : 'Erro ao instalar componente.';
        Notify.create({ type: 'negative', message: message as string });
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    async discardComponent(componentId: number, machineId: number) {
      this.isLoading = true;
      try {
        await api.put(`/machine-components/${componentId}/discard`);
        Notify.create({ type: 'positive', message: 'Componente marcado como descartado.' });
        await this.fetchComponents(machineId);
        return true; // Recarrega a lista
      } catch {
        Notify.create({ type: 'negative', message: 'Erro ao descartar componente.' });
        return false;
      } finally {
        this.isLoading = false;
      }
    },
  },
});
import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import type { Tools, ToolsCreate, ToolsUpdate } from 'src/models/tools-models';
// FIX: Import the ImplementStatus enum to use its values
import { ToolsStatus } from 'src/models/tools-models';

const initialState = () => ({
  implementList: [] as Tools[],
  isLoading: false,
});

export const useImplementStore = defineStore('implement', {
  state: initialState,

  getters: {
    availableImplements: (state) =>
      // FIX: Compare against the enum value instead of a magic string
      state.implementList.filter((i) => i.status === ToolsStatus.AVAILABLE),
  },

  actions: {
    async fetchAllImplementsForManagement() {
      this.isLoading = true;
      try {
        const response = await api.get<Tools[]>('/implements/management-list');
        this.implementList = response.data;
      } catch (error) {
        console.error('Falha ao buscar implementos para gerenciamento:', error);
        Notify.create({ type: 'negative', message: 'Falha ao buscar lista de implementos.' });
      } finally {
        this.isLoading = false;
      }
    },

    async fetchAvailableImplements() {
      this.isLoading = true;
      try {
        const response = await api.get<Tools[]>('/implements/');
        this.implementList = response.data;
      } catch (error) {
        console.error('Falha ao buscar implementos disponíveis:', error);
        Notify.create({ type: 'negative', message: 'Falha ao buscar implementos disponíveis.' });
      } finally {
        this.isLoading = false;
      }
    },

    async addImplement(payload: ToolsCreate) {
      try {
        await api.post('/implements/', payload);
        Notify.create({ type: 'positive', message: 'Implemento adicionado com sucesso!' });
        await this.fetchAllImplementsForManagement();
      } catch (error) {
        Notify.create({ type: 'negative', message: 'Erro ao adicionar implemento.' });
        throw error;
      }
    },

    async updateImplement(id: number, payload: ToolsUpdate) {
      try {
        await api.put(`/implements/${id}`, payload);
        Notify.create({ type: 'positive', message: 'Implemento atualizado com sucesso!' });
        await this.fetchAllImplementsForManagement();
      } catch (error) {
        Notify.create({ type: 'negative', message: 'Erro ao atualizar implemento.' });
        throw error;
      }
    },

    async deleteImplement(id: number) {
      try {
        await api.delete(`/implements/${id}`);
        Notify.create({ type: 'positive', message: 'Implemento excluído com sucesso.' });
        await this.fetchAllImplementsForManagement();
      } catch (error) {
        Notify.create({ type: 'negative', message: 'Erro ao excluir implemento.' });
        throw error;
      }
    },
  },
});
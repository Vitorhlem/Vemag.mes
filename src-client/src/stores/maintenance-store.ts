import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import type {
  MaintenanceRequest,
  MaintenanceRequestCreate,
  MaintenanceRequestUpdate,
  MaintenanceComment,
  MaintenanceCommentCreate,
  ReplaceComponentPayload, 
  ReplaceComponentResponse,
  InstallComponentPayload,
  InstallComponentResponse, 
  MaintenanceServiceItemCreate
} from 'src/models/maintenance-models';
import { isAxiosError } from 'axios';
interface FetchMaintenanceParams {
  search?: string | null;
  machineId?: number;
  limit?: number;
}

export const useMaintenanceStore = defineStore('maintenance', {
  state: () => ({
    maintenances: [] as MaintenanceRequest[],
    isLoading: false,
  }),
  actions: {
    async fetchMaintenanceRequests(params: FetchMaintenanceParams = {}) {
      this.isLoading = true;
      try {
        const response = await api.get<MaintenanceRequest[]>('/maintenance/', { params });
        this.maintenances = response.data;
      } catch {
        Notify.create({ type: 'negative', message: 'Falha ao carregar manutenções.' });
      } finally {
        this.isLoading = false;
      }
    },

    async addServiceItem(requestId: number, payload: MaintenanceServiceItemCreate): Promise<boolean> {
      try {
        const response = await api.post(`/maintenance/${requestId}/services`, payload);
        
        const request = this.maintenances.find(r => r.id === requestId);
        if (request) {
            if (!request.services) request.services = [];
            request.services.push(response.data);
        }
        
        Notify.create({ type: 'positive', message: 'Serviço adicionado e custo lançado!' });
        return true;
      } catch {
        Notify.create({ type: 'negative', message: 'Erro ao adicionar serviço.' });
        return false;
      }
    },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    async createIndustrialOS(payload: any) {
  this.isLoading = true;
  try {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const response = await api.post('/maintenance/industrial-os', payload);
    const isDraft = payload.status === 'RASCUNHO';
    
    Notify.create({
      type: 'positive',
      message: isDraft ? 'Rascunho atualizado!' : 'Documento finalizado e arquivado!',
      icon: isDraft ? 'save' : 'verified'
    });
    
    await this.fetchMaintenanceRequests();
    return true;
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (error) {
    Notify.create({ type: 'negative', message: 'Erro ao processar OS Industrial.' });
    return false;
  } finally {
    this.isLoading = false;
  }
},

    async fetchRequestById(requestId: number) {
      this.isLoading = true;
      try {
        const response = await api.get<MaintenanceRequest>(`/maintenance/${requestId}`);
        const index = this.maintenances.findIndex(r => r.id === requestId);
        if (index !== -1) {
          this.maintenances[index] = response.data;
        }
      } catch (error) {
        console.error('Falha ao buscar detalhes do chamado:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async createRequest(payload: MaintenanceRequestCreate): Promise<boolean> {
      try {
        await api.post<MaintenanceRequest>('/maintenance/', payload);
        Notify.create({ type: 'positive', message: 'Solicitação enviada com sucesso!' });
        await this.fetchMaintenanceRequests();
        return true;
      } catch {
        Notify.create({ type: 'negative', message: 'Erro ao enviar solicitação.' });
        return false;
      }
    },

    async updateRequest(requestId: number, payload: MaintenanceRequestUpdate): Promise<void> {
  try {

    await api.put<MaintenanceRequest>(`/maintenance/requests/${requestId}/status`, payload);
    
    Notify.create({ type: 'positive', message: 'Status da solicitação atualizado!' });
    await this.fetchMaintenanceRequests();
  } catch (error) {
    Notify.create({ type: 'negative', message: 'Erro ao atualizar solicitação.' });
    throw error;
  }
},

    async addComment(requestId: number, payload: MaintenanceCommentCreate): Promise<void> {
      try {
        const response = await api.post<MaintenanceComment>(`/maintenance/${requestId}/comments`, payload);
        
        const request = this.maintenances.find(r => r.id === requestId);
        
        if (request) {

           if (!request.comments) {
             request.comments = [];
           }
           request.comments.push(response.data);
        }

      } catch (error) {
        Notify.create({ type: 'negative', message: 'Erro ao enviar comentário.' });
        throw error;
      }
    },

    async installComponent(
      requestId: number,
      payload: InstallComponentPayload
    ): Promise<boolean> {
      this.isLoading = true;
      try {
        const response = await api.post<InstallComponentResponse>(
          `/maintenance/${requestId}/install-component`,
          payload
        );

        const requestToUpdate = this.maintenances.find((r) => r.id === requestId);

        if (requestToUpdate) {
          const { new_comment, part_change_log } = response.data;

          if (!requestToUpdate.comments) requestToUpdate.comments = [];
          requestToUpdate.comments.push(new_comment);

          if (!requestToUpdate.part_changes) requestToUpdate.part_changes = [];
          requestToUpdate.part_changes.push(part_change_log);
        } else {
          await this.fetchMaintenanceRequests();
          await this.fetchRequestById(requestId);
        }

        Notify.create({ type: 'positive', message: 'Componente instalado com sucesso!' });
        return true;
      } catch (error) {
        const message = isAxiosError(error) ? error.response?.data?.detail : 'Erro ao instalar componente.';
        Notify.create({ type: 'negative', message: message as string });
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    async revertPartChange(requestId: number, changeId: number): Promise<boolean> {
      this.isLoading = true;
      try {
        const newComment = await api.post<MaintenanceComment>(
          `/maintenance/part-changes/${changeId}/revert`
        );

        const requestToUpdate = this.maintenances.find(
          (r) => r.id === requestId
        );
        
        if (requestToUpdate) {
          const logToUpdate = requestToUpdate.part_changes.find(
            (log) => log.id === changeId
          );
          if (logToUpdate) {
            logToUpdate.is_reverted = true;
          }
          
          requestToUpdate.comments.push(newComment.data);
        }

        Notify.create({
          type: 'positive',
          message: 'Troca revertida com sucesso! O item retornou ao estoque.',
        });
        return true;

      } catch (error) {
         const message = isAxiosError(error) 
          ? error.response?.data?.detail 
          : 'Erro ao reverter a troca.';
        Notify.create({ type: 'negative', message: message as string });
        return false;
      } finally {
        this.isLoading = false;
      }
    },
    
    async replaceComponent(
      requestId: number,
      payload: ReplaceComponentPayload
    ): Promise<boolean> {
      this.isLoading = true;
      try {
        const response = await api.post<ReplaceComponentResponse>(
          `/maintenance/${requestId}/replace-component`,
          payload
        );

        const requestToUpdate = this.maintenances.find(
          (r) => r.id === requestId
        );

        if (requestToUpdate) {
          const { new_comment, part_change_log } = response.data;

          requestToUpdate.comments.push(new_comment);

          if (!requestToUpdate.part_changes) {
            requestToUpdate.part_changes = [];
          }
          requestToUpdate.part_changes.push(part_change_log);
          
        } else {
          await this.fetchMaintenanceRequests();
          await this.fetchRequestById(requestId);
        }

        Notify.create({
          type: 'positive',
          message: 'Componente substituído com sucesso!',
        });
        return true;
      } catch (error) {
        const message = isAxiosError(error)
          ? error.response?.data?.detail
          : 'Erro ao substituir componente.';
        Notify.create({ type: 'negative', message: message as string });
        return false;
      } finally {
        this.isLoading = false;
      }
    },
  },
});
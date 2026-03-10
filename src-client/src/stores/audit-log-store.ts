import { defineStore } from 'pinia';
import { api } from 'boot/axios';

export interface AuditLog {
  id: number;
  user_id: number | null;
  user_name: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  details: Record<string, any> | null;
  created_at: string;
}

interface AuditLogState {
  logs: AuditLog[];
  isLoading: boolean;
  error: string | null;
}

export const useAuditLogStore = defineStore('audit-log', {
  state: (): AuditLogState => ({
    logs: [],
    isLoading: false,
    error: null,
  }),

  actions: {
    async fetchLogs(skip = 0, limit = 50, resourceType?: string) {
      this.isLoading = true;
      this.error = null;
      
      try {
        let url = `/audit-logs/?skip=${skip}&limit=${limit}`;
        if (resourceType) {
          url += `&resource_type=${resourceType}`;
        }

        const response = await api.get<AuditLog[]>(url);
        this.logs = response.data;
        
      } catch (error) {
        console.error('Erro ao carregar logs de auditoria:', error);
        this.error = 'Falha ao carregar o histórico de ações.';

      } finally {
        this.isLoading = false;
      }
    },
    
    clearLogs() {
      this.logs = [];
    }
  },
});
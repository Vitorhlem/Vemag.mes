import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import type { Notification, NotificationCreate } from 'src/models/notification-models';
import { Notify } from 'quasar';
import type { RouteLocationRaw } from 'vue-router';

export const useNotificationStore = defineStore('notification', {
  state: () => ({
    notifications: [] as Notification[],
    unreadCount: 0,
    isLoading: false,
  }),

  actions: {
    async fetchUnreadCount() {
      try {
        const response = await api.get<number>('/notifications/unread-count');
        this.unreadCount = response.data;
      } catch (error) {
        console.error('Falha ao buscar contagem de notificações:', error);
      }
    },

    async fetchNotifications() {
      this.isLoading = true;
      try {
        const response = await api.get<Notification[]>('/notifications/');
        this.notifications = response.data;
        this.unreadCount = response.data.filter(n => !n.is_read).length;
      } catch (error) {
        console.error('Falha ao buscar notificações:', error);
      } finally {
        this.isLoading = false;
      }
    },

    async markAsRead(notificationId: number) {
      try {
        const response = await api.post<Notification>(`/notifications/${notificationId}/read`);
        const index = this.notifications.findIndex(n => n.id === notificationId);
        if (index !== -1) {
          this.notifications[index] = response.data;
        }
        this.unreadCount = this.notifications.filter(n => !n.is_read).length;
        return response.data;
      } catch (error) {
        console.error('Falha ao marcar notificação como lida:', error);
        return null;
      }
    },

    async handleNotificationClick(notification: Notification): Promise<RouteLocationRaw | null> {
      let updatedNotification = notification;

      // 1. Marca como lida no backend
      if (!notification.is_read) {
        const result = await this.markAsRead(notification.id);
        if (result) {
          updatedNotification = result;
        }
      }

      // 2. Decide a rota
      return this.getNotificationRoute(updatedNotification);
    },

    // --- LÓGICA DE ROTEAMENTO CORRIGIDA E ROBUSTA ---
    getNotificationRoute(notification: Notification): RouteLocationRaw | null {
      // 1. Normalização: Converte para minúsculo para evitar erro de Case Sensitivity
      const type = (notification.notification_type || '').toLowerCase();
      
      // LOG DE DEBUG: Abra o console do navegador (F12) para ver isso
      console.log('Tentando navegar. Tipo recebido:', type, 'Dados completos:', notification);

      switch (type) {
        
        // --- MANUTENÇÃO ---
        case 'maintenance_due_date':
        case 'maintenance_due_km':
          if (notification.related_machine_id) {
            return { 
              name: 'machine-details', 
              params: { id: notification.related_machine_id.toString() }
            };
          }
          return { name: 'maintenance' };

        case 'maintenance_request_new':
        case 'maintenance_request_status_update':
        case 'maintenance_request_new_comment':
          return { name: 'maintenance' };

        // --- DOCUMENTOS ---
        case 'document_expiring':
          if (notification.related_machine_id) {
            return { 
              name: 'machine-details', 
              params: { id: notification.related_machine_id.toString() }
            };
          }
          return { name: 'documents' };

        // --- COMBUSTÍVEL E CUSTOS ---
        case 'cost_exceeded':
          return { name: 'costs' };

        // --- ESTOQUE / PEÇAS ---
        case 'low_stock':
          return { name: 'parts' };

        case 'tire_status_bad':
          if (notification.related_machine_id) {
            return { 
              name: 'machine-details', 
              params: { id: notification.related_machine_id.toString() }
            };
          }
          return { name: 'machines' };

        // --- OPERACIONAL / JORNADAS ---
        case 'journey_started':
        case 'journey_ended':
          return { name: 'journeys' };

        case 'freight_assigned':
        case 'freight_updated':
          return { path: '/freight-orders' };

        // --- GAMIFICAÇÃO ---
        case 'achievement_unlocked':
        case 'leaderboard_top3':
          return { name: 'performance' };

        default:
          console.warn(`ALERTA: Tipo de notificação desconhecido: "${type}". Redirecionando para Dashboard.`);
          return { name: 'dashboard' };
      }
    },

    async createNotification(payload: NotificationCreate): Promise<boolean> {
      try {
        await api.post('/notifications/', payload);
        Notify.create({
          type: 'info',
          message: 'Nova notificação de sistema gerada.',
          icon: 'warning',
          position: 'top-right',
        });
        await this.fetchUnreadCount();
        return true;
      } catch (error) {
        console.error('Falha ao criar notificação:', error);
        return false;
      }
    },
  },
});
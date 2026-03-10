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

      if (!notification.is_read) {
        const result = await this.markAsRead(notification.id);
        if (result) {
          updatedNotification = result;
        }
      }

      return this.getNotificationRoute(updatedNotification);
    },

    getNotificationRoute(notification: Notification): RouteLocationRaw | null {
      const type = (notification.notification_type || '').toLowerCase();
      
      console.log('Tentando navegar. Tipo recebido:', type, 'Dados completos:', notification);

      switch (type) {
        
        case 'maintenance_due_date':
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

        case 'document_expiring':
          if (notification.related_machine_id) {
            return { 
              name: 'machine-details', 
              params: { id: notification.related_machine_id.toString() }
            };
          }
          return { name: 'documents' };

        case 'cost_exceeded':
          return { name: 'costs' };

        case 'low_stock':
          return { name: 'parts' };

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
import { boot } from 'quasar/wrappers';
import { PushNotifications } from '@capacitor/push-notifications';
import { api } from 'boot/axios';
import { useAuthStore } from 'stores/auth-store';
import { Platform } from 'quasar'; 

export default boot(async ({ store }) => {

  if (!Platform.is.capacitor) {
    console.log('🌐 Modo Web detectado: Push Notifications nativos desativados.');
    return;
  }

  console.log('📱 Inicializando Push Notifications (Modo Nativo)...');
  
  const authStore = useAuthStore(store);

  try {
      // 1. Pedir permissão ao usuário
      let permStatus = await PushNotifications.checkPermissions();

      if (permStatus.receive === 'prompt') {
        permStatus = await PushNotifications.requestPermissions();
      }

      if (permStatus.receive !== 'granted') {
        console.error('❌ Permissão de notificação negada!');
        return;
      }

      await PushNotifications.register();

      // eslint-disable-next-line @typescript-eslint/no-misused-promises
      await PushNotifications.addListener('registration', async (token) => {
        console.log('✅ Push Token recebido:', token.value);
        
        if (authStore.isAuthenticated) {
            try {
                await api.post('/users/me/device-token', { token: token.value });
                console.log('📡 Token enviado no Boot.');
            } catch (err) {
                console.error('⚠️ Erro envio Boot:', err);
            }
        } else {
            console.log('⏳ Usuário não logado. Guardando token no storage...');
            localStorage.setItem('fcm_token_pending', token.value);
        }
      });

      await PushNotifications.addListener('registrationError', err => {
        console.error('❌ Erro no registro do Push:', err);
      });

      await PushNotifications.addListener('pushNotificationReceived', notification => {
        console.log('🔔 Notificação recebida:', notification);
      });

      await PushNotifications.addListener('pushNotificationActionPerformed', notification => {
        console.log('👆 Clicou na notificação:', notification);
      });

  } catch (e) {
      console.warn('⚠️ Push Notifications não suportado neste ambiente:', e);
  }
});
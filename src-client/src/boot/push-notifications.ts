import { boot } from 'quasar/wrappers';
import { PushNotifications } from '@capacitor/push-notifications';
import { api } from 'boot/axios';
import { useAuthStore } from 'stores/auth-store';
import { Platform } from 'quasar'; // <--- IMPORTANTE: Importar o detector de plataforma

export default boot(async ({ store }) => {
  // --- CORREÇÃO DO ERRO ---
  // Verifica se está rodando no Celular (Capacitor/Cordova)
  // Se estiver no PC (Web/Electron), encerra a função imediatamente.
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

      // 2. Registrar no Firebase para ganhar o Token
      await PushNotifications.register();

      // 3. Ouvir o sucesso do registro
      // eslint-disable-next-line @typescript-eslint/no-misused-promises
      await PushNotifications.addListener('registration', async (token) => {
        console.log('✅ Push Token recebido:', token.value);
        
        // Se JÁ ESTIVER LOGADO, tenta enviar direto
        if (authStore.isAuthenticated) {
            try {
                await api.post('/users/me/device-token', { token: token.value });
                console.log('📡 Token enviado no Boot.');
            } catch (err) {
                console.error('⚠️ Erro envio Boot:', err);
            }
        } else {
            // SE NÃO LOGADO: Salva no LocalStorage para o AuthStore pegar depois
            console.log('⏳ Usuário não logado. Guardando token no storage...');
            localStorage.setItem('fcm_token_pending', token.value);
        }
      });

      // 4. Se der erro
      await PushNotifications.addListener('registrationError', err => {
        console.error('❌ Erro no registro do Push:', err);
      });

      // 5. Quando a notificação chega com o app aberto
      await PushNotifications.addListener('pushNotificationReceived', notification => {
        console.log('🔔 Notificação recebida:', notification);
      });

      // 6. Quando clica na notificação
      await PushNotifications.addListener('pushNotificationActionPerformed', notification => {
        console.log('👆 Clicou na notificação:', notification);
      });

  } catch (e) {
      // Blinda contra qualquer outro erro que possa acontecer na inicialização
      console.warn('⚠️ Push Notifications não suportado neste ambiente:', e);
  }
});
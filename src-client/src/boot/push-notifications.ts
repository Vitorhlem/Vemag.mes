import { boot } from 'quasar/wrappers';
import { PushNotifications } from '@capacitor/push-notifications';
import { api } from 'boot/axios';
import { useAuthStore } from 'stores/auth-store';

export default boot(async ({ store }) => {
  if (process.env.MODE !== 'capacitor') return;

  console.log('📱 Inicializando Push Notifications...');
  
  const authStore = useAuthStore(store);

  // 1. Pedir permissão
  let permStatus = await PushNotifications.checkPermissions();

  if (permStatus.receive === 'prompt') {
    permStatus = await PushNotifications.requestPermissions();
  }

  if (permStatus.receive !== 'granted') {
    console.error('❌ Permissão de notificação negada!');
    return;
  }

  // 2. Registrar
  await PushNotifications.register();

  // 3. Ouvir o sucesso do registro
  // eslint-disable-next-line @typescript-eslint/no-misused-promises
  await PushNotifications.addListener('registration', async (token) => {
    console.log('✅ Push Token recebido:', token.value);
    
    if (authStore.isAuthenticated) {
        // Se já logado, envia direto
        try {
            await api.post('/users/me/device-token', { token: token.value });
            console.log('📡 Token enviado no Boot.');
        } catch (err) {
            console.error('⚠️ Erro envio Boot:', err);
        }
    } else {
        // --- CORREÇÃO AQUI ---
        // Salva no LocalStorage para o AuthStore pegar depois do login
        console.log('⏳ Guardando token para pós-login...');
        localStorage.setItem('fcm_token_pending', token.value);
    }
  });

  // Listeners de erro e clique
  await PushNotifications.addListener('registrationError', err => console.error('❌ Erro Push:', err));
  
  await PushNotifications.addListener('pushNotificationReceived', notification => {
    console.log('🔔 Notificação recebida:', notification);
  });

  await PushNotifications.addListener('pushNotificationActionPerformed', notification => {
    console.log('👆 Clicou na notificação:', notification);
  });
});
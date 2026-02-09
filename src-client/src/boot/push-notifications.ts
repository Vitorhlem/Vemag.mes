import { boot } from 'quasar/wrappers';
import { PushNotifications } from '@capacitor/push-notifications';
import { api } from 'boot/axios';

export default boot(async () => {
  // Só roda se for um app nativo (Android/iOS)
  if (process.env.MODE !== 'capacitor') return;

  console.log('📱 Inicializando Push Notifications...');

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

  // 3. Ouvir o sucesso do registro (O Token chega aqui!)
  PushNotifications.addListener('registration', token => {
    console.log('✅ Push Token recebido:', token.value);
    
    // Envia para o Backend salvar no banco
    api.post('/users/me/device-token', { token: token.value })
       .then(() => console.log('Token salvo no servidor!'))
       .catch(err => console.error('Erro ao salvar token:', err));
  });

  // 4. Se der erro
  PushNotifications.addListener('registrationError', err => {
    console.error('❌ Erro no registro do Push:', err);
  });

  // 5. Quando a notificação chega com o app aberto
  PushNotifications.addListener('pushNotificationReceived', notification => {
    console.log('🔔 Notificação recebida:', notification);
  });

  // 6. Quando clica na notificação
  PushNotifications.addListener('pushNotificationActionPerformed', notification => {
    console.log('👆 Clicou na notificação:', notification);
    // Aqui você pode redirecionar para uma página específica
  });
});
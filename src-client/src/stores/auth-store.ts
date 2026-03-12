import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import type { UserNotificationPrefsUpdate } from 'src/models/user-models';
import type {
  LoginForm,
  TokenData,
  User,
  UserSector,
} from 'src/models/auth-models';

function getFromLocalStorage<T>(key: string): T | null {
  const itemString = localStorage.getItem(key);
  if (!itemString || itemString === 'undefined') return null;
  try {
    return JSON.parse(itemString) as T;
  } catch (e) {
    console.error(`Falha ao interpretar '${key}' do localStorage.`, e);
    localStorage.removeItem(key);
    return null;
  }
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'));
  const user = ref<User | null>(getFromLocalStorage<User>('user'));

  const originalUser = ref<User | null>(getFromLocalStorage<User>('original_user'));

  const isAuthenticated = computed(() => !!accessToken.value);
  const isManager = computed(() => ['cliente_ativo', 'cliente_demo', 'admin'].includes(user.value?.role ?? ''));
  const canEditMaintenance = computed(() => 
  ['admin', 'maintenance', 'pcp', 'quality', 'cliente_ativo'].includes(user.value?.role ?? '')
);
  const isoperator = computed(() => user.value?.role === 'operator');
  const userSector = computed((): UserSector => user.value?.organization?.sector ?? null);
  const isSuperuser = computed(() => user.value?.is_superuser === true);
  const isImpersonating = computed(() => !!originalUser.value);

  async function login(loginForm: LoginForm): Promise<void> {
    const params = new URLSearchParams();
    params.append('username', loginForm.email);
    params.append('password', loginForm.password);
    
    try {
      const response = await api.post<TokenData>('/login/token', params);
      _setSession(response.data.access_token, response.data.user);
    } catch (error) {
      console.error('Falha no login:', error);
      logout();
      throw error;
    }
  }

  async function loginByBadge(badge: string): Promise<void> {
    try {
      const response = await api.post('/login/badge', { badge });
      const { access_token } = response.data;

      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      const userResponse = await getMe();

      _setSession(access_token, userResponse);
      
    } catch (error) {
      console.error('Falha no login por crachá:', error);
      logout();
      throw error;
    }
  }

  async function getMe(): Promise<User> {
    const response = await api.get<User>('/users/me');
    return response.data;
  }

  async function updateMyPreferences(payload: UserNotificationPrefsUpdate) {
    try {
      const response = await api.put<User>('/users/me/preferences', payload);
      user.value = response.data;
      localStorage.setItem('user', JSON.stringify(response.data));
      Notify.create({ type: 'positive', message: 'Preferências salvas.' });
    } catch (error) {
      Notify.create({ type: 'negative', message: 'Erro ao salvar preferências.' });
      throw error;
    }
  }

  function logout() {
    console.log('Iniciando logout...');
    accessToken.value = null;
    user.value = null;
    originalUser.value = null;
    
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    localStorage.removeItem('original_accessToken');
    localStorage.removeItem('original_user');
    
    delete api.defaults.headers.common['Authorization'];
    console.log('Logout concluído.');
  }

  function startImpersonation(newToken: string, targetUser: User) {
    if (!user.value || !accessToken.value) {
      console.error('Erro: Admin não logado para iniciar impersonation.');
      return;
    }
    localStorage.setItem('original_accessToken', accessToken.value);
    localStorage.setItem('original_user', JSON.stringify(user.value));
    originalUser.value = user.value;

    _setSession(newToken, targetUser);
    window.location.href = '/dashboard';
  }

  function stopImpersonation() {
    const originalToken = localStorage.getItem('original_accessToken');
    const originalAdminUser = getFromLocalStorage<User>('original_user');

    if (!originalToken || !originalAdminUser) {
      console.error('Sessão original não encontrada. Fazendo logout.');
      logout();
      window.location.href = '/auth/login';
      return;
    }

    _setSession(originalToken, originalAdminUser);
    
    localStorage.removeItem('original_accessToken');
    localStorage.removeItem('original_user');
    originalUser.value = null;
    
    window.location.href = '/admin';
  }


  function updateUser(updates: Partial<User>) {
    if (user.value) {
      user.value = { ...user.value, ...updates };
      localStorage.setItem('user', JSON.stringify(user.value));
    }
  }

  function _setSession(token: string, userData: User) {
    accessToken.value = token;
    user.value = userData;



    localStorage.setItem('accessToken', token);
    localStorage.setItem('user', JSON.stringify(userData));
    
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

    const pendingToken = localStorage.getItem('fcm_token_pending');
    if (pendingToken) {
        console.log('🚀 [Auth] Token Pendente encontrado. Enviando...');
        api.post('/users/me/device-token', { token: pendingToken })
           .then(() => {
               console.log('✅ [Auth] Token vinculado com sucesso!');
               localStorage.removeItem('fcm_token_pending');
           })
           .catch(err => console.error('⚠️ [Auth] Falha ao enviar token:', err));
    }
  }

  function init() {
    const token = accessToken.value;
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }

  init();

  return {
    // State
    accessToken,
    user,
    originalUser,
    
    // Getters
    isAuthenticated,
    isManager,
    isoperator,
    userSector,
    isSuperuser,
    isImpersonating,
    canEditMaintenance,
    
    // Actions
    login,
    loginByBadge, 
    getMe,       
    logout,
    updateMyPreferences,
    updateUser,
    startImpersonation,
    stopImpersonation,
  };
});
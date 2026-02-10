import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import { isAxiosError } from 'axios'; // <-- IMPORTAÇÃO ESSENCIAL
import type { UserNotificationPrefsUpdate } from 'src/models/user-models';
import type {
  LoginForm,
  TokenData,
  User,
  UserSector,
  PasswordRecoveryRequest,
  PasswordResetRequest
} from 'src/models/auth-models';
import { useTerminologyStore } from './terminology-store';

// Helper para ler do LocalStorage com segurança
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
  // --- ESTADO PRINCIPAL ---
  const accessToken = ref<string | null>(localStorage.getItem('accessToken'));
  const user = ref<User | null>(getFromLocalStorage<User>('user'));

  // --- ESTADO PARA O LOGIN SOMBRA (IMPERSONATION) ---
  const originalUser = ref<User | null>(getFromLocalStorage<User>('original_user'));

  // --- GETTERS (COMPUTED) ---
  const isAuthenticated = computed(() => !!accessToken.value);
  const isManager = computed(() => ['cliente_ativo', 'cliente_demo', 'admin'].includes(user.value?.role ?? ''));
  const canEditMaintenance = computed(() => 
  ['admin', 'maintenance', 'pcp', 'quality', 'cliente_ativo'].includes(user.value?.role ?? '')
);
  const isDriver = computed(() => user.value?.role === 'driver');
  const userSector = computed((): UserSector => user.value?.organization?.sector ?? null);
  const isSuperuser = computed(() => user.value?.is_superuser === true);
  const isDemo = computed(() => user.value?.role === 'cliente_demo');
  const isImpersonating = computed(() => !!originalUser.value);

  // --- AÇÕES ---

  // 1. Login Tradicional (Email/Senha)
  async function login(loginForm: LoginForm): Promise<void> {
    const params = new URLSearchParams();
    params.append('username', loginForm.email);
    params.append('password', loginForm.password);
    
    try {
      // O endpoint /login/token geralmente retorna { access_token, user, ... }
      // Se o seu backend retornar apenas o token, você precisará chamar getMe() depois.
      const response = await api.post<TokenData>('/login/token', params);
      _setSession(response.data.access_token, response.data.user);
    } catch (error) {
      console.error('Falha no login:', error);
      logout();
      throw error;
    }
  }

  // 2. Login por Crachá (PARA O KIOSK)
  async function loginByBadge(badge: string): Promise<void> {
    try {
      // 1. Obtém o token usando apenas o crachá
      const response = await api.post('/login/badge', { badge });
      const { access_token } = response.data;

      // 2. Define o header temporariamente para buscar os dados do usuário
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      // 3. Busca os dados completos do usuário (necessário para pegar o employee_id, nome, etc)
      const userResponse = await getMe();

      // 4. Salva a sessão completa
      _setSession(access_token, userResponse);
      
    } catch (error) {
      console.error('Falha no login por crachá:', error);
      logout();
      throw error;
    }
  }

  // 3. Buscar dados do usuário atual
  async function getMe(): Promise<User> {
    const response = await api.get<User>('/users/me');
    return response.data;
  }

  // 4. Atualizar Preferências
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

  // 5. Logout
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

  // --- AÇÕES DO LOGIN SOMBRA ---
  function startImpersonation(newToken: string, targetUser: User) {
    if (!user.value || !accessToken.value) {
      console.error('Erro: Admin não logado para iniciar impersonation.');
      return;
    }
    // Salva o admin original
    localStorage.setItem('original_accessToken', accessToken.value);
    localStorage.setItem('original_user', JSON.stringify(user.value));
    originalUser.value = user.value;

    // Loga como o alvo
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

    // Restaura o admin
    _setSession(originalToken, originalAdminUser);
    
    // Limpa dados temporários
    localStorage.removeItem('original_accessToken');
    localStorage.removeItem('original_user');
    originalUser.value = null;
    
    window.location.href = '/admin';
  }
  
  // --- RECUPERAÇÃO DE SENHA ---
  async function requestPasswordReset(payload: PasswordRecoveryRequest): Promise<void> {
    try {
      await api.post('/login/password-recovery', payload);
      Notify.create({
        type: 'positive',
        message: 'Se o e-mail existir, um link de redefinição será enviado.',
      });
    } catch (error) {
      console.error('Erro requestPasswordReset:', error);
      // Mantém a mesma mensagem por segurança
      Notify.create({
        type: 'positive',
        message: 'Se o e-mail existir, um link de redefinição será enviado.',
      });
    }
  }

  async function resetPassword(payload: PasswordResetRequest): Promise<boolean> {
    try {
      await api.post('/login/reset-password', payload);
      Notify.create({
        type: 'positive',
        message: 'Senha redefinida! Faça login.',
        icon: 'lock_reset'
      });
      return true;
    } catch (error: unknown) {
      console.error('Erro resetPassword:', error);
      
      let detail = 'Ocorreu um erro. Token inválido ou expirado.';
      
      // Validação correta com isAxiosError
      if (isAxiosError(error) && error.response?.data?.detail) {
        detail = error.response.data.detail;
      }

      Notify.create({
        type: 'negative',
        message: detail,
        icon: 'error'
      });
      return false;
    }
  }

  // Atualização local do usuário (sem ir ao backend)
  function updateUser(updates: Partial<User>) {
    if (user.value) {
      user.value = { ...user.value, ...updates };
      localStorage.setItem('user', JSON.stringify(user.value));
    }
  }

  // --- HELPERS INTERNOS ---
  function _setSession(token: string, userData: User) {
    accessToken.value = token;
    user.value = userData;

    // Configura Terminologia baseada no setor
    if (userData.organization) {
      useTerminologyStore().setSector(userData.organization.sector);
    }

    // Persistência
    localStorage.setItem('accessToken', token);
    localStorage.setItem('user', JSON.stringify(userData));
    
    // Configura Axios
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

    // --- GATILHO DE NOTIFICAÇÃO (NOVO) ---
    // Verifica se existe um token que chegou antes do login
    const pendingToken = localStorage.getItem('fcm_token_pending');
    if (pendingToken) {
        console.log('🚀 [Auth] Token Pendente encontrado. Enviando...');
        // Envia em segundo plano (sem await para não travar o login visualmente)
        api.post('/users/me/device-token', { token: pendingToken })
           .then(() => {
               console.log('✅ [Auth] Token vinculado com sucesso!');
               localStorage.removeItem('fcm_token_pending');
           })
           .catch(err => console.error('⚠️ [Auth] Falha ao enviar token:', err));
    }
  }

  // Inicialização (Roda ao recarregar a página)
  function init() {
    const token = accessToken.value;
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    // Restaura terminologia se usuário existir
    useTerminologyStore().setSector(user.value?.organization?.sector ?? null);
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
    isDriver,
    userSector,
    isSuperuser,
    isDemo,
    isImpersonating,
    
    // Actions
    login,
    loginByBadge, // Nova ação
    getMe,        // Nova ação
    logout,
    updateMyPreferences,
    updateUser,
    startImpersonation,
    stopImpersonation,
    requestPasswordReset,
    resetPassword,
    canEditMaintenance
  };
});
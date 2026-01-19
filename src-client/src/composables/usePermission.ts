import { computed } from 'vue';
import { useAuthStore } from 'stores/auth-store';

export function usePermission() {
  const authStore = useAuthStore();

  const role = computed(() => authStore.user?.role);

  // --- REGRAS DE NEGÓCIO ---
  
  const canViewReports = computed(() => {
    return ['admin', 'cliente_ativo', 'manager', 'pcp'].includes(role.value || '');
  });

  const canManageUsers = computed(() => {
    return ['admin', 'cliente_ativo', 'manager'].includes(role.value || '');
  });

  const canOpenMaintenanceRequest = computed(() => {
    // Quase todos no chão de fábrica podem abrir chamado
    return ['operator', 'maintenance', 'quality', 'logistics', 'manager'].includes(role.value || '');
  });

  const canEditSettings = computed(() => {
    return ['admin', 'cliente_ativo'].includes(role.value || '');
  });

  // Acesso à tela de Produção/Kiosk
  const isOperatorAccess = computed(() => {
    return ['operator'].includes(role.value || '');
  });

  // Acesso à tela de Resolução de Chamados (Técnicos)
  const isResponderAccess = computed(() => {
    return ['maintenance', 'quality', 'logistics'].includes(role.value || '');
  });

  return {
    role,
    canViewReports,
    canManageUsers,
    canOpenMaintenanceRequest,
    canEditSettings,
    isOperatorAccess,
    isResponderAccess
  };
}
import { computed } from 'vue';
import { useAuthStore } from 'stores/auth-store';

export function usePermission() {
  const authStore = useAuthStore();

  const role = computed(() => authStore.user?.role);
  
  const canViewReports = computed(() => {
    return ['admin', 'manager', 'pcp'].includes(role.value || '');
  });

  const canManageUsers = computed(() => {
    return ['admin', 'manager'].includes(role.value || '');
  });

  const canOpenMaintenanceRequest = computed(() => {
    return ['operator', 'maintenance', 'quality', 'logistics', 'manager'].includes(role.value || '');
  });

  const canEditSettings = computed(() => {
    return ['admin'].includes(role.value || '');
  });

  const isOperatorAccess = computed(() => {
    return ['operator'].includes(role.value || '');
  });

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
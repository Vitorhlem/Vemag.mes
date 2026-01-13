import { route } from 'quasar/wrappers';
import {
  createMemoryHistory,
  createRouter,
  createWebHashHistory,
  createWebHistory,
} from 'vue-router';
import routes from './routes';
import { useAuthStore } from 'stores/auth-store';

export default route(function (/* { store, ssrContext } */) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : (process.env.VUE_ROUTER_MODE === 'history' ? createWebHistory : createWebHashHistory);

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,
    history: createHistory(process.env.VUE_ROUTER_BASE),
  });

  Router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();
    
    // 1. Se a rota não requer autenticação, deixa passar
    if (!to.meta.requiresAuth && !to.matched.some(record => record.meta.requiresAuth)) {
      return next();
    }

    // 2. Se não está logado, manda pro login
    if (!authStore.isAuthenticated) {
      return next({ name: 'login' });
    }

    const userRole = authStore.user?.role || '';

    // 3. Lógica de Redirecionamento Inteligente da Raiz
    // Se o usuário tentar acessar a raiz '/' ou o '/dashboard' e for Motorista,
    // forçamos o envio para o Kiosk.
    if (to.path === '/' || to.name === 'dashboard') {
      if (userRole === 'driver') {
        return next({ name: 'machine-kiosk' });
      }
    }

    // 4. Verificação de Permissões (Roles)
    // Se a rota exige roles específicas e o usuário não tem...
    if (to.meta.roles && Array.isArray(to.meta.roles)) {
      if (!to.meta.roles.includes(userRole)) {
        console.warn(`Acesso negado: Usuário ${userRole} tentou acessar ${to.path}`);
        
        // Redirecionamento de Segurança
        if (userRole === 'driver') {
          return next({ name: 'machine-kiosk' });
        } else {
          return next({ name: 'dashboard' });
        }
      }
    }

    // 5. Correção para o erro "No match for driver-cockpit"
    // Se por acaso o sistema tentar enviar para a rota antiga, corrigimos para a nova
    if (to.name === 'driver-cockpit') {
       return next({ name: 'machine-kiosk' });
    }

    next();
  });

  return Router;
});
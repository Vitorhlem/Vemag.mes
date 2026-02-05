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
    
    if (!to.meta.requiresAuth && !to.matched.some(record => record.meta.requiresAuth)) {
      return next();
    }

    if (!authStore.isAuthenticated) {
      return next({ name: 'login' });
    }

    const userRole = authStore.user?.role || '';

    // 3. Lógica de Redirecionamento Inteligente da Raiz
    if (to.path === '/' || to.name === 'dashboard') {
      if (userRole === 'driver') {
        return next({ name: 'machine-kiosk' });
      }
      if (userRole === 'maintenance') {
        if (to.name === 'manutencao') return next();
        return next({ name: 'manutencao' }); 
      }
      if (userRole === 'pcp') {
        if (to.path === '/') return next({ name: 'dashboard' });
        return next();
      }
      if (userRole === 'admin') {
        if (to.path === '/') return next({ name: 'dashboard' });
        return next();
      }

      // FALLBACK PARA OUTROS CARGOS (Quality, etc) -> Andon TELA CHEIA
      if (to.name !== 'andon-full') {
        return next({ name: 'andon-full' });
      }
    }

    // 4. Verificação de Permissões (Roles)
    if (to.meta.roles && Array.isArray(to.meta.roles)) {
      if (!to.meta.roles.includes(userRole)) {
        console.warn(`Acesso negado: Usuário ${userRole} tentou acessar ${to.path}`);
        
        // Redirecionamento de Segurança baseado no cargo
        if (userRole === 'driver') return next({ name: 'machine-kiosk' });
        if (userRole === 'maintenance') return next({ name: 'manutencao' });
        if (userRole === 'pcp') return next({ name: 'dashboard' });
        
        // Se for qualidade ou outro setor tentando entrar no Admin/Dashboard
        if (to.name !== 'andon-full') {
          return next({ name: 'andon-full' });
        }
      }
    }

    if (to.name === 'driver-cockpit') {
       return next({ name: 'machine-kiosk' });
    }

    next();
  });

  return Router;
});
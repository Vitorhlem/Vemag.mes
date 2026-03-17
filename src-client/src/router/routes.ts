import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [

  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requiresAuth: true }, 
    children: [
      { path: '', redirect: '/dashboard' },
      
      { 
        path: 'dashboard', 
        name: 'dashboard', 
        component: () => import('pages/DashboardPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance', 'cliente_ativo', 'cliente_demo'] }
      },
      { 
        path: 'auditlogs', 
        name: 'auditlogs', 
        component: () => import('pages/AuditLogsPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance', 'cliente_ativo', 'cliente_demo'] }
      },
      { 
        path: 'supervisory', 
        name: 'supervisory', 
        component: () => import('pages/SupervisoryPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance'] }
      },

      { 
        path: 'andon-board', 
        name: 'andon-board', 
        component: () => import('pages/AndonBoardPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance'] }
      },

      { 
        path: 'machines', 
        name: 'machines', 
        component: () => import('pages/MachinesPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance'] }
      },

      { 
        path: 'machines/:id', 
        name: 'machine-details', 
        component: () => import('pages/MachineDetailsPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance'] }
      },

      { 
        path: 'manutencao', 
        name: 'manutencao', 
        component: () => import('pages/IndustrialMaintenancePage.vue'),
        meta: { roles: ['admin', 'maintenance', 'pcp'] }
      },
      { 
        path: 'maintenance', 
        name: 'maintenance', 
        component: () => import('pages/MaintenancePage.vue'),
        meta: { roles: ['admin', 'maintenance', 'pcp'] }
      },

      {
        path: 'inventory-items',
        name: 'inventory-items',
        component: () => import('pages/InventoryItemsPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance'] }
      },
      {
        path: 'inventory-items/:id',
        name: 'item-details',
        component: () => import('pages/ItemDetailsPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance'] }
      },

      { path: 'parts', name: 'parts', component: () => import('pages/PartsPage.vue'), meta: { roles: ['admin', 'pcp', 'maintenance'] } },
      { path: 'users/:id/stats', name: 'user-details', component: () => import('pages/UserDetailsPage.vue'), meta: { roles: ['admin', 'pcp'] } },
      { path: 'feedback', name: 'feedback', component: () => import('pages/FeedbackPage.vue') },
      { path: 'settings', name: 'settings', component: () => import('pages/SettingsPage.vue') },
      
      { path: 'employees', name: 'employees', component: () => import('pages/EmployeesPage.vue'), meta: { roles: ['admin', 'pcp'] } },
      { path: 'users', name: 'users', component: () => import('pages/UsersPage.vue'), meta: { roles: ['admin'] } },
      { path: 'audit-logs', name: 'audit-logs', component: () => import('pages/AuditLogsPage.vue'), meta: { roles: ['admin'] } },
      
      { path: 'documents', name: 'documents', component: () => import('pages/DocumentPage.vue'), meta: { roles: ['admin'] } },
      { path: 'implements', name: 'implements', component: () => import('pages/ToolsPage.vue'), meta: { roles: ['admin'] } },
    ],
  },

  {
    path: '/factory',
    component: () => import('layouts/BlankLayout.vue'),
    meta: { requiresAuth: true }, 
    children: [
      { path: 'kiosk', name: 'machine-kiosk', component: () => import('pages/MachineKioskPage.vue') },
      
      { 
        path: 'andon-tv', 
        name: 'andon-full', 
        component: () => import('pages/AndonBoardPage.vue') 
      },
      
      { path: 'cockpit/:machineId', name: 'operator-cockpit', component: () => import('pages/OperatorCockpitPage.vue') },
      { path: '', redirect: 'kiosk' }
    ]
  },


  {
    path: '/auth',
    component: () => import('layouts/BlankLayout.vue'),
    children: [
      { path: 'login', name: 'login', component: () => import('pages/LoginPage.vue') },
      { path: 'register', name: 'register', component: () => import('pages/RegisterPage.vue') },
    ],
  },

  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
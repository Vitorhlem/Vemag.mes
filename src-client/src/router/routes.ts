import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  // =========================================================================
  // 1. ÁREA ADMINISTRATIVA / GESTOR (Com Menu Lateral - MainLayout)
  // =========================================================================
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requiresAuth: true }, 
    children: [
      { path: '', redirect: '/dashboard' },
      
      // Dashboard Geral
      { 
        path: 'dashboard', 
        name: 'dashboard', 
        component: () => import('pages/DashboardPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance', 'cliente_ativo', 'cliente_demo'] }
      },
      { 
        path: 'supervisory', 
        name: 'supervisory', 
        component: () => import('pages/SupervisoryPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance'] }
      },

      // ANDON VERSÃO COM MENU (Para Admin, PCP e Manutenção)
      { 
        path: 'andon-board', 
        name: 'andon-board', 
        component: () => import('pages/AndonBoardPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance'] }
      },

      // Módulos de Gestão de Máquinas
      { 
        path: 'vehicles', 
        name: 'vehicles', 
        component: () => import('pages/MachinesPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance'] }
      },

      { 
        path: 'vehicles/:id', 
        name: 'vehicle-details', 
        component: () => import('pages/MachineDetailsPage.vue'),
        meta: { roles: ['admin', 'pcp', 'maintenance'] }
      },

      // Manutenção
      { 
        path: 'manutencao', 
        name: 'manutencao', 
        component: () => import('pages/IndustrialMaintenancePage.vue'),
        meta: { roles: ['admin', 'maintenance'] }
      },
      { 
        path: 'maintenance', 
        name: 'maintenance', 
        component: () => import('pages/MaintenancePage.vue'),
        meta: { roles: ['admin', 'maintenance', 'pcp'] }
      },

      // Inventário e Rastreabilidade
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

      // Outras páginas (PCP e Admin)
      { path: 'reports', name: 'reports', component: () => import('pages/ReportsPage.vue'), meta: { roles: ['admin', 'pcp'] } },
      { path: 'performance', name: 'performance', component: () => import('pages/PerformancePage.vue'), meta: { roles: ['admin', 'pcp', 'maintenance'] } },
      { path: 'reports/daily', component: () => import('pages/DailyReportPage.vue'), meta: { roles: ['admin', 'pcp'] } },
      { path: 'costs', name: 'costs', component: () => import('pages/CostsPage.vue'), meta: { roles: ['admin', 'pcp'] } },
      { path: 'parts', name: 'parts', component: () => import('pages/PartsPage.vue'), meta: { roles: ['admin', 'pcp', 'maintenance'] } },
      { path: 'users/:id/stats', name: 'user-details', component: () => import('pages/UserDetailsPage.vue'), meta: { roles: ['admin', 'pcp'] } },
      // Feedback e Configurações (Acessível por todos)
      { path: 'feedback', name: 'feedback', component: () => import('pages/FeedbackPage.vue') },
      { path: 'settings', name: 'settings', component: () => import('pages/SettingsPage.vue') },
      
      // Administrativo Puro
      { path: 'employees', name: 'employees', component: () => import('pages/EmployeesPage.vue'), meta: { roles: ['admin', 'pcp'] } },
      { path: 'users', name: 'users', component: () => import('pages/UsersPage.vue'), meta: { roles: ['admin'] } },
      { path: 'admin', name: 'admin', component: () => import('pages/AdminPage.vue'), meta: { roles: ['admin'] } },
      { path: 'audit-logs', name: 'audit-logs', component: () => import('pages/AuditLogsPage.vue'), meta: { roles: ['admin'] } },
      
      // Legado / Frota
      { path: 'fuel-logs', name: 'fuel-logs', component: () => import('pages/FuelLogsPage.vue'), meta: { roles: ['admin'] } },
      { path: 'fines', name: 'fines', component: () => import('pages/FinesPage.vue'), meta: { roles: ['admin'] } },
      { path: 'documents', name: 'documents', component: () => import('pages/DocumentPage.vue'), meta: { roles: ['admin'] } },
      { path: 'implements', name: 'implements', component: () => import('pages/ToolsPage.vue'), meta: { roles: ['admin'] } },
      { path: 'freight-orders', component: () => import('pages/FreightOrdersPage.vue'), meta: { roles: ['admin'] } },
      { path: 'clients', component: () => import('pages/ClientsPage.vue'), meta: { roles: ['admin'] } },
    ],
  },

  // =========================================================================
  // 2. ÁREA DO FUNCIONÁRIO / TABLET (BlankLayout)
  // =========================================================================
  {
    path: '/factory',
    component: () => import('layouts/BlankLayout.vue'),
    meta: { requiresAuth: true }, 
    children: [
      { path: 'kiosk', name: 'machine-kiosk', component: () => import('pages/MachineKioskPage.vue') },
      
      // ANDON VERSÃO TELA CHEIA (Para Quality e outros setores)
      { 
        path: 'andon-tv', 
        name: 'andon-full', 
        component: () => import('pages/AndonBoardPage.vue') 
      },
      
      { path: 'cockpit/:machineId', name: 'operator-cockpit', component: () => import('pages/OperatorCockpitPage.vue') },
      { path: '', redirect: 'kiosk' }
    ]
  },

  // =========================================================================
  // 3. AUTENTICAÇÃO E IMPRESSÃO
  // =========================================================================
  {
    path: '/auth',
    component: () => import('layouts/BlankLayout.vue'),
    children: [
      { path: 'login', name: 'login', component: () => import('pages/LoginPage.vue') },
      { path: 'register', name: 'register', component: () => import('pages/RegisterPage.vue') },
      { path: 'forgot-password', name: 'forgot-password', component: () => import('pages/ForgotPasswordPage.vue') },
      { path: 'reset-password', name: 'reset-password', component: () => import('pages/ResetPasswordPage.vue') }
    ],
  },

  {
    path: '/print',
    component: () => import('layouts/BlankLayout.vue'),
    children: [
      { path: 'mes-report', component: () => import('pages/PrintMesReportPage.vue') }
    ]
  },

  // =========================================================================
  // 4. ERROS (404)
  // =========================================================================
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
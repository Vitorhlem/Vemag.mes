import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  // =========================================================================
  // 1. ÁREA ADMINISTRATIVA / GESTOR (Com Menu Lateral - MainLayout)
  // =========================================================================
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requiresAuth: true, roles: ['driver','admin', 'cliente_ativo', 'cliente_demo'] }, // Motorista/Operador NÃO entra aqui por padrão
    children: [
      { path: '', redirect: '/dashboard' },
      
      // Dashboard Geral
      { 
        path: 'dashboard', 
        name: 'dashboard', 
        component: () => import('pages/DashboardPage.vue') 
      },

      
      
      // --- Módulos de Gestão ---
      { 
        path: 'vehicles', 
        name: 'vehicles', 
        component: () => import('pages/MachinesPage.vue') 
      },

      { path: 'reports/daily', component: () => import('pages/DailyReportPage.vue') },

      { path: 'employees', component: () => import('pages/EmployeesPage.vue'), name: 'employees' },
      { 
        path: 'vehicles/:id', 
        name: 'vehicle-details', 
        component: () => import('pages/MachineDetailsPage.vue') 
      },
      { 
        path: 'maintenance', 
        name: 'maintenance', 
        component: () => import('pages/MaintenancePage.vue') 
      },
      { 
        path: 'fuel-logs', 
        name: 'fuel-logs', 
        component: () => import('pages/FuelLogsPage.vue') 
      },
      {
        path: 'fines',
        name: 'fines',
        component: () => import('pages/FinesPage.vue')
      },
      { 
        path: 'documents', 
        name: 'documents', 
        component: () => import('pages/DocumentPage.vue') 
      },
      { 
        path: 'journeys', 
        name: 'journeys', 
        component: () => import('pages/JourneysPage.vue') 
      },
      { 
        path: 'users', 
        name: 'users', 
        component: () => import('pages/UsersPage.vue') 
      },
      { 
        path: 'users/:id/stats', 
        name: 'user-stats', 
        component: () => import('pages/UserDetailsPage.vue') 
      },
      { 
        path: 'map', 
        name: 'map', 
        component: () => import('pages/MapPage.vue') 
      },
      { 
        path: 'live-map', 
        name: 'live-map',
        component: () => import('pages/LiveMapPage.vue')
      },
      { 
        path: 'performance', 
        name: 'performance', 
        component: () => import('pages/PerformancePage.vue') 
      },
      { 
        path: 'reports', 
        name: 'reports', 
        component: () => import('pages/ReportsPage.vue') 
      },
      {
        path: 'costs',
        name: 'costs',
        component: () => import('pages/CostsPage.vue')
      },
      {
        path: 'parts',
        name: 'parts',
        component: () => import('pages/PartsPage.vue')
      },
      {
        path: 'inventory-items',
        name: 'inventory-items',
        component: () => import('pages/InventoryItemsPage.vue')
      },
      { 
        path: 'feedback', 
        name: 'feedback', 
        component: () => import('pages/FeedbackPage.vue')
      },
      {
        path: 'implements',
        name: 'implements',
        component: () => import('pages/ToolsPage.vue')
      },
      { 
        path: 'freight-orders', 
        component: () => import('pages/FreightOrdersPage.vue')
      },
      { 
        path: 'clients', 
        component: () => import('pages/ClientsPage.vue')
      },
      { 
        path: 'settings', 
        name: 'settings', 
        component: () => import('pages/SettingsPage.vue')
      },
      {
        path: 'admin',
        name: 'admin',
        component: () => import('pages/AdminPage.vue'),
        meta: { roles: ['admin'] } 
      },
      { path: 'audit-logs', name: 'audit-logs', component: () => import('pages/AuditLogsPage.vue') },
    ],
  },

  // =========================================================================
  // 2. ÁREA DO FUNCIONÁRIO / TABLET (Sem Menu Lateral)
  // =========================================================================
  // Usamos o BlankLayout (ou nenhum) para garantir tela cheia e foco total.
  {
    path: '/factory',
    component: () => import('layouts/BlankLayout.vue'), // Layout vazio (sem sidebar)
    meta: { requiresAuth: true, roles: ['driver', 'operator', 'admin'] }, // 'driver' é o funcionario
    children: [
      // Tela de "Descanso" do Tablet (Login da Máquina)
      { 
        path: 'kiosk', 
        name: 'machine-kiosk', 
        component: () => import('pages/MachineKioskPage.vue') 
      },
      {
    path: '/andon-board',
    component: () => import('layouts/BlankLayout.vue'),
    children: [
      { 
        path: '', 
        name: 'andon-board', 
        component: () => import('pages/AndonBoardPage.vue') 
      }
    ]
  },
      
      // Painel de Trabalho do Operador (O Cockpit)
      { 
        path: 'cockpit/:machineId', 
        name: 'operator-cockpit', 
        component: () => import('pages/OperatorCockpitPage.vue') 
      },

      // Caso precise de uma "Home" simples com botões grandes para escolher a função
      // Se não tiver, redireciona para o Kiosk
      { path: '', redirect: 'kiosk' }
    ]
  },

  // =========================================================================
  // 3. AUTENTICAÇÃO
  // =========================================================================
  {
    path: '/auth',
    component: () => import('layouts/BlankLayout.vue'),
    children: [
      { path: 'login', name: 'login', component: () => import('pages/LoginPage.vue') },
      { path: 'register', name: 'register', component: () => import('pages/RegisterPage.vue') },
      { 
        path: 'forgot-password', 
        name: 'forgot-password', 
        component: () => import('pages/ForgotPasswordPage.vue') 
      },
      { 
        path: 'reset-password', 
        name: 'reset-password', 
        component: () => import('pages/ResetPasswordPage.vue') 
      }
    ],
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
<template>
  <q-layout view="lHh LpR lFf" class="main-layout-container font-inter bg-grey-1">
    
    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      :width="260"
      :breakpoint="800"
      class="glass-drawer drawer-style"
    >
    
      <q-scroll-area class="fit" :thumb-style="{ width: '4px', borderRadius: '2px', opacity: '0.5' }">        
        <div class="q-pa-md row items-center justify-center relative-position" style="height: 110px;">
          <img src="~assets/trucar-logo-dark.png" class="logo-light animate-fade" style="height: 65px; max-width: 90%; transition: all 0.3s;" alt="Trucar Logo">
          <img src="~assets/trucar-logo-white.png" class="logo-dark animate-fade" style="height: 65px; max-width: 90%; display: none; transition: all 0.3s;" alt="Trucar Logo">
        </div>
        
        <q-separator class="q-mx-lg q-mb-md opacity-10" />

        <q-list padding class="q-px-md text-grey-7">
          <template v-for="category in menuStructure" :key="category.label">
            
            <q-item-label header class="text-weight-bold text-uppercase text-caption text-teal-8 q-pt-md q-pl-xs letter-spacing-1" style="font-size: 0.7rem; opacity: 0.7;">
              {{ category.label }}
            </q-item-label>

            <q-item
              v-for="link in category.children"
              :key="link.title"
              clickable
              :to="link.to"
              exact
              v-ripple
              class="q-mb-xs rounded-borders navigation-item transition-all"
              active-class="active-item shadow-1"
            >
              <q-item-section avatar style="min-width: 40px;">
                <div class="icon-wrapper flex flex-center">
                   <q-icon :name="link.icon" size="20px" class="nav-icon" />
                </div>
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">{{ link.title }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-separator v-if="category.separator" class="q-my-md q-mx-sm opacity-10" />
          </template>

          
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <q-header bordered class="glass-header text-grey-9 header-style">
      <q-toolbar style="height: 70px;">
        <q-btn 
          flat 
          dense 
          round 
          :icon="leftDrawerOpen ? 'menu_open' : 'menu'" 
          color="teal-9" 
          aria-label="Menu" 
          @click="toggleLeftDrawer" 
          class="q-mr-sm" 
        >
          <q-tooltip>{{ leftDrawerOpen ? 'Recolher Menu' : 'Expandir Menu' }}</q-tooltip>
        </q-btn>
        <q-btn flat dense round icon="menu_open" color="teal-9" aria-label="Menu" @click="toggleLeftDrawer" class="lt-md" />
        
        <div class="row items-center q-ml-sm cursor-pointer logo-area" @click="router.push('/')">
          <div class="bg-primary text-white rounded-borders flex flex-center q-mr-md shadow-2 transition-transform hover-rotate" style="width: 36px; height: 36px; background: linear-gradient(135deg, #128c7e, #70c0b0) !important;">
             <q-icon name="hub" size="20px" />
          </div>
          <div>
            <q-toolbar-title class="text-weight-bold text-dark gt-xs font-mono q-pl-none" style="font-size: 1.35rem; letter-spacing: -0.5px; line-height: 1;">
              VEMAG<span class="text-primary">.mes</span>
            </q-toolbar-title>
            
            <div class="text-caption text-teal-8 gt-sm" style="line-height: 1; font-size: 0.7rem; letter-spacing: 1px; font-weight: 600;">INTELLIGENT MANUFACTURING</div>
          </div>
        </div>

        <q-space />

        <div class="row q-gutter-sm items-center">
          <q-space /> <q-select
          v-model="searchModel"
          use-input
          hide-selected
          fill-input
          hide-dropdown-icon
          input-debounce="400"
          :options="searchResults"
          @filter="onSearchFilter"
          @update:model-value="onItemSelected"
          placeholder="Pesquisar O.S, Máquina ou Operador (Ex: 3943)..."
          dense
          standout="bg-teal-9 text-white"
          class="q-mx-md omni-search-bar"
        >
          <template v-slot:prepend>
            <q-icon name="search" color="teal-8" />
          </template>
          
          <template v-slot:no-option>
            <q-item>
              <q-item-section class="text-grey">
                Nenhum resultado encontrado.
              </q-item-section>
            </q-item>
          </template>

          <template v-slot:option="scope">
            <q-item v-bind="scope.itemProps" class="q-py-md border-bottom-light hover-grey">
              <q-item-section avatar>
                <q-avatar :color="scope.opt.color" text-color="white" :icon="scope.opt.icon" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold text-dark">{{ scope.opt.label }}</q-item-label>
                <q-item-label caption :class="{'text-red-10 text-weight-bold': scope.opt.sublabel.includes('RODANDO AGORA')}">
                  {{ scope.opt.sublabel }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </template>
        </q-select>
          <q-btn v-if="authStore.isManager" flat round dense class="text-teal-9 relative-position hover-scale q-mr-sm">
            <q-icon name="notifications_none" size="26px" />
            <q-badge v-if="notificationStore.unreadCount > 0" color="red" floating rounded mini class="shadow-1 animate-pulse" style="top: 4px; right: 4px;" />
            
            <q-menu 
              @show="notificationStore.fetchNotifications()" 
              anchor="bottom right" 
              self="top right" 
              :offset="[0, 14]" 
              class="shadow-10 rounded-borders glass-menu"
              style="width: 380px; max-width: 95vw;" 
            >
              <div class="row no-wrap items-center q-pa-md border-bottom bg-teal-1 text-teal-10">
                  <div class="text-subtitle1 text-weight-bolder">Alertas da Fábrica</div>
                  <q-badge color="teal-8" class="q-ml-sm" v-if="notificationStore.unreadCount > 0">
                    {{ notificationStore.unreadCount }} novos
                  </q-badge>
                  <q-space />
                  <q-btn round flat icon="done_all" size="sm" @click="markAllRead">
                    <q-tooltip>Marcar tudo como lido</q-tooltip>
                  </q-btn>
                </div>

                <q-scroll-area style="height: 400px;">
                  <q-list separator>
                    <q-item 
                      v-for="notification in notificationStore.notifications" 
                      :key="notification.id" 
                      clickable 
                      v-ripple 
                      class="q-py-lg q-px-md notification-item-ui" 
                      :class="!notification.is_read ? 'bg-blue-50' : ''"
                      @click="handleNotificationClick(notification)"
                    >
                      <q-item-section avatar style="min-width: 50px;">
                        <q-avatar 
                          :color="!notification.is_read ? 'teal-1' : 'grey-2'" 
                          :text-color="!notification.is_read ? 'teal-9' : 'grey-6'"
                          size="42px"
                          class="shadow-sm"
                        >
                          <q-icon :name="getNotificationIcon(notification.notification_type)" size="22px" />
                        </q-avatar>
                      </q-item-section>

                      <q-item-section>
                        <q-item-label 
                          class="text-body2 line-height-normal" 
                          :class="!notification.is_read ? 'text-weight-bold text-dark' : 'text-grey-8'"
                        >
                          {{ notification.message }}
                        </q-item-label>
                        <q-item-label caption class="text-grey-6 q-mt-xs row items-center">
                          <q-icon name="schedule" size="12px" class="q-mr-xs" />
                          {{ formatNotificationDate(notification.created_at) }}
                        </q-item-label>
                      </q-item-section>

                      <q-item-section side v-if="!notification.is_read">
                          <div class="new-indicator-glow"></div>
                      </q-item-section>
                    </q-item>

                    <div v-if="notificationStore.notifications.length === 0" class="column flex-center q-pa-xl text-grey-5" style="height: 300px;">
                      <q-icon name="notifications_off" size="60px" class="opacity-20 q-mb-md" />
                      <div class="text-weight-medium">Nenhum alerta recente</div>
                      <div class="text-caption">Tudo em ordem na planta industrial.</div>
                    </div>
                  </q-list>
                </q-scroll-area>
                
                <q-separator />
                <q-btn flat color="primary" label="Ver todos os alertas" class="full-width q-py-sm" to="/audit-logs" />
            </q-menu>
          </q-btn>

          <div style="height: 30px; width: 1px; background: rgba(18, 140, 126, 0.2);" class="q-mx-sm"></div>

          <q-btn-dropdown flat no-caps class="text-grey-9 profile-btn q-ml-none rounded-borders q-px-sm hover-bg-gray" content-class="profile-menu shadow-10 rounded-borders glass-menu">
            <template v-slot:label>
              <div class="row items-center no-wrap">
                <q-avatar size="40px" class="shadow-1 border-2 border-white">
                  <img :src="getAvatarUrl(authStore.user?.avatar_url)" style="object-fit: cover;">
                </q-avatar>
                
                <div class="text-left gt-sm q-ml-md">
                  <div class="text-weight-bold text-body2 font-inter" style="line-height: 1.2;">{{ firstName(authStore.user?.full_name) }}</div>
                  <div class="text-caption text-primary font-weight-bold text-uppercase" style="font-size: 0.65rem; letter-spacing: 0.5px;">{{ roleLabel }}</div>
                </div>
                
                <q-icon name="expand_more" color="grey-5" size="xs" class="q-ml-xs gt-sm" />
              </div>
            </template>

            <div class="row no-wrap q-pa-md" style="min-width: 290px;">
              <div class="column" style="flex: 1;">
                <div class="text-overline text-teal-9 q-mb-sm">Sistema</div>
                
                <div class="q-mb-md">
                  <div class="text-caption text-weight-medium text-grey-8 q-mb-xs">Cor do Tema</div>
                  <div class="row q-gutter-xs">
                    <q-btn round size="xs" class="shadow-1" color="teal-9" @click="changeTheme('#128c7e')" /> 
                    <q-btn round size="xs" class="shadow-1" color="blue-10" @click="changeTheme('#154ec1')" /> 
                    <q-btn round size="xs" class="shadow-1" color="grey-9" @click="changeTheme('#263238')" /> 
                    <q-btn round size="xs" class="shadow-1" color="red-9" @click="changeTheme('#c62828')" /> 
                    <q-btn round size="xs" icon="palette" flat class="text-grey-6 bg-grey-2">
                      <q-popup-proxy>
                        <q-color v-model="customColor" @update:model-value="(val) => val && changeTheme(val)" no-header no-footer default-view="palette" />
                      </q-popup-proxy>
                    </q-btn>
                  </div>
                </div>

                <q-separator class="q-mb-md opacity-20" />
                
                <q-list dense>
                  <q-item clickable v-close-popup to="/settings" class="rounded-borders hover-bg-gray q-py-sm">
                    <q-item-section avatar style="min-width: 30px;"><q-icon name="tune" size="18px" color="teal-7" /></q-item-section>
                    <q-item-section>Configurações</q-item-section>
                  </q-item>
                  <q-item clickable v-close-popup @click="handleLogout" class="rounded-borders hover-bg-red-soft q-py-sm text-negative">
                    <q-item-section avatar style="min-width: 30px;"><q-icon name="logout" size="18px" /></q-item-section>
                    <q-item-section>Encerrar Sessão</q-item-section>
                  </q-item>
                </q-list>
              </div>
            </div>
          </q-btn-dropdown>
        </div>
      </q-toolbar>
    </q-header>

    <q-page-container class="app-page-container">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { setCssVar, useQuasar } from 'quasar';
import { useAuthStore } from 'stores/auth-store';
import { useNotificationStore } from 'stores/notification-store';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import defaultAvatar from 'assets/default-avatar.png';

// --- NOVOS IMPORTS PARA NOTIFICAÇÃO ---
import { api } from 'boot/axios';
const leftDrawerOpen = ref(true);
const customColor = ref('#128c7e');
const router = useRouter();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const $q = useQuasar();
const searchModel = ref(null);
const searchResults = ref([]);

// Função que bate no servidor enquanto o usuário digita
async function onSearchFilter(val: string, update: (fn: () => void) => void, abort: () => void) {
  if (val.length < 2) {
    abort();
    return;
  }

  try {
    // Chama a rota que acabamos de criar no backend
    const { data } = await api.get(`/production/search?q=${val}`);
    update(() => {
      searchResults.value = data;
    });
  } catch (error) {
    console.error('Erro na busca global:', error);
    abort();
  }
}

// Função executada quando o usuário CLICA em uma opção da lista
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function onItemSelected(item: any) {
  if (item && item.route) {
    // Joga o usuário pra página correspondente!
    void router.push(item.route);
    
    // Limpa a barra depois de clicar
    searchModel.value = null; 
  }
}

// --- Lógica de Tema ---
function changeTheme(color: string) {
  customColor.value = color;
  setCssVar('primary', color);
  setCssVar('secondary', color); 
}
function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

function handleLogout() {
  authStore.logout();
  void router.push('/auth/login');
}

function getAvatarUrl(url: string | null | undefined): string {
  if (!url) return defaultAvatar;
  if (url.startsWith('http')) return url;
  const backendUrl = 'http://127.0.0.1:8000'; 
  if (url.startsWith('/static') || url.startsWith('/')) return `${backendUrl}${url}`;
  return url;
}

function firstName(name: string | undefined) {
    return name ? name.split(' ')[0] : 'Usuário';
}

const roleLabel = computed(() => {
    if (authStore.isManager) return 'Gestor Industrial';
    if (authStore.isDriver) return 'Técnico Operacional';
    if (authStore.isSuperuser) return 'Engenheiro Chefe';
    return 'Colaborador';
});

function formatNotificationDate(date: string) {
  return formatDistanceToNow(new Date(date), { addSuffix: true, locale: ptBR });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function handleNotificationClick(notification: any) {
  if (!notification.is_read) {
    await notificationStore.markAsRead(notification.id);
  }

  const type = notification.related_entity_type;
  if (type === 'andon') {
    void router.push('/andon-board');
  } else if (type === 'maintenance_request' || type === 'maintenance') {
    void router.push('/maintenance');
  } else if (type === 'document') {
    void router.push('/documents');
  } else if (type === 'vehicle' || type === 'machine') {
    void router.push(`/vehicles/${notification.related_vehicle_id}`);
  } else {
    void router.push('/dashboard');
  }
}

// --- Definição do Menu Industrial ---
interface MenuItem { title: string; icon: string; to: string; }
interface MenuCategory { label: string; icon?: string; children: MenuItem[]; separator?: boolean; }

const menuStructure = computed(() => {
    if (authStore.isManager) return getManagerMenu();
    if (authStore.isDriver) return getOperatorMenu();
    if (authStore.user?.role === 'maintenance') return getMaintenanceMenu(); 
    if (authStore.user?.role === 'pcp') return getPCPMenu();
    return getGenericSectorMenu();
});

function getGenericSectorMenu(): MenuCategory[] {
    return [
        {
            label: 'Monitorização Industrial',
            children: [
                { title: 'Quadro Andon', icon: 'campaign', to: '/andon-board' }
            ]
        }
    ];
}

function getMaintenanceMenu(): MenuCategory[] {
    return [
        {
            label: 'Manutenção Industrial',
            children: [
                { title: 'Formulários', icon: 'fact_check', to: '/manutencao' },
                { title: 'Ordens de Manutenção', icon: 'engineering', to: '/maintenance' },
                { title: 'Máquinas/Ativos', icon: 'precision_manufacturing', to: '/vehicles' },
                { title: 'Quadro Andon', icon: 'campaign', to: '/andon-board' },
                { title: 'Feedback', icon: 'chat', to: '/feedback' },
                { title: 'Rastreabilidade', icon: 'qr_code_2', to: '/inventory-items' }
            ]
        }
    ];
}

function getPCPMenu(): MenuCategory[] {
    return [
        {
            label: 'Planejamento e Controle',
            children: [
                { title: 'Dashboard Geral', icon: 'dashboard', to: '/dashboard' },
                { title: 'Performance (OEE)', icon: 'trending_up', to: '/employees' },
                { title: 'Máquinas e Ativos', icon: 'precision_manufacturing', to: '/vehicles' },
                { title: 'Quadro Andon', icon: 'campaign', to: '/andon-board' },
                { title: 'Relatórios Históricos', icon: 'bar_chart', to: '/reports' },
                { title: 'Ordens de Manutenção', icon: 'engineering', to: '/maintenance' },
                { title: 'Formulários', icon: 'fact_check', to: '/manutencao' },
                { title: 'Gestão de Feedback', icon: 'chat', to: '/feedback' }
            ]
        }
    ];
}

function getOperatorMenu(): MenuCategory[] {
    return [
        {
            label: 'Operacional',
            children: [
                { title: 'Chão de Fábrica', icon: 'precision_manufacturing', to: '/dashboard' },
                { title: 'Minhas O.P.s', icon: 'assignment', to: '/journeys' },
                { title: 'Apontamento', icon: 'timer', to: '/driver-cockpit' }
            ]
        },
        {
            label: 'Suporte',
            children: [
                { title: 'Abrir Chamado', icon: 'build', to: '/maintenance' },
                { title: 'Minhas Máquinas', icon: 'dns', to: '/vehicles' }
            ]
        }
    ];
}

async function markAllRead() {
  const unreadNotifications = notificationStore.notifications.filter(n => !n.is_read);
  for (const notification of unreadNotifications) {
    await notificationStore.markAsRead(notification.id);
  }
  await notificationStore.fetchUnreadCount();
}

function getNotificationIcon(type: string) {
  if (type.includes('maintenance')) return 'engineering';
  if (type.includes('andon')) return 'campaign';
  if (type.includes('document')) return 'description';
  if (type.includes('achievement')) return 'emoji_events';
  return 'notifications';
}

function getManagerMenu(): MenuCategory[] {
  const menu: MenuCategory[] = [];

  menu.push({
    label: 'Visão Geral', 
    children: [
      { title: 'Dashboard da Planta', icon: 'analytics', to: '/dashboard' },
      { title: 'Apontamentos', icon: 'groups', to: '/employees' }, 
      { title: 'Supervisorio', icon: 'dashboard', to: '/supervisory' },
    ]
  });

  menu.push({ 
      label: 'Ativos & Recursos', 
      children: [        
        { title: 'Máquinas Industriais', icon: 'precision_manufacturing', to: '/vehicles' },
      ] 
  });

  menu.push({
      label: 'PCP & Manutenção', 
      children: [
          { title: 'Ordens de Manutenção', icon: 'engineering', to: '/maintenance' },
          { title: 'Manutenção Industrial', icon: 'fact_check', to: '/manutencao' },
      ]
  });

  menu.push({
      label: 'Administração',
      children: [
          { title: 'Usuários do Sistema', icon: 'manage_accounts', to: '/users' },
      ]
  });

  return menu;
}

function connectNotificationSocket() {
    const orgId = authStore.user?.organization_id;
    
    // 1. Previne a conexão "undefined"
    if (!orgId) {
        console.warn('⏳ Aguardando dados do usuário para conectar o WebSocket...');
        return;
    }

    // 2. Pega a URL dinâmica da API (vinda do .env) e transforma HTTP em WS
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    const wsBase = apiBase.replace(/^http/, 'ws'); 
    
    const wsUrl = `${wsBase}/andon/ws/${orgId}`;
    
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'NEW_NOTIFICATION') {
            void notificationStore.fetchUnreadCount();
            $q.notify({
                icon: 'notifications_active',
                color: 'teal-9',
                message: 'Você tem um novo alerta da fábrica!',
                position: 'top-right'
            });
        }
    };
}

onMounted(async () => {
    setCssVar('primary', '#128c7e');
    
    // Configurações do usuário logado (Gestor)
    if (authStore.isManager) {
        void notificationStore.fetchUnreadCount();
        connectNotificationSocket();
    }

    // --- CORREÇÃO: VERIFICAR E ENVIAR TOKEN PENDENTE ---
    // Só executa se o usuário estiver autenticado (login feito com sucesso)
    if (authStore.token) {
        
        // Verifica se o arquivo de boot deixou algum token guardado na variável global
        if (window.FCM_TOKEN_PENDING) {
            console.log('📦 Encontrado token pendente do boot. Enviando para API...');
            
            try {
                await api.post('/users/me/device-token', { token: window.FCM_TOKEN_PENDING });
                console.log('✅ Token pendente enviado com sucesso!');
                
                // Limpa a variável para não enviar novamente sem necessidade
                window.FCM_TOKEN_PENDING = undefined; 
            } catch (e) {
                console.error('❌ Erro ao enviar token pendente:', e);
            }
        }
    }
});

</script>

<style lang="scss" scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

.font-inter { font-family: 'Inter', sans-serif; }
.font-mono { font-family: 'JetBrains Mono', monospace; }

/* --- Glassmorphism Effect --- */
.glass-header { 
  background-color: rgba(255, 255, 255, 0.7) !important;
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
}

.glass-drawer {
  background-color: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(10px) saturate(160%);
  -webkit-backdrop-filter: blur(10px) saturate(160%);
}

.glass-menu {
  background-color: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(15px);
  border: 1px solid rgba(18, 140, 126, 0.1);
}

/* --- Colors & Backgrounds --- */
.bg-grey-1 { background-color: #f0f4f4; }

/* --- Navigation & Drawer --- */
.drawer-style { border-right: 1px solid rgba(18, 140, 126, 0.1); }

.navigation-item {
  color: #334e4b;
  border-radius: 8px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 0.9rem;
  
  &:hover {
    background-color: rgba(112, 192, 176, 0.15);
    color: #128c7e;
    transform: translateX(4px);
  }
}

.active-item {
  background: linear-gradient(90deg, rgba(112, 192, 176, 0.2) 0%, rgba(255, 255, 255, 0.8) 100%) !important;
  color: #128c7e !important;
  font-weight: 600;
  border-left: 4px solid #128c7e;
  border-radius: 4px 8px 8px 4px;
  
  .icon-wrapper {
    background-color: rgba(18, 140, 126, 0.15);
    border-radius: 6px;
    width: 32px; height: 32px;
  }
  
  .nav-icon { color: #128c7e; }
}

/* --- Header Styling --- */
.header-style {
  border-bottom: 1px solid rgba(18, 140, 126, 0.1);
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.03);
}

.logo-area {
  transition: opacity 0.2s;
  &:hover { opacity: 0.8; }
}

.hover-rotate:hover { transform: rotate(180deg); transition: transform 0.5s ease-in-out; }

/* --- Utilities --- */
.icon-wrapper { width: 32px; height: 32px; transition: background-color 0.3s; }
.border-2 { border: 2px solid white; }
.shadow-sm { box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05); }
.border-bottom { border-bottom: 1px solid rgba(18, 140, 126, 0.1); }
.hover-bg-gray:hover { background-color: rgba(112, 192, 176, 0.1); }
.hover-bg-red-soft:hover { background-color: #fef2f2; }
.hover-scale { transition: transform 0.2s; &:hover { transform: scale(1.05); } }
.hover-red:hover { background-color: #fee2e2 !important; }
.border-red-soft { border: 1px solid #fecaca; }

.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
  box-shadow: 0 0 0 2px white;
}

.opacity-10 { opacity: 0.1; }
.letter-spacing-1 { letter-spacing: 1px; }

/* --- Animations --- */
.transition-all { transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-slide-enter-active, .fade-slide-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.fade-slide-enter-from { opacity: 0; transform: translateX(-8px); }
.fade-slide-leave-to { opacity: 0; transform: translateX(8px); }
.animate-fade { animation: fadeIn 0.8s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* --- Dark Mode Overrides (Dark Forest Theme) --- */
.body--dark {
  /* Fundo principal: Verde muito escuro, quase preto (Dark Forest) */
  .bg-grey-1 { background-color: #05100e !important; }

  /* Header e Drawer: Translúcidos com tom esverdeado */
  .glass-header { 
    background-color: rgba(5, 20, 18, 0.85) !important;
    border-bottom-color: rgba(18, 140, 126, 0.3);
  }
  .glass-drawer { 
    background-color: rgba(5, 20, 18, 0.85) !important;
    border-right-color: rgba(18, 140, 126, 0.3);
  }

  /* Menus Dropdown: Fundo mais preto para contraste */
  .glass-menu {
    background-color: rgba(2, 10, 8, 0.95) !important;
    border: 1px solid rgba(18, 140, 126, 0.2);
  }
  
  /* Lógica do Logo */
  .logo-light { display: none; }
  .logo-dark { display: block !important; }
  
  /* Itens de navegação */
  .navigation-item {
    color: #cbd5e1; /* Texto cinza claro */
    &:hover { 
      background-color: rgba(18, 140, 126, 0.15); /* Hover verde suave */
      color: #4db6ac; 
    }
  }

  /* Item Ativo (Destaque) */
  .active-item { 
    background: linear-gradient(90deg, rgba(18, 140, 126, 0.25) 0%, transparent 100%) !important;
    color: #4db6ac !important; /* Teal brilhante */
    border-left-color: #4db6ac;
    .nav-icon { color: #4db6ac !important; }
  }
  
  /* Cores de Texto e Utilitários */
  .text-teal-8 { color: #4db6ac !important; }
  .text-teal-9 { color: #80cbc4 !important; }
  .text-dark { color: #ffffff !important; }
  .text-grey-9 { color: #e2e8f0 !important; }
  .text-grey-8 { color: #cbd5e1 !important; }
  .border-bottom { border-bottom-color: rgba(255,255,255,0.1); }

  /* Notificações */
  .bg-blue-50 {
     background-color: rgba(18, 140, 126, 0.12) !important; /* Destaque verde escuro para não lidos */
  }
  .bg-teal-1 {
     background-color: rgba(18, 140, 126, 0.2) !important; /* Header da notificação */
  }
  .text-teal-10 {
     color: #ffffff !important;
  }
}

.line-height-normal {
  line-height: 1.4;
  letter-spacing: 0.2px;
}

.notification-item-ui {
  transition: background-color 0.3s;
  &:hover {
    background-color: rgba(18, 140, 126, 0.05) !important;
  }
}

.bg-blue-50 {
  background-color: #f0f9f9;
}

/* Indicador de "Novo" com brilho suave */
.new-indicator-glow {
  width: 8px;
  height: 8px;
  background-color: #128c7e;
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(18, 140, 126, 0.6);
}

.rounded-circle {
  border-radius: 50%;
}
</style>
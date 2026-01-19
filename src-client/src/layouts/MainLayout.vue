<template>
  <q-layout view="lHh LpR lFf" class="main-layout-container font-inter bg-grey-1">
    
    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      :width="260"
      :breakpoint="800"
      class="bg-surface drawer-style"
    >
      <q-scroll-area class="fit" :thumb-style="{ width: '4px', borderRadius: '2px', opacity: 0.5 }">
        
        <div class="q-pa-md row items-center justify-center relative-position" style="height: 110px;">
          <img src="~assets/trucar-logo-dark.png" class="logo-light animate-fade" style="height: 55px; max-width: 90%; transition: all 0.3s;" alt="Vemag Logo">
          <img src="~assets/trucar-logo-white.png" class="logo-dark animate-fade" style="height: 55px; max-width: 90%; display: none; transition: all 0.3s;" alt="Vemag Logo">
        </div>
        
        <q-separator class="q-mx-lg q-mb-md opacity-10" />

        <q-list padding class="q-px-md text-grey-7">
          <template v-for="category in menuStructure" :key="category.label">
            
            <q-item-label header class="text-weight-bold text-uppercase text-caption text-grey-5 q-pt-md q-pl-xs letter-spacing-1" style="font-size: 0.7rem;">
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

          <div v-if="authStore.isSuperuser" class="q-mt-xl bg-red-1 rounded-borders q-pa-xs border-red-soft">
            <q-item-label header class="text-weight-bold text-uppercase text-caption text-negative q-pt-sm q-pl-md">
              Zona de Perigo
            </q-item-label>
            <q-item clickable to="/admin" exact v-ripple class="q-ma-xs rounded-borders navigation-item text-negative hover-red">
              <q-item-section avatar><q-icon name="security" color="negative" size="20px"/></q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-bold">Painel Admin</q-item-label>
                <q-item-label caption class="text-red-4">Configuração SAP</q-item-label>
              </q-item-section>
            </q-item>
          </div>
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <q-header bordered class="bg-white-blur text-grey-9 header-style">
      <q-toolbar style="height: 70px;">
        <q-btn flat dense round icon="menu_open" color="grey-8" aria-label="Menu" @click="toggleLeftDrawer" class="lt-md" />
        
        <div class="row items-center q-ml-sm cursor-pointer logo-area" @click="router.push('/')">
          <div class="bg-primary text-white rounded-borders flex flex-center q-mr-md shadow-2 transition-transform hover-rotate" style="width: 36px; height: 36px;">
             <q-icon name="hub" size="20px" />
          </div>
          <div>
            <q-toolbar-title class="text-weight-bold text-dark gt-xs font-mono q-pl-none" style="font-size: 1.35rem; letter-spacing: -0.5px; line-height: 1;">
              vemag<span class="text-primary">.mes</span>
            </q-toolbar-title>
            <div class="text-caption text-grey-5 gt-xs" style="line-height: 1; font-size: 0.7rem; letter-spacing: 1px;">INTELLIGENT MANUFACTURING</div>
          </div>
        </div>

        <q-space />

        <div class="row q-gutter-sm items-center">
          
          <q-btn v-if="authStore.isManager" flat round dense class="text-grey-7 relative-position hover-scale q-mr-sm">
            <q-icon name="notifications_none" size="26px" />
            <q-badge v-if="notificationStore.unreadCount > 0" color="red" floating rounded mini class="shadow-1 animate-pulse" style="top: 4px; right: 4px;" />
            
            <q-menu @show="notificationStore.fetchNotifications()" fit anchor="bottom right" self="top right" :offset="[0, 14]" class="shadow-10 rounded-borders" style="width: 360px; max-width: 95vw;">
              <div class="row no-wrap items-center q-pa-md bg-white border-bottom">
                <div class="text-subtitle1 text-weight-bold text-grey-9">Alertas da Fábrica</div>
                <q-space />
                <q-btn round flat icon="done_all" size="sm" color="primary" @click="notificationStore.markAllRead"><q-tooltip>Marcar tudo como lido</q-tooltip></q-btn>
              </div>
              <q-scroll-area style="height: 300px;" class="bg-grey-1">
                  <q-list separator>
                    <q-item v-for="notification in notificationStore.notifications" :key="notification.id" clickable v-ripple class="bg-white q-py-md hover-bg-gray" @click="handleNotificationClick(notification)">
                      <q-item-section avatar>
                        <div class="bg-orange-1 q-pa-sm rounded-circle text-orange-9 shadow-sm"><q-icon name="notifications_active" size="20px" /></div>
                      </q-item-section>
                      <q-item-section>
                        <q-item-label class="text-body2 text-weight-medium text-grey-9">{{ notification.message }}</q-item-label>
                        <q-item-label caption class="text-grey-6 q-mt-xs">{{ formatNotificationDate(notification.created_at) }}</q-item-label>
                      </q-item-section>
                      <q-item-section side v-if="!notification.is_read">
                         <div class="status-dot bg-blue-5"></div>
                      </q-item-section>
                    </q-item>
                    <div v-if="notificationStore.notifications.length === 0" class="column flex-center full-height q-pa-xl text-grey-5">
                      <q-icon name="check_circle_outline" size="40px" class="q-mb-sm text-green-4" />
                      <div class="text-caption">Nenhum alerta pendente.</div>
                    </div>
                  </q-list>
              </q-scroll-area>
            </q-menu>
          </q-btn>

          <div style="height: 30px; width: 1px; background: #e2e8f0;" class="q-mx-sm"></div>

          <q-btn-dropdown flat no-caps class="text-grey-9 profile-btn q-ml-none rounded-borders q-px-sm hover-bg-gray" content-class="profile-menu shadow-10 rounded-borders">
            <template v-slot:label>
              <div class="row items-center no-wrap">
                <q-avatar size="40px" class="shadow-1 border-2 border-white">
                  <img :src="getAvatarUrl(authStore.user?.avatar_url)" style="object-fit: cover;">
                </q-avatar>
                <div class="text-left gt-xs q-ml-md">
                  <div class="text-weight-bold text-body2 font-inter" style="line-height: 1.2;">{{ firstName(authStore.user?.full_name) }}</div>
                  <div class="text-caption text-primary font-weight-bold text-uppercase" style="font-size: 0.65rem; letter-spacing: 0.5px;">{{ roleLabel }}</div>
                </div>
                <q-icon name="expand_more" color="grey-5" size="xs" class="q-ml-xs gt-xs" />
              </div>
            </template>

            <div class="row no-wrap q-pa-md" style="min-width: 290px;">
              <div class="column" style="flex: 1;">
                <div class="text-overline text-grey-5 q-mb-sm">Sistema</div>
                
                <div class="q-mb-md">
                  <div class="text-caption text-weight-medium text-grey-8 q-mb-xs">Cor do Tema</div>
                  <div class="row q-gutter-xs">
                    <q-btn round size="xs" class="shadow-1" color="blue-10" @click="changeTheme('#154ec1')" /> 
                    <q-btn round size="xs" class="shadow-1" color="grey-9" @click="changeTheme('#263238')" /> 
                    <q-btn round size="xs" class="shadow-1" color="red-9" @click="changeTheme('#c62828')" /> 
                    <q-btn round size="xs" class="shadow-1" color="teal-9" @click="changeTheme('#00695c')" /> 
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
                    <q-item-section avatar style="min-width: 30px;"><q-icon name="tune" size="18px" color="grey-7" /></q-item-section>
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
import { setCssVar } from 'quasar';
import { useAuthStore } from 'stores/auth-store';
import { useNotificationStore } from 'stores/notification-store';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import defaultAvatar from 'assets/default-avatar.png';

const leftDrawerOpen = ref(false);
const customColor = ref('#154ec1'); // Azul Vemag padrão
const router = useRouter();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();

// --- Lógica de Tema ---
function changeTheme(color: string) {
  customColor.value = color;
  setCssVar('primary', color);
  setCssVar('secondary', color); 
}

function toggleLeftDrawer() { leftDrawerOpen.value = !leftDrawerOpen.value; }

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
  if (!notification.is_read) await notificationStore.markAsRead(notification.id);
  void router.push('/maintenance'); 
}

// --- Definição do Menu Industrial ---
interface MenuItem { title: string; icon: string; to: string; }
interface MenuCategory { label: string; icon?: string; children: MenuItem[]; separator?: boolean; }

const menuStructure = computed(() => {
    if (authStore.isManager) return getManagerMenu();
    if (authStore.isDriver) return getOperatorMenu();
    return [];
});

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

function getManagerMenu(): MenuCategory[] {
  const menu: MenuCategory[] = [];

  menu.push({
    label: 'Visão Geral', 
    children: [
      { title: 'Dashboard da Planta', icon: 'analytics', to: '/dashboard' },
      { title: 'Equipe Técnica', icon: 'groups', to: '/employees' }, 
      { title: 'Relatórios', icon: 'summarize', to: '/reports' },
    ]
  });

  menu.push({ 
      label: 'Ativos & Recursos', 
      children: [
        { title: 'Máquinas Industriais', icon: 'precision_manufacturing', to: '/vehicles' },
        { title: 'Almoxarifado (Peças)', icon: 'inventory_2', to: '/parts' },
        { title: 'Ferramental', icon: 'handyman', to: '/implements' }
      ] 
  });

  menu.push({
      label: 'PCP & Manutenção', 
      children: [
          { title: 'Ordens de Manutenção', icon: 'engineering', to: '/maintenance' },
          { title: 'Roteiros de Produção', icon: 'fact_check', to: '/journeys' },
      ]
  });

  menu.push({
      label: 'Gestão Financeira',
      children: [
          { title: 'Custos Operacionais', icon: 'monetization_on', to: '/costs' },
          { title: 'Rastreabilidade', icon: 'qr_code_2', to: '/inventory-items' },
          { title: 'Usuários do Sistema', icon: 'manage_accounts', to: '/users' },
          { title: 'Auditoria SAP', icon: 'history_edu', to: '/audit-logs' } 
      ]
  });

  return menu;
}

onMounted(() => {
  setCssVar('primary', '#154ec1');
  if (authStore.isManager) {
    void notificationStore.fetchUnreadCount();
  }
});
</script>

<style lang="scss" scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

.font-inter { font-family: 'Inter', sans-serif; }
.font-mono { font-family: 'JetBrains Mono', monospace; }

/* --- Colors & Backgrounds --- */
.bg-surface { background-color: #ffffff; }
.bg-grey-1 { background-color: #f8fafc; }
.bg-white-blur { 
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

/* --- Navigation & Drawer --- */
.drawer-style { border-right: 1px solid #f1f5f9; }

.navigation-item {
  color: #475569; /* Slate-600 */
  border-radius: 8px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 0.9rem;
  
  &:hover {
    background-color: #f1f5f9;
    color: #1e293b;
    transform: translateX(4px);
  }
  
  .nav-icon { transition: color 0.2s ease; }
}

.active-item {
  background: linear-gradient(90deg, #eff6ff 0%, #ffffff 100%); /* Gradiente sutil */
  color: var(--q-primary);
  font-weight: 600;
  border-left: 3px solid var(--q-primary);
  border-radius: 4px 8px 8px 4px; /* Canto reto na esquerda */
  
  .icon-wrapper {
    background-color: rgba(var(--q-primary), 0.1);
    border-radius: 6px;
    width: 32px; height: 32px;
  }
  
  .nav-icon { color: var(--q-primary); }
}

/* --- Header Styling --- */
.header-style {
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02);
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
.border-bottom { border-bottom: 1px solid #f1f5f9; }
.hover-bg-gray:hover { background-color: #f8fafc; }
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

/* --- Dark Mode Overrides --- */
.body--dark {
  .bg-surface { background-color: #0f172a; border-color: #1e293b; }
  .text-primary-text { color: #f8fafc; }
  .logo-light { display: none; }
  .logo-dark { display: block !important; }
  .bg-grey-1 { background-color: #020617; }
  .bg-white-blur { background-color: rgba(15, 23, 42, 0.9); border-bottom-color: #1e293b; }
  .drawer-style { border-right-color: #1e293b; }
  
  .navigation-item {
    color: #94a3b8;
    &:hover { background-color: rgba(255,255,255,0.05); color: #f1f5f9; }
  }
  .active-item { 
    background: linear-gradient(90deg, rgba(var(--q-primary), 0.2) 0%, transparent 100%);
    color: var(--q-primary);
    .icon-wrapper { background-color: rgba(var(--q-primary), 0.2); }
  }
  .bg-white { background-color: #1e293b !important; color: white; }
  .text-grey-9 { color: #f1f5f9 !important; }
  .text-dark { color: white !important; }
  .border-bottom { border-bottom-color: #334155; }
}
</style>
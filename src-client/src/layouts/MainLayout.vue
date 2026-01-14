<template>
  <q-layout view="lHh LpR lFf" class="main-layout-container">
    
    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      class="app-sidebar"
      :width="260"
      :breakpoint="700"
    >
      <q-scroll-area class="fit">
        <div class="q-pa-md row items-center justify-center sidebar-header" style="height: 80px;">
          <img src="~assets/trucar-logo-dark.png" class="logo-light-theme" style="height: 32px; max-width: 100%;" alt="Logo">
          <img src="~assets/trucar-logo-white.png" class="logo-dark-theme" style="height: 32px; max-width: 100%;" alt="Logo">
        </div>
        
        <q-separator class="q-mb-md q-mx-md" />

        <q-list padding class="q-px-sm">
          <template v-for="category in menuStructure" :key="category.label">
            
            <q-expansion-item
              v-if="category.children.length > 0"
              :icon="category.icon"
              :label="category.label"
              expand-separator
              default-opened
              header-class="text-weight-medium text-grey-8 nav-header"
              class="q-mb-sm overflow-hidden rounded-borders"
            >
              <q-item
                v-for="link in category.children"
                :key="link.title"
                clickable
                :to="link.to"
                exact
                v-ripple
                class="nav-link"
                active-class="nav-link--active"
              >
                <q-item-section avatar style="min-width: 40px;">
                  <q-icon :name="link.icon" size="20px" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ link.title }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-expansion-item>

          </template>

          <div v-if="authStore.isSuperuser">
            <q-separator class="q-my-md" />
            <div class="text-caption text-grey-6 q-px-md q-mb-sm text-uppercase text-weight-bold">Sistema</div>
            <q-item clickable to="/admin" exact v-ripple class="nav-link" active-class="nav-link--active">
              <q-item-section avatar><q-icon name="admin_panel_settings" /></q-item-section>
              <q-item-section>
                <q-item-label>Painel Admin</q-item-label>
                <q-item-label caption>Configuração SAP</q-item-label>
              </q-item-section>
            </q-item>
          </div>
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <q-header bordered class="main-header">
      <q-toolbar style="height: 64px;">
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" class="lt-md text-grey-8" />
        
        <q-toolbar-title class="lt-md text-grey-8 text-weight-bold">
          Gestão Manutenção
        </q-toolbar-title>

        <q-space />

        <div class="row q-gutter-sm items-center">
          <q-btn flat round dense icon="settings" to="/settings" class="text-grey-7">
            <q-tooltip>Configurações</q-tooltip>
          </q-btn>
          
          <q-btn v-if="authStore.isManager" flat round dense icon="notifications" class="text-grey-7 q-mr-sm">
            <q-badge v-if="notificationStore.unreadCount > 0" color="red" floating rounded>{{ notificationStore.unreadCount }}</q-badge>
            <q-menu @show="notificationStore.fetchNotifications()" fit anchor="bottom left" self="top right" :offset="[0, 10]" style="width: 350px; max-width: 90vw;">
              <div class="row no-wrap items-center q-pa-md  bb-1">
                <div class="text-subtitle1 text-weight-bold">Alertas da Fábrica</div>
                <q-space />
                <q-spinner v-if="notificationStore.isLoading" color="primary" size="1.2em" />
              </div>
              <q-scroll-area style="height: 300px;">
                 <q-list separator class="q-pa-none">
                    <q-item v-for="notification in notificationStore.notifications" :key="notification.id" clickable v-ripple class="q-py-md" @click="handleNotificationClick(notification)">
                      <q-item-section avatar>
                        <q-avatar icon="warning" color="warning" text-color="white" size="md" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label class="text-body2">{{ notification.message }}</q-item-label>
                        <q-item-label caption class="q-mt-xs text-grey-6">{{ formatNotificationDate(notification.created_at) }}</q-item-label>
                      </q-item-section>
                    </q-item>
                 </q-list>
              </q-scroll-area>
            </q-menu>
          </q-btn>

          <q-btn-dropdown flat no-caps class="text-grey-8 profile-btn" content-class="profile-menu">
          <template v-slot:label>
            <div class="row items-center no-wrap">
              <q-avatar size="36px" class="shadow-1">
                <img :src="getAvatarUrl(authStore.user?.avatar_url)" style="object-fit: cover;">
              </q-avatar>
              <div class="text-left gt-xs q-ml-sm">
                <div class="text-weight-bold" style="line-height: 1.1;">{{ firstName(authStore.user?.full_name) }}</div>
                <div class="text-caption text-grey-6" style="line-height: 1;">{{ roleLabel }}</div>
              </div>
            </div>
          </template>

            <div class="row no-wrap q-pa-md">
              <div class="column">
                <div class="text-h6 q-mb-xs">Perfil</div>
                <q-list dense>
                  <q-item clickable v-close-popup to="/settings">
                    <q-item-section avatar style="min-width: 30px;"><q-icon name="settings" size="xs" /></q-item-section>
                    <q-item-section>Configurações</q-item-section>
                  </q-item>
                </q-list>
              </div>

              <q-separator vertical inset class="q-mx-lg" />

              <div class="column items-center justify-center">
              <q-avatar size="72px" class="q-mb-sm">
                  <img :src="getAvatarUrl(authStore.user?.avatar_url)" style="object-fit: cover;">
              </q-avatar>
              <div class="text-subtitle1 q-mt-sm text-center">{{ authStore.user?.full_name }}</div>
              <q-btn color="primary" label="Sair" push size="sm" v-close-popup @click="handleLogout" />
            </div>
          </div>
        </q-btn-dropdown>
      </div>
    </q-toolbar>
    </q-header>

    <q-page-container class="app-page-container">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from 'stores/auth-store';
import { useNotificationStore } from 'stores/notification-store';
import { useTerminologyStore } from 'stores/terminology-store';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import defaultAvatar from 'assets/default-avatar.png';

const leftDrawerOpen = ref(false);
const router = useRouter();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const terminologyStore = useTerminologyStore();

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
    if (authStore.isManager) return 'Gerente de Planta';
    if (authStore.isDriver) return 'Operador/Técnico';
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
const menuStructure = computed(() => {
    if (authStore.isManager) return getManagerMenu();
    if (authStore.isDriver) return getOperatorMenu();
    return [];
});

interface MenuItem { title: string; icon: string; to: string; }
interface MenuCategory { label: string; icon: string; children: MenuItem[]; }

function getOperatorMenu(): MenuCategory[] {
    return [
        {
            label: 'Chão de Fábrica', icon: 'factory',
            children: [
                { title: 'Painel do Operador', icon: 'precision_manufacturing', to: '/dashboard' },
                { title: 'Minhas Ordens', icon: 'assignment', to: '/journeys' },
                { title: 'Apontar Horas', icon: 'timer', to: '/driver-cockpit' }
            ]
        },
        {
            label: 'Manutenção', icon: 'build',
            children: [
                { title: 'Solicitar Reparo', icon: 'report_problem', to: '/maintenance' },
                { title: 'Histórico', icon: 'history', to: '/vehicles' }
            ]
        }
    ];
}

function getManagerMenu(): MenuCategory[] {
  const menu: MenuCategory[] = [];

  // 1. Visão Geral
  menu.push({
    label: 'Supervisão', icon: 'monitor_heart',
    children: [
      { title: 'Dashboard Geral', icon: 'analytics', to: '/dashboard' },
      { title: 'Colaboradores', icon: 'people', to: '/employees' }, 
    ]
  });

  // 2. Gestão de Ativos
  menu.push({ 
      label: 'Ativos Industriais', icon: 'precision_manufacturing', 
      children: [

        { title: terminologyStore.vehiclePageTitle, icon: 'settings_suggest', to: '/vehicles' },
        { title: 'Inventário de Peças', icon: 'inventory', to: '/parts' },
        { title: 'Ferramentas', icon: 'handyman', to: '/implements' }
      ] 
  });

  // 3. Manutenção e Ordens
  menu.push({
      label: 'Planejamento (PCP)', icon: 'calendar_month',
      children: [
          { title: 'Ordens de Manutenção', icon: 'build_circle', to: '/maintenance' },
          { title: 'Ordens de Produção', icon: 'fact_check', to: '/journeys' },
      ]
  });

  // 4. Custos e Pessoas
  menu.push({
      label: 'Gestão', icon: 'manage_accounts',
      children: [
          { title: 'Rastreabilidade', icon: 'arrow_upward', to: '/inventory-items' },
          { title: 'Custos de Manutenção', icon: 'attach_money', to: '/costs' },
          { title: 'Técnicos/Operadores', icon: 'engineering', to: '/users' },
          { title: 'Integração SAP', icon: 'sync_alt', to: '/audit-logs' } 
      ]
  });

  return menu;
}

onMounted(() => {
  if (authStore.isManager) {
    void notificationStore.fetchUnreadCount();
  }
});
</script>

<style lang="scss" scoped>
.main-layout-container {
  background-color: #f8fafc;
  .body--dark & { background-color: #0f172a; }
}
.app-sidebar {
  background-color: white;
  .nav-link {
    color: #475569; margin: 4px 8px; border-radius: 8px;
    &--active { background-color: #eff6ff; color: $primary; font-weight: 600; }
    &:hover:not(.nav-link--active) { background-color: #f1f5f9; }
  }
}
.body--dark .app-sidebar { background-color: #1e293b; color: #cbd5e1; }
.main-header { background-color: white; border-bottom: 1px solid #e2e8f0; }
</style>
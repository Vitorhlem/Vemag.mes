<template>
  <q-layout view="lHh LpR lFf" class="main-layout-container font-inter">
    
    <q-drawer
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      :width="260"
      :breakpoint="700"
      class="bg-surface border-r-light"
    >
      <q-scroll-area class="fit">
        <div class="q-pa-md row items-center justify-center" style="height: 80px;">
          <img src="~assets/trucar-logo-dark.png" class="logo-light" style="height: 55px; max-width: 100%; transition: all 0.3s;" alt="Vemag Logo">
          <img src="~assets/trucar-logo-white.png" class="logo-dark" style="height: 50px; max-width: 100%; display: none; transition: all 0.3s;" alt="Vemag Logo">
        </div>
        
        <q-separator class="q-mx-md q-mb-md opacity-20" />

        <q-list padding class="text-grey-8">
          <template v-for="category in menuStructure" :key="category.label">
            
            <q-item-label header class="text-weight-bold text-uppercase text-caption text-grey-6 q-pt-md">
              {{ category.label }}
            </q-item-label>

            <q-item
              v-for="link in category.children"
              :key="link.title"
              clickable
              :to="link.to"
              exact
              v-ripple
              class="q-mx-sm q-mb-xs rounded-borders navigation-item"
              active-class="active-item shadow-1"
            >
              <q-item-section avatar style="min-width: 40px;">
                <q-icon :name="link.icon" size="22px" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">{{ link.title }}</q-item-label>
              </q-item-section>
            </q-item>

            <q-separator v-if="category.separator" class="q-my-sm q-mx-lg opacity-20" />
          </template>

          <div v-if="authStore.isSuperuser" class="q-mt-md">
            <q-item-label header class="text-weight-bold text-uppercase text-caption text-negative">
              Zona de Perigo
            </q-item-label>
            <q-item clickable to="/admin" exact v-ripple class="q-mx-sm rounded-borders navigation-item">
              <q-item-section avatar><q-icon name="admin_panel_settings" color="negative" /></q-item-section>
              <q-item-section>
                <q-item-label>Painel Admin</q-item-label>
                <q-item-label caption>Configuração SAP</q-item-label>
              </q-item-section>
            </q-item>
          </div>
        </q-list>
      </q-scroll-area>
    </q-drawer>

    <q-header bordered class="bg-surface text-primary-text header-blur">
      <q-toolbar style="height: 64px;">
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" class="lt-md text-grey-8" />
        
        <div class="row items-center q-ml-sm">
          <q-icon name="factory" class="text-primary q-mr-sm" size="24px" />
          <q-toolbar-title class="text-weight-bold text-grey-9 gt-xs" style="font-size: 1.1rem; letter-spacing: -0.5px;">
            VEMAG <span class="text-weight-regular text-grey-6">Smart Factory</span>
          </q-toolbar-title>
        </div>

        <q-space />

        <div class="row q-gutter-sm items-center">
          
          <q-btn v-if="authStore.isManager" flat round dense icon="notifications_none" class="text-grey-7 relative-position">
            <q-badge v-if="notificationStore.unreadCount > 0" color="red" floating rounded mini />
            <q-menu @show="notificationStore.fetchNotifications()" fit anchor="bottom right" self="top right" :offset="[0, 10]" style="width: 350px; max-width: 90vw;">
              <div class="row no-wrap items-center q-pa-md bg-grey-1 border-bottom">
                <div class="text-subtitle2 text-weight-bold">Alertas da Fábrica</div>
                <q-space />
                <q-spinner v-if="notificationStore.isLoading" color="primary" size="1em" />
              </div>
              <q-scroll-area style="height: 300px;">
                 <q-list separator>
                    <q-item v-for="notification in notificationStore.notifications" :key="notification.id" clickable v-ripple @click="handleNotificationClick(notification)">
                      <q-item-section avatar>
                        <q-avatar icon="priority_high" color="orange-1" text-color="orange-9" size="md" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label class="text-caption text-weight-medium">{{ notification.message }}</q-item-label>
                        <q-item-label caption class="text-grey-5" style="font-size: 0.7rem;">{{ formatNotificationDate(notification.created_at) }}</q-item-label>
                      </q-item-section>
                    </q-item>
                    <div v-if="notificationStore.notifications.length === 0" class="text-center q-pa-lg text-grey-5">
                      <q-icon name="check_circle" size="md" class="q-mb-sm" />
                      <div>Tudo operando normalmente.</div>
                    </div>
                 </q-list>
              </q-scroll-area>
            </q-menu>
          </q-btn>

          <q-btn-dropdown flat no-caps class="text-grey-8 profile-btn q-ml-sm" content-class="profile-menu shadow-10">
            <template v-slot:label>
              <div class="row items-center no-wrap">
                <q-avatar size="36px" class="shadow-2 border-primary">
                  <img :src="getAvatarUrl(authStore.user?.avatar_url)" style="object-fit: cover;">
                </q-avatar>
                <div class="text-left gt-xs q-ml-sm">
                  <div class="text-weight-bold text-body2" style="line-height: 1.1;">{{ firstName(authStore.user?.full_name) }}</div>
                  <div class="text-caption text-primary" style="line-height: 1; font-size: 0.7rem;">{{ roleLabel }}</div>
                </div>
              </div>
            </template>

            <div class="row no-wrap q-pa-md" style="min-width: 280px;">
              
              <div class="column q-mr-md" style="flex: 1;">
                <div class="text-overline text-grey-6 q-mb-xs">Personalização</div>
                
                <div class="q-mb-md">
                  <div class="text-caption text-grey-8 q-mb-sm">Cor do Tema:</div>
                  <div class="row q-gutter-xs">
                    <q-btn round size="xs" color="blue-10" @click="changeTheme('#154ec1')" /> <q-btn round size="xs" color="grey-9" @click="changeTheme('#263238')" /> <q-btn round size="xs" color="red-9" @click="changeTheme('#c62828')" /> <q-btn round size="xs" color="teal-9" @click="changeTheme('#00695c')" /> <q-btn round size="xs" icon="colorize" flat class="text-grey-6">
                      <q-popup-proxy>
<q-color v-model="customColor" @update:model-value="(val) => val && changeTheme(val)" no-header no-footer default-view="palette" />                      </q-popup-proxy>
                    </q-btn>
                  </div>
                </div>

                <q-separator class="q-mb-md" />
                
                <q-list dense>
                  <q-item clickable v-close-popup to="/settings">
                    <q-item-section avatar style="min-width: 20px;"><q-icon name="settings" size="xs" /></q-item-section>
                    <q-item-section>Ajustes do Sistema</q-item-section>
                  </q-item>
                </q-list>
              </div>

              <q-separator vertical inset />

              <div class="column items-center justify-center q-ml-md" style="width: 100px;">
                <q-avatar size="64px" class="q-mb-sm shadow-2">
                    <img :src="getAvatarUrl(authStore.user?.avatar_url)" style="object-fit: cover;">
                </q-avatar>
                <q-btn outline color="primary" label="Sair" size="sm" class="full-width" v-close-popup @click="handleLogout" />
              </div>
            </div>
          </q-btn-dropdown>
        </div>
      </q-toolbar>
    </q-header>

    <q-page-container class="app-page-container bg-grey-1">
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
import { setCssVar } from 'quasar';
import { useAuthStore } from 'stores/auth-store';
import { useNotificationStore } from 'stores/notification-store';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import defaultAvatar from 'assets/default-avatar.png';

const leftDrawerOpen = ref(false);
const customColor = ref('#154ec1'); // Cor Inicial (Azul Vemag)
const router = useRouter();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();

// --- Lógica de Tema ---
function changeTheme(color: string) {
  customColor.value = color;
  setCssVar('primary', color);
  // Ajusta cor secundária para uma variação mais clara
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

// --- Definição do Menu Industrial (Vemag) ---
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

  // 1. Visão Geral
  menu.push({
    label: 'Visão Geral', 
    children: [
      { title: 'Dashboard da Planta', icon: 'analytics', to: '/dashboard' },
      { title: 'Equipe Técnica', icon: 'groups', to: '/employees' }, 
    ]
  });

  // 2. Gestão de Ativos
  menu.push({ 
      label: 'Ativos & Recursos', 
      children: [
        { title: 'Máquinas Industriais', icon: 'precision_manufacturing', to: '/vehicles' },
        { title: 'Almoxarifado (Peças)', icon: 'inventory_2', to: '/parts' },
        { title: 'Ferramental', icon: 'handyman', to: '/implements' }
      ] 
  });

  // 3. Manutenção e Ordens
  menu.push({
      label: 'PCP & Manutenção', 
      children: [
          { title: 'Ordens de Manutenção', icon: 'engineering', to: '/maintenance' },
          { title: 'Roteiros de Produção', icon: 'fact_check', to: '/journeys' },
      ]
  });

  // 4. Gestão
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
  // Define cor inicial padrão (Vemag Blue)
  setCssVar('primary', '#154ec1');
  
  if (authStore.isManager) {
    void notificationStore.fetchUnreadCount();
  }
});
</script>

<style lang="scss" scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.font-inter {
  font-family: 'Inter', sans-serif;
}

/* Background suave */
.bg-surface { background-color: #ffffff; }
.bg-grey-1 { background-color: #f8fafc; }

/* Dark Mode Automático para componentes */
.body--dark {
  .bg-surface { background-color: #1e293b; border-color: #334155; }
  .text-primary-text { color: #f1f5f9; }
  .logo-light { display: none; }
  .logo-dark { display: block !important; }
  .bg-grey-1 { background-color: #0f172a; }
  
  .navigation-item {
    color: #94a3b8;
    &:hover { background-color: rgba(255,255,255,0.05); color: #f1f5f9; }
  }
  .active-item { background-color: rgba(var(--q-primary), 0.2); color: var(--q-primary); }
}

/* Sidebar Styling */
.navigation-item {
  color: #475569;
  border-radius: 8px;
  transition: all 0.2s ease;
  
  &:hover {
    background-color: #f1f5f9;
    color: #1e293b;
  }
}

.active-item {
  background-color: #eff6ff; /* Azul bem claro */
  color: var(--q-primary);
  font-weight: 600;
  
  .q-icon {
    color: var(--q-primary);
  }
}

/* Header Styling */
.header-blur {
  backdrop-filter: blur(10px);
  background-color: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid #e2e8f0;
}

.border-primary {
  border: 2px solid var(--q-primary);
}

/* Transições */
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
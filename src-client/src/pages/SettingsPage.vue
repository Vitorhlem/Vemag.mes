<template>
  <q-page padding class="bg-grey-1">
    <div class="row items-center justify-between q-mb-lg">
      <div>
        <h1 class="text-h4 text-weight-bold text-primary q-my-none">Configurações</h1>
        <div class="text-caption text-grey-7">Gerencie suas preferências, segurança e integrações industriais.</div>
      </div>
    </div>

    <div class="row q-col-gutter-lg">
      <div class="col-12 col-md-3">
        <q-card flat bordered class="rounded-borders bg-white">
          <q-list separator class="text-grey-8">
            <q-item
              v-for="tab in visibleTabs"
              :key="tab.name"
              clickable
              v-ripple
              :active="currentTab === tab.name"
              @click="currentTab = tab.name"
              active-class="bg-primary text-white"
              class="q-py-md transition-generic"
            >
              <q-item-section avatar>
                <q-icon :name="tab.icon" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">{{ tab.label }}</q-item-label>
                <q-item-label caption :class="currentTab === tab.name ? 'text-blue-2' : 'text-grey-6'">
                  {{ tab.caption }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card>
      </div>

      <div class="col-12 col-md-9">
        <q-card flat bordered class="fit bg-white">
          <q-tab-panels v-model="currentTab" animated transition-prev="fade" transition-next="fade">
            
            <q-tab-panel name="account" class="q-pa-lg">
              <div class="text-h6 q-mb-xs">Meu Perfil</div>
              <p class="text-grey-6 q-mb-lg">Gerencie suas informações de acesso.</p>
              
              <div class="row q-col-gutter-xl">
                <div class="col-12 col-md-5 text-center">
                  <div class="relative-position inline-block">
                    <q-avatar size="120px" class="shadow-3">
                      <img :src="getAvatarUrl(authStore.user?.avatar_url)">
                    </q-avatar>
                    
                    <input 
                      type="file" 
                      ref="fileInput" 
                      accept="image/*" 
                      style="display: none" 
                      @change="handleFileUpload"
                    />
                    
                    <q-btn 
                      round 
                      color="primary" 
                      icon="edit" 
                      size="sm" 
                      class="absolute-bottom-right" 
                      style="bottom: 5px; right: 5px"
                      @click="triggerFileInput"
                      :loading="isUploading"
                    >
                      <q-tooltip>Alterar Foto</q-tooltip>
                    </q-btn>
                  </div>
                  <div class="q-mt-md text-h6">{{ authStore.user?.full_name }}</div>
                  <div class="text-grey-6">{{ authStore.user?.role }}</div>
                  <div class="text-caption text-grey-5 q-mt-xs" v-if="authStore.user?.employee_id">
                    Matrícula: {{ authStore.user?.employee_id }}
                  </div>
                </div>

                <div class="col-12 col-md-7">
                  <q-form @submit.prevent="handleUpdateProfile" class="q-gutter-y-md">
                    <q-input outlined v-model="profileForm.full_name" label="Nome Completo" dense />
                    <q-input outlined v-model="profileForm.email" label="E-mail" dense disable hint="Para alterar o e-mail, contate o administrador do sistema." />
                    <q-input outlined v-model="profileForm.phone" label="Telefone / Ramal" mask="(##) #####-####" dense />
                    
                    <div class="row justify-end">
                      <q-btn type="submit" label="Salvar Alterações" color="primary" unelevated :loading="isUpdatingProfile" />
                    </div>
                  </q-form>
                </div>
              </div>

              <q-separator class="q-my-xl" />

              <div class="text-h6 q-mb-md text-negative">Segurança</div>
              <q-form @submit.prevent="handleChangePassword" class="row q-col-gutter-md items-start" style="max-width: 800px">
                <div class="col-12 col-md-4">
                  <q-input 
                    outlined 
                    v-model="passwordForm.current_password" 
                    type="password" 
                    label="Senha Atual" 
                    dense 
                    :rules="[val => !!val || 'Obrigatório']"
                  />
                </div>
                <div class="col-12 col-md-4">
                  <q-input 
                    outlined 
                    v-model="passwordForm.new_password" 
                    type="password" 
                    label="Nova Senha" 
                    dense 
                    :rules="[val => !!val || 'Obrigatório', val => val.length >= 6 || 'Mínimo 6 caracteres']"
                  />
                </div>
                <div class="col-12 col-md-4">
                  <q-input 
                    outlined 
                    v-model="passwordForm.confirm_password" 
                    type="password" 
                    label="Confirmar" 
                    dense 
                    :rules="[
                      val => !!val || 'Obrigatório',
                      val => val === passwordForm.new_password || 'As senhas não conferem'
                    ]"
                  />
                </div>
                <div class="col-12 text-right">
                  <q-btn type="submit" label="Atualizar Senha" outline color="negative" :loading="isSubmittingPassword" />
                </div>
              </q-form>
            </q-tab-panel>

            <q-tab-panel name="interface" class="q-pa-lg">
              <div class="text-h6 q-mb-xs">Interface do Operador</div>
              <p class="text-grey-6 q-mb-lg">Personalize a visualização para o ambiente de fábrica.</p>

              <div class="row q-col-gutter-md">
                <div class="col-12">
                  <q-list bordered class="rounded-borders">
                    <q-item>
                      <q-item-section avatar>
                        <q-icon name="dark_mode" color="grey-7" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>Modo Escuro (Chão de Fábrica)</q-item-label>
                        <q-item-label caption>Recomendado para ambientes com pouca luz ou cabines de máquinas.</q-item-label>
                      </q-item-section>
                      <q-item-section side>
                        <q-btn-toggle
                          v-model="settingsStore.darkMode"
                          @update:model-value="updateDarkMode"
                          push unelevated toggle-color="primary"
                          :options="[
                            {icon: 'light_mode', value: false},
                            {icon: 'brightness_auto', value: 'auto'},
                            {icon: 'dark_mode', value: true}
                          ]"
                        />
                      </q-item-section>
                    </q-item>
                  </q-list>
                </div>
              </div>
            </q-tab-panel>
            
            <q-tab-panel name="integrations" class="q-pa-lg" v-if="authStore.isManager">
              <div class="text-h6 q-mb-xs">Integrações ERP & IoT</div>
              <p class="text-grey-6 q-mb-lg">Conecte o TruMachine aos seus sistemas corporativos.</p>

              <q-card flat bordered class="bg-blue-grey-1 q-mb-md">
                <q-card-section>
                  <div class="row items-center">
                    <q-avatar rounded color="white" text-color="primary" icon="dns" size="lg" />
                    <div class="q-ml-md col">
                      <div class="text-subtitle1 text-weight-bold">SAP Business One (Service Layer)</div>
                      <div class="text-caption text-grey-8">
                        Sincronização bidirecional de Máquinas (Assets) e Operadores (Employees).
                        <br>
                        <span class="text-weight-medium">Status:</span> {{ lastSyncStatus || 'Aguardando sincronização' }}
                      </div>
                    </div>
                    <div>
                      <q-btn 
                        label="Sincronizar Agora" 
                        color="primary" 
                        icon="sync" 
                        :loading="isSyncingSap"
                        @click="triggerSapSync"
                      >
                        <template v-slot:loading>
                          <q-spinner-hourglass class="on-left" />
                          Processando...
                        </template>
                      </q-btn>
                    </div>
                  </div>
                </q-card-section>
              </q-card>

              <q-card flat bordered class="bg-grey-1 q-mb-md">
                <q-card-section>
                  <div class="row items-center">
                    <q-avatar rounded color="blue-10" text-color="white" font-size="20px">RM</q-avatar>
                    <div class="q-ml-md col">
                      <div class="text-subtitle1 text-weight-bold">RM TOTVS (Labore)</div>
                      <div class="text-caption text-grey-8">
                        Importação de Colaboradores via Banco de Dados (PFUNC).
                      </div>
                    </div>
                    <div>
                      <q-btn 
                        label="Sincronizar RM" 
                        color="blue-10" 
                        icon="sync" 
                        :loading="isSyncingRM"
                        @click="triggerRmSync"
                      />
                    </div>
                  </div>
                </q-card-section>
              </q-card>

              <q-card flat bordered class="q-mb-md opacity-8">
                <q-card-section>
                  <div class="row items-center">
                    <q-avatar rounded color="grey-3" text-color="grey-7" icon="hub" size="lg" />
                    <div class="q-ml-md col">
                      <div class="text-subtitle1 text-grey-8">Coletor IoT (OPC UA / MQTT)</div>
                      <div class="text-caption text-grey-6">Conexão direta com PLCs das máquinas. Em breve.</div>
                    </div>
                    <q-chip label="Em Breve" color="grey-4" text-color="grey-7" />
                  </div>
                </q-card-section>
              </q-card>

            </q-tab-panel>

          </q-tab-panels>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue';
import { useQuasar } from 'quasar';
import { useAuthStore } from 'stores/auth-store';
import { useSettingsStore } from 'stores/settings-store';
import { useUserStore } from 'stores/user-store';
import { api } from 'boot/axios';
import defaultAvatar from 'assets/AvatarDefault.png';

const $q = useQuasar();
const authStore = useAuthStore();
const settingsStore = useSettingsStore();
const userStore = useUserStore();

const currentTab = ref('account');

// --- UTILITÁRIOS ---
function getAvatarUrl(url: string | null | undefined): string {
  if (!url) return defaultAvatar;
  if (url.startsWith('http')) return url;
  // Ajuste para desenvolvimento local se necessário, ou produção
  const backendUrl = process.env.API_URL || 'http://127.0.0.1:8000'; 
  if (url.startsWith('/static') || url.startsWith('/')) {
    return `${backendUrl}${url}`;
  }
  return url;
}

// --- UPLOAD DE FOTO ---
const fileInput = ref<HTMLInputElement | null>(null);
const isUploading = ref(false);

function triggerFileInput() {
  fileInput.value?.click();
}

async function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const file = target.files[0];
    isUploading.value = true;
    try {
      const formData = new FormData();
      formData.append('file', file);
      const uploadRes = await api.post('/upload-photo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      const newAvatarUrl = uploadRes.data.file_url;
      await api.put('/users/me', { avatar_url: newAvatarUrl });
      
      // Atualiza localmente
      if (authStore.user) {
        authStore.user.avatar_url = newAvatarUrl;
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            const parsed = JSON.parse(storedUser);
            parsed.avatar_url = newAvatarUrl;
            localStorage.setItem('user', JSON.stringify(parsed));
        }
      }
      $q.notify({ type: 'positive', message: 'Foto atualizada!' });
    } catch (error) {
      console.error(error);
      $q.notify({ type: 'negative', message: 'Erro ao enviar foto.' });
    } finally {
      isUploading.value = false;
    }
  }
}

// --- PERFIL ---
const profileForm = reactive({
  full_name: authStore.user?.full_name || '',
  email: authStore.user?.email || '',
  phone: authStore.user?.phone || '',
});
const isUpdatingProfile = ref(false);

async function handleUpdateProfile() {
  isUpdatingProfile.value = true;
  try {
    if (authStore.user?.id) {
      await userStore.updateUser(authStore.user.id, { 
          full_name: profileForm.full_name,
          phone: profileForm.phone 
      });
      if (authStore.user) {
          authStore.user.full_name = profileForm.full_name;
      }
      $q.notify({ type: 'positive', message: 'Perfil atualizado!' });
    }
  } catch {
    $q.notify({ type: 'negative', message: 'Erro ao atualizar perfil.' });
  } finally {
    isUpdatingProfile.value = false;
  }
}

// --- SENHA ---
const passwordForm = ref({ current_password: '', new_password: '', confirm_password: '' });
const isSubmittingPassword = ref(false);

const isSyncingRM = ref(false);

async function triggerRmSync() {
  isSyncingRM.value = true;
  try {
    await api.post('/integrations/sync/rm');
    $q.notify({ type: 'positive', message: 'Sync RM iniciado!' });
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (e) {
    $q.notify({ type: 'negative', message: 'Erro ao chamar Sync RM' });
  } finally {
    isSyncingRM.value = false;
  }
}

async function handleChangePassword() {
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    $q.notify({ type: 'warning', message: 'Senhas não conferem.' });
    return;
  }
  isSubmittingPassword.value = true;
  try {
    await api.put('/users/me/password', {
      current_password: passwordForm.value.current_password,
      new_password: passwordForm.value.new_password,
    });
    $q.notify({ type: 'positive', message: 'Senha alterada com sucesso!' });
    passwordForm.value = { current_password: '', new_password: '', confirm_password: '' };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
    const msg = error.response?.data?.detail || 'Erro ao alterar senha.';
    $q.notify({ type: 'negative', message: msg });
  } finally {
    isSubmittingPassword.value = false;
  }
}

// --- INTERFACE ---
function updateDarkMode(val: boolean | 'auto') {
  settingsStore.setDarkMode(val);
}

// --- INTEGRAÇÃO SAP (NOVO CÓDIGO) ---
const isSyncingSap = ref(false);
const lastSyncStatus = ref('');

async function triggerSapSync() {
  isSyncingSap.value = true;
  lastSyncStatus.value = 'Iniciando conexão...';
  
  try {
    await api.post('/integrations/sync/sap');
    
    $q.notify({
      type: 'positive',
      message: 'Sincronização iniciada em segundo plano!',
      caption: 'As máquinas e operadores aparecerão em instantes.'
    });
    lastSyncStatus.value = 'Sincronização solicitada com sucesso.';
    
  } catch (error) {
    console.error('Erro no SAP Sync:', error);
    $q.notify({
      type: 'negative',
      message: 'Falha ao conectar com SAP Service Layer',
      caption: 'Verifique os logs do servidor.'
    });
    lastSyncStatus.value = 'Erro na última tentativa.';
  } finally {
    isSyncingSap.value = false;
  }
}

// --- TABS VISÍVEIS ---
const visibleTabs = computed(() => {
  const tabs = [
    { name: 'account', label: 'Minha Conta', caption: 'Perfil e Segurança', icon: 'person' },
    { name: 'interface', label: 'Interface', caption: 'Tema e Visualização', icon: 'tune' }
  ];
  if (authStore.isManager) {
    tabs.push(
      { name: 'integrations', label: 'Integrações', caption: 'SAP / ERP / IoT', icon: 'hub' }, 
    );
  }
  return tabs;
});
</script>

<style lang="scss" scoped>
.transition-generic {
  transition: all 0.3s ease;
}
.opacity-8 { opacity: 0.8; }
</style>
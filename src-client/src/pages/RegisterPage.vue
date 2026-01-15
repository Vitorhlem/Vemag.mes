<template>
  <q-page>
    <div class="row window-height">
      <div 
        ref="formPanel"
        class="col-12 col-md-6 flex flex-center form-panel"
        @mousemove="handleMouseMove"
        @mouseleave="handleMouseLeave"
      >
        <q-card ref="registerCard" flat class="register-card q-pa-md">
          <div class="card-shine"></div>
          
          <q-card-section class="text-center q-pb-none">
            <img 
              src="~assets/trucar-logo-white.png" 
              alt="VEMAG Logo" 
              class="animated-form-element"
              style="height: 40px; margin-bottom: 1rem; animation-delay: 0.1s;"
            >
            <div class="text-h5 text-weight-bold text-white animated-form-element" style="animation-delay: 0.2s;">
              Nova Planta Industrial
            </div>
            <div class="text-subtitle1 text-grey-5 animated-form-element" style="animation-delay: 0.3s;">
              Configure o ambiente da sua fábrica.
            </div>
          </q-card-section>
          
          <q-stepper
            v-model="step"
            ref="stepper"
            color="primary"
            animated
            flat
            dark
            header-nav
            class="q-mt-md transparent-stepper animated-form-element"
            style="animation-delay: 0.4s;"
          >
            <q-step
              :name="1"
              title="A Empresa"
              icon="factory"
              :done="step > 1"
            >
              <q-input 
                dark
                standout="bg-grey-10"
                v-model="formData.organization_name" 
                label="Nome da Indústria *" 
                :rules="[val => !!val || 'Campo obrigatório']"
                class="q-mb-md"
              >
                <template v-slot:prepend><q-icon name="business" /></template>
              </q-input>

              <q-select
                dark
                standout="bg-grey-10"
                v-model="formData.sector"
                :options="sectorOptions"
                label="Ramo de Atividade *"
                emit-value
                map-options
                :rules="[val => !!val || 'Selecione um setor']"
              >
                <template v-slot:prepend>
                  <q-icon :name="sectorIcon" />
                </template>
              </q-select>

              <q-stepper-navigation class="q-mt-lg">
                <q-btn @click="() => stepper?.next()" color="primary" label="Continuar" class="full-width" unelevated />
              </q-stepper-navigation>
            </q-step>

            <q-step
              :name="2"
              title="Administrador"
              icon="admin_panel_settings"
            >
              <q-input dark standout="bg-grey-10" v-model="formData.full_name" label="Nome do Gestor *" :rules="[val => !!val || 'Campo obrigatório']" class="q-mb-md">
                  <template v-slot:prepend><q-icon name="person" /></template>
              </q-input>
              <q-input dark standout="bg-grey-10" v-model="formData.email" type="email" label="E-mail Corporativo *" :rules="[val => !!val || 'Campo obrigatório']" class="q-mb-md">
                  <template v-slot:prepend><q-icon name="alternate_email" /></template>
              </q-input>
              <q-input dark standout="bg-grey-10" v-model="formData.password" type="password" label="Definir Senha *" :rules="[val => !!val || 'Campo obrigatório']">
                  <template v-slot:prepend><q-icon name="lock" /></template>
              </q-input>
              
              <q-stepper-navigation class="q-mt-lg row q-col-gutter-sm">
                <div class="col-6">
                    <q-btn flat @click="() => stepper?.previous()" color="primary" label="Voltar" class="full-width" />
                </div>
                  <div class="col-6">
                    <q-btn 
                      @click="onSubmit" 
                      :color="getButtonColor" 
                      class="full-width register-btn" 
                      unelevated 
                      :loading="isLoading"
                    >
                      <transition name="fade" mode="out-in">
                        <span v-if="!isLoading && registerStatus === 'idle'">Inicializar Sistema</span>
                        <q-icon v-else-if="!isLoading && registerStatus === 'success'" name="check" />
                        <q-icon v-else-if="!isLoading && registerStatus === 'error'" name="close" />
                      </transition>
                    </q-btn>
                  </div>
              </q-stepper-navigation>
            </q-step>
          </q-stepper>
          
            <div class="text-center q-mt-md animated-form-element" style="animation-delay: 0.5s;">
               <span>Empresa já cadastrada? <q-btn to="/auth/login" label="Acessar" flat no-caps dense class="text-primary text-weight-bold"/></span>
            </div>

            <q-separator dark class="q-my-lg animated-form-element" style="animation-delay: 0.6s;" />

            <div class="security-seals text-center animated-form-element" style="animation-delay: 0.7s;">
              <div class="seal-item">
                <q-icon name="cloud_done" color="positive" />
                <span>Cloud Native</span>
              </div>
              <div class="seal-item">
                <q-icon name="lock" color="positive" />
                <span>Indústria 4.0</span>
              </div>
              <div class="seal-item">
                <q-icon name="shield" color="positive" />
                <span>Enterprise</span>
              </div>
            </div>

        </q-card>
      </div>

      <div class="col-md-6 register-visual-container gt-sm">
        <div class="image-strip" :style="{ backgroundImage: `url(${visual1})` }"></div>
        <div class="image-strip" :style="{ backgroundImage: `url(${visual2})` }"></div>
        <div class="image-strip" :style="{ backgroundImage: `url(${visual3})` }"></div>
        <div class="image-strip" :style="{ backgroundImage: `url(${visual4})` }"></div>
        <div class="visual-content text-white">
            <h2 class="text-h2 text-weight-bolder">VEMAG</h2>
            <h5 class="text-h5 text-weight-light q-mb-xl">Gestão inteligente para o chão de fábrica.</h5>

            <q-list dark separator class="benefits-list">
              <q-item>
                <q-item-section avatar>
                  <q-icon color="white" name="settings_suggest" />
                </q-item-section>
                <q-item-section>Controle total de Ordens de Produção (O.P.).</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar>
                  <q-icon color="white" name="build_circle" />
                </q-item-section>
                <q-item-section>Gestão de Manutenção Corretiva e Preventiva.</q-item-section>
              </q-item>
              <q-item>
                <q-item-section avatar>
                  <q-icon color="white" name="insights" />
                </q-item-section>
                <q-item-section>Monitore OEE e eficiência em tempo real.</q-item-section>
              </q-item>
            </q-list>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, type ComponentPublicInstance } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar, QStepper } from 'quasar';
import { api } from 'boot/axios';
import axios from 'axios';
import type { UserRegister, UserSector } from 'src/models/auth-models';

// Assets visuais (mantenha os nomes, só mudamos o contexto do texto)
import visual1 from 'assets/register-visual-1.jpg';
import visual2 from 'assets/register-visual-2.jpg';
import visual3 from 'assets/register-visual-3.jpg';
import visual4 from 'assets/register-visual-4.jpg';

const formPanel = ref<HTMLElement | null>(null);
const registerCard = ref<ComponentPublicInstance | null>(null);
const router = useRouter();
const $q = useQuasar();
const isLoading = ref(false);
const registerStatus = ref<'idle' | 'success' | 'error'>('idle');

const step = ref(1);
const stepper = ref<QStepper | null>(null);

const formData = ref<UserRegister>({
  organization_name: '',
  sector: 'servicos', // Default já setado para o novo setor
  full_name: '',
  email: '',
  password: '',
});

const getButtonColor = computed(() => {
  if (registerStatus.value === 'success') return 'positive';
  if (registerStatus.value === 'error') return 'negative';
  return 'primary';
});

// AQUI ESTÁ A MUDANÇA PRINCIPAL:
// Apenas "Indústria Metalúrgica" aparece, mas o valor enviado é 'servicos'
// para compatibilidade com o Enum do Backend.
const sectorOptions: { label: string, value: UserSector }[] = [
  { label: 'Indústria Metalúrgica', value: 'servicos' }, 
];

const sectorIcon = computed(() => {
  return 'precision_manufacturing'; // Ícone fixo de indústria
});

async function onSubmit() {
  if (isLoading.value) return;
  isLoading.value = true;
  registerStatus.value = 'idle';

  try {
    await api.post('/login/register', formData.value);
    registerStatus.value = 'success';
    isLoading.value = false;
    
    $q.notify({
      type: 'positive',
      message: 'Ambiente industrial configurado! Redirecionando...',
    });
    
    setTimeout(() => {
    void router.push('/auth/login');
    }, 1200);

  } catch (error) {
    registerStatus.value = 'error'
    isLoading.value = false;
    let errorMessage = 'Erro ao criar conta. Tente novamente.';
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      errorMessage = error.response.data.detail as string;
    }
    $q.notify({ type: 'negative', message: errorMessage });
    setTimeout(() => {
      registerStatus.value = 'idle';
    }, 2500);
  }
}

function handleMouseMove(event: MouseEvent) {
  if (registerCard.value && registerCard.value.$el) {
    const cardEl = registerCard.value.$el as HTMLElement;
    const rect = cardEl.getBoundingClientRect();
    const shineX = event.clientX - rect.left;
    const shineY = event.clientY - rect.top;
    
    cardEl.style.setProperty('--shine-x', `${shineX}px`);
    cardEl.style.setProperty('--shine-y', `${shineY}px`);
    cardEl.style.setProperty('--shine-opacity', '1');
  }
}

function handleMouseLeave() {
  if (registerCard.value && registerCard.value.$el) {
    const cardEl = registerCard.value.$el as HTMLElement;
    cardEl.style.setProperty('--shine-opacity', '0');
  }
}
</script>

<style lang="scss" scoped>
.form-panel {
  background-color: #050a14;
}

.register-card {
  width: 500px;
  max-width: 90vw;
  background: rgba(18, 23, 38, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  position: relative;
  overflow: hidden;
}

.card-shine {
  position: absolute;
  top: var(--shine-y, 0);
  left: var(--shine-x, 0);
  transform: translate(-50%, -50%);
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0) 60%);
  opacity: var(--shine-opacity, 0);
  transition: opacity 0.3s ease-out;
  pointer-events: none;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.animated-form-element {
  opacity: 0;
  animation: fadeInUp 0.5s ease-out forwards;
}

.transparent-stepper {
  background-color: transparent !important;
}

:deep(.q-field--standout.q-field--focused .q-field__control) {
  box-shadow: 0 0 10px rgba(var(--q-color-primary-rgb), 0.5);
}
:deep(.q-field--standout .q-field__control) {
  transition: box-shadow 0.3s ease;
}

.register-btn {
  transition: background-color 0.3s ease;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

// Estilos para o painel visual direito
.register-visual-container {
  position: relative;
  display: flex;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.6); /* Mais escuro para contraste */
    z-index: 2;
    transition: background-color 0.4s ease;
  }

  &:hover::before {
    background-color: rgba(0, 0, 0, 0.7);
  }
}

.image-strip {
  flex: 1;
  height: 100%;
  background-size: cover;
  background-position: center;
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  filter: grayscale(60%);
}

.register-visual-container:hover .image-strip {
  filter: grayscale(100%);
}

.image-strip:hover {
  flex: 2;
  filter: grayscale(0%);
}

.visual-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  max-width: 500px;
  z-index: 3;
  text-align: center;
}

.benefits-list {
  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(5px);
  border-radius: 8px;
  margin-top: 3rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.security-seals {
  display: flex;
  justify-content: space-around;
  color: #21BA45; /* $positive no SCSS do Quasar */
  font-size: 0.8rem;
  font-weight: 500;
  opacity: 0.9;
  padding: 0 1rem;
}
.seal-item {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
</style>
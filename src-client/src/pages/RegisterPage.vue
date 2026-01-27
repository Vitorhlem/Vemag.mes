<template>
  <div class="industrial-register-container">
    
    <div class="technical-grid"></div>

    <div class="row full-width full-height relative-position z-top">
      
      <div 
        ref="formPanel"
        class="col-12 col-md-6 flex flex-center form-panel-industrial"
        @mousemove="handleMouseMove"
        @mouseleave="handleMouseLeave"
      >
        <q-card ref="registerCard" class="register-card shadow-24">
          <div class="card-shine"></div>
          <div class="safety-stripe"></div>
          
          <q-card-section class="text-center q-pt-lg">
            <div class="logo-container q-mb-md">
              <img src="/Logo-Oficial.png" class="login-logo" />
            </div>
            <div class="text-h5 text-weight-bolder text-white tracking-widest">
                NOVA PLANTA<span class="text-vemag-primary">.IND</span>
            </div>
            <div class="text-caption text-grey-5 text-uppercase q-mt-xs">
              Configuração do Ambiente Fabril
            </div>
          </q-card-section>
          
          <q-stepper
            v-model="step"
            ref="stepper"
            active-color="teal"
            done-color="teal-10"
            animated
            flat
            dark
            header-nav
            class="bg-transparent"
          >
            <q-step
              :name="1"
              title="A INDÚSTRIA"
              icon="factory"
              :done="step > 1"
              class="step-content"
            >
              <q-input 
                v-model="formData.organization_name" 
                label="Razão Social / Nome da Planta *" 
                dark outlined dense color="teal"
                class="industrial-input q-mb-md"
                :rules="[val => !!val || 'Obrigatório']"
              >
                <template v-slot:prepend><q-icon name="business" color="teal" /></template>
              </q-input>

              <q-select
                v-model="formData.sector"
                :options="sectorOptions"
                label="Segmento Industrial *"
                emit-value map-options
                dark outlined dense color="teal"
                class="industrial-input"
                :rules="[val => !!val || 'Obrigatório']"
                readonly
              >
                <template v-slot:prepend>
                  <q-icon name="precision_manufacturing" color="teal" />
                </template>
              </q-select>

              <q-stepper-navigation class="q-mt-lg">
                <q-btn @click="() => stepper?.next()" class="full-width industrial-btn bg-vemag-primary text-white" unelevated label="PRÓXIMO" />
              </q-stepper-navigation>
            </q-step>

            <q-step
              :name="2"
              title="GESTOR PCP"
              icon="admin_panel_settings"
              class="step-content"
            >
              <q-input 
                v-model="formData.full_name" 
                label="Nome do Responsável *" 
                dark outlined dense color="teal"
                class="industrial-input q-mb-md"
                :rules="[val => !!val || 'Obrigatório']"
              >
                  <template v-slot:prepend><q-icon name="person" color="teal" /></template>
              </q-input>
              
              <q-input 
                v-model="formData.email" 
                type="email" 
                label="E-mail Corporativo *" 
                dark outlined dense color="teal"
                class="industrial-input q-mb-md"
                :rules="[val => !!val || 'Obrigatório']"
              >
                  <template v-slot:prepend><q-icon name="alternate_email" color="teal" /></template>
              </q-input>
              
              <q-input 
                v-model="formData.password" 
                type="password" 
                label="Senha de Acesso *" 
                dark outlined dense color="teal"
                class="industrial-input"
                :rules="[val => !!val || 'Obrigatório']"
              >
                  <template v-slot:prepend><q-icon name="lock" color="teal" /></template>
              </q-input>
              
              <q-stepper-navigation class="q-mt-lg row q-col-gutter-md">
                <div class="col-6">
                    <q-btn flat @click="() => stepper?.previous()" color="grey-5" label="VOLTAR" class="full-width border-grey" />
                </div>
                  <div class="col-6">
                    <q-btn 
                      @click="onSubmit" 
                      :class="registerStatus === 'success' ? 'bg-positive text-white' : (registerStatus === 'error' ? 'bg-negative text-white' : 'bg-vemag-primary text-white')"
                      class="full-width industrial-btn" 
                      unelevated 
                      :loading="isLoading"
                    >
                      <span v-if="!isLoading && registerStatus === 'idle'">FINALIZAR</span>
                      <q-icon v-else-if="!isLoading && registerStatus === 'success'" name="check" />
                      <q-icon v-else-if="!isLoading && registerStatus === 'error'" name="close" />
                      <template v-slot:loading><q-spinner-gears class="on-left" /> Criando...</template>
                    </q-btn>
                  </div>
              </q-stepper-navigation>
            </q-step>
          </q-stepper>
          
            <div class="text-center q-mt-md">
               <span class="text-grey-5">Já possui planta ativa? 
                   <span class="text-vemag-primary cursor-pointer text-weight-bold hover-underline" @click="goToLogin">
                       ACESSAR PAINEL
                   </span>
               </span>
            </div>

            <q-separator dark class="q-my-lg opacity-20" />

            <div class="security-seals text-center">
              <div class="seal-item">
                <q-icon name="cloud_done" color="positive" />
                <span>Cloud MES</span>
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

      <div class="col-md-6 gt-sm relative-position overflow-hidden flex flex-center bg-black">
        <div class="industrial-bg"></div>
        <div class="bg-overlay"></div>
        
        <div class="visual-content text-white text-center q-pa-xl">
            <h2 class="text-h2 text-weight-bolder tracking-widest q-mb-sm">VEMAG<span class="text-vemag-primary">.MES</span></h2>
            <h5 class="text-h5 text-weight-light text-grey-4 q-mb-xl">Otimização e Controle Total do Chão de Fábrica.</h5>

            <div class="features-grid">
                 <div class="feature-item">
                     <q-icon name="settings_suggest" size="md" color="teal" />
                     <div class="text-subtitle1 text-weight-bold q-mt-sm">Controle de O.P.</div>
                     <div class="text-caption text-grey-5">Rastreamento em tempo real de cada ordem.</div>
                 </div>
                 <div class="feature-item">
                     <q-icon name="build_circle" size="md" color="teal" />
                     <div class="text-subtitle1 text-weight-bold q-mt-sm">Manutenção</div>
                     <div class="text-caption text-grey-5">Gestão preventiva e corretiva integrada.</div>
                 </div>
                 <div class="feature-item">
                     <q-icon name="insights" size="md" color="teal" />
                     <div class="text-subtitle1 text-weight-bold q-mt-sm">OEE & KPIs</div>
                     <div class="text-caption text-grey-5">Métricas de eficiência instantâneas.</div>
                 </div>
            </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, type ComponentPublicInstance } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar, QStepper } from 'quasar';
import { api } from 'boot/axios';
import axios from 'axios';
import type { UserRegister, UserSector } from 'src/models/auth-models';

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
  sector: 'servicos', // Mantém 'servicos' para compatibilidade com backend
  full_name: '',
  email: '',
  password: '',
});

// Opção Única Fixa
const sectorOptions: { label: string, value: UserSector }[] = [
  { label: 'Indústria Metalúrgica / Manufatura', value: 'servicos' }, 
];

async function onSubmit() {
  if (isLoading.value) return;
  isLoading.value = true;
  registerStatus.value = 'idle';

  try {
    await api.post('/login/register', formData.value);
    registerStatus.value = 'success';
    
    $q.notify({
      type: 'positive',
      message: 'Planta registrada com sucesso! Redirecionando...',
      timeout: 1500
    });
    
    setTimeout(() => {
        void router.push('/auth/login');
    }, 1500);

  } catch (error) {
    registerStatus.value = 'error';
    let errorMessage = 'Erro ao criar conta.';
    if (axios.isAxiosError(error) && error.response?.data?.detail) {
      errorMessage = error.response.data.detail as string;
    }
    $q.notify({ type: 'negative', message: errorMessage });
    setTimeout(() => { registerStatus.value = 'idle'; }, 2500);
  } finally {
      isLoading.value = false;
  }
}

function goToLogin() {
    void router.push('/auth/login');
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

<style scoped>
/* --- CORES VEMAG --- */
.text-vemag-primary { color: #008478 !important; }
.bg-vemag-primary { background-color: #008478 !important; }
.bg-vemag-dark { background-color: #003D38 !important; }
.bg-vemag-muted { background-color: #00665E !important; }

/* --- ESTRUTURA GERAL --- */
.industrial-register-container {
    width: 100vw;
    height: 100vh;
    background-color: #121212;
    overflow: hidden;
    position: relative;
}

.technical-grid {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background-image: 
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    z-index: 0;
}

/* --- CARD DE REGISTRO --- */
.register-card {
    width: 500px;
    max-width: 90vw;
    background: rgba(30, 30, 30, 0.85);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px; /* Cantos retos = industrial */
    position: relative;
    overflow: hidden;
}

.safety-stripe {
    height: 4px;
    /* Alterado de amarelo/laranja para #008478 */
    background: repeating-linear-gradient(45deg, #008478, #008478 10px, #000 10px, #000 20px);
    width: 100%;
}

.card-shine {
    position: absolute;
    top: var(--shine-y, 0); left: var(--shine-x, 0);
    transform: translate(-50%, -50%);
    width: 400px; height: 400px;
    /* Alterado de laranja para #008478 */
    background: radial-gradient(circle, rgba(0, 132, 120, 0.15) 0%, rgba(0, 132, 120, 0) 60%);
    opacity: var(--shine-opacity, 0);
    transition: opacity 0.3s ease-out;
    pointer-events: none;
    z-index: 1;
}

.login-logo {
    height: 50px;
    filter: brightness(0) invert(1);
    opacity: 0.9;
}

.tracking-widest { letter-spacing: 3px; }

/* INPUTS */
.industrial-input :deep(.q-field__control) {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.industrial-input :deep(.q-field__label) {
    font-family: monospace;
    text-transform: uppercase;
    font-size: 11px;
}

/* BOTÕES */
.industrial-btn {
    border-radius: 2px;
    border: 1px solid #008478; /* VEMAG Primary */
    font-weight: bold;
    letter-spacing: 1px;
    transition: all 0.3s ease;
}
.industrial-btn:hover {
    background-color: #00665E !important; /* VEMAG Muted */
    box-shadow: 0 0 15px rgba(0, 132, 120, 0.4);
}
.border-grey {
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 2px;
}

.hover-underline:hover { text-decoration: underline; }

/* --- LADO DIREITO (VISUAL) --- */
.industrial-bg {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background-image: url('~assets/register-visual-1.jpg'); 
    background-size: cover;
    background-position: center;
    filter: grayscale(100%);
    opacity: 0.4;
}

.bg-overlay {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at center, transparent 0%, #000 90%);
}

.visual-content {
    z-index: 2;
    position: relative;
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-top: 40px;
}

.feature-item {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 20px;
    border-radius: 4px;
    transition: transform 0.3s;
}
.feature-item:hover {
    transform: translateY(-5px);
    border-color: #008478; /* VEMAG Primary */
}

/* SELOS */
.security-seals {
    display: flex;
    justify-content: space-around;
    color: #21BA45;
    font-size: 0.75rem;
    font-family: monospace;
    opacity: 0.8;
    padding: 0 1rem;
}
.seal-item {
    display: flex;
    align-items: center;
    gap: 6px;
}
.opacity-20 { opacity: 0.2; }
</style>
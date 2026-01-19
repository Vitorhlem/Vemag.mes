<template>
  <div 
    class="industrial-login-container" 
    @mousemove="handleMouseMove"
  >
    <div class="technical-grid"></div>

    <div class="scanner-bar"></div>

    <div 
        class="axis-y" 
        :style="{ transform: `translateX(${mouseX}px)` }"
    >
        <div class="axis-label top">X: {{ mouseX.toFixed(1) }}</div>
    </div>

    <div 
        class="axis-x" 
        :style="{ transform: `translateY(${mouseY}px)` }"
    >
        <div class="axis-label left">Y: {{ mouseY.toFixed(1) }}</div>
    </div>

    <div 
        class="machine-head" 
        :style="{ transform: `translate(${mouseX}px, ${mouseY}px)` }"
    >
        <div class="head-spinner"></div>
        <div class="head-glow"></div>
    </div>

    <div class="login-content relative-position z-top">
      
      <q-card class="login-card shadow-24">
        <div class="safety-stripe"></div>

        <q-card-section class="text-center q-pt-lg">
          <div class="logo-container q-mb-md">
            <img src="/Logo-Oficial.png" class="login-logo" />
          </div>
          <div class="text-h5 text-weight-bolder text-white tracking-widest">
            VEMAG<span class="text-orange-5">.MES</span>
          </div>
          <div class="text-caption text-grey-5 text-uppercase q-mt-xs">
            Acesso ao Chão de Fábrica
          </div>
        </q-card-section>

        <q-card-section class="q-px-lg">
          <q-form @submit.prevent="handleLogin" class="q-gutter-md">
            
            <q-input
              v-model="email"
              label="Identificação / Email"
              dark
              outlined
              dense
              color="orange-5"
              class="industrial-input"
              :disable="isLoading"
            >
              <template v-slot:prepend>
                <q-icon name="badge" color="orange-5" />
              </template>
            </q-input>

            <q-input
              v-model="password"
              label="Senha de Acesso"
              type="password"
              dark
              outlined
              dense
              color="orange-5"
              class="industrial-input"
              :disable="isLoading"
            >
              <template v-slot:prepend>
                <q-icon name="lock" color="orange-5" />
              </template>
            </q-input>

            <div class="row justify-between items-center q-mt-sm">
                <q-checkbox v-model="remember" label="Manter conectado" dark dense color="grey-6" size="sm" />
                
                <div 
                    class="text-grey-5 text-caption cursor-pointer link-hover" 
                    @click="goToForgotPassword"
                >
                    Esqueceu a senha?
                </div>
            </div>

            <q-btn
              type="submit"
              color="orange-9"
              text-color="white"
              label="INICIAR SISTEMA"
              class="full-width q-mt-lg text-weight-bold tracking-widest industrial-btn"
              :loading="isLoading"
              unelevated
            >
                <template v-slot:loading>
                    <q-spinner-gears class="on-left" /> Validando...
                </template>
            </q-btn>

            <div class="text-center q-mt-md">
                <q-btn 
                    flat 
                    dense
                    no-caps
                    size="sm"
                    color="orange-5" 
                    label="Não tem acesso? Solicite aqui (Registrar)" 
                    class="opacity-80"
                    @click="goToRegister"
                />
            </div>

          </q-form>
        </q-card-section>

        <q-card-section class="text-center q-pb-lg">
            <div class="status-indicator row items-center justify-center q-gutter-x-sm">
                <div class="led-light"></div>
                <span class="text-caption text-grey-6">SISTEMA ONLINE • V.2.0</span>
            </div>
        </q-card-section>
      </q-card>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from 'stores/auth-store';
import { useQuasar } from 'quasar';

const router = useRouter();
const authStore = useAuthStore();
const $q = useQuasar();

const email = ref('');
const password = ref('');
const remember = ref(false);
const isLoading = ref(false);

const mouseX = ref(0);
const mouseY = ref(0);

function handleMouseMove(event: MouseEvent) {
    mouseX.value = event.clientX;
    mouseY.value = event.clientY;
}

function goToForgotPassword() {
    void router.push('/auth/forgot-password');
}

function goToRegister() {
    void router.push('/auth/register');
}

async function handleLogin() {
  if (!email.value || !password.value) {
    $q.notify({ type: 'warning', message: 'Preencha todos os campos.' });
    return;
  }

  isLoading.value = true;

  try {
  
      await authStore.login({ email: email.value, password: password.value });

      if (authStore.user?.role === 'admin') {
          void router.push('/admin');
      } else if (authStore.user?.role === 'driver') {
          void router.push('/factory/kiosk-select');
      } else {
          void router.push('/dashboard');
      }
      
      $q.notify({ type: 'positive', message: 'Bem-vindo ao Vemag MES!' });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } catch (error: any) {
      console.error(error);
      let msg = 'Falha no login. Verifique suas credenciais.';
      
      if (error.response && error.response.status === 401) {
          msg = 'Email ou senha incorretos.';
      } else if (error.message) {
          msg = error.message;
      }
      
      $q.notify({ type: 'negative', message: msg });
  } finally {
      isLoading.value = false;
  }
}

onMounted(() => {
    if (typeof window !== 'undefined') {
        mouseX.value = window.innerWidth / 2;
        mouseY.value = window.innerHeight / 2;
    }
});
</script>

<style scoped>
/* --- CONTAINER E FUNDO --- */
.industrial-login-container {
    width: 100vw;
    height: 100vh;
    background-color: #121212;
    overflow: hidden;
    position: relative;
    cursor: crosshair;
    display: flex;
    align-items: center;
    justify-content: center;
}

.technical-grid {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    z-index: 0;
}

/* --- NOVO: SCANNER BAR (ANIMAÇÃO CONTÍNUA) --- */
.scanner-bar {
    position: absolute;
    top: -20%;
    left: 0;
    width: 100%;
    height: 40px; /* Altura do gradiente */
    /* Gradiente laranja transparente que some nas bordas */
    background: linear-gradient(to bottom, transparent, rgba(255, 152, 0, 0.15) 50%, transparent);
    border-bottom: 2px solid rgba(255, 152, 0, 0.4); /* Linha mais forte embaixo */
    z-index: 1;
    pointer-events: none;
    animation: scan 6s linear infinite; /* Animação infinita de 6 segundos */
    box-shadow: 0 0 15px rgba(255, 152, 0, 0.2);
}

@keyframes scan {
    0% { top: -20%; opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { top: 120%; opacity: 0; }
}

/* --- EIXOS --- */
.axis-x, .axis-y {
    position: absolute;
    background-color: rgba(255, 152, 0, 0.3);
    pointer-events: none;
    z-index: 1;
    box-shadow: 0 0 10px rgba(255, 152, 0, 0.1);
}

.axis-x {
    top: 0;
    left: 0;
    width: 100%;
    height: 1px;
    border-bottom: 1px dashed rgba(255, 152, 0, 0.5);
}

.axis-y {
    top: 0;
    left: 0;
    width: 1px;
    height: 100%;
    border-right: 1px dashed rgba(255, 152, 0, 0.5);
}

.axis-label {
    position: absolute;
    background: #FF9800;
    color: #000;
    font-size: 10px;
    font-family: monospace;
    padding: 2px 4px;
    font-weight: bold;
}
.axis-label.top { top: 10px; left: 5px; }
.axis-label.left { left: 10px; top: -20px; }

.machine-head {
    position: absolute;
    top: 0; 
    left: 0;
    width: 0;
    height: 0;
    z-index: 2;
    pointer-events: none;
}

.head-spinner {
    position: absolute;
    top: -15px;
    left: -15px;
    width: 30px;
    height: 30px;
    border: 2px solid #FF9800;
    border-radius: 50%;
    border-top-color: transparent;
    animation: spin 1s linear infinite;
}

.head-glow {
    position: absolute;
    top: -4px;
    left: -4px;
    width: 8px;
    height: 8px;
    background-color: #FF9800;
    border-radius: 50%;
    box-shadow: 0 0 15px 5px rgba(255, 152, 0, 0.6);
}

/* --- CARD --- */
.login-content {
    z-index: 10;
    width: 100%;
    max-width: 400px;
    padding: 20px;
}

.login-card {
    background: rgba(30, 30, 30, 0.85);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    position: relative;
    overflow: hidden;
}

.safety-stripe {
    height: 4px;
    background: repeating-linear-gradient(
        45deg,
        #F2C037,
        #F2C037 10px,
        #000 10px,
        #000 20px
    );
    width: 100%;
}

.login-logo {
    height: 60px;
    filter: brightness(0) invert(1);
    opacity: 0.9;
}

.tracking-widest { letter-spacing: 3px; }

.industrial-input :deep(.q-field__control) {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.industrial-input :deep(.q-field__label) {
    font-family: monospace;
    text-transform: uppercase;
    font-size: 12px;
}

.industrial-btn {
    border-radius: 2px;
    border: 1px solid #FF9800;
    transition: all 0.3s ease;
}
.industrial-btn:hover {
    background-color: #F57C00 !important;
    box-shadow: 0 0 15px rgba(255, 152, 0, 0.4);
}

.link-hover:hover {
    color: #FF9800 !important;
    text-decoration: underline;
}

.led-light {
    width: 8px;
    height: 8px;
    background-color: #00E676;
    border-radius: 50%;
    box-shadow: 0 0 5px #00E676;
    animation: pulse-green 2s infinite;
}

.opacity-80 { opacity: 0.8; }

@keyframes spin { 100% { transform: rotate(360deg); } }
@keyframes pulse-green {
    0% { opacity: 0.5; }
    50% { opacity: 1; }
    100% { opacity: 0.5; }
}
</style>
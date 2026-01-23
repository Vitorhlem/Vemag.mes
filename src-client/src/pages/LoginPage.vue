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
            <img src="~assets/trucar-logo-white.png" class="login-logo" style="height: 70px;" />
          </div>
          <div class="text-h5 text-weight-bolder text-white tracking-widest font-mono">
            VEMAG<span class="text-primary">.MES</span>
          </div>
          <div class="text-caption text-teal-4 text-uppercase q-mt-xs text-weight-bold letter-spacing-1">
            Intelligent Manufacturing Access
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
              color="primary"
              class="industrial-input"
              :disable="isLoading"
            >
              <template v-slot:prepend>
                <q-icon name="badge" color="primary" />
              </template>
            </q-input>

            <q-input
              v-model="password"
              label="Senha de Acesso"
              type="password"
              dark
              outlined
              dense
              color="primary"
              class="industrial-input"
              :disable="isLoading"
            >
              <template v-slot:prepend>
                <q-icon name="lock" color="primary" />
              </template>
            </q-input>

            <div class="row justify-between items-center q-mt-sm">
                <q-checkbox v-model="remember" label="Manter conectado" dark dense color="teal-4" size="sm" class="text-grey-5" />
                
                <div 
                    class="text-teal-4 text-caption cursor-pointer link-hover" 
                    @click="goToForgotPassword"
                >
                    Esqueceu a senha?
                </div>
            </div>

            <q-btn
              type="submit"
              color="primary"
              text-color="white"
              label="INICIAR SISTEMA"
              class="full-width q-mt-lg text-weight-bold tracking-widest industrial-btn shadow-green"
              :loading="isLoading"
              unelevated
            >
                <template v-slot:loading>
                    <q-spinner-gears class="on-left" /> Validando Protocolos...
                </template>
            </q-btn>

            <div class="text-center q-mt-md">
                <q-btn 
                    flat 
                    dense
                    no-caps
                    size="sm"
                    color="teal-4" 
                    label="Não tem acesso? Solicite aqui (Registrar)" 
                    class="opacity-80 font-inter"
                    @click="goToRegister"
                />
            </div>

          </q-form>
        </q-card-section>

        <q-card-section class="text-center q-pb-lg">
            <div class="status-indicator row items-center justify-center q-gutter-x-sm">
                <div class="led-light"></div>
                <span class="text-caption text-teal-8 text-weight-medium font-mono">SISTEMA ONLINE • VEMAG V.2.0</span>
            </div>
        </q-card-section>
      </q-card>

    </div>
  </div>
</template>

<script setup lang="ts">
/* LÓGICA ORIGINAL MANTIDA INTEGRALMENTE */
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from 'stores/auth-store';
import { useQuasar, setCssVar } from 'quasar';

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
      
      $q.notify({ type: 'positive', message: 'Autenticação bem-sucedida. Bem-vindo à Trucar!' });

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
    setCssVar('primary', '#128c7e');
    if (typeof window !== 'undefined') {
        mouseX.value = window.innerWidth / 2;
        mouseY.value = window.innerHeight / 2;
    }
});
</script>

<style scoped lang="scss">
/* --- CONFIGURAÇÃO DE CORES TRUCAR --- */
$trucar-green: #128c7e;
$trucar-mint: #70c0b0;

/* --- CONTAINER E FUNDO --- */
.industrial-login-container {
    width: 100vw;
    height: 100vh;
    background-color: #060d0d; /* Fundo levemente esverdeado escuro */
    overflow: hidden;
    position: relative;
    cursor: crosshair;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Inter', sans-serif;
}

.technical-grid {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
        linear-gradient(rgba(18, 140, 126, 0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(18, 140, 126, 0.08) 1px, transparent 1px);
    background-size: 50px 50px;
    z-index: 0;
}

/* --- SCANNER BAR --- */
.scanner-bar {
    position: absolute;
    top: -20%;
    left: 0;
    width: 100%;
    height: 60px;
    background: linear-gradient(to bottom, transparent, rgba(112, 192, 176, 0.15) 50%, transparent);
    border-bottom: 2px solid #008f7266;
    z-index: 1;
    pointer-events: none;
    animation: scan 8s linear infinite;
    box-shadow: 0 5px 20px rgba(18, 140, 126, 0.1);
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
    background-color: rgba(112, 192, 176, 0.25);
    pointer-events: none;
    z-index: 1;
}

.axis-x {
    top: 0; left: 0; width: 100%; height: 1px;
    border-bottom: 1px dashed rgba(18, 140, 126, 0.4);
}

.axis-y {
    top: 0; left: 0; width: 1px; height: 100%;
    border-right: 1px dashed rgba(18, 140, 126, 0.4);
}

.axis-label {
    position: absolute;
    background: $trucar-green;
    color: #fff;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 6px;
    font-weight: bold;
    border-radius: 2px;
}
.axis-label.top { top: 15px; left: 5px; }
.axis-label.left { left: 15px; top: -25px; }

.machine-head {
    position: absolute;
    top: 0; left: 0; width: 0; height: 0;
    z-index: 2;
    pointer-events: none;
}

.head-spinner {
    position: absolute;
    top: -20px; left: -20px; width: 40px; height: 40px;
    border: 1px solid $trucar-mint;
    border-radius: 50%;
    border-top-color: transparent;
    animation: spin 2s linear infinite;
}

.head-glow {
    position: absolute;
    top: -5px; left: -5px; width: 10px; height: 10px;
    background-color: $trucar-mint;
    border-radius: 50%;
    box-shadow: 0 0 20px 8px rgba(112, 192, 176, 0.6);
}

/* --- CARD GLASS --- */
.login-content {
    z-index: 10;
    width: 100%;
    max-width: 420px;
    padding: 20px;
}

.login-card {
    background: rgba(10, 26, 26, 0.7); /* Vidro Escuro */
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    border: 1px solid rgba(112, 192, 176, 0.15);
    border-radius: 12px;
    position: relative;
    overflow: hidden;
}

.safety-stripe {
    height: 5px;
    background: repeating-linear-gradient(
        45deg,
        $trucar-green,
        $trucar-green 15px,
        #000 15px,
        #000 30px
    );
    width: 100%;
}

.tracking-widest { letter-spacing: 4px; }
.letter-spacing-1 { letter-spacing: 1px; }

.industrial-input :deep(.q-field__control) {
    background: rgba(0, 0, 0, 0.4);
    border-radius: 6px;
    transition: all 0.3s ease;
}

.industrial-input :deep(.q-field__label) {
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 1px;
}

.industrial-btn {
    border-radius: 6px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    height: 48px;
    background: linear-gradient(135deg, $trucar-green, $trucar-mint) !important;
}

.industrial-btn:hover {
    filter: brightness(1.1);
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(18, 140, 126, 0.3);
}

.link-hover:hover {
    color: #fff !important;
    text-decoration: underline;
    text-shadow: 0 0 8px rgba(112, 192, 176, 0.8);
}

.led-light {
    width: 10px; height: 10px;
    background-color: #00ff88;
    border-radius: 50%;
    box-shadow: 0 0 10px #00ff88;
    animation: pulse-green 2s infinite;
}

.shadow-green { box-shadow: 0 4px 15px rgba(18, 140, 126, 0.2); }
.font-mono { font-family: 'JetBrains Mono', monospace; }

@keyframes spin { 100% { transform: rotate(360deg); } }
@keyframes pulse-green {
    0%, 100% { opacity: 0.4; transform: scale(0.9); }
    50% { opacity: 1; transform: scale(1.1); }
}

.animate-fade { animation: fadeIn 1s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
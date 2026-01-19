<template>
  <div 
    class="industrial-forgot-container" 
    @mousemove="handleMouseMove"
  >
    <div class="technical-grid"></div>

    <div class="axis-y" :style="{ transform: `translateX(${mouseX}px)` }">
        <div class="axis-label top">X: {{ mouseX.toFixed(1) }}</div>
    </div>
    <div class="axis-x" :style="{ transform: `translateY(${mouseY}px)` }">
        <div class="axis-label left">Y: {{ mouseY.toFixed(1) }}</div>
    </div>
    <div class="machine-head" :style="{ transform: `translate(${mouseX}px, ${mouseY}px)` }">
        <div class="head-spinner"></div>
        <div class="head-glow"></div>
    </div>

    <div class="forgot-content relative-position z-top">
      
      <q-card class="forgot-card shadow-24">
        <div class="safety-stripe"></div>

        <q-card-section class="text-center q-pt-lg">
          <div class="logo-container q-mb-md">
            <img src="/Logo-Oficial.png" class="login-logo" />
          </div>
          <div class="text-h5 text-weight-bolder text-white tracking-widest">
            VEMAG<span class="text-orange-5">.MES</span>
          </div>
          <div class="text-caption text-grey-5 text-uppercase q-mt-xs">
            Recuperação de Acesso
          </div>
        </q-card-section>

        <q-card-section class="q-px-lg">
          <q-form @submit.prevent="handleRecoveryRequest" class="q-gutter-md">
            
            <div class="text-grey-4 q-mb-sm text-center">
              Insira seu e-mail corporativo para receber as instruções de reset.
            </div>

            <q-input
              v-model="email"
              label="E-mail Cadastrado"
              dark outlined dense color="orange-5"
              class="industrial-input"
              :rules="[val => !!val || 'Obrigatório', val => /.+@.+\..+/.test(val) || 'E-mail inválido']"
            >
              <template v-slot:prepend><q-icon name="alternate_email" color="orange-5" /></template>
            </q-input>

            <q-btn
              type="submit"
              color="orange-9"
              text-color="white"
              label="ENVIAR INSTRUÇÕES"
              class="full-width q-mt-lg text-weight-bold tracking-widest industrial-btn"
              :loading="isLoading"
              unelevated
            >
                <template v-slot:loading>
                    <q-spinner-gears class="on-left" /> Enviando...
                </template>
            </q-btn>

            <div class="text-center q-mt-md">
                <q-btn 
                    flat dense no-caps size="sm" color="grey-5" 
                    label="Lembrou da senha? Voltar ao Login" 
                    @click="goToLogin"
                />
            </div>

          </q-form>
        </q-card-section>
      </q-card>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAuthStore } from 'stores/auth-store';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';

const email = ref('');
const isLoading = ref(false);
const authStore = useAuthStore();
const router = useRouter();
const $q = useQuasar();

// Variáveis para a animação do mouse
const mouseX = ref(0);
const mouseY = ref(0);

function handleMouseMove(event: MouseEvent) {
    mouseX.value = event.clientX;
    mouseY.value = event.clientY;
}

function goToLogin() {
    void router.push('/auth/login');
}

onMounted(() => {
    if (typeof window !== 'undefined') {
        mouseX.value = window.innerWidth / 2;
        mouseY.value = window.innerHeight / 2;
    }
});

async function handleRecoveryRequest() {
  if (isLoading.value) return;
  isLoading.value = true;
  
  try {
    await authStore.requestPasswordReset({ email: email.value });
    
    $q.notify({ 
        type: 'positive', 
        message: 'Email enviado! Verifique sua caixa de entrada.',
        icon: 'mark_email_read'
    });

    setTimeout(() => {
      void router.push({ name: 'login' });
    }, 4000);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (error) {
      $q.notify({ type: 'negative', message: 'Erro ao solicitar reset. Verifique o email.' });
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
/* --- CONTAINER E FUNDO (Reutilizado para consistência) --- */
.industrial-forgot-container {
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
    top: 0; left: 0; width: 100%; height: 100%;
    background-image: 
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    z-index: 0;
}

/* --- EIXOS --- */
.axis-x, .axis-y {
    position: absolute;
    background-color: rgba(255, 152, 0, 0.3);
    pointer-events: none;
    z-index: 1;
    box-shadow: 0 0 10px rgba(255, 152, 0, 0.1);
}
.axis-x { top: 0; left: 0; width: 100%; height: 1px; border-bottom: 1px dashed rgba(255, 152, 0, 0.5); }
.axis-y { top: 0; left: 0; width: 1px; height: 100%; border-right: 1px dashed rgba(255, 152, 0, 0.5); }

.axis-label {
    position: absolute;
    background: #FF9800; color: #000;
    font-size: 10px; font-family: monospace;
    padding: 2px 4px; font-weight: bold;
}
.axis-label.top { top: 10px; left: 5px; }
.axis-label.left { left: 10px; top: -20px; }

/* --- CABEÇOTE --- */
.machine-head {
    position: absolute; top: 0; left: 0; width: 0; height: 0; z-index: 2; pointer-events: none;
}
.head-spinner {
    position: absolute; top: -15px; left: -15px; width: 30px; height: 30px;
    border: 2px solid #FF9800; border-radius: 50%; border-top-color: transparent;
    animation: spin 1s linear infinite;
}
.head-glow {
    position: absolute; top: -4px; left: -4px; width: 8px; height: 8px;
    background-color: #FF9800; border-radius: 50%;
    box-shadow: 0 0 15px 5px rgba(255, 152, 0, 0.6);
}

/* --- CARD --- */
.forgot-content { z-index: 10; width: 100%; max-width: 420px; padding: 20px; }

.forgot-card {
    background: rgba(30, 30, 30, 0.85);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    position: relative;
    overflow: hidden;
}

.safety-stripe {
    height: 4px;
    background: repeating-linear-gradient(45deg, #F2C037, #F2C037 10px, #000 10px, #000 20px);
    width: 100%;
}

.login-logo { height: 60px; filter: brightness(0) invert(1); opacity: 0.9; }
.tracking-widest { letter-spacing: 3px; }

.industrial-input :deep(.q-field__control) {
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.industrial-input :deep(.q-field__label) {
    font-family: monospace; text-transform: uppercase; font-size: 12px;
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

@keyframes spin { 100% { transform: rotate(360deg); } }
</style>
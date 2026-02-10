<template>
  <div 
    class="industrial-login-container" 
    @mousemove="handleMouseMove"
  >
    <div class="technical-grid"></div>
    <div class="scanner-bar"></div>
    
    <div class="axis-y" :style="{ transform: `translateX(${mouseX}px)` }">
        <div class="axis-label top">X: {{ mouseX.toFixed(0) }}</div>
    </div>
    <div class="axis-x" :style="{ transform: `translateY(${mouseY}px)` }">
        <div class="axis-label left">Y: {{ mouseY.toFixed(0) }}</div>
    </div>
    <div class="machine-head" :style="{ transform: `translate(${mouseX}px, ${mouseY}px)` }">
        <div class="head-spinner"></div>
        <div class="head-glow"></div>
    </div>

    <div class="login-content relative-position z-top">
      
      <q-card class="login-card shadow-24">
        <q-btn 
            icon="settings" 
            flat 
            round 
            dense 
            color="grey-7" 
            class="absolute-top-right q-ma-sm z-max" 
            @click="showConfig = true"
        />

        <div class="safety-stripe"></div>

        <q-card-section class="text-center q-pt-lg">
          <div class="logo-container q-mb-md">
            <q-icon name="factory" size="50px" color="teal" v-if="!hasLogo" />
            <img v-else src="/Logo-Oficial.png" class="login-logo" style="height: 70px;" @error="hasLogo=false" />
          </div>
          <div class="text-h5 text-weight-bolder text-white tracking-widest font-mono">
            VEMAG<span class="text-vemag-primary">.MES</span>
          </div>
          <div class="text-caption text-vemag-muted text-uppercase q-mt-xs text-weight-bold letter-spacing-1">
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
              color="teal"
              class="industrial-input"
              :disable="isLoading"
            >
              <template v-slot:prepend>
                <q-icon name="badge" class="text-vemag-primary" />
              </template>
            </q-input>

            <q-input
              v-model="password"
              label="Senha de Acesso"
              type="password"
              dark
              outlined
              dense
              color="teal"
              class="industrial-input"
              :disable="isLoading"
            >
              <template v-slot:prepend>
                <q-icon name="lock" class="text-vemag-primary" />
              </template>
            </q-input>

            <div class="row justify-between items-center q-mt-sm">
                <q-checkbox v-model="remember" label="Manter conectado" dark dense color="teal" size="sm" class="text-grey-5" />
                <div class="text-vemag-primary text-caption cursor-pointer link-hover">Esqueceu?</div>
            </div>

            <q-btn
              type="submit"
              class="full-width q-mt-lg text-weight-bold tracking-widest industrial-btn shadow-vemag"
              :loading="isLoading"
              unelevated
            >
                <span class="text-white">INICIAR SISTEMA</span>
                <template v-slot:loading>
                    <q-spinner-gears class="on-left" /> Conectando...
                </template>
            </q-btn>
            
            <div v-if="customIp" class="text-center q-mt-sm">
                <q-badge color="orange" label="MODO DEV" outline />
                <div class="text-caption text-grey-6 text-tiny q-mt-xs">{{ customIp }}</div>
            </div>

          </q-form>
        </q-card-section>

        <q-card-section class="text-center q-pb-lg">
            <div class="status-indicator row items-center justify-center q-gutter-x-sm">
                <div class="led-light"></div>
                <span class="text-caption text-vemag-dark text-weight-medium font-mono">SISTEMA ONLINE • V.2.0</span>
            </div>
        </q-card-section>
      </q-card>
    </div>

    <q-dialog v-model="showConfig" class="z-max" style="z-index: 99999 !important">
        <q-card class="bg-grey-10 text-white shadow-24" style="width: 350px; border: 1px solid #008478; max-width: 90vw;">
            <q-card-section class="row items-center q-pb-none">
                <div class="text-h6 text-vemag-primary">Configurações de DEV</div>
                <q-space />
                <q-btn icon="close" flat round dense v-close-popup />
            </q-card-section>

            <q-card-section class="q-gutter-y-md">
                <div class="text-caption text-grey">Ajuste a conexão do Tablet sem recompilar</div>

                <q-input 
                    v-model="tempIp" 
                    label="URL da API (ex: http://192.168.0.22:8000)" 
                    dark outlined dense color="teal" 
                />
                <q-btn label="Salvar IP" color="teal" class="full-width" size="sm" @click="salvarIp" />

                <q-separator dark spaced />

                <div class="text-subtitle2 text-orange">Teste de Notificação FCM</div>
                <q-btn 
                    label="Pedir Permissão / Gerar Token" 
                    icon="notifications_active"
                    color="purple" 
                    class="full-width" 
                    outline
                    @click="testarNotificacao" 
                />

                <div v-if="tokenGerado" class="bg-black q-pa-sm rounded-borders q-mt-sm">
                    <div class="text-caption text-grey" style="word-break: break-all; font-family: monospace; font-size: 10px;">
                        {{ tokenGerado }}
                    </div>
                    <q-btn flat size="xs" label="Copiar Token" color="teal" class="full-width q-mt-xs" @click="copiarToken" />
                </div>
            </q-card-section>
        </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from 'stores/auth-store';
import { useQuasar, setCssVar } from 'quasar';
import { api } from 'boot/axios';
import { PushNotifications } from '@capacitor/push-notifications';
import { Clipboard } from '@capacitor/clipboard';

const router = useRouter();
const authStore = useAuthStore();
const $q = useQuasar();

const email = ref('');
const password = ref('');
const remember = ref(false);
const isLoading = ref(false);
const hasLogo = ref(true);

// Mouse tracking vars
const mouseX = ref(0);
const mouseY = ref(0);

// Configs Vars
const showConfig = ref(false);
const customIp = ref('');
const tempIp = ref('');
const tokenGerado = ref('');

function handleMouseMove(event: MouseEvent) {
    mouseX.value = event.clientX;
    mouseY.value = event.clientY;
}

// --- Lógica de Configuração de IP ---
function carregarConfig() {
    const savedIp = localStorage.getItem('VEMAG_API_URL');
    if (savedIp) {
        customIp.value = savedIp;
        tempIp.value = savedIp;
        api.defaults.baseURL = savedIp + '/api/v1';
        console.log('API apontada para:', api.defaults.baseURL);
    }
}

function salvarIp() {
    if(!tempIp.value.startsWith('http')) {
        $q.notify({type: 'warning', message: 'Comece com http:// ou https://'});
        return;
    }
    localStorage.setItem('VEMAG_API_URL', tempIp.value);
    customIp.value = tempIp.value;
    api.defaults.baseURL = tempIp.value + '/api/v1';
    $q.notify({type: 'positive', message: 'IP Salvo! Tente logar agora.'});
    showConfig.value = false;
}

// --- Lógica de Notificação (Debug) ---
async function testarNotificacao() {
    try {
        const perm = await PushNotifications.requestPermissions();
        if (perm.receive === 'granted') {
            await PushNotifications.register();
            $q.notify({type: 'info', message: 'Registrando... aguarde o token'});
        } else {
            $q.notify({type: 'negative', message: 'Permissão negada!'});
        }
    } catch (e) {
        // CORREÇÃO 1: Converter 'e' para String explicitamente
        $q.notify({type: 'negative', message: 'Erro: ' + String(e)});
    }
}

async function copiarToken() {
    await Clipboard.write({ string: tokenGerado.value });
    $q.notify({type: 'positive', message: 'Token copiado!'});
}

// --- Login ---
async function handleLogin() {
  if (!email.value || !password.value) {
    $q.notify({ type: 'warning', message: 'Preencha todos os campos.' });
    return;
  }

  isLoading.value = true;

  try {
      await authStore.login({ email: email.value, password: password.value });

      const role = authStore.user?.role || 'user';
      if (role === 'admin') void router.push('/admin');
      else if (role === 'driver') void router.push('/factory/kiosk-select');
      else void router.push('/dashboard');
      
      $q.notify({ type: 'positive', message: 'Bem-vindo à VEMAG!' });
      
  } catch (err) {
      // CORREÇÃO 2: Tratar o erro como 'any' dentro do bloco, não na declaração
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const error = err as any;

      console.error(error);
      let msg = 'Erro de conexão. Verifique o IP nas configurações.';
      
      if (error.response && error.response.status === 401) {
          msg = 'Credenciais inválidas.';
      } else if (error.code === 'ERR_NETWORK') {
          msg = 'Não foi possível conectar ao servidor. Verifique o Wi-Fi e o IP.';
      }
      $q.notify({ type: 'negative', message: msg });
  } finally {
      isLoading.value = false;
  }
}

// CORREÇÃO 3: Tornar onMounted async para usar await nos listeners
onMounted(async () => {
    setCssVar('primary', '#008478');
    if (typeof window !== 'undefined') {
        mouseX.value = window.innerWidth / 2;
        mouseY.value = window.innerHeight / 2;
    }
    
    carregarConfig();

    // Listeners de Notificação com await (para satisfazer a regra de Promises)
    await PushNotifications.addListener('registration', token => {
        tokenGerado.value = token.value;
        if(showConfig.value) $q.notify({type: 'positive', message: 'Token Gerado!'});
    });

    await PushNotifications.addListener('registrationError', error => {
         if(showConfig.value) $q.notify({type: 'negative', message: 'Erro FCM: ' + JSON.stringify(error)});
    });
});
</script>

<style scoped lang="scss">
/* --- CORES VEMAG --- */
$vemag-dark: #003D38;
$vemag-primary: #008478;
$vemag-muted: #00665E;

.text-vemag-primary { color: $vemag-primary !important; }
.text-vemag-muted { color: $vemag-muted !important; }
.text-vemag-dark { color: #002925 !important; }

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
    font-family: 'Inter', sans-serif;
}

.technical-grid {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    background-image: 
        linear-gradient(rgba(0, 132, 120, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 132, 120, 0.05) 1px, transparent 1px);
    background-size: 50px 50px;
    z-index: 0;
}

.scanner-bar {
    position: absolute;
    top: -20%; left: 0; width: 100%; height: 60px;
    background: linear-gradient(to bottom, transparent, rgba(0, 132, 120, 0.15) 50%, transparent);
    border-bottom: 2px solid rgba(0, 132, 120, 0.3);
    z-index: 1;
    pointer-events: none;
    animation: scan 8s linear infinite;
}

@keyframes scan {
    0% { top: -20%; opacity: 0; }
    10% { opacity: 1; }
    100% { top: 120%; opacity: 0; }
}

.axis-x, .axis-y {
    position: absolute;
    background-color: rgba(0, 102, 94, 0.25);
    pointer-events: none;
    z-index: 1;
}
.axis-x { top: 0; left: 0; width: 100%; height: 1px; border-bottom: 1px dashed rgba(0, 132, 120, 0.3); }
.axis-y { top: 0; left: 0; width: 1px; height: 100%; border-right: 1px dashed rgba(0, 132, 120, 0.3); }

.axis-label {
    position: absolute;
    background: $vemag-primary;
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
    border: 1px solid $vemag-muted;
    border-radius: 50%;
    border-top-color: transparent;
    animation: spin 2s linear infinite;
}
.head-glow {
    position: absolute;
    top: -5px; left: -5px; width: 10px; height: 10px;
    background-color: $vemag-primary;
    border-radius: 50%;
    box-shadow: 0 0 20px 8px rgba(0, 132, 120, 0.4);
}

.login-content { z-index: 10; width: 100%; max-width: 420px; padding: 20px; }

.login-card {
    background: rgba(15, 20, 20, 0.85);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 132, 120, 0.2);
    border-radius: 12px;
    position: relative;
    overflow: hidden;
}

.safety-stripe {
    height: 5px;
    background: repeating-linear-gradient(45deg, $vemag-primary, $vemag-primary 15px, #000 15px, #000 30px);
    width: 100%;
}

.industrial-input :deep(.q-field__control) {
    background: rgba(0, 0, 0, 0.5);
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.industrial-btn {
    border-radius: 6px;
    height: 48px;
    background: linear-gradient(135deg, $vemag-primary, $vemag-muted) !important;
    transition: transform 0.2s;
}
.industrial-btn:active { transform: scale(0.98); }

.text-tiny { font-size: 10px; }
.z-max { z-index: 9999; }
.led-light {
    width: 8px; height: 8px;
    background-color: #00ff88;
    border-radius: 50%;
    box-shadow: 0 0 8px #00ff88;
    animation: pulse-green 2s infinite;
}

@keyframes spin { 100% { transform: rotate(360deg); } }
@keyframes pulse-green {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}
</style>
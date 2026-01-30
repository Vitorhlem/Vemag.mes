<template>
  <div class="col-12 col-md-4 column no-wrap full-height justify-between">
    
    <q-card class="col-auto bg-white text-center q-py-sm relative-position shadow-3" style="border-radius: 16px;">
       <div class="row items-center justify-center q-gutter-x-sm">
          <q-icon name="timer" class="vemag-text-secondary" size="24px" />
          <div class="text-subtitle1 vemag-text-primary text-uppercase font-weight-bold">
            Tempo no Estado
          </div>
       </div>
       <div class="text-h4 text-weight-bolder font-monospace q-my-xs text-dark">{{ elapsedTime }}</div>
       <q-linear-progress stripe query :class="statusTextClass" size="6px" class="q-mt-xs absolute-bottom" />
    </q-card>

    <div class="col relative-position q-mb-sm q-mt-sm">
       <q-btn 
          class="fit shadow-6 hover-scale-producing" 
          :class="getButtonClass" 
          push :loading="isLoadingAction"
          style="border-radius: 20px;"
          @click="$emit('main-action')"
       >
          <div class="column items-center justify-center full-height">
            <q-icon size="60px" :name="isPaused ? 'play_arrow' : (normalizedStatus === 'EM OPERAÇÃO' ? 'pause_circle' : 'play_circle_filled')" />
            <div class="text-h4 text-weight-bolder q-mt-sm">
                {{ isPaused ? 'RETOMAR' : (normalizedStatus === 'EM OPERAÇÃO' ? 'PAUSAR' : 'INICIAR') }}
            </div>
            <div class="text-subtitle2 text-uppercase letter-spacing-1 opacity-80 q-mt-xs">
                {{ isPaused ? 'VOLTAR A PRODUZIR' : (normalizedStatus === 'EM OPERAÇÃO' ? 'REGISTRAR PARADA' : 'INICIAR OPERAÇÃO') }}
            </div>
          </div>
       </q-btn>
    </div>

    <div class="col-auto row q-gutter-x-sm q-mb-sm" style="height: 80px;">
       <q-btn 
          class="col shadow-3 hover-scale"
          :class="isInSetup ? 'bg-purple-9 text-white' : 'bg-blue-grey-2 text-blue-grey-9'"
          push style="border-radius: 16px;" 
          :loading="isLoadingAction"
          @click="$emit('setup-action')"
        >
          <div class="column items-center justify-center">
              <q-icon :name="isInSetup ? 'check_circle' : 'build'" size="28px" class="q-mb-xs" />
              <div class="text-subtitle1 text-weight-bold">
                  {{ isInSetup ? 'FIM SETUP' : 'SETUP' }}
              </div>
              <div v-if="isInSetup" class="text-caption text-weight-bold bg-black-transparent q-px-sm rounded-borders q-mt-xs">
                  {{ elapsedTime }}
              </div>
          </div>
        </q-btn>
       <q-btn 
          class="col shadow-3 hover-scale vemag-bg-secondary text-white"
          push style="border-radius: 16px;"
          @click="$emit('open-andon')"
       >
          <div class="column items-center justify-center">
             <q-icon name="notifications_active" size="28px" class="q-mb-xs" />
             <div class="text-subtitle1 text-weight-bold">AJUDA</div>
          </div>
       </q-btn>
    </div>

    <div class="col-auto">
       <q-btn 
          class="full-width shadow-4" color="red-10" text-color="white"
          push size="18px" icon="stop_circle" label="FINALIZAR O.P."
          style="border-radius: 16px; min-height: 60px;"
          @click="$emit('finish-op')"
       />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  elapsedTime: string;
  statusTextClass: string;
  getButtonClass: string;
  isLoadingAction: boolean;
  isPaused: boolean;
  normalizedStatus: string;
  isInSetup: boolean;
}>();

defineEmits(['main-action', 'setup-action', 'open-andon', 'finish-op']);
</script>

<style scoped>
.vemag-text-primary { color: #008C7A !important; }
.vemag-text-secondary { color: #66B8B0 !important; }
.vemag-bg-secondary { background-color: #66B8B0 !important; }
.font-monospace { font-family: 'Courier New', monospace; letter-spacing: -1px; }
.hover-scale-producing { transition: all 0.2s ease-in-out; }
.hover-scale-producing:active { transform: scale(0.98); }
.hover-scale:active { transform: scale(0.98); }
.bg-black-transparent { background-color: rgba(0,0,0,0.15); }
.letter-spacing-1 { letter-spacing: 1px; }
.opacity-80 { opacity: 0.8; }
</style>
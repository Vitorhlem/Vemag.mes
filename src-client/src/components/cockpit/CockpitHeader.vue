<template>
  <q-header bordered class="q-py-xs shadow-3 text-white" style="height: 65px; background-color: #008C7A;">
    <q-toolbar class="full-height q-px-lg">
      <div class="row items-center no-wrap">
        <img :src="logoPath" alt="Logo" style="height: 40px; max-width: 180px; object-fit: contain; filter: brightness(0) invert(1);" />
        <q-separator vertical inset class="q-mx-md mobile-hide bg-white opacity-50" />
        <div class="column justify-center">
          <div class="text-caption text-uppercase text-grey-3 letter-spacing-1" style="line-height: 1;">
            {{ machineSector }}
          </div>
          <div class="row items-center q-mt-xs">
            <div class="text-h6 text-weight-bolder lh-small text-white q-mr-sm">
              {{ machineName }}
            </div>
            <q-badge rounded :class="statusBgClass" class="shadow-2 text-white q-py-xs q-px-sm text-caption">
              <q-icon :name="statusIcon" color="white" class="q-mr-xs" size="14px" />
              {{ displayStatus }}
            </q-badge>
          </div>
        </div>
      </div>

      <q-space />

      <div class="row items-center q-gutter-x-md">
        <div class="row items-center bg-white text-dark q-py-xs q-px-sm rounded-borders shadow-2" style="height: 42px; border-radius: 10px;">
          <q-avatar size="28px" class="shadow-1 vemag-bg-primary text-white" icon="person" font-size="18px" />
          <div class="column items-start justify-center q-ml-sm mobile-hide" style="line-height: 1.1;">
            <div class="text-caption text-weight-bold vemag-text-primary text-uppercase" style="font-size: 0.6rem;">OP</div>
            <div class="text-caption text-grey-9 text-weight-bold">
              {{ operatorName }}
            </div>
          </div>
          <q-separator vertical inset class="q-mx-sm bg-grey-4" />
          <div class="text-h6 font-monospace vemag-text-primary text-weight-bold" style="margin-top: 1px;">
            {{ timeDisplay }}
          </div>
        </div>
        <q-btn flat round icon="logout" class="text-white" size="md" padding="xs" @click="$emit('logout')" />
      </div>
    </q-toolbar>
    <q-linear-progress :value="1" color="green" class="q-mt-none" size="4px" />
  </q-header>
</template>

<script setup lang="ts">
defineProps<{
  logoPath: string;
  machineSector: string;
  machineName: string;
  statusBgClass: string;
  statusIcon: string;
  displayStatus: string;
  operatorName: string;
  timeDisplay: string;
}>();
defineEmits(['logout']);
</script>

<style scoped>
.vemag-bg-primary { background-color: #008C7A !important; }
.vemag-text-primary { color: #008C7A !important; }
.font-monospace { font-family: 'Courier New', monospace; letter-spacing: -1px; }
.lh-small { line-height: 1.1; }
.letter-spacing-1 { letter-spacing: 1px; }
</style>
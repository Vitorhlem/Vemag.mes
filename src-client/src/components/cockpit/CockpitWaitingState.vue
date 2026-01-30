<template>
  <div class="col flex flex-center column">
    <q-card class="q-pa-lg text-center shadow-10 bg-white" style="border-radius: 20px; max-width: 500px; width: 90%;">
      <div class="vemag-bg-light q-pa-md rounded-borders inline-block q-mb-md">
        <q-icon name="qr_code_scanner" size="60px" class="vemag-text-primary" />
      </div>
      <div class="text-h4 text-weight-bolder vemag-text-primary q-mb-sm">Aguardando O.P.</div>
      <div class="text-subtitle1 text-grey-7 q-mb-lg">A máquina está parada.<br>Selecione uma opção:</div>
      
      <div class="column q-gutter-y-md">
        <q-btn push rounded color="blue-grey-9" text-color="white" class="full-width shadow-3" size="18px" padding="md" icon="list_alt" label="SELECIONAR DA LISTA" @click="$emit('open-list')" />
        <div class="text-caption text-grey-5">- OU -</div>
        <q-btn push rounded class="vemag-bg-primary text-white full-width shadow-4" size="18px" padding="md" icon="photo_camera" label="LER QR CODE" @click="$emit('scan-qr')" />
      </div>
    </q-card>
  </div>
</template>

<script setup lang="ts">
defineEmits(['open-list', 'scan-qr']);
</script>

<style scoped>
.vemag-bg-light { background-color: #E0F2F1 !important; }
.vemag-text-primary { color: #008C7A !important; }
.vemag-bg-primary { background-color: #008C7A !important; }
</style>
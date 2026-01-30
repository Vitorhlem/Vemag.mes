<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" maximized transition-show="slide-up" transition-hide="slide-down">
      <q-card class="bg-grey-10 text-white column">
          <q-bar class="bg-grey-9 q-pa-sm z-top" style="height: 60px;">
              <q-icon name="picture_as_pdf" size="24px" />
              <div class="text-h6 q-ml-md">Desenho: {{ partCode }}</div>
              <q-space />
              <q-btn flat icon="refresh" label="Recarregar" @click="$emit('refresh')" class="q-mr-sm" />
              <q-btn dense flat icon="close" size="20px" v-close-popup />
          </q-bar>

          <q-card-section class="col q-pa-none relative-position bg-grey-3">
              <iframe v-if="url" :src="url" class="fit" style="border: none;"></iframe>
              <div v-else class="absolute-full flex flex-center text-grey-8">Carregando visualizador...</div>
          </q-card-section>
      </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
defineProps<{ modelValue: boolean; url: string; partCode: string }>();
defineEmits(['update:modelValue', 'refresh']);
</script>
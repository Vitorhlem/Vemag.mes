<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" persistent maximized transition-show="slide-up" transition-hide="slide-down">
    <q-card class="bg-grey-2 column">
      <q-toolbar class="bg-white text-dark q-py-md shadow-2 z-top">
        <q-toolbar-title class="text-weight-bold text-h6 row items-center">
          <q-icon name="warning" color="warning" size="30px" class="q-mr-md"/> SELECIONE O MOTIVO
        </q-toolbar-title>
        <q-btn flat round icon="close" size="lg" v-close-popup />
      </q-toolbar>
      
      <q-card-section class="col column q-pa-none">
        <div class="q-pa-md">
           <q-input :model-value="stopSearch" @update:model-value="$emit('update:stopSearch', $event)" outlined bg-color="white" placeholder="Pesquisar..." class="text-subtitle1" dense autofocus clearable>
              <template v-slot:prepend><q-icon name="search" /></template>
           </q-input>
        </div>
        <div class="col scroll q-px-md q-pb-md">
           <div class="row q-col-gutter-sm">
              <div v-for="(reason, idx) in filteredReasons" :key="idx" class="col-12 col-sm-6 col-md-4">
                <q-btn flat bordered class="full-width reason-card" :class="{ 'special-active': reason.isSpecial }" @click="$emit('select-reason', reason)">
                  <div class="row items-center no-wrap full-width q-pa-sm">
                    <q-avatar size="48px" :color="reason.code === '111' ? 'blue-8' : (reason.requiresMaintenance ? 'red-8' : 'grey-3')" :text-color="reason.requiresMaintenance || reason.code === '111' ? 'white' : 'grey-9'" :class="{ 'pulse-animation': reason.isSpecial }">
                      <q-icon :name="reason.code === '111' ? 'sync_alt' : (reason.requiresMaintenance ? 'engineering' : 'pause')" size="28px" />
                    </q-avatar>
                    <div class="column q-ml-md text-left">
                      <div class="text-subtitle1 text-weight-bold lh-tight" :class="reason.isSpecial ? 'text-dark' : 'text-grey-9'">{{ reason.label }}</div>
                      <div class="text-caption text-grey-6">Cód: {{ reason.code }}</div>
                    </div>
                  </div>
                </q-btn>
              </div>
           </div>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
defineProps<{ modelValue: boolean; stopSearch: string; filteredReasons: any[] }>();
defineEmits(['update:modelValue', 'update:stopSearch', 'select-reason']);
</script>

<style scoped>
.reason-card { border-radius: 12px; background: white; transition: all 0.3s ease; border: 1px solid #e0e0e0; min-height: 85px; }
.reason-card:hover { background: #f5f5f5; transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
.special-active { border: 2px solid #008C7A !important; background: #f0fdfa !important; }
.pulse-animation { animation: pulse-shadow 2s infinite; }
@keyframes pulse-shadow { 0% { box-shadow: 0 0 0 0 rgba(0, 140, 122, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(0, 140, 122, 0); } 100% { box-shadow: 0 0 0 0 rgba(0, 140, 122, 0); } }
.lh-tight { line-height: 1.2; }
</style>
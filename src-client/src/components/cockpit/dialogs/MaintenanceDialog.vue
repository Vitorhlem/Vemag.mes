<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" persistent transition-show="slide-up" transition-hide="slide-down">
    <q-card class="maintenance-card shadow-24">
      <q-card-section class="bg-red-10 text-white row items-center q-py-lg">
        <q-avatar icon="engineering" color="white" text-color="red-10" size="50px" class="q-mr-md shadow-3" />
        <div class="column">
          <div class="text-h5 text-weight-bolder uppercase letter-spacing-1">Registrar Quebra</div>
          <div class="text-caption opacity-80">A máquina será bloqueada e uma O.M. será aberta.</div>
        </div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup @click="$emit('cancel')" />
      </q-card-section>

      <q-card-section class="q-pa-lg">
        <div class="text-overline text-grey-7 q-mb-sm">Onde está o problema?</div>
        <div class="row q-col-gutter-sm q-mb-lg">
          <div v-for="opt in subReasonOptions" :key="opt.value" class="col-6 col-sm-4">
            <q-btn flat bordered class="full-width sub-reason-btn" :class="{ 'sub-reason-active': subReason === opt.value }" @click="$emit('update:subReason', opt.value)">
              <div class="column items-center">
                <q-icon :name="opt.icon" size="24px" class="q-mb-xs" />
                <div class="text-caption text-weight-bold">{{ opt.label }}</div>
              </div>
            </q-btn>
          </div>
        </div>

        <div class="text-overline text-grey-7 q-mb-sm">Descreva o que aconteceu:</div>
        <q-input :model-value="note" @update:model-value="$emit('update:note', $event)" filled type="textarea" placeholder="Ex: Mangueira de óleo estourou no eixo X..." bg-color="grey-2" rows="3" class="text-subtitle1" />
      </q-card-section>

      <q-card-actions align="between" class="q-px-lg q-pb-lg">
        <q-btn flat label="CANCELAR" color="grey-7" size="lg" @click="$emit('cancel')" />
        <q-btn push rounded label="ABRIR O.M. AGORA" color="red-10" icon-right="send" size="lg" class="q-px-xl text-weight-bolder" @click="$emit('confirm')" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: boolean;
  subReason: string;
  note: string;
  subReasonOptions: any[];
}>();
defineEmits(['update:modelValue', 'update:subReason', 'update:note', 'cancel', 'confirm']);
</script>

<style scoped>
.maintenance-card { width: 600px; max-width: 95vw; border-radius: 20px; }
.sub-reason-btn { border-radius: 12px; height: 80px; border: 1px solid #e0e0e0; color: #616161; background: #fafafa; transition: all 0.2s ease; }
.sub-reason-active { background: #ffebee !important; border: 2px solid #b71c1c !important; color: #b71c1c !important; transform: scale(1.03); }
.letter-spacing-1 { letter-spacing: 1px; }
</style>
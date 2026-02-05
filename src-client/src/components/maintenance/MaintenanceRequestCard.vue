<template>
  <q-card flat bordered class="column no-wrap cursor-pointer q-hoverable maintenance-card" @click="emit('click')">
    <span class="q-focus-helper"></span>
    
    <q-card-section>
      <div class="row items-center no-wrap">
        <div class="col">
          <div class="text-caption text-grey-8 text-uppercase flex items-center">
             OS #{{ request.id }} 
             <q-icon name="circle" size="6px" class="q-mx-xs text-grey-5" /> 
             {{ request.category || 'Industrial' }}
          </div>
          <div class="text-subtitle1 text-weight-bold ellipsis text-primary">
             {{ request.vehicle?.brand }} {{ request.vehicle?.model }}
          </div>
          <div class="text-caption text-grey-7">
             Tag: <strong>{{ request.vehicle?.license_plate || request.vehicle?.identifier || 'N/A' }}</strong>
          </div>
        </div>
        
        <q-chip 
            :color="getStatusColor(request.status)" 
            text-color="white" 
            size="sm" 
            class="text-weight-bold shadow-1"
        >
          {{ translateStatus(request.status) }}
        </q-chip>
      </div>
    </q-card-section>

    <q-separator inset />

    <q-card-section class="q-py-sm" style="flex-grow: 1;">
      <div class="text-body2 ellipsis-3-lines text-grey-9">
         {{ request.problem_description }}
      </div>
    </q-card-section>

    <q-separator />

    <q-card-section class="row justify-between items-center q-pa-sm text-caption bg-grey-1 text-grey-7">
      <div class="flex items-center">
         <q-icon name="person" size="xs" class="q-mr-xs"/> {{ firstName(request.reporter?.full_name) }}
      </div>
      <div class="flex items-center">
         <q-icon name="event" size="xs" class="q-mr-xs"/> {{ new Date(request.created_at).toLocaleDateString('pt-BR') }}
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { MaintenanceStatus, type MaintenanceRequest } from 'src/models/maintenance-models';

defineProps<{ request: MaintenanceRequest }>();
const emit = defineEmits(['click']);

function firstName(name: string | undefined) {
    return name ? name.split(' ')[0] : 'Sistema';
}

function getStatusColor(status: MaintenanceStatus) {
  const colorMap: Record<MaintenanceStatus, string> = {
    [MaintenanceStatus.PENDENTE]: 'orange',
    [MaintenanceStatus.APROVADA]: 'primary',
    [MaintenanceStatus.REJEITADA]: 'negative',
    [MaintenanceStatus.EM_ANDAMENTO]: 'info',
    [MaintenanceStatus.CONCLUIDA]: 'positive',
  };
  return colorMap[status];
}

function translateStatus(status: MaintenanceStatus) {
    if (status === MaintenanceStatus.EM_ANDAMENTO) return 'EM EXECUÇÃO';
    if (status === MaintenanceStatus.CONCLUIDA) return 'FINALIZADA';
    return status;
}
</script>

<style lang="scss" scoped>
.maintenance-card {
    transition: transform 0.2s, box-shadow 0.2s;
    &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
}
.ellipsis-3-lines {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  min-height: 42px; /* Garante altura uniforme */
}
</style>
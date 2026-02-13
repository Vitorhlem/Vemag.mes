<template>
  <q-page class="q-pa-md q-pa-lg-xl bg-glass-layout">
    
    <div class="row items-center justify-between q-mb-lg q-col-gutter-y-md">
      <div class="col-12 col-md-auto">
        <h1 class="text-h4 text-weight-bolder q-my-none text-gradient-trucar flex items-center gap-sm">
          <q-icon name="precision_manufacturing" size="md" class="text-primary" />
          {{ terminologyStore.vehiclePageTitle }}
        </h1>
        <div class="text-subtitle2 text-teal-9 opacity-80 q-mt-xs">
          Gestão de Ativos, CNCs e Equipamentos Industriais
        </div>
      </div>

      <div class="col-12 col-md-auto row q-gutter-sm items-center">
        <q-input 
          outlined 
          dense 
          v-model="searchTerm" 
          placeholder="Buscar..." 
          class="search-input glass-input" 
          style="min-width: 250px"
        >
          <template v-slot:prepend><q-icon name="search" class="text-teal-9" /></template>
          <template v-slot:append v-if="searchTerm"><q-icon name="close" @click="searchTerm = ''" class="cursor-pointer text-teal-9" /></template>
        </q-input>
        
        <q-btn-toggle 
          v-model="viewMode" 
          push 
          glossy 
          toggle-color="primary" 
          text-color="grey-8" 
          :options="[{value: 'folders', icon: 'folder_open'}, {value: 'grid', icon: 'grid_view'}]" 
          class="glass-toggle"
        />
        
        <q-btn v-if="authStore.isManager" @click="openCreateDialog" color="primary" icon="add" :label="terminologyStore.addVehicleButtonLabel" unelevated class="q-ml-sm shadow-green" />
      </div>
    </div>

    <div v-if="vehicleStore.isLoading" class="row justify-center q-py-xl"><q-spinner-dots size="3em" color="primary" /></div>
    <div v-else-if="!hasVehicles" class="text-center q-pa-xl text-grey-6 glass-card opacity-60">
        <q-icon name="precision_manufacturing" size="4em" />
        <div class="text-h6 q-mt-md">Nenhuma máquina encontrada</div>
    </div>

    <div v-else>
      
      <div v-if="viewMode === 'folders'" class="q-gutter-y-md animate-fade">
        <q-expansion-item 
          v-for="(machines, brandName) in groupedVehicles" 
          :key="brandName" 
          class="shadow-1 overflow-hidden glass-card rounded-borders" 
          header-class="bg-glass-header text-primary text-weight-bold" 
          expand-icon-class="text-primary" 
          :default-opened="!!searchTerm"
        >
          <template v-slot:header>
            <q-item-section avatar><q-avatar icon="folder" color="primary" text-color="white" size="sm" font-size="16px" /></q-item-section>
            <q-item-section><span class="text-h6 text-teal-10">{{ brandName }}</span></q-item-section>
            <q-item-section side><q-badge color="grey-7" :label="`${machines.length} un.`" class="glass-badge" /></q-item-section>
          </template>
          <q-card class="bg-transparent">
            <q-card-section class="q-pa-none">
              <q-list separator class="glass-separator">
                <q-item v-for="vehicle in machines" :key="vehicle.id" clickable v-ripple @click="handleCardClick(vehicle)" class="hover-bg-teal transition-bg">
                  <q-item-section avatar>
                    <q-avatar rounded size="50px" class="shadow-1">
                      <img v-if="getImageUrl(vehicle.photo_url)" :src="getImageUrl(vehicle.photo_url)!" style="object-fit: cover">
                      <q-icon v-else name="precision_manufacturing" color="grey-5" size="28px" class="bg-grey-2 full-width full-height" />
                    </q-avatar>
                  </q-item-section>
                  <q-item-section>
                    <div class="row items-center q-gutter-x-sm">
                        <span class="text-weight-bold text-grey-9 vehicle-title">{{ vehicle.model }}</span>
                        <q-badge outline color="primary" size="sm" class="glass-badge-outline">{{ vehicle.year }}</q-badge>
                    </div>
                    <q-item-label caption class="row items-center q-gutter-x-xs q-mt-xs text-grey-7">
                      <q-icon name="qr_code" size="xs" /><span>{{ vehicle.identifier || 'S/N' }}</span>
                      <span class="text-grey-5">|</span>
                      <q-icon name="speed" size="xs" /><span>{{ (vehicle.current_engine_hours || 0).toFixed(1) }} h</span>
                      <span v-if="vehicle.sap_resource_code" class="text-primary text-weight-bold q-ml-sm">
                         [SAP: {{ vehicle.sap_resource_code }}]
                      </span>
                    </q-item-label>
                    
                    <div class="q-mt-xs" style="max-width: 180px">
                        <div class="row justify-between text-caption" style="font-size: 10px; line-height: 10px">
                          <span class="text-grey-7">Manutenção</span>
                          <span :class="'text-weight-bold text-' + getMaintenanceColor(vehicle)">
                             {{ getHoursRemaining(vehicle) }}h rest.
                          </span>
                        </div>
                        <q-linear-progress 
                            :value="getMaintenanceProgress(vehicle)" 
                            rounded size="4px" 
                            :color="getMaintenanceColor(vehicle)" 
                            track-color="grey-3" 
                            class="q-mt-xs glass-progress" 
                        />
                    </div>
                  </q-item-section>
                  <q-item-section side>
                    <div class="row items-center q-gutter-x-sm">
                        <q-chip dense :color="getStatusColor(vehicle.status)" text-color="white" class="text-caption text-weight-bold shadow-1">{{ translateStatusShort(vehicle.status) }}</q-chip>
                        <q-btn flat round dense icon="edit" color="grey-7" @click.stop="openEditDialog(vehicle)" />
                    </div>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-card-section>
          </q-card>
        </q-expansion-item>
      </div>

      <div v-else class="row q-col-gutter-md animate-fade">
        <div v-for="vehicle in filteredList" :key="vehicle.id" class="col-xs-12 col-sm-6 col-md-4 col-lg-3">
          <q-card class="column no-wrap full-height vehicle-card glass-card" flat bordered @click="handleCardClick(vehicle)">
            <div class="relative-position">
              <q-img :src="getImageUrl(vehicle.photo_url) ?? undefined" height="180px" fit="cover" class="bg-grey-3">
                <template v-slot:error><div class="absolute-full flex flex-center bg-grey-3 text-grey-5"><q-icon name="precision_manufacturing" size="56px" /></div></template>
                <div class="absolute-bottom text-subtitle2 text-white p-2" style="background: linear-gradient(to top, rgba(5,20,18,0.9), transparent);">
                    <div class="text-weight-bold">{{ vehicle.identifier || 'Sem ID' }}</div>
                </div>
              </q-img>
              <q-badge :color="getStatusColor(vehicle.status)" class="absolute-top-right q-ma-sm shadow-2">{{ translateStatus(vehicle.status) }}</q-badge>
            </div>

            <q-card-section class="col q-pb-none">
              <div class="row justify-between items-start">
                  <div>
                      <div class="text-overline text-grey-7">{{ vehicle.brand }}</div>
                      <div class="text-h6 text-weight-bold ellipsis text-teal-10">{{ vehicle.model }}</div>
                      <div v-if="vehicle.sap_resource_code" class="text-caption text-primary text-weight-bold">
                        SAP: {{ vehicle.sap_resource_code }}
                      </div>
                  </div>
                  <q-btn round flat icon="qr_code_2" size="sm" color="primary" @click.stop="openQrDialog(vehicle)" />
              </div>
            </q-card-section>

            <q-card-section class="q-py-sm">
                <div class="row items-center justify-between text-caption text-grey-7 q-mb-xs">
                    <span>Prox. Revisão</span>
                    <span :class="'text-weight-bold text-' + getMaintenanceColor(vehicle)">
                        {{ getHoursRemaining(vehicle) }}h restantes
                    </span>
                </div>
                <q-linear-progress 
                    :value="1 - getMaintenanceProgress(vehicle)" 
                    rounded 
                    size="8px" 
                    :color="getMaintenanceColor(vehicle)" 
                    track-color="red-1"
                    class="q-mb-sm glass-progress"
                />
            </q-card-section>

            <q-card-section class="q-pt-none">
                <div class="row q-col-gutter-sm">
                  <div class="col-6">
                    <div class="bg-grey-2 q-pa-sm rounded-borders glass-metric-box">
                      <div class="text-caption text-grey-6 text-uppercase">Horímetro</div>
                      <div class="text-weight-bold text-primary">{{ (vehicle.current_engine_hours || 0).toFixed(0) }} h</div>
                    </div>
                  </div>
                  <div class="col-6">
                    <div class="bg-grey-2 q-pa-sm rounded-borders glass-metric-box">
                      <div class="text-caption text-grey-6 text-uppercase">Meta (h)</div>
                      <div class="text-weight-bold text-grey-8">{{ vehicle.next_maintenance_km ? vehicle.next_maintenance_km.toFixed(0) : '--' }}</div>
                    </div>
                  </div>
                </div>
            </q-card-section>
            
            <q-separator class="glass-separator" />
            <q-card-actions align="right" class="q-px-md">
                <q-btn flat round dense size="sm" color="primary" icon="edit" @click.stop="openEditDialog(vehicle)" />
                <q-btn flat round dense size="sm" color="negative" icon="delete" @click.stop="promptToDelete(vehicle)" />
            </q-card-actions>
          </q-card>
        </div>
      </div>
    </div>
    
    <q-dialog v-model="isFormDialogOpen" persistent>
        <q-card style="width: 600px; max-width: 95vw;" class="glass-card-dialog">
          <q-card-section class="row items-center bg-primary text-white">
            <div class="text-h6">{{ isEditing ? 'Editar Equipamento' : 'Novo Equipamento' }}</div>
            <q-space />
            <q-btn icon="close" flat round dense v-close-popup class="text-white" />
          </q-card-section>

          <q-form @submit.prevent="onFormSubmit">
            <q-card-section class="q-gutter-y-md q-pt-lg">
              
              <div class="row justify-center q-mb-md">
                  <div class="column items-center q-gutter-y-sm full-width">
                     <q-avatar size="100px" rounded class="shadow-1 bg-grey-3">
                        <img v-if="formData.photo_url" :src="getImageUrl(formData.photo_url)!" style="object-fit: cover">
                        <q-icon v-else name="add_a_photo" color="grey-6" size="40px" />
                        <div v-if="isUploading" class="absolute-full flex flex-center bg-white" style="opacity: 0.8"><q-spinner color="primary" size="2em" /></div>
                     </q-avatar>
                     <div class="row items-center q-gutter-x-sm">
                       <q-file v-model="photoFile" label="Alterar Foto" outlined dense accept=".jpg, .png" class="glass-input" style="min-width: 200px" @update:model-value="handlePhotoUpload" :loading="isUploading">
                         <template v-slot:prepend><q-icon name="cloud_upload" /></template>
                       </q-file>
                     </div>
                  </div>
              </div>

              <div class="row q-col-gutter-md">
                  <div class="col-6"><q-input outlined v-model="formData.brand" label="Fabricante *" :rules="[val => !!val || 'Obrigatório']" dense class="glass-input" /></div>
                  <div class="col-6"><q-input outlined v-model="formData.model" label="Modelo *" :rules="[val => !!val || 'Obrigatório']" dense class="glass-input" /></div>
              </div>

              <div class="row q-col-gutter-md">
                <div class="col-12 col-md-6">
                  <q-input 
                    outlined 
                    v-model="formData.identifier" 
                    label="Código do Ativo (AT...)" 
                    :rules="[val => !!val || 'Obrigatório']" 
                    dense 
                    class="glass-input"
                  />
                </div>
                
                <div class="col-12 col-md-6">
                  <q-input 
                    outlined 
                    v-model="formData.sap_resource_code" 
                    label="Recurso SAP (Ex: 4.02.01)" 
                    hint="Usado para apontamento de produção"
                    dense 
                    class="glass-input-highlight"
                  >
                    <template v-slot:prepend>
                      <q-icon name="precision_manufacturing" color="orange-8" />
                    </template>
                  </q-input>
                </div>
              </div>

              <q-input outlined v-model="formData.license_plate" label="TAG / Patrimônio" dense class="glass-input" />
              
              <div class="row q-col-gutter-md">
                  <div class="col-6"><q-input outlined v-model.number="formData.year" label="Ano" type="number" dense class="glass-input" /></div>
                  
                  <div class="col-6">
                      <q-input 
                        outlined 
                        v-model.number="formData.current_engine_hours" 
                        label="Horímetro Atual (h)" 
                        type="number" 
                        dense 
                        class="glass-input"
                        hint="Leitura atual da máquina"
                        @update:model-value="recalcTarget" 
                      />
                  </div>
              </div>

              <div class="text-subtitle2 text-primary q-mt-md flex items-center">
                  <q-icon name="build_circle" class="q-mr-xs"/> Plano de Manutenção
              </div>
              <div class="bg-glass-inner q-pa-md rounded-borders relative-position">
                
                <div class="row q-col-gutter-md items-start">
                    <div class="col-6">
                        <q-input 
                            outlined 
                            v-model.number="maintenanceInterval" 
                            label="A cada X horas (Ciclo)" 
                            type="number" 
                            dense 
                            class="glass-input"
                            hint="Ex: 500 para revisar a cada 500h"
                            @update:model-value="recalcTarget"
                        >
                            <template v-slot:append><span class="text-caption">h</span></template>
                        </q-input>
                    </div>

                    <div class="col-6">
                        <q-input 
                            outlined 
                            v-model.number="formData.next_maintenance_km" 
                            label="Próxima Meta (h)" 
                            type="number" 
                            dense 
                            class="glass-input"
                            input-class="text-weight-bold"
                            hint="Calculado: Atual + Ciclo"
                        >
                             <template v-slot:prepend><q-icon name="flag" color="orange"/></template>
                        </q-input>
                    </div>
                </div>

                <div class="text-caption text-grey-7 q-mt-sm">
                    <q-icon name="info" /> 
                    Ao definir o ciclo como <strong>{{ maintenanceInterval || 0 }}h</strong> e o horímetro atual sendo <strong>{{ formData.current_engine_hours || 0 }}h</strong>, a próxima revisão será agendada para <strong>{{ (formData.current_engine_hours || 0) + (maintenanceInterval || 0) }}h</strong>.
                </div>
              </div>

            </q-card-section>
            <q-card-actions align="right" class="q-pa-md bg-transparent">
              <q-btn flat label="Cancelar" v-close-popup color="grey-8" />
              <q-btn type="submit" unelevated color="primary" label="Salvar Dados" :loading="isSubmitting" />
            </q-card-actions>
          </q-form>
        </q-card>
    </q-dialog>

    <q-dialog v-model="isQrDialogOpen">
        <q-card style="width: 350px" class="glass-card-dialog">
            <q-card-section class="bg-primary text-white text-center">
                <div class="text-h6">Etiqueta de Máquina</div>
                <div class="text-caption">{{ selectedVehicleForQr?.model }}</div>
            </q-card-section>
            <q-card-section class="flex flex-center q-pa-lg">
                <img v-if="selectedVehicleForQr" :src="`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${getQrData(selectedVehicleForQr)}`" style="width: 200px; height: 200px" class="shadow-2 bg-white q-pa-sm rounded-borders">
            </q-card-section>
            <q-card-section class="text-center text-teal-9">
                <div class="text-weight-bold">{{ selectedVehicleForQr?.identifier }}</div>
                <div class="text-caption text-grey-7" v-if="selectedVehicleForQr?.sap_resource_code">SAP: {{ selectedVehicleForQr?.sap_resource_code }}</div>
            </q-card-section>
            <q-card-actions align="center" class="q-pb-md"><q-btn label="Fechar" flat v-close-popup color="primary" /></q-card-actions>
        </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar, setCssVar } from 'quasar';
import { api } from 'boot/axios';
import { useVehicleStore } from 'stores/vehicle-store';
import { useAuthStore } from 'stores/auth-store';
import { useTerminologyStore } from 'stores/terminology-store';
import { VehicleStatus, type Vehicle, type VehicleCreate, type VehicleUpdate } from 'src/models/vehicle-models';
import { format, parse, isValid } from 'date-fns';

const $q = useQuasar();
const vehicleStore = useVehicleStore();
const authStore = useAuthStore();
const terminologyStore = useTerminologyStore();
const router = useRouter();

// --- ESTADO ---
const viewMode = ref<'folders' | 'grid'>('folders');
const searchTerm = ref('');
const isFormDialogOpen = ref(false);
const isQrDialogOpen = ref(false);
const isSubmitting = ref(false);
const isUploading = ref(false);
const editingVehicleId = ref<number | null>(null);
const selectedVehicleForQr = ref<Vehicle | null>(null);
const isEditing = computed(() => editingVehicleId.value !== null);
const photoFile = ref<File | null>(null);

const currentParams = { page: 1, rowsPerPage: 100, search: '' };

interface MachineFormData {
    brand: string;
    model: string;
    year: number;
    status: VehicleStatus;
    license_plate: string | null;
    identifier: string | null;
    sap_resource_code: string | null;
    current_engine_hours: number;
    current_km: number;
    next_maintenance_km: number | null;
    next_maintenance_date: string | null;
    photo_url: string | null;
}

const formData = ref<MachineFormData>({
    brand: '',
    model: '',
    year: new Date().getFullYear(),
    status: VehicleStatus.AVAILABLE,
    license_plate: '',
    identifier: '',
    sap_resource_code: '', 
    current_engine_hours: 0,
    current_km: 0,
    next_maintenance_km: null,
    next_maintenance_date: null,
    photo_url: null
});

const maintenanceInterval = ref<number>(0);

// --- FILTROS ---
const filteredList = computed(() => {
  const all = vehicleStore.vehicles;
  if (!searchTerm.value) return all;
  const lower = searchTerm.value.toLowerCase();
  return all.filter(v => 
    (v.model && v.model.toLowerCase().includes(lower)) ||
    (v.brand && v.brand.toLowerCase().includes(lower)) ||
    (v.identifier && v.identifier.toLowerCase().includes(lower)) ||
    (v.sap_resource_code && v.sap_resource_code.toLowerCase().includes(lower))
  );
});

const groupedVehicles = computed(() => {
  const groups: Record<string, Vehicle[]> = {};
  const sortedList = [...filteredList.value].sort((a, b) => {
      const brandA = a.brand || 'OUTROS';
      const brandB = b.brand || 'OUTROS';
      return brandA.localeCompare(brandB);
  });
  sortedList.forEach(vehicle => {
    const folderName = vehicle.brand ? vehicle.brand.toUpperCase() : 'DIVERSOS';
    if (!groups[folderName]) groups[folderName] = [];
    groups[folderName].push(vehicle);
  });
  return groups;
});

const hasVehicles = computed(() => filteredList.value.length > 0);

// --- CÁLCULOS VISUAIS ---

function getHoursRemaining(vehicle: Vehicle) {
    if (!vehicle.next_maintenance_km || !vehicle.current_engine_hours) return 0;
    const remaining = vehicle.next_maintenance_km - vehicle.current_engine_hours;
    return remaining > 0 ? remaining.toFixed(0) : 0;
}

function getMaintenanceProgress(vehicle: Vehicle) {
    if (!vehicle.next_maintenance_km || !vehicle.current_engine_hours) return 0;
    const remaining = vehicle.next_maintenance_km - vehicle.current_engine_hours;
    if (remaining <= 0) return 1;
    
    const visualCycle = 500; 
    const progress = (visualCycle - remaining) / visualCycle;
    
    if (progress < 0) return 0;
    if (progress > 1) return 1;
    return progress;
}

function getMaintenanceColor(vehicle: Vehicle) {
    const p = getMaintenanceProgress(vehicle);
    if (p >= 1) return 'negative';
    if (p > 0.8) return 'warning';
    return 'positive';
}

const statusTranslationShort: Record<VehicleStatus, string> = {
    [VehicleStatus.AVAILABLE]: 'Disp.',
    [VehicleStatus.IN_USE]: 'Oper.',
    [VehicleStatus.MAINTENANCE]: 'Manut.'
};

const statusTranslation: Record<VehicleStatus, string> = {
    [VehicleStatus.AVAILABLE]: 'DISPONÍVEL',
    [VehicleStatus.IN_USE]: 'EM OPERAÇÃO',
    [VehicleStatus.MAINTENANCE]: 'MANUTENÇÃO'
};

const statusColors: Record<VehicleStatus, string> = {
    [VehicleStatus.AVAILABLE]: 'positive',
    [VehicleStatus.IN_USE]: 'blue-8',
    [VehicleStatus.MAINTENANCE]: 'negative'
};

function translateStatus(status: VehicleStatus): string {
    return statusTranslation[status] || status;
}

function translateStatusShort(status: VehicleStatus): string {
    return statusTranslationShort[status] || status;
}

function getStatusColor(status: VehicleStatus): string {
    return statusColors[status] || 'grey';
}

// --- LÓGICA DO FORMULÁRIO ---

function recalcTarget() {
    const current = Number(formData.value.current_engine_hours || 0);
    const interval = Number(maintenanceInterval.value || 0);
    
    if (interval > 0) {
        formData.value.next_maintenance_km = current + interval;
    }
}

function openCreateDialog() {
    editingVehicleId.value = null;
    photoFile.value = null;
    maintenanceInterval.value = 500;
    formData.value = {
        brand: '', model: '', year: new Date().getFullYear(),
        status: VehicleStatus.AVAILABLE,
        current_engine_hours: 0, 
        current_km: 0, 
        license_plate: '',
        identifier: '',
        sap_resource_code: '',
        next_maintenance_km: 500,
        next_maintenance_date: null,
        photo_url: null
    };
    isFormDialogOpen.value = true;
}

function openEditDialog(vehicle: Vehicle) {
    editingVehicleId.value = vehicle.id;
    photoFile.value = null;
    
    const remaining = (vehicle.next_maintenance_km || 0) - (vehicle.current_engine_hours || 0);
    maintenanceInterval.value = remaining > 0 ? remaining : 0; 

    const nextDate = vehicle.next_maintenance_date 
        ? format(new Date(vehicle.next_maintenance_date), 'dd/MM/yyyy') 
        : null;
        
    formData.value = { 
        brand: vehicle.brand,
        model: vehicle.model,
        year: vehicle.year,
        status: vehicle.status,
        license_plate: vehicle.license_plate ?? '',
        identifier: vehicle.identifier ?? '',
        sap_resource_code: vehicle.sap_resource_code ?? '', 
        current_engine_hours: vehicle.current_engine_hours ?? 0,
        current_km: vehicle.current_km,
        next_maintenance_km: vehicle.next_maintenance_km ?? null,
        next_maintenance_date: nextDate,
        photo_url: vehicle.photo_url ?? null
    };
    isFormDialogOpen.value = true;
}

function convertDateForBackend(dateStr: string | null | undefined): string | null {
    if (!dateStr) return null;
    if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) return dateStr;
    try {
        const parsed = parse(dateStr, 'dd/MM/yyyy', new Date());
        if (isValid(parsed)) {
            return format(parsed, 'yyyy-MM-dd');
        }
    } catch { 
        return null; 
    }
    return null;
}

async function onFormSubmit() {
    isSubmitting.value = true;
    try {
        const rawData = formData.value;
        
        const commonPayload = {
            brand: rawData.brand,
            model: rawData.model,
            year: Number(rawData.year),
            status: rawData.status,
            license_plate: rawData.license_plate || undefined,
            identifier: rawData.identifier || undefined,
            sap_resource_code: rawData.sap_resource_code || undefined, 
            current_engine_hours: Number(rawData.current_engine_hours || 0),
            next_maintenance_km: rawData.next_maintenance_km ? Number(rawData.next_maintenance_km) : undefined,
            next_maintenance_date: convertDateForBackend(rawData.next_maintenance_date) || undefined,
            photo_url: rawData.photo_url || undefined
        };

        if (isEditing.value && editingVehicleId.value) {
            const updatePayload: VehicleUpdate = { ...commonPayload };
            await vehicleStore.updateVehicle(editingVehicleId.value, updatePayload, currentParams);
        } else {
            const createPayload: VehicleCreate = { 
                ...commonPayload, 
                current_km: 0 
            };
            await vehicleStore.addNewVehicle(createPayload, currentParams);
        }

        isFormDialogOpen.value = false;
        await vehicleStore.fetchAllVehicles(currentParams);
        $q.notify({ type: 'positive', message: 'Salvo com sucesso!' });
    } catch (error) {
        console.error(error);
        $q.notify({ type: 'negative', message: 'Erro ao salvar.' });
    } finally {
        isSubmitting.value = false;
    }
}

// --- OUTROS MÉTODOS ---
function openQrDialog(vehicle: Vehicle) { 
    selectedVehicleForQr.value = vehicle; 
    isQrDialogOpen.value = true; 
}

function getQrData(vehicle: Vehicle) { 
    return `${window.location.origin}/vehicles/${vehicle.id}`; 
}

function getImageUrl(url: string | null | undefined) { 
    if (!url) return null; 
    return url.startsWith('http') ? url : `http://127.0.0.1:8000${url}`; 
}

async function handlePhotoUpload(file: File | null) { 
    if (!file) return; 
    isUploading.value = true; 
    const data = new FormData(); 
    data.append('file', file); 
    try { 
        const res = await api.post('/upload-photo', data); 
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-type-assertion, @typescript-eslint/no-explicit-any
        formData.value.photo_url = (res.data as any).file_url; 
    } catch(e) { 
        console.error(e); 
    } finally { 
        isUploading.value = false; 
    } 
}

function handleCardClick(vehicle: Vehicle) { 
    void router.push(`/vehicles/${vehicle.id}`); 
}

function promptToDelete(vehicle: Vehicle) { 
    $q.dialog({ title: 'Excluir', message: 'Tem certeza?', cancel: true }).onOk(() => {
        void (async () => {
             await vehicleStore.deleteVehicle(vehicle.id, currentParams); 
             await vehicleStore.fetchAllVehicles(currentParams); 
        })();
    }); 
}

onMounted(() => { 
    setCssVar('primary', '#128c7e');
    void vehicleStore.fetchAllVehicles(currentParams); 
});
</script>

<style scoped lang="scss">
/* --- IDENTIDADE TRUCAR --- */
.bg-glass-layout {
  background-color: #f0f4f4; // Default Light
  min-height: 100vh;
  transition: background-color 0.3s;
}

.text-gradient-trucar {
  background: linear-gradient(to right, #128c7e, #70c0b0);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* --- GLASSMORPHISM --- */
.glass-card, .glass-card-dialog {
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(12px) saturate(180%);
  border: 1px solid rgba(18, 140, 126, 0.1);
  border-radius: 12px;
}

.glass-input {
  background: rgba(255, 255, 255, 0.5) !important;
  backdrop-filter: blur(8px);
  border-radius: 4px;
}

.glass-input-highlight {
  background: rgba(255, 235, 59, 0.1) !important; /* Amarelo leve */
  backdrop-filter: blur(8px);
  border-radius: 4px;
}

.glass-header {
  background: rgba(18, 140, 126, 0.05);
}

.glass-badge {
  background: rgba(18, 140, 126, 0.1) !important;
  color: #128c7e;
}

.glass-metric-box {
  background: rgba(18, 140, 126, 0.05);
  border: 1px solid rgba(18, 140, 126, 0.1);
}

.bg-glass-inner {
  background: rgba(18, 140, 126, 0.05);
  border-radius: 8px;
}

/* --- INTERACTIONS --- */
.vehicle-card { 
  cursor: pointer; 
  transition: transform 0.2s, box-shadow 0.2s; 
}
.vehicle-card:hover { 
  transform: translateY(-5px); 
  box-shadow: 0 10px 25px -5px rgba(18, 140, 126, 0.2);
  border-color: #128c7e;
}

.hover-bg-teal:hover { 
  background-color: rgba(18, 140, 126, 0.08) !important; 
  transition: background-color 0.2s; 
}

.shadow-green { box-shadow: 0 4px 14px 0 rgba(18, 140, 126, 0.2); }
.animate-fade { animation: fadeIn 0.4s ease-in-out; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* =========================================
   DARK MODE OVERRIDES (DARK FOREST)
   ========================================= */
.body--dark {
  .bg-glass-layout { 
    background-color: #05100e !important; 
  }

  .glass-card, .glass-card-dialog {
    background: rgba(5, 20, 18, 0.7) !important;
    border-color: rgba(18, 140, 126, 0.2);
    color: #e0f2f1;
  }

  .glass-input, .glass-input-highlight {
    background: rgba(18, 140, 126, 0.1) !important;
    :deep(.q-field__native), :deep(.q-field__label) {
        color: #b2dfdb !important;
    }
    :deep(.q-icon) {
        color: #80cbc4 !important;
    }
  }

  /* Expansion Item Header */
  .bg-glass-header {
    background: rgba(18, 140, 126, 0.15) !important;
  }

  /* Separators */
  .glass-separator {
    border-color: rgba(18, 140, 126, 0.2) !important;
  }

  /* Badges & Metrics */
  .glass-metric-box {
    background: rgba(255, 255, 255, 0.05) !important;
    border-color: rgba(18, 140, 126, 0.2);
  }
  .bg-grey-2 {
    background: rgba(255, 255, 255, 0.05) !important;
  }
  .bg-grey-3 {
    background: rgba(255, 255, 255, 0.1) !important;
  }

  /* Texts */
  .text-teal-9, .text-teal-10 { color: #80cbc4 !important; }
  .text-grey-9 { color: #ffffff !important; }
  .text-grey-7, .text-grey-6, .text-grey-8 { color: #b0bec5 !important; }
  .vehicle-title { color: #80cbc4 !important; }

  /* Buttons */
  .q-btn-toggle {
    background: rgba(18, 140, 126, 0.1) !important;
    color: #b2dfdb !important;
  }
  
  .glass-progress {
    :deep(.q-linear-progress__track) {
      opacity: 0.3;
    }
  }
}
</style>
<template>
  <q-page class="q-pa-md q-pa-lg-xl">
    
    <div class="row items-center justify-between q-mb-lg q-col-gutter-y-md">
      <div class="col-12 col-md-auto">
        <h1 class="text-h4 text-weight-bolder q-my-none text-primary flex items-center gap-sm">
          <q-icon name="precision_manufacturing" size="md" />
          Parque de Máquinas
        </h1>
        <div class="text-subtitle2 text-grey-7 q-mt-xs">
          Gerencie suas CNCs, Tornos e Equipamentos
        </div>
      </div>

      <div class="col-12 col-md-auto row q-gutter-sm">
        <q-input
          outlined dense debounce="300"
          v-model="searchTerm"
          placeholder="Buscar por Patrimônio ou Modelo..."
          class="search-input"
        >
          <template v-slot:prepend><q-icon name="search" /></template>
        </q-input>
        
        <q-btn
          v-if="authStore.isManager"
          @click="openCreateDialog" 
          color="primary"
          icon="add" 
          label="Adicionar Máquina" 
          unelevated
        />
      </div>
    </div>

    <div v-if="vehicleStore.vehicles.length > 0" class="row q-col-gutter-md">
      <div v-for="vehicle in vehicleStore.vehicles" :key="vehicle.id" class="col-xs-12 col-sm-6 col-md-4 col-lg-3">
        <q-card class="column no-wrap full-height vehicle-card" flat bordered @click="handleCardClick(vehicle)">
          <div class="relative-position">
            <q-img :src="getImageUrl(vehicle.photo_url) ?? undefined" height="180px" fit="cover" class="bg-grey-3">
              <template v-slot:error>
                <div class="absolute-full flex flex-center bg-grey-3 text-grey-5">
                  <q-icon name="precision_manufacturing" size="56px" />
                </div>
              </template>
              
              <div class="absolute-bottom text-subtitle2 text-white p-2" style="background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);">
                 <div class="row items-center justify-between full-width">
                   <div class="text-weight-bold">Tag: {{ vehicle.license_plate || vehicle.identifier || 'S/N' }}</div>
                 </div>
              </div>
            </q-img>
            
            <q-badge :color="getStatusColor(vehicle.status)" class="absolute-top-right q-ma-sm shadow-2">
              {{ translateStatus(vehicle.status) }}
            </q-badge>
          </div>

          <q-card-section class="col q-pb-none">
            <div class="text-overline text-grey-7">{{ vehicle.brand }}</div>
            <div class="text-h6 text-weight-bold ellipsis q-mb-xs">{{ vehicle.model }}</div>
            <div class="text-caption text-grey-8">
               <q-icon name="factory" size="16px" class="q-mr-xs text-primary" />
               Setor: {{ vehicle.year ? `Linha ${vehicle.year}` : 'Geral' }}
            </div>
          </q-card-section>

          <q-card-section class="q-pt-sm">
             <div class="row q-col-gutter-sm">
               <div class="col-6">
                 <div class="bg-grey-2 q-pa-sm rounded-borders">
                    <div class="text-caption text-grey-6 text-uppercase">Horímetro Total</div>
                    <div class="text-weight-bold text-primary">{{ (vehicle.current_engine_hours || 0).toFixed(1) }} h</div>
                 </div>
               </div>
               
               <div class="col-6">
                 <div class="bg-grey-2 q-pa-sm rounded-borders">
                    <div class="text-caption text-grey-6 text-uppercase">Próx. Preventiva</div>
                    <div class="text-weight-bold text-warning-9">
                       {{ vehicle.next_maintenance_date ? formatDate(vehicle.next_maintenance_date) : `${vehicle.next_maintenance_km || '--'} h` }}
                    </div>
                 </div>
               </div>
             </div>
          </q-card-section>

          <q-card-actions align="right" class="q-px-md" v-if="authStore.isManager">
             <q-btn flat round dense size="sm" color="primary" icon="edit" @click.stop="openEditDialog(vehicle)" />
             <q-btn flat round dense size="sm" color="negative" icon="delete" @click.stop="promptToDelete(vehicle)" />
          </q-card-actions>
        </q-card>
      </div>
    </div>
    
    <div v-else class="text-center q-pa-xl text-grey-6">
        <q-icon name="precision_manufacturing" size="4em" />
        <div class="text-h6">Nenhuma máquina cadastrada</div>
    </div>

    <q-dialog v-model="isFormDialogOpen" persistent>
        <q-card style="width: 600px; max-width: 95vw;">
          <q-card-section class="row items-center">
            <div class="text-h6">{{ isEditing ? 'Editar Máquina' : 'Nova Máquina' }}</div>
            <q-space />
            <q-btn icon="close" flat round dense v-close-popup />
          </q-card-section>

          <q-form @submit.prevent="onFormSubmit">
            <q-card-section class="q-gutter-y-md">
              <div class="row q-col-gutter-md">
                 <div class="col-6">
                    <q-input outlined v-model="formData.brand" label="Fabricante (Ex: Romi) *" :rules="[val => !!val || 'Obrigatório']" dense />
                 </div>
                 <div class="col-6">
                    <q-input outlined v-model="formData.model" label="Modelo (Ex: D800) *" :rules="[val => !!val || 'Obrigatório']" dense />
                 </div>
              </div>
              
              <q-input outlined v-model="formData.license_plate" label="Cód. Patrimônio / TAG (Ex: CNC-01)" dense hint="Identificador único no SAP" />
              
              <div class="row q-col-gutter-md">
                 <div class="col-6">
                    <q-input outlined v-model.number="formData.year" type="number" label="Ano de Fabricação *" :rules="[val => !!val || 'Obrigatório']" dense />
                 </div>
                 <div class="col-6">
                    <q-input outlined v-model.number="formData.current_engine_hours" label="Horímetro Atual (h)" type="number" dense />
                 </div>
              </div>

              <div class="text-subtitle2 text-primary q-mt-sm">Plano de Manutenção Preventiva</div>
              <div class="row q-col-gutter-md">
                 <div class="col-6">
                    <q-input outlined v-model.number="formData.next_maintenance_km" label="A cada X horas (Ciclo)" type="number" dense hint="Ex: 500 para revisão a cada 500h" />
                 </div>
                 <div class="col-6">
                    <q-input 
                        outlined 
                        v-model="formData.next_maintenance_date" 
                        label="Próxima Data Limite" 
                        mask="##/##/####" 
                        dense 
                        hint="Formato: DD/MM/AAAA"
                    >
                        <template v-slot:append>
                            <q-icon name="event" class="cursor-pointer">
                            <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                                <q-date v-model="formData.next_maintenance_date" mask="DD/MM/YYYY">
                                <div class="row items-center justify-end">
                                    <q-btn v-close-popup label="OK" color="primary" flat />
                                </div>
                                </q-date>
                            </q-popup-proxy>
                            </q-icon>
                        </template>
                    </q-input>
                 </div>
              </div>
            </q-card-section>
            
            <q-card-actions align="right" class="q-pa-md">
              <q-btn flat label="Cancelar" v-close-popup />
              <q-btn type="submit" unelevated color="primary" label="Salvar" :loading="isSubmitting" />
            </q-card-actions>
          </q-form>
        </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useVehicleStore } from 'stores/vehicle-store';
import { useAuthStore } from 'stores/auth-store';
import { VehicleStatus, type Vehicle, type VehicleCreate, type VehicleUpdate } from 'src/models/vehicle-models';
import { format, parse, isValid } from 'date-fns';

const $q = useQuasar();
const vehicleStore = useVehicleStore();
const authStore = useAuthStore();
const router = useRouter();

const isFormDialogOpen = ref(false);
const isSubmitting = ref(false);
const editingVehicleId = ref<number | null>(null);
const isEditing = computed(() => editingVehicleId.value !== null);

// FormData tipado como Partial para flexibilidade no formulário
const formData = ref<Partial<Vehicle> & { next_maintenance_date?: string | null }>({});
const searchTerm = ref('');
const currentParams = { page: 1, rowsPerPage: 10, search: '' };

function getImageUrl(url: string | null | undefined) {
    if (!url) return null;
    return url.startsWith('http') ? url : `http://127.0.0.1:8000${url}`;
}

function translateStatus(status: VehicleStatus) {
    if (status === VehicleStatus.AVAILABLE) return 'PARADA / DISPONÍVEL';
    if (status === VehicleStatus.IN_USE) return 'EM OPERAÇÃO';
    if (status === VehicleStatus.MAINTENANCE) return 'MANUTENÇÃO';
    return status;
}

function getStatusColor(status: VehicleStatus) {
    if (status === VehicleStatus.AVAILABLE) return 'grey-7';
    if (status === VehicleStatus.IN_USE) return 'positive';
    if (status === VehicleStatus.MAINTENANCE) return 'negative';
    return 'grey';
}

function formatDate(dateStr: string) {
    if (!dateStr) return '--';
    try {
        return new Date(dateStr).toLocaleDateString('pt-BR');
    } catch {
        return dateStr;
    }
}

function handleCardClick(vehicle: Vehicle) {
    void router.push(`/vehicles/${vehicle.id}`);
}

function openCreateDialog() {
    editingVehicleId.value = null;
    formData.value = {
        brand: '',
        model: '',
        year: new Date().getFullYear(),
        status: VehicleStatus.AVAILABLE,
        current_engine_hours: 0,
        current_km: 0, 
        license_plate: '',
        identifier: '',
        next_maintenance_date: null // Inicializa nulo
    };
    isFormDialogOpen.value = true;
}

function openEditDialog(vehicle: Vehicle) {
    editingVehicleId.value = vehicle.id;
    // Clona o objeto e formata a data para DD/MM/YYYY para o input visual
    const nextDate = vehicle.next_maintenance_date 
        ? format(new Date(vehicle.next_maintenance_date), 'dd/MM/yyyy') 
        : null;

    formData.value = { 
        ...vehicle,
        next_maintenance_date: nextDate 
    };
    isFormDialogOpen.value = true;
}

// --- FUNÇÃO DE CONVERSÃO DE DATA (DD/MM/YYYY -> YYYY-MM-DD) ---
function convertDateForBackend(dateStr: string | null | undefined): string | null {
    if (!dateStr) return null;
    // Se já estiver em formato ISO (YYYY-MM-DD), retorna direto
    if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) return dateStr;
    
    try {
        // Tenta parsear DD/MM/YYYY
        const parsedDate = parse(dateStr, 'dd/MM/yyyy', new Date());
        if (isValid(parsedDate)) {
            return format(parsedDate, 'yyyy-MM-dd');
        }
    } catch (e) {
        console.error('Erro ao converter data:', e);
    }
    return null; // Retorna null se falhar
}

async function onFormSubmit() {
    isSubmitting.value = true;
    try {
        const rawData = { ...formData.value };

        // Prepara o payload convertendo a data
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const payload: any = {
            brand: rawData.brand,
            model: rawData.model,
            year: Number(rawData.year),
            status: rawData.status,
            
            license_plate: rawData.license_plate ? rawData.license_plate : null,
            identifier: rawData.identifier ? rawData.identifier : null,
            
            current_engine_hours: Number(rawData.current_engine_hours || 0),
            current_km: Number(rawData.current_km || 0),
            
            // AQUI ESTÁ A CORREÇÃO PRINCIPAL
            next_maintenance_date: convertDateForBackend(rawData.next_maintenance_date),
            next_maintenance_km: rawData.next_maintenance_km ? Number(rawData.next_maintenance_km) : null,
        };

        const params = { ...currentParams, search: searchTerm.value };

        if (isEditing.value && editingVehicleId.value) {
            await vehicleStore.updateVehicle(editingVehicleId.value, payload as VehicleUpdate, params);
        } else {
            await vehicleStore.addNewVehicle(payload as VehicleCreate, params);
        }
        
        isFormDialogOpen.value = false;
        await vehicleStore.fetchAllVehicles(params);
        $q.notify({ type: 'positive', message: 'Máquina salva com sucesso!' });

    } catch (error: any) { // eslint-disable-line @typescript-eslint/no-explicit-any
        console.error('Erro no submit:', error);
        const msg = error.response?.data?.detail 
            ? JSON.stringify(error.response.data.detail) 
            : 'Erro ao salvar (verifique campos obrigatórios e datas)';
        
        $q.notify({ type: 'negative', message: msg, timeout: 5000 });
    } finally {
        isSubmitting.value = false;
    }
}

function promptToDelete(vehicle: Vehicle) {
    $q.dialog({
        title: 'Confirmar', message: 'Excluir esta máquina?', cancel: true
    }).onOk(() => {
        void (async () => {
             const params = { ...currentParams, search: searchTerm.value };
             await vehicleStore.deleteVehicle(vehicle.id, params);
             await vehicleStore.fetchAllVehicles(params);
        })();
    });
}

onMounted(() => {
    void vehicleStore.fetchAllVehicles({ ...currentParams, search: searchTerm.value });
});
</script>

<style scoped>
.vehicle-card { cursor: pointer; transition: transform 0.2s; }
.vehicle-card:hover { transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
</style>
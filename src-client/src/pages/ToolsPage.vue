<template>
  <q-page padding>
    <div class="flex items-center justify-between q-mb-md">
      <div>
        <h1 class="text-h5 text-weight-bold q-my-none flex items-center">
          <q-icon name="handyman" class="q-mr-sm text-primary" />
          Gerenciamento de Ferramentas
        </h1>
        <div class="text-caption text-grey-7">Moldes, Matrizes e Dispositivos Auxiliares</div>
      </div>
      
      <q-btn
        v-if="authStore.isManager"
        @click="openDialog()"
        color="primary"
        icon="add"
        label="Nova Ferramenta"
        unelevated
      />
    </div>

    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="row q-col-gutter-md">
          <div class="col-12 col-sm-6">
            <q-input
              outlined
              dense
              debounce="300"
              v-model="searchTerm"
              placeholder="Buscar por código, nome ou fabricante..."
            >
              <template v-slot:prepend><q-icon name="search" /></template>
            </q-input>
          </div>
          <div class="col-6 col-sm-3">
            <q-select
              outlined
              dense
              v-model="filterStatus"
              :options="statusOptions"
              label="Status"
              emit-value
              map-options
              clearable
            >
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.label }}</q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
          </div>
          <div class="col-6 col-sm-3">
            <q-select
              outlined
              dense
              v-model="filterType"
              :options="typeOptions"
              label="Categoria"
              clearable
              :disable="typeOptions.length === 0"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>

    <div v-if="implementStore.isLoading" class="row q-col-gutter-md">
      <div v-for="n in 4" :key="n" class="col-xs-12 col-sm-6 col-md-4 col-lg-3">
        <q-card flat bordered><q-skeleton height="150px" square /></q-card>
      </div>
    </div>

    <div v-else-if="filteredImplements.length > 0" class="row q-col-gutter-md">
      <div v-for="tool in filteredImplements" :key="tool.id" class="col-xs-12 col-sm-6 col-md-4 col-lg-3">
        <HoverCard>
          <q-card-section>
            <div class="row items-start justify-between no-wrap q-mb-xs">
              <div class="text-h6 ellipsis">{{ tool.name }}</div>
              <q-badge
                :color="getStatusColor(tool.status)"
                :label="getStatusLabel(tool.status)"
                class="q-ml-sm shadow-1"
              />
            </div>
            
            <div class="text-subtitle2 text-grey-8">
               {{ tool.brand }} <span v-if="tool.model">- {{ tool.model }}</span>
            </div>
            
            <div v-if="tool.type" class="row items-center q-mt-xs">
               <q-icon name="category" size="xs" class="q-mr-xs text-grey-6" />
               <span class="text-caption text-primary text-weight-medium">{{ tool.type }}</span>
            </div>
          </q-card-section>

          <q-separator inset />

          <q-card-section class="q-pt-sm">
            <div class="row q-col-gutter-y-xs text-caption text-grey-7">
               <div class="col-12 flex items-center">
                  <q-icon name="calendar_today" size="xs" class="q-mr-xs"/> 
                  Ano Fab.: {{ tool.year || '--' }}
               </div>
               <div class="col-12 flex items-center" v-if="tool.identifier">
                  <q-icon name="qr_code" size="xs" class="q-mr-xs"/> 
                  Tag/Patrimônio: <strong>{{ tool.identifier }}</strong>
               </div>
               <div class="col-12 flex items-center" v-if="tool.acquisition_value">
                  <q-icon name="attach_money" size="xs" class="q-mr-xs"/> 
                  Valor: {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(tool.acquisition_value) }}
               </div>
            </div>
          </q-card-section>

          <q-separator />
          
          <q-card-actions align="right">
            <template v-if="authStore.isManager">
              <q-btn flat dense round icon="edit" color="primary" @click.stop="openDialog(tool)">
                 <q-tooltip>Editar</q-tooltip>
              </q-btn>
              <q-btn flat dense round icon="delete" color="negative" @click.stop="promptToDelete(tool)">
                 <q-tooltip>Excluir</q-tooltip>
              </q-btn>
            </template>
          </q-card-actions>
        </HoverCard>
      </div>
    </div>

    <div v-else class="text-center q-pa-xl text-grey-7">
      <q-icon name="handyman" size="4em" color="grey-4" />
      <div class="text-h6 q-mt-md">Nenhuma ferramenta encontrada</div>
      <p class="text-grey-5" v-if="searchTerm || filterStatus || filterType">
        Tente ajustar os filtros de busca.
      </p>
      <p class="text-grey-5" v-else>
        Cadastre seus moldes, matrizes e ferramentas especiais.
      </p>
      
      <q-btn
        v-if="authStore.isManager && !searchTerm && !filterStatus && !filterType"
        @click="openDialog()"
        color="primary"
        label="Cadastrar Ferramenta"
        unelevated
        class="q-mt-md"
      />
    </div>

    <q-dialog v-model="isDialogOpen">
      <q-card style="width: 500px; max-width: 90vw;">
        <q-card-section class="row items-center bg-grey-1">
          <div class="text-h6">{{ isEditing ? 'Editar Ferramenta' : 'Nova Ferramenta' }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-form @submit.prevent="handleSubmit">
          <q-card-section class="q-gutter-y-md">
            
            <q-input 
                outlined 
                v-model="formData.name" 
                label="Nome / Descrição *" 
                hint="Ex: Molde Injeção Tampa D80"
                :rules="[val => !!val || 'Campo obrigatório']" 
            />

            <div class="row q-col-gutter-md">
              <div class="col-6">
                <q-input outlined v-model="formData.brand" label="Fabricante *" :rules="[val => !!val || 'Campo obrigatório']" />
              </div>
              <div class="col-6">
                <q-input outlined v-model="formData.model" label="Modelo *" :rules="[val => !!val || 'Campo obrigatório']" />
              </div>
            </div>
            
            <div class="row q-col-gutter-md">
                <div class="col-6">
                    <q-input 
                      outlined 
                      v-model="formData.type" 
                      label="Categoria" 
                      hint="Ex: Molde, Matriz, Dispositivo"
                    />
                </div>
                <div class="col-6">
                    <q-input outlined v-model.number="formData.year" type="number" label="Ano Fabricação" />
                </div>
            </div>

            <q-input outlined v-model="formData.identifier" label="Cód. Patrimônio / Tag" />

            <div class="row q-col-gutter-md">
              <div class="col-6">
                <q-input 
                  outlined 
                  v-model="formData.acquisition_date" 
                  label="Data Aquisição"
                  type="date"
                  stack-label
                />
              </div>
              <div class="col-6">
                <q-input 
                  outlined 
                  v-model.number="formData.acquisition_value" 
                  label="Valor (R$)" 
                  type="number"
                  prefix="R$"
                  :step="0.01"
                />
              </div>
            </div>

            <q-input 
              outlined 
              v-model="formData.notes" 
              label="Observações Técnicas" 
              type="textarea" 
              autogrow 
            />

          </q-card-section>
          
          <q-separator />
          
          <q-card-actions align="right" class="q-pa-md">
            <q-btn flat label="Cancelar" v-close-popup color="grey-7" />
            <q-btn type="submit" unelevated color="primary" label="Salvar Dados" :loading="isSubmitting" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useQuasar } from 'quasar';
// Reutilizamos a store existente, mas a interface muda visualmente
import { useImplementStore } from 'stores/implement-store';
import { useAuthStore } from 'stores/auth-store';
import type { Implement, ImplementCreate, ImplementUpdate } from 'src/models/implement-models';
import HoverCard from 'components/HoverCard.vue';
import { ImplementStatus } from 'src/models/implement-models';

const $q = useQuasar();
const implementStore = useImplementStore();
const authStore = useAuthStore();

const isDialogOpen = ref(false);
const isSubmitting = ref(false);
const editingImplement = ref<Implement | null>(null);
const isEditing = computed(() => !!editingImplement.value);

// Filtros
const searchTerm = ref('');
const filterStatus = ref<ImplementStatus | null>(null);
const filterType = ref<string | null>(null);

const formData = ref<Partial<Implement>>({});

// Opções de Status (Traduzido para Indústria)
const statusOptions = [
  { label: 'Disponível', value: ImplementStatus.AVAILABLE },
  { label: 'Em Uso (Acoplado)', value: ImplementStatus.IN_USE },
  { label: 'Em Manutenção', value: ImplementStatus.MAINTENANCE }
];

// Opções de Tipo Dinâmicas
const typeOptions = computed(() => {
  const types = implementStore.implementList
    .map(impl => impl.type)
    .filter((type): type is string => !!type);
  return [...new Set(types)].sort();
});

// Lógica de Filtragem
const filteredImplements = computed(() => {
  const lowerCaseSearch = searchTerm.value.toLowerCase();

  return implementStore.implementList.filter(implement => {
    const searchMatch = !searchTerm.value || (
      implement.name.toLowerCase().includes(lowerCaseSearch) ||
      implement.brand.toLowerCase().includes(lowerCaseSearch) ||
      implement.model.toLowerCase().includes(lowerCaseSearch) ||
      (implement.identifier && implement.identifier.toLowerCase().includes(lowerCaseSearch)) ||
      (implement.type && implement.type.toLowerCase().includes(lowerCaseSearch))
    );

    const statusMatch = !filterStatus.value || implement.status === filterStatus.value;
    const typeMatch = !filterType.value || implement.type === filterType.value;

    return searchMatch && statusMatch && typeMatch;
  });
});

function getStatusColor(status: ImplementStatus) {
  switch (status) {
    case ImplementStatus.AVAILABLE: return 'positive';
    case ImplementStatus.IN_USE: return 'primary'; // Azul para 'Em Uso' industrial
    case ImplementStatus.MAINTENANCE: return 'negative';
    default: return 'grey';
  }
}

function getStatusLabel(status: ImplementStatus) {
  switch (status) {
    case ImplementStatus.AVAILABLE: return 'Disponível';
    case ImplementStatus.IN_USE: return 'Em Produção';
    case ImplementStatus.MAINTENANCE: return 'Manutenção';
    default: return status;
  }
}

function resetForm() {
  editingImplement.value = null;
  formData.value = {
    name: '', 
    brand: '', 
    model: '', 
    type: '',
    year: new Date().getFullYear(), 
    identifier: '',
    acquisition_date: null,
    acquisition_value: null,
    notes: ''
  };
}

function openDialog(implement: Implement | null = null) {
  if (implement) {
    editingImplement.value = implement;
    formData.value = { ...implement };
  } else {
    resetForm();
  }
  isDialogOpen.value = true;
}

async function handleSubmit() {
  isSubmitting.value = true;
  try {
    const payload = { ...formData.value };
    // Sanitização
    if (!payload.acquisition_date) payload.acquisition_date = null;
    if (!payload.acquisition_value) payload.acquisition_value = null;
    if (!payload.notes) payload.notes = null;
    if (!payload.type) payload.type = null;
    if (!payload.identifier) payload.identifier = null;

    if (isEditing.value && editingImplement.value) {
      await implementStore.updateImplement(editingImplement.value.id, payload as ImplementUpdate);
    } else {
      await implementStore.addImplement(payload as ImplementCreate);
    }
    isDialogOpen.value = false;
    $q.notify({ type: 'positive', message: 'Salvo com sucesso!' });
  } catch (e) {
      console.error(e); // Adicione esta linha para usar 'e'
      $q.notify({ type: 'negative', message: 'Erro ao salvar.' });
  } finally {
    isSubmitting.value = false;
  }
}

function promptToDelete(implement: Implement) {
  $q.dialog({
    title: 'Confirmar Exclusão',
    message: `Deseja realmente remover a ferramenta "${implement.name}"?`,
    cancel: true,
    persistent: false,
    ok: { label: 'Excluir', color: 'negative', unelevated: true }
  }).onOk(() => {
    void implementStore.deleteImplement(implement.id);
  });
}

onMounted(() => {
  void implementStore.fetchAllImplementsForManagement();
});
</script>
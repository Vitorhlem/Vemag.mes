<template>
  <q-page padding>
    
    
    <div class="flex items-center justify-between q-mb-md">
      <h1 class="text-h5 text-weight-bold q-my-none">Gestão de Equipe & Acessos</h1>
    </div>
    <div class="flex items-center justify-between q-mb-md">
      <h1 class="text-h5 text-weight-bold q-my-none">Gestão de Equipe & Acessos</h1>
      
      <q-btn 
        color="primary" 
        icon="person_add" 
        label="Novo Colaborador" 
        @click="openCreateDialog" 
        unelevated
      />
    </div>
     
    <q-card flat bordered>
      <q-table
        @row-click="goToUserDetails"
        class="cursor-pointer"
        :rows="userStore.users"
        :columns="columns"
        row-key="id"
        :loading="userStore.isLoading"
        no-data-label="Nenhum usuário cadastrado"
        :pagination="{ rowsPerPage: 10 }"
      >
        <template v-slot:body-cell-role="props">
          <q-td :props="props">
             <q-badge :color="getRoleColor(props.value)" class="q-py-xs q-px-sm shadow-1">
                <q-icon :name="getRoleIcon(props.value)" class="q-mr-xs" size="14px" />
                {{ getRoleLabel(props.value) }}
             </q-badge>
          </q-td>
        </template>

        <template v-slot:body-cell-is_active="props">
          <q-td :props="props">
            <q-icon :name="props.value ? 'check_circle' : 'cancel'" :color="props.value ? 'positive' : 'grey'" size="sm" class="q-mr-xs" />
            <span>{{ props.value ? 'Ativo' : 'Inativo' }}</span>
          </q-td>
        </template>

        <template v-slot:body-cell-actions="props">
          <q-td :props="props">
              <q-btn @click.stop="openEditDialog(props.row)" flat round dense icon="edit" color="primary" class="q-mr-sm" />
            <q-btn @click.stop="promptToDelete(props.row)" flat round dense icon="delete" color="negative" />
          </q-td>
        </template>
      </q-table>
    </q-card>

    
    <q-dialog v-model="isFormDialogOpen">
      <q-card style="width: 500px; max-width: 90vw;" :dark="$q.dark.isActive">
        <q-card-section class="row items-center q-pb-none bg-grey-2 q-pa-md">
          <div class="text-h6 text-dark">{{ isEditing ? 'Editar Colaborador' : 'Novo Colaborador' }}</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup color="dark" />
        </q-card-section>

        <q-form @submit.prevent="onFormSubmit">
          <q-card-section class="q-gutter-y-md q-pt-lg">
            
            <q-input outlined v-model="formData.full_name" label="Nome Completo *" :rules="[val => !!val || 'Campo obrigatório']" bg-color="white">
                <template v-slot:prepend><q-icon name="person" /></template>
            </q-input>

            <q-input outlined v-model="formData.job_title" label="Cargo / Função" hint="Ex: Operador CNC, Supervisor" bg-color="white">
                <template v-slot:prepend><q-icon name="badge" /></template>
            </q-input>
            
            <q-input outlined v-model="formData.email" type="email" label="E-mail / Login *" :rules="[val => !!val || 'Campo obrigatório']" bg-color="white">
                <template v-slot:prepend><q-icon name="email" /></template>
            </q-input>
            
            <q-input outlined v-model="formData.employee_id" label="Matrícula / Crachá" hint="Usado para login rápido no Kiosk" bg-color="white">
                <template v-slot:prepend><q-icon name="pin" /></template>
            </q-input>
            
            <q-select
              outlined
              v-model="formData.role"
              :options="roleOptions"
              label="Perfil de Acesso *"
              emit-value
              map-options
              bg-color="white"
              :rules="[val => !!val || 'Selecione uma função']"
            >
              <template v-slot:prepend><q-icon name="security" /></template>
              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section avatar>
                    <q-avatar :icon="scope.opt.icon" :text-color="scope.opt.color" color="grey-2" size="md" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label class="text-weight-bold">{{ scope.opt.label }}</q-item-label>
                    <q-item-label caption>{{ scope.opt.description }}</q-item-label>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>

            <q-separator class="q-my-md" />

            <q-input outlined v-model="formData.password" type="password" :label="isEditing ? 'Nova Senha (opcional)' : 'Senha *'" :rules="isEditing ? [] : [val => !!val || 'Campo obrigatório']" bg-color="white">
                <template v-slot:prepend><q-icon name="lock" /></template>
            </q-input>
            
            <div v-if="isEditing" class="bg-grey-2 q-pa-sm rounded-borders">
                <q-toggle v-model="formData.is_active" label="Acesso Ativo" color="positive" />
            </div>

          </q-card-section>
          
          <q-card-actions align="right" class="bg-grey-1 q-pa-md">
            <q-btn flat label="Cancelar" color="grey-8" v-close-popup />
            <q-btn type="submit" unelevated color="primary" label="Salvar Dados" :loading="isSubmitting" />
          </q-card-actions>
        </q-form>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useQuasar, type QTableColumn } from 'quasar';
import { useUserStore } from 'stores/user-store';
import { useRouter } from 'vue-router';
import { isAxiosError } from 'axios';
import type { User } from 'src/models/auth-models';
import type { UserCreate, UserUpdate } from 'src/models/user-models';

const $q = useQuasar();
const userStore = useUserStore();
const router = useRouter();

const isFormDialogOpen = ref(false);
const isSubmitting = ref(false);
const editingUserId = ref<number | null>(null);

const isEditing = computed(() => editingUserId.value !== null);


// --- OPÇÕES DE CARGO (ROLES) - MES ---
const roleOptions = computed(() => {
  const options = [
    { label: 'Colaborador (Padrão)', value: 'operator', icon: 'badge', color: 'green-7', description: 'Acesso Básico' },
    { label: 'Manutenção', value: 'maintenance', icon: 'build', color: 'orange-9', description: 'Recebe chamados de quebra' },
    { label: 'Qualidade', value: 'quality', icon: 'verified', color: 'purple-9', description: 'Aprova peças e inspeções' },
    { label: 'Logística Interna', value: 'logistics', icon: 'forklift', color: 'brown', description: 'Abastecimento de linha' },
    { label: 'PCP / Planejamento', value: 'pcp', icon: 'schedule', color: 'teal', description: 'Visualiza cronograma' },
    { label: 'Gerente / Supervisor', value: 'admin', icon: 'admin_panel_settings', color: 'red-10', description: 'Acesso total aos indicadores' }
  ];

  return options;
});

const formData = ref<Partial<UserCreate & UserUpdate>>({});

// --- COLUNAS DA TABELA ---
const columns: QTableColumn[] = [
  { name: 'full_name', label: 'Nome', field: 'full_name', align: 'left', sortable: true },
  { name: 'job_title', label: 'Cargo', field: 'job_title', align: 'left', sortable: true }, // <--- NOVA COLUNA
  { name: 'employee_id', label: 'Matrícula', field: 'employee_id', align: 'left', sortable: true },
  { name: 'role', label: 'Perfil de Acesso', field: 'role', align: 'left', sortable: true },
  { name: 'email', label: 'Login', field: 'email', align: 'left', sortable: true },
  { name: 'is_active', label: 'Status', field: 'is_active', align: 'center' },
  { name: 'actions', label: '', field: 'actions', align: 'right' },
];

// Helpers
function getRoleLabel(roleVal: string) {
    const opt = roleOptions.value.find(r => r.value === roleVal || r.value === roleVal.toLowerCase());
    return opt ? opt.label : roleVal;
}

function getRoleColor(roleVal: string) {
    const opt = roleOptions.value.find(r => r.value === roleVal || r.value === roleVal.toLowerCase());
    return opt ? opt.color : 'grey';
}

function getRoleIcon(roleVal: string) {
    const opt = roleOptions.value.find(r => r.value === roleVal || r.value === roleVal.toLowerCase());
    return opt ? opt.icon : 'person';
}

function goToUserDetails(evt: Event, row: User) {
  void router.push({ name: 'user-stats', params: { id: row.id } });
}

function resetForm() {
  editingUserId.value = null;

  formData.value = { 
    full_name: '', 
    email: '', 
    role: 'operator', 
    password: '', 
    is_active: true, 
    employee_id: '',
    job_title: '' 
  };
}


function openEditDialog(user: User) {
  resetForm();
  editingUserId.value = user.id;
  formData.value = { 
    ...user, 
    password: '' 
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any; 
  isFormDialogOpen.value = true;
}

function openCreateDialog() {
  resetForm(); // Limpa o formulário e garante que não está editando
  isFormDialogOpen.value = true;
}

async function onFormSubmit() {
  isSubmitting.value = true;
  try {
    const payload = { ...formData.value };

    if (isEditing.value && !payload.password) delete payload.password;

    if (isEditing.value && editingUserId.value) {
      await userStore.updateUser(editingUserId.value, payload as UserUpdate);
      $q.notify({ type: 'positive', message: 'Dados atualizados!' });
    } else {
      await userStore.addNewUser(payload as UserCreate);
      $q.notify({ type: 'positive', message: 'Colaborador cadastrado!' });
      
    }
    isFormDialogOpen.value = false;
  } catch (error) {
    let message = 'Erro ao salvar.';
    if (isAxiosError(error) && error.response?.data?.detail) {
      message = error.response.data.detail as string;
    }
    $q.notify({ type: 'negative', message });
  } finally {
    isSubmitting.value = false;
  }
}

function promptToDelete(user: User) {
  $q.dialog({
    title: 'Excluir Usuário',
    message: `Confirma exclusão de ${user.full_name}?`,
    cancel: true,
    ok: { label: 'Excluir', color: 'negative' }
  }).onOk(() => {
    void (async () => {
        await userStore.deleteUser(user.id);
                $q.notify({ type: 'positive', message: 'Excluído com sucesso.' });
    })();
  });
}

onMounted(async () => {
  await userStore.fetchAllUsers();
});
</script>
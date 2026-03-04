import { defineStore } from 'pinia';
import { Dark } from 'quasar';
import { ref } from 'vue';
import { api } from 'boot/axios';
import { Notify } from 'quasar';
import type { 
  OrganizationPublic,  
  OrganizationUpdate 
} from 'src/models/organization-models';

export const useSettingsStore = defineStore('settings', () => {
  // --- Dark Mode State ---
  const darkMode = ref<boolean | 'auto'>(
    JSON.parse(localStorage.getItem('darkMode') || '"auto"')
  );

  function setDarkMode(value: boolean | 'auto') {
    darkMode.value = value;
    Dark.set(value);
    localStorage.setItem('darkMode', JSON.stringify(value));
  }

  function init() {
    Dark.set(darkMode.value);
  }

  

  // --- ORGANIZATION STATE (NOVO) ---
  const organizationSettings = ref<OrganizationPublic | null>(null);
  const isLoadingOrgSettings = ref(false);
  // --------------------------------


  // --- AÇÕES PARA ORGANIZAÇÃO (NOVO) ---
  async function fetchOrganizationSettings() {
    isLoadingOrgSettings.value = true;
    try {
      const response = await api.get<OrganizationPublic>('/settings/organization');
      organizationSettings.value = response.data;
    } catch (error) {
      console.error('Erro ao buscar dados da organização:', error);
      Notify.create({ type: 'negative', message: 'Erro ao carregar dados da empresa.' });
    } finally {
      isLoadingOrgSettings.value = false;
    }
  }

  async function updateOrganizationSettings(payload: OrganizationUpdate) {
    isLoadingOrgSettings.value = true;
    try {
      const response = await api.put<OrganizationPublic>('/settings/organization', payload);
      organizationSettings.value = response.data;
      Notify.create({ type: 'positive', message: 'Dados da empresa atualizados com sucesso!' });
    } catch (error) {
      console.error('Erro ao atualizar organização:', error);
      Notify.create({ type: 'negative', message: 'Erro ao salvar dados da empresa.' });
    } finally {
      isLoadingOrgSettings.value = false;
    }
  }
  // -------------------------------------

  return {
    darkMode,
    setDarkMode,
    init,
    organizationSettings,
    isLoadingOrgSettings,
    fetchOrganizationSettings,
    updateOrganizationSettings
  };
});
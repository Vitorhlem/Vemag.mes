import { boot } from 'quasar/wrappers';
import { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'; 
import { useAuthStore } from 'stores/auth-store';
import api from 'src/services/api';

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $api: AxiosInstance;
  }
}

export default boot(({ app, store }) => {
  // Puxa o IP dinamicamente baseado no ambiente (.env)
  api.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
  
  api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore(store);
    
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`;
    }
    
    return config;
  });

  app.config.globalProperties.$api = api;
});

export { api };
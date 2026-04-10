import axios from 'axios';

const getBaseURL = () => {
    // Tenta ler o .env, se falhar, assume que é a máquina local
    return import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
};

const api = axios.create({
    baseURL: getBaseURL(),
    withCredentials: true,
});

export default api;
export { api };
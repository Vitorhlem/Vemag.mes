import axios from 'axios';

const getBaseURL = () => {
    // Tiramos a porta :8000 daqui também!
    return import.meta.env.VITE_API_URL || 'http://192.168.0.5/api/v1';
};

const api = axios.create({
    baseURL: getBaseURL(),
    withCredentials: true,
});

export default api;
export { api };
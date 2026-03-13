import axios from 'axios';

const getBaseURL = () => {
    return import.meta.env.VITE_API_URL || 'http://192.168.0.5:8000/api/v1';
};

const api = axios.create({
    baseURL: getBaseURL(),
    withCredentials: true,
});

export default api;
export { api };
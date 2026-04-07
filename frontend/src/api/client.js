import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: API_BASE });

export const sendChat = (msg, userId) => api.post('/api/chat', { message: msg, user_id: userId });
export const getTasks = (userId) => api.get(`/api/tasks?user_id=${userId}`);
export const createTask = (data) => api.post('/api/tasks', data);
export const getEvents = (userId) => api.get(`/api/calendar/events?user_id=${userId}`);
export const getInsights = (userId) => api.get(`/api/insights?user_id=${userId}`);
export const runWorkflow = (type, userId) => api.post(`/api/workflows/${type}`, { user_id: userId });

export default api;

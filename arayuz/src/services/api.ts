import axios from 'axios';

// Backend REST API adresi
const API_BASE_URL = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Oturum Token'ı varsa istek başlıklarına otomatik ekler
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth Servis Katmanı
export const authService = {
  login: async (username: string, password: string) => {
    const response = await api.post('/login', { username, password });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
};

// Katılımcı Servis Katmanı
export const participantService = {
  getParticipants: async () => {
    const response = await api.get('/katilimcilar');
    return response.data;
  },
  getAll: async () => {
    const response = await api.get('/katilimcilar');
    return response.data;
  },
  create: async (data: { ad_soyad: string; tc_no?: string; yas?: number; cinsiyet?: string }) => {
    const response = await api.post('/katilimcilar', data);
    return response.data;
  },
};

// Oturum Servis Katmanı
export const sessionService = {
  getSessions: async () => {
    const response = await api.get('/oturumlar');
    return response.data;
  },
  createSession: async (data: {
    katilimci_id: number;
    test_adi?: string;
    notlar?: string;
    ortalama_bpm?: number;
    ortalama_gsr?: number;
    yalan_skoru?: number;
  }) => {
    const response = await api.post('/oturumlar', data);
    return response.data;
  },
  saveSession: async (data: {
    katilimci_id: number;
    test_adi?: string;
    notlar?: string;
    ortalama_bpm?: number;
    ortalama_gsr?: number;
    yalan_skoru?: number;
  }) => {
    const response = await api.post('/oturumlar', data);
    return response.data;
  },
  finishSession: async (
    kayitId: string,
    data: { ortalama_bpm: number; ortalama_gsr: number; sure_sn: number; yalan_skoru?: number },
  ) => {
    const response = await api.put(`/oturumlar/kayit/${kayitId}`, data);
    return response.data;
  },
};
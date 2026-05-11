// fe/src/features/auth/api.js
import { api } from '@/lib/Axios.js';

const BACKEND_URL = import.meta.env.VITE_API_BACKEND_URL || '';

export const INSTAGRAM_AUTH_PURPOSE = {
  LOGIN: 'login',
  ONBOARDING: 'onboarding',
};

export const authApi = {
  loginWithInstagram(purpose = INSTAGRAM_AUTH_PURPOSE.LOGIN) {
    sessionStorage.setItem('instagramAuthPurpose', purpose);

    window.location.href = `${BACKEND_URL}/api/v1/oauth2/authorization/instagram`;
  },

  getMe() {
    return api.get('/api/v1/users/me');
  },

  logout() {
    return api.post('/api/v1/users/logout');
  },

  deleteAccount() {
    return api.delete('/api/v1/users/me');
  },
};

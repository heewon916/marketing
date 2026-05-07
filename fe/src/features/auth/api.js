import { api } from '@/lib/Axios.js';

const BACKEND_URL = import.meta.env.VITE_API_BACKEND_URL || '';

export const INSTAGRAM_AUTH_PURPOSE = {
  LOGIN: 'login',
  ONBOARDING: 'onboarding',
};

export const authApi = {
  loginWithInstagram(purpose = INSTAGRAM_AUTH_PURPOSE.LOGIN) {
    sessionStorage.setItem('instagramAuthPurpose', purpose);

    window.location.href = `${BACKEND_URL}/api/v1/users/instagram`;
  },

  verifyPosPin(pin) {
    return api.post('/api/v1/onboarding/pin/verify', {
      pin,
    });
  },

  syncPosStore(merchantId) {
    return api.post('/api/v1/onboarding/toss/sync', {
      merchantId,
    });
  },
};

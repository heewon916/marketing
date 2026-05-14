import { api } from '@/lib/Axios.js';

export const onboardingApi = {
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

  searchStores(keyword) {
    return api.get('/api/v1/onboarding/search', {
      params: { keyword },
    });
  },

  getStoreDetail(placeId) {
    return api.get(`/api/v1/onboarding/search/${placeId}`);
  },

  completeOnboarding(storeId, payload) {
    return api.put(`/api/v1/onboarding/store/${storeId}`, payload);
  },
};

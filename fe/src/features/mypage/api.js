import { api } from '@/lib/Axios.js';

export const mypageApi = {
  getMyInfo() {
    return api.get('/api/v1/users/me');
  },

  updateMyInfo(data) {
    return api.patch('/api/v1/users/me', data);
  },

  syncInstagramProfile() {
    return api.post('/api/v1/users/me/instagram/sync');
  },
};

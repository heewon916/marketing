import { api } from '@/lib/Axios.js';

export const mypageApi = {
  getMyInfo() {
    return api.get('/api/v1/users/me');
  },
};

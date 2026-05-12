import { api } from '@/lib/Axios.js';

export const mypageApi = {
  // 마이페이지
  getMyInfo() {
    return api.get('/api/v1/users/me');
  },

  updateMyInfo(data) {
    return api.patch('/api/v1/users/me', data);
  },

  syncInstagramProfile() {
    return api.post('/api/v1/users/me/instagram/sync');
  },

  // 통계
  getWeeklyReach() {
    return api.get('/api/v1/analytics/reach');
  },

  getWeeklyVisitIntent() {
    return api.get('/api/v1/analytics/visit-intent');
  },

  getWeeklyAchievement() {
    return api.get('/api/v1/analytics/achievement');
  },
};

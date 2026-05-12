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
    const authUrl = `${BACKEND_URL}/api/v1/oauth2/authorization/instagram`;
    
    // 팝업 창에서 Instagram 로그인 진행
    const width = 500;
    const height = 700;
    const left = window.screenX + (window.outerWidth - width) / 2;
    const top = window.screenY + (window.outerHeight - height) / 2;
    
    const popup = window.open(
      authUrl,
      'instagram-login',
      `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );
    
    // 팝업 창 모니터링
    return new Promise((resolve, reject) => {
      const checkPopupClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkPopupClosed);
          // 로그인 완료 후 사용자 정보 재조회
          api.get('/api/v1/users/me')
            .then(resolve)
            .catch(reject);
        }
      }, 500);
      
      // 타임아웃 설정 (5분)
      setTimeout(() => {
        clearInterval(checkPopupClosed);
        if (popup && !popup.closed) popup.close();
        reject(new Error('로그인 시간이 초과되었습니다'));
      }, 5 * 60 * 1000);
    });
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

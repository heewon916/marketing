// fe/src/features/auth/api.js
import { api } from '@/lib/Axios.js';

const BACKEND_URL = import.meta.env.VITE_API_BACKEND_URL || '';

export const INSTAGRAM_AUTH_PURPOSE = {
  LOGIN: 'login',
  ONBOARDING: 'onboarding',
};

const INSTAGRAM_AUTH_POPUP = {
  WIDTH: 500,
  HEIGHT: 700,
  CHECK_INTERVAL: 500,
  TIMEOUT: 5 * 60 * 1000,
};

export const authApi = {
  loginWithInstagram(purpose = INSTAGRAM_AUTH_PURPOSE.LOGIN) {
    sessionStorage.setItem('instagramAuthPurpose', purpose);

    const authUrl = `${BACKEND_URL}/api/v1/oauth2/authorization/instagram`;

    const width = INSTAGRAM_AUTH_POPUP.WIDTH;
    const height = INSTAGRAM_AUTH_POPUP.HEIGHT;
    const left = window.screenX + (window.outerWidth - width) / 2;
    const top = window.screenY + (window.outerHeight - height) / 2;

    const popup = window.open(
      authUrl,
      'instagram-login',
      `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
    );

    if (!popup) {
      return Promise.reject(
        new Error('팝업이 차단되었습니다. 브라우저 팝업 허용 후 다시 시도해주세요.')
      );
    }

    popup.focus();

    return new Promise((resolve, reject) => {
      let isFinished = false;

      const cleanup = (intervalId, timeoutId) => {
        clearInterval(intervalId);
        clearTimeout(timeoutId);
      };

      const finish = async (intervalId, timeoutId) => {
        if (isFinished) return;

        isFinished = true;
        cleanup(intervalId, timeoutId);

        try {
          const response = await api.get('/api/v1/users/me');
          resolve(response);
        } catch (error) {
          reject(error);
        }
      };

      const intervalId = setInterval(() => {
        if (popup.closed) {
          finish(intervalId, timeoutId);
        }
      }, INSTAGRAM_AUTH_POPUP.CHECK_INTERVAL);

      const timeoutId = setTimeout(() => {
        if (isFinished) return;

        isFinished = true;
        cleanup(intervalId, timeoutId);

        if (!popup.closed) {
          popup.close();
        }

        reject(new Error('로그인 시간이 초과되었습니다.'));
      }, INSTAGRAM_AUTH_POPUP.TIMEOUT);
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

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { INSTAGRAM_AUTH_PURPOSE } from '@/features/auth/api.js';

const AUTH_ERROR_MESSAGE = {
  LOGIN_FAILED: {
    title: '인스타그램 로그인에 실패했어요',
    description: '로그인을 다시 시도해주세요.',
  },
  TOKEN_MISSING: {
    title: '로그인 정보를 확인할 수 없어요',
    description: '인증 정보가 전달되지 않았어요. 다시 로그인해주세요.',
  },
};

function InstagramCallbackPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get('token');
    const error = params.get('error');

    const purpose =
      sessionStorage.getItem('instagramAuthPurpose') ||
      INSTAGRAM_AUTH_PURPOSE.LOGIN;

    sessionStorage.removeItem('instagramAuthPurpose');

    window.history.replaceState({}, document.title, '/auth/callback');

    if (error) {
      navigate('/', {
        replace: true,
        state: {
          authError: AUTH_ERROR_MESSAGE.LOGIN_FAILED,
        },
      });
      return;
    }

    if (!accessToken) {
      navigate('/', {
        replace: true,
        state: {
          authError: AUTH_ERROR_MESSAGE.TOKEN_MISSING,
        },
      });
      return;
    }

    localStorage.setItem('accessToken', accessToken);

    if (purpose === INSTAGRAM_AUTH_PURPOSE.ONBOARDING) {
      navigate('/auth/onboarding?instagram=success', { replace: true });
      return;
    }

    navigate('/home', { replace: true });
  }, [navigate]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-white px-6">
      <p className="text-base font-semibold text-gray-700">
        인스타그램 인증을 완료하고 있어요.
      </p>
    </main>
  );
}

export default InstagramCallbackPage;

import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  authApi,
  INSTAGRAM_AUTH_PURPOSE,
} from '@/features/auth/api.js';
import { registerFcmToken } from '@/features/notification/api/FcmApi';

const AUTH_ERROR_MESSAGE = {
  LOGIN_FAILED: {
    title: '인스타그램 로그인에 실패했어요',
    description: '로그인을 다시 시도해주세요.',
  },
  TOKEN_MISSING: {
    title: '로그인 정보를 확인할 수 없어요',
    description: '인증 정보가 전달되지 않았어요.\n다시 로그인해주세요.',
  },
  ME_FETCH_FAILED: {
    title: '로그인 정보를 불러오지 못했어요',
    description: '잠시 후 다시 시도해주세요.',
  },
};

const AUTH_NOTICE_MESSAGE = {
  NEEDS_ONBOARDING: {
    title: '가입한 이력이 없는 계정이에요',
    description: '서비스 이용을 위해\n몇 가지 준비를 먼저 도와드릴게요.',
  },
  ALREADY_ONBOARDED: {
    title: '이미 가입된 계정이에요',
    description: '홈 화면으로 이동할게요.',
  },
};

function InstagramCallbackPage() {
  const navigate = useNavigate();
  const hasHandledCallback = useRef(false);

  useEffect(() => {
    if (hasHandledCallback.current) return;
    hasHandledCallback.current = true;

    const handleCallback = async () => {
      const params = new URLSearchParams(window.location.search);
      const accessToken = params.get('token');
      const error = params.get('error');

      const purpose =
        sessionStorage.getItem('instagramAuthPurpose') ||
        INSTAGRAM_AUTH_PURPOSE.LOGIN;

      sessionStorage.removeItem('instagramAuthPurpose');

      if (error) {
        window.history.replaceState({}, document.title, '/auth/callback');

        navigate('/', {
          replace: true,
          state: {
            authError: AUTH_ERROR_MESSAGE.LOGIN_FAILED,
          },
        });
        return;
      }

      if (!accessToken) {
        window.history.replaceState({}, document.title, '/auth/callback');

        navigate('/', {
          replace: true,
          state: {
            authError: AUTH_ERROR_MESSAGE.TOKEN_MISSING,
          },
        });
        return;
      }

      localStorage.setItem('accessToken', accessToken);
      void registerFcmToken({ requestPermission: true });
      window.history.replaceState({}, document.title, '/auth/callback');

      try {
        const response = await authApi.getMe();

        const { isOnboarded } = response.data;

        if (purpose === INSTAGRAM_AUTH_PURPOSE.ONBOARDING) {
          if (isOnboarded) {
            navigate('/auth/onboarding', {
              replace: true,
              state: {
                authNotice: AUTH_NOTICE_MESSAGE.ALREADY_ONBOARDED,
                redirectTo: '/home',
              },
            });
            return;
          }

          navigate('/auth/onboarding?instagram=success', { replace: true });
          return;
        }

        if (!isOnboarded) {
          navigate('/', {
            replace: true,
            state: {
              authError: AUTH_NOTICE_MESSAGE.NEEDS_ONBOARDING,
              redirectTo: '/auth/onboarding',
            },
          });
          return;
        }

        navigate('/home', { replace: true });
      } catch (error) {
        console.error('내 정보 조회 실패:', error);

        localStorage.removeItem('accessToken');

        navigate('/', {
          replace: true,
          state: {
            authError: AUTH_ERROR_MESSAGE.ME_FETCH_FAILED,
          },
        });
      }
    };

    void handleCallback();
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

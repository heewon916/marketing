import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';


const AUTH_ERROR_MESSAGE = {
  LOGIN_FAILED: {
    title: '인스타그램 로그인에 실패했어요',
    description: '로그인을 다시 시도해주세요.',
  },
  TOKEN_MISSING: {
    title: '로그인 정보를 확인할 수 없어요',
    description: '인증 정보가 전달되지 않았어요.\n다시 로그인해주세요.',
  },
};

function InstagramCallbackPage() {
  const navigate = useNavigate();
  const hasHandledCallback = useRef(false);

  useEffect(() => {
    if (hasHandledCallback.current) return;
    hasHandledCallback.current = true;

    const isPopupWindow =
      !!window.opener || window.name === 'instagram-login';

    const closePopup = () => {
      window.history.replaceState({}, document.title, '/auth/callback');

      if (isPopupWindow) {
        window.close();
        return true;
      }

      return false;
    };

    const handleCallback = () => {
      const params = new URLSearchParams(window.location.search);
      const accessToken = params.get('token');
      const error = params.get('error');

      if (error) {
        localStorage.setItem(
          'instagramAuthResult',
          JSON.stringify({
            status: 'error',
            reason: 'LOGIN_FAILED',
            timestamp: Date.now(),
          })
        );

        const isClosed = closePopup();

        if (isClosed) return;

        navigate('/', {
          replace: true,
          state: {
            authError: AUTH_ERROR_MESSAGE.LOGIN_FAILED,
          },
        });
        return;
      }

      if (!accessToken) {
        localStorage.setItem(
          'instagramAuthResult',
          JSON.stringify({
            status: 'error',
            reason: 'TOKEN_MISSING',
            timestamp: Date.now(),
          })
        );

        const isClosed = closePopup();

        if (isClosed) return;

        navigate('/', {
          replace: true,
          state: {
            authError: AUTH_ERROR_MESSAGE.TOKEN_MISSING,
          },
        });
        return;
      }

      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem(
        'instagramAuthResult',
        JSON.stringify({
          status: 'success',
          timestamp: Date.now(),
        })
      );


      const isClosed = closePopup();

      if (isClosed) return;

      navigate('/', {
        replace: true,
      });
    };

    handleCallback();
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

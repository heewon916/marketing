// fe/src/pages/landing/LandingPage.jsx
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Button from '@/components/common/Button.jsx';
import Modal from '@/components/common/Modal.jsx';
import Character from '@/assets/character/CharacterWaving.mp4';
import {
  authApi,
  INSTAGRAM_AUTH_PURPOSE,
} from '@/features/auth/api.js';

const AUTH_ERROR_MESSAGE = {
  LOGIN_FAILED: {
    title: '인스타그램 로그인에 실패했어요',
    description: '로그인을 다시 시도해주세요.',
  },
  NEEDS_ONBOARDING: {
    title: '가입한 이력이 없는 계정이에요',
    description: '서비스 이용을 위해\n몇 가지 준비를 먼저 도와드릴게요.',
  },
};

function LandingPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [authError, setAuthError] = useState(
    () => location.state?.authError ?? null
  );

  const [authRedirectTo, setAuthRedirectTo] = useState(
    () => location.state?.redirectTo ?? null
  );

  const [isLoggingIn, setIsLoggingIn] = useState(false);

  useEffect(() => {
    if (!location.state?.authError) return;

    navigate(location.pathname, {
      replace: true,
      state: null,
    });
  }, [location.pathname, location.state, navigate]);

  const handleInstagramLogin = async () => {
    if (isLoggingIn) return;

    setIsLoggingIn(true);

    try {
      const response = await authApi.loginWithInstagram(
        INSTAGRAM_AUTH_PURPOSE.LOGIN
      );

      const user = response.data?.data ?? response.data;
      const isOnboarded = user?.isOnboarded;

      if (isOnboarded) {
        navigate('/home', { replace: true });
        return;
      }

      setAuthError(AUTH_ERROR_MESSAGE.NEEDS_ONBOARDING);
      setAuthRedirectTo('/auth/onboarding');
    } catch (error) {
      setAuthError({
        title: AUTH_ERROR_MESSAGE.LOGIN_FAILED.title,
        description:
          error?.message || AUTH_ERROR_MESSAGE.LOGIN_FAILED.description,
      });
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleOnboarding = () => {
    navigate('/auth/onboarding');
  };

  const handleCloseAuthErrorModal = () => {
    setAuthError(null);

    if (authRedirectTo) {
      const nextPath = authRedirectTo;
      setAuthRedirectTo(null);
      navigate(nextPath, { replace: true });
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
      <div className="mb-4 px-5 py-1.5 bg-surface-100 rounded-full text-base font-medium text-gray-500">
        사장님의 든든한 AI 홍보 도우미
      </div>

      <h1 className="text-4xl font-extrabold text-accent-100 mb-2 tracking-tight">
        이제 맡겨주세요
      </h1>

      <h2 className="text-6xl font-extrabold text-primary-100 mb-8 tracking-tight">
        맡케팅
      </h2>

      <video
        src={Character}
        className="w-full max-w-[340px] mb-12 bg-white brightness-[1.03]"
        autoPlay
        loop
        muted
        playsInline
      />

      <Button
        onClick={handleInstagramLogin}
        disabled={isLoggingIn}
        className="w-full max-w-[340px] font-bold shadow-lg shadow-primary-100/40 mb-6"
      >
        {isLoggingIn ? '로그인 확인 중...' : '인스타그램으로 로그인'}
      </Button>

      <button
        onClick={handleOnboarding}
        className="text-gray-400 text-lg font-medium"
      >
        처음이세요? 제가 도와드릴게요
      </button>

      <Modal
        isOpen={!!authError}
        onClose={handleCloseAuthErrorModal}
        showClose={false}
        closeOnBackdrop={false}
      >
        <div className="text-center">
          <h3 className="text-xl font-bold text-gray-900">
            {authError?.title}
          </h3>

          <p className="mt-4 text-base leading-6 text-gray-500 whitespace-pre-line">
            {authError?.description}
          </p>

          <Button
            onClick={handleCloseAuthErrorModal}
            className="mt-8 w-full font-bold"
          >
            확인
          </Button>
        </div>
      </Modal>
    </main>
  );
}

export default LandingPage;

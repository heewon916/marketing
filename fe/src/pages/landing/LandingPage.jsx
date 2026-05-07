import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Button from '@/components/common/Button.jsx';
import Modal from '@/components/common/Modal.jsx';
import Character from '@/assets/character/CharacterDdabong.png';
import { registerFcmToken } from '@/features/notification/api/FcmApi';
import {
  authApi,
  INSTAGRAM_AUTH_PURPOSE,
} from '@/features/auth/api.js';

function LandingPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [authError, setAuthError] = useState(
    () => location.state?.authError ?? null
  );

  useEffect(() => {
    void registerFcmToken({ requestPermission: true });
  }, []);

  useEffect(() => {
    if (!location.state?.authError) return;

    navigate(location.pathname, {
      replace: true,
      state: null,
    });
  }, [location.pathname, location.state, navigate]);

  const handleInstagramLogin = () => {
    authApi.loginWithInstagram(INSTAGRAM_AUTH_PURPOSE.LOGIN);
  };

  const handleOnboarding = () => {
    navigate('/auth/onboarding');
  };

  const handleCloseAuthErrorModal = () => {
    setAuthError(null);
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

      <img
        src={Character}
        alt="character"
        className="w-full max-w-[340px] mb-12"
      />

      <Button
        onClick={handleInstagramLogin}
        className="w-full max-w-[340px] font-bold shadow-lg shadow-primary-100/40 mb-6"
      >
        인스타그램으로 로그인
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

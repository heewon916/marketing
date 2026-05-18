// fe/src/features/auth/onboarding/steps/InstagramConnectStep.jsx
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '@/components/common/Button.jsx';
import Character from '@/assets/character/CharacterIdea.mp4';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import {
  authApi,
  INSTAGRAM_AUTH_PURPOSE,
} from '@/features/auth/api.js';

function InstagramConnectStep({ onNext }) {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const [isConnecting, setIsConnecting] = useState(false);

  useEffect(() => {
    if (!videoRef.current) return;

    videoRef.current.playbackRate = 1.3;
  }, []);

  const handleConnect = async () => {
    if (isConnecting) return;

    setIsConnecting(true);

    try {
      const response = await authApi.loginWithInstagram(
        INSTAGRAM_AUTH_PURPOSE.ONBOARDING
      );

      const user = response.data?.data ?? response.data;
      const isOnboarded = user?.isOnboarded;

      if (isOnboarded) {
        navigate('/auth/onboarding', {
          replace: true,
          state: {
            authNotice: {
              title: '이미 가입된 계정이에요',
              description: '홈 화면으로 이동할게요.',
              titleColor: 'primary',
            },
            redirectTo: '/home',
          },
        });
        return;
      }

      onNext();
    } catch (error) {
      console.error('인스타그램 연동 실패:', error);

      navigate('/auth/onboarding', {
        replace: true,
        state: {
          authNotice: {
            title: '로그인에 실패했어요',
            description: '로그인을 다시 시도해 주세요.',
            titleColor: 'primary',
          },
        },
      });
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <OnboardingLayout
      currentStep={1}
      totalStep={7}
      contentAlign="left"
      header={
        <OnboardingHeader
          title={
            <>
              맡케팅 이용을 위해
              <br />
              <span className="text-primary-100 font-extrabold">
                인스타그램 계정 연동
              </span>
              이
              <br />
              필요해요
            </>
          }
        />
      }
      footer={
        <>
          <Button
            onClick={handleConnect}
            disabled={isConnecting}
            className="w-full font-bold"
          >
            {isConnecting ? '연동 확인 중...' : '인스타그램 연동하기'}
          </Button>

          {import.meta.env.DEV && (
            <button
              type="button"
              onClick={onNext}
              className="mt-3 text-sm font-medium text-gray-400 underline"
            >
              개발용: 인스타그램 연동 건너뛰기
            </button>
          )}
        </>
      }
    >
      <div className="w-full flex justify-center mt-10">
        <video
          ref={videoRef}
          src={Character}
          className="w-full max-w-[340px]"
          autoPlay
          loop
          muted
          playsInline
        />
      </div>
    </OnboardingLayout>
  );
}

export default InstagramConnectStep;

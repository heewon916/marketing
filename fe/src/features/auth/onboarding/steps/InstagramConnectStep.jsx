import Button from '@/components/common/Button.jsx';
import Character from '@/assets/character/CharacterDdabong.png';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import {
  authApi,
  INSTAGRAM_AUTH_PURPOSE,
} from '@/features/auth/api.js';

function InstagramConnectStep({ onNext }) {
  const handleConnect = () => {
    authApi.loginWithInstagram(INSTAGRAM_AUTH_PURPOSE.ONBOARDING);
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
              마케팅 이용을 위해
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
          <Button onClick={handleConnect} className="w-full font-bold">
            인스타그램 연동하기
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
        <img
          src={Character}
          alt="character"
          className="w-full max-w-[320px]"
        />
      </div>
    </OnboardingLayout>
  );
}

export default InstagramConnectStep;

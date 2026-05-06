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

  const handleTempSuccess = () => {
    onNext();
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
        <div className="w-full flex flex-col gap-3">
          <Button onClick={handleConnect} className="w-full font-bold">
            인스타그램 연동하기
          </Button>

          {import.meta.env.DEV && (
            <button
              type="button"
              onClick={handleTempSuccess}
              className="w-full py-3 text-sm font-bold text-gray-500 underline"
            >
              개발용: 인스타그램 연동 완료 처리
            </button>
          )}
        </div>
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

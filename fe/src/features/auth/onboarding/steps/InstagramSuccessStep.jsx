import Button from '@/components/common/Button.jsx';
import Character from '@/assets/character/CharacterDdabong.png';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';

function InstagramSuccessStep({ onNext, onPrev }) {
  return (
    <OnboardingLayout
      currentStep={2}
      totalStep={7}
      contentAlign="center"
      header={
        <OnboardingHeader
          title={
            <>
              <span className="text-primary-100 font-extrabold">
                계정이 연결
              </span>
              되었어요
            </>
          }
        />
      }
      footer={
        <div className="flex gap-3">
          <button
            onClick={onPrev}
            className="flex-1 py-3 border rounded-xl text-gray-500"
          >
            이전
          </button>

          <Button onClick={onNext} className="flex-1 font-bold">
            다음
          </Button>
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

export default InstagramSuccessStep;

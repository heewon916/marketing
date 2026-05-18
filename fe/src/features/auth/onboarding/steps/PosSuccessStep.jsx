import Character from '@/assets/character/CharacterDdabong.mp4';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';

function PosSuccessStep({ onNext, onPrev }) {
  return (
    <OnboardingLayout
      currentStep={4}
      totalStep={7}
      contentAlign="center"
      header={
        <OnboardingHeader
          title={
            <>
              <span className="text-primary-100 font-extrabold">
                토스 POS와 연결
              </span>
              되었어요
            </>
          }
        />
      }
      footer={
        <>
        <OnboardingFooterButtons
          onPrev={onPrev}
          onNext={onNext}
        />
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
          src={Character}
          autoPlay
          loop
          muted
          playsInline
          className="w-full max-w-[320px]"
        />
      </div>
    </OnboardingLayout>
  );
}

export default PosSuccessStep;

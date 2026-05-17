import Character from '@/assets/character/CharacterDdabong.mp4';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';

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
        <OnboardingFooterButtons
          onPrev={onPrev}
          onNext={onNext}
        />
      }
    >
      <div className="w-full flex justify-center mt-10">
        <video
          src={Character}
          className="w-full max-w-[320px]"
          autoPlay
          loop
          muted
          playsInline
        />
      </div>
    </OnboardingLayout>
  );
}

export default InstagramSuccessStep;

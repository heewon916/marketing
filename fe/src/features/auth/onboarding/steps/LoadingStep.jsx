import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import tossLoading from '@/assets/videos/toss-loading.mp4';

function LoadingStep({ onNext, onPrev }) {
  return (
    <OnboardingLayout
      currentStep={3}
      totalStep={7}
      header={
        <OnboardingHeader
          title={
            <>
              토스 POS와
              <br />
              연결하고 있어요
            </>
          }
        />
      }
      footer={
        <OnboardingFooterButtons
          onPrev={onPrev}
          onNext={onNext}
          nextText="다음"
        />
      }
    >
      <video
        src={tossLoading}
        autoPlay
        loop
        muted
        playsInline
        className="w-full h-full justify-center object-contain"
      />
    </OnboardingLayout>
  );
}

export default LoadingStep;
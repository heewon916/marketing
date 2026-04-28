import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import Character from '@/assets/character/CharacterDdabong.png';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';

function PosConnectStep({ onNext, onPrev }) {
  return (
    <OnboardingLayout
      currentStep={3}
      totalStep={7}
      contentAlign="left"
      header={
        <OnboardingHeader
          title={
            <>
              가게 정보를 가져오기 위해
              <br />
              <span className="text-primary-100 font-extrabold">
                토스 POS를 연결
              </span>
              할게요
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
        <img
          src={Character}
          alt="character"
          className="w-full max-w-[320px]"
        />
      </div>
    </OnboardingLayout>
  );
}

export default PosConnectStep;

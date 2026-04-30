import Character from '@/assets/character/CharacterRun.png';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';

// 개발용 플래그
const IS_DEV = true;

function StoreLoadingStep({ onNext, onPrev }) {
  return (
    <OnboardingLayout
      currentStep={5}
      totalStep={7}
      contentAlign="center"
      header={
        <OnboardingHeader
          title={
            <>
              영업 정보를
              <br />
              가져오고 있어요
            </>
          }
          subtitle="화면을 나가지 말고 기다려주세요"
        />
      }
      footer={
        IS_DEV && (
          <OnboardingFooterButtons
            onPrev={onPrev}
            onNext={onNext}
            nextText="다음 (DEV)"
          />
        )
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

export default StoreLoadingStep;
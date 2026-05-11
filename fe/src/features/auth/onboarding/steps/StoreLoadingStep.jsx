import Character from '@/assets/character/CharacterRun.png';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';

function StoreLoadingStep() {
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

import Button from '@/components/common/Button.jsx';
import CharacterFail from '@/assets/character/CharacterFail.mp4';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';

function StoreSearchFailStep({ onNext, onPrev }) {
  return (
    <OnboardingLayout
      currentStep={5}
      totalStep={7}
      contentAlign="left"
      header={
        <OnboardingHeader
          title={
            <>
              가게 목록을
              <br />
              받아올 수 없어요
            </>
          }
          subtitle="상호명을 직접 입력해주세요"
        />
      }
      footer={
        <div className="flex w-full gap-3">
          {onPrev && (
            <Button
              type="button"
              variant="white"
              size="sm"
              onClick={onPrev}
              className="flex-1 font-bold"
            >
              이전
            </Button>
          )}

          <Button
            type="button"
            size={onPrev ? 'sm' : 'lg'}
            onClick={onNext}
            className="flex-1 font-bold"
          >
            직접 입력
          </Button>
        </div>
      }
    >
      <div className="w-full flex justify-center mt-10">
        <video
          src={CharacterFail}
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

export default StoreSearchFailStep;

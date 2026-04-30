import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import RoundedInput from '../components/RoundedInput.jsx';

function StoreNameStep({ value, onChange, onNext, onPrev }) {
  return (
    <OnboardingLayout
      currentStep={6}
      totalStep={7}
      contentAlign="left"
      header={
        <OnboardingHeader
          title={
            <>
              <span className="text-primary-100 font-extrabold">
                상호명
              </span>
              을
              <br />
              확인해주세요
            </>
          }
          subtitle="정보가 다르면 수정해주세요"
        />
      }
      footer={
        <OnboardingFooterButtons
          onPrev={onPrev}
          onNext={onNext}
          nextText="저장"
          nextDisabled={!value?.trim()}
        />
      }
    >
      <div className="mt-2 w-full">
        <RoundedInput
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="상호명을 입력해 주세요"
        />
      </div>
    </OnboardingLayout>
  );
}

export default StoreNameStep;

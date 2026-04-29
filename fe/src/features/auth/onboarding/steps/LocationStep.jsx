import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import RoundedInput from '../components/RoundedInput.jsx';
import StaticMap from '../components/StaticMap.jsx';

function LocationStep({ value, onChange, onNext, onPrev }) {
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
                가게 위치
              </span>
              를
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
          nextDisabled={!value}
        />
      }
    >
      {/* 주소 입력 */}
      <div className="mt-2 w-full">
        <RoundedInput
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="주소를 입력해주세요"
          icon="search"
        />
      </div>

      {/* 지도 */}
      <StaticMap storeName={value} />
    </OnboardingLayout>
  );
}

export default LocationStep;
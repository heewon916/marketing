import { useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import RoundedInput from '../components/RoundedInput.jsx';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

function StoreNameStep({ value = '', onChange, onNext, onPrev }) {
  const storeName = useOnboardingStore((state) => state.storeName);
  const setStoreName = useOnboardingStore((state) => state.setStoreName);

  const [inputValue, setInputValue] = useState(() => storeName || value || '');

  const handleChange = (e) => {
    const nextValue = e.target.value;

    setInputValue(nextValue);
    onChange?.(nextValue);
  };

  const handleNext = () => {
    const trimmedValue = inputValue.trim();

    if (!trimmedValue) return;

    setStoreName(trimmedValue);
    onChange?.(trimmedValue);
    onNext?.();
  };

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
          onNext={handleNext}
          nextText="저장"
          nextDisabled={!inputValue.trim()}
        />
      }
    >
      <div className="mt-2 w-full">
        <RoundedInput
          value={inputValue}
          onChange={handleChange}
          placeholder="상호명을 입력해 주세요"
        />
      </div>
    </OnboardingLayout>
  );
}

export default StoreNameStep;

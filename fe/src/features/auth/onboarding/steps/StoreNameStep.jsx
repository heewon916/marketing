import { useState } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import RoundedInput from '../components/RoundedInput.jsx';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';
import { onboardingApi } from '@/features/auth/onboarding/api.js';

function StoreNameStep({
  value = '',
  onChange,
  onPrev,
  onSearchSuccess,
  onSearchFail,
}) {
  const storeName = useOnboardingStore((state) => state.storeName);
  const setStoreName = useOnboardingStore((state) => state.setStoreName);
  const setLocation = useOnboardingStore((state) => state.setLocation);
  const setOperatingHours = useOnboardingStore(
    (state) => state.setOperatingHours
  );

  const [inputValue, setInputValue] = useState(() => storeName || value || '');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleChange = (e) => {
    const nextValue = e.target.value;

    setInputValue(nextValue);
    setErrorMessage('');
    onChange?.(nextValue);
  };

  const handleNext = async () => {
    const trimmedValue = inputValue.trim();

    if (!trimmedValue || isLoading) return;

    const prevStoreName = (storeName || '').trim();
    const isStoreNameChanged = trimmedValue !== prevStoreName;

    if (isStoreNameChanged) {
      setLocation({
        address: '',
        latitude: null,
        longitude: null,
      });
      setOperatingHours({});
    }

    setStoreName(trimmedValue);
    onChange?.(trimmedValue);

    try {
      setIsLoading(true);
      setErrorMessage('');

      const response = await onboardingApi.searchStores(trimmedValue);
      const stores = response.data?.data ?? [];

      if (stores.length > 0) {
        onSearchSuccess?.();
        return;
      }

      onSearchFail?.();
    } catch {
      onSearchFail?.();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <OnboardingLayout
      currentStep={5}
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
              입력해주세요
            </>
          }
          subtitle="상호명은 온보딩 완료 후에는 변경할 수 없어요."
        />
      }
      footer={
        <OnboardingFooterButtons
          onPrev={onPrev}
          onNext={handleNext}
          nextText={isLoading ? '검색 중' : '다음'}
          nextDisabled={!inputValue.trim() || isLoading}
        />
      }
    >
      <div className="mt-2 w-full">
        <RoundedInput
          value={inputValue}
          onChange={handleChange}
          placeholder="상호명을 입력해 주세요"
          disabled={isLoading}
        />

        {errorMessage && (
          <p className="mt-3 text-sm font-medium text-red-500">
            {errorMessage}
          </p>
        )}
      </div>
    </OnboardingLayout>
  );
}

export default StoreNameStep;

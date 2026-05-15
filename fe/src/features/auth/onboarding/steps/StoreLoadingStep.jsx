import { useEffect } from 'react';
import Character from '@/assets/character/CharacterRun.png';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import { onboardingApi } from '@/features/auth/onboarding/api.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

function StoreLoadingStep({ onSearchSuccess, onSearchFail }) {
  const storeName = useOnboardingStore((state) => state.storeName);

  useEffect(() => {
    const searchStores = async () => {
      const keyword = storeName?.trim();

      if (!keyword) {
        onSearchFail?.();
        return;
      }

      try {
        const response = await onboardingApi.searchStores(keyword);
        const stores = response.data?.data ?? [];

        if (stores.length > 0) {
          onSearchSuccess?.();
          return;
        }

        onSearchFail?.();
      } catch {
        onSearchFail?.();
      }
    };

    void searchStores();
  }, [storeName, onSearchSuccess, onSearchFail]);

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

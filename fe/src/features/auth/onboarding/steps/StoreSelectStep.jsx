import { useEffect, useRef, useState } from 'react';

import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import StoreCard from '../components/StoreCard.jsx';
import ScrollFadeArrow from '../../../../components/common/ScrollFadeArrow.jsx';

import { onboardingApi } from '@/features/auth/onboarding/api.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

function LoadingText() {
  return (
    <div className="flex items-end justify-center gap-2 pt-2" style={{ height: '36px' }}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="block h-3 w-3 rounded-full bg-primary-100"
          style={{
            animation: 'dotBounce 0.8s ease-in-out infinite',
            animationDelay: `${i * 0.15}s`,
          }}
        />
      ))}
      <style>{`
        @keyframes dotBounce {
          0%, 100% { transform: translateY(0); opacity: 1; }
          45%       { transform: translateY(-20px); opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}

function StoreSelectStep({ onNext, onPrev, onManualInput, onSearchFail }) {
  const listRef = useRef(null);

  const storeName = useOnboardingStore((state) => state.storeName);
  const setSelectedPlaceId = useOnboardingStore(
    (state) => state.setSelectedPlaceId
  );

  const [stores, setStores] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [isLoading, setIsLoading] = useState(() => !!storeName?.trim());

  const keyword = storeName?.trim() ?? '';

  useEffect(() => {
    if (!keyword) {
      onSearchFail?.();
      return;
    }

    let isMounted = true;

    const searchStores = async () => {
      try {
        setIsLoading(true);

        const response = await onboardingApi.searchStores(keyword);
        const result = response.data?.data ?? [];

        if (!isMounted) return;

        const normalizedStores = result.map((store) => ({
          id: store.place_id,
          placeId: store.place_id,
          name: store.name,
          address: store.address,
        }));

        if (normalizedStores.length === 0) {
          onSearchFail?.();
          return;
        }

        setStores(normalizedStores);
        setSelectedId('');
      } catch {
        if (!isMounted) return;

        onSearchFail?.();
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    void searchStores();

    return () => {
      isMounted = false;
    };
  }, [keyword, onSearchFail]);

  const handleSelectStore = (id) => {
    setSelectedId(id);
  };

  const handleNext = () => {
    const selectedStore = stores.find((store) => store.id === selectedId);

    if (!selectedStore) return;

    setSelectedPlaceId(selectedStore.placeId);

    onNext?.();
  };

  const handleManualInput = () => {
    setSelectedPlaceId('');
    onManualInput?.();
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
                가게를 선택
              </span>
              해 주세요
            </>
          }
          emphasis="어떤 가게가 사장님 가게인가요?"
          subtitle="하단 목록에서 우리 매장을 선택해 주세요"
        />
      }
      footer={
        <div className="w-full">
          {!isLoading && stores.length > 0 && (
            <div className="mb-8 text-center">
              <p className="text-sm font-medium text-gray-500">
                원하는 가게가 목록에 없나요?
              </p>

              <button
                type="button"
                onClick={handleManualInput}
                className="mt-1 text-sm font-semibold text-primary-100 underline underline-offset-4"
              >
                직접 입력할게요
              </button>
            </div>
          )}

          <OnboardingFooterButtons
            onPrev={onPrev}
            onNext={handleNext}
            nextDisabled={!selectedId}
            nextText="다음"
          />
        </div>
      }
    >
      <div className="relative mt-2 w-full flex-1">
        <div className="absolute inset-0">
          {isLoading && <LoadingText />}

          {!isLoading && stores.length > 0 && (
            <div className="flex h-full w-full flex-col">
              <div
                ref={listRef}
                className="flex h-full w-full flex-col gap-3 overflow-y-auto px-1 pb-24 pt-2 [&::-webkit-scrollbar]:hidden"
              >
                {stores.map((store) => (
                  <StoreCard
                    key={store.id}
                    store={store}
                    isSelected={selectedId === store.id}
                    onSelect={handleSelectStore}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {stores.length > 0 && <ScrollFadeArrow targetRef={listRef} />}
      </div>
    </OnboardingLayout>
  );
}

export default StoreSelectStep;

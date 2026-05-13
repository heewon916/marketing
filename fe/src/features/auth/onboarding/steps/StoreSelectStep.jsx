import { useEffect, useRef, useState } from 'react';

import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import StoreCard from '../components/StoreCard.jsx';
import ScrollFadeArrow from '../../../../components/common/ScrollFadeArrow.jsx';

import { onboardingApi } from '@/features/auth/onboarding/api.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

function StoreSelectStep({ onNext, onPrev }) {
  const listRef = useRef(null);

  const storeName = useOnboardingStore((state) => state.storeName);
  const setStoreName = useOnboardingStore((state) => state.setStoreName);
  const setSelectedPlaceId = useOnboardingStore(
    (state) => state.setSelectedPlaceId
  );

  const [stores, setStores] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [isLoading, setIsLoading] = useState(() => !!storeName?.trim());
  const [errorMessage, setErrorMessage] = useState('');

  const keyword = storeName?.trim() ?? '';
  const displayErrorMessage =
    !keyword ? '상호명 정보가 없어 가게 목록을 불러올 수 없어요.' : errorMessage;

  useEffect(() => {
    if (!keyword) return;

    let isMounted = true;

    const searchStores = async () => {
      try {
        const response = await onboardingApi.searchStores(keyword);
        const result = response.data?.data ?? [];

        if (!isMounted) return;

        const normalizedStores = result.map((store) => ({
          id: store.place_id,
          placeId: store.place_id,
          name: store.name,
          address: store.address,
        }));

        setStores(normalizedStores);
        setSelectedId('');
        setErrorMessage(
          normalizedStores.length === 0 ? '가게 목록을 찾을 수 없어요.' : ''
        );
      } catch {
        if (!isMounted) return;

        setStores([]);
        setSelectedId('');
        setErrorMessage('가게 목록을 불러오지 못했어요.');
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
  }, [keyword]);

  const handleSelectStore = (id) => {
    setSelectedId(id);
  };

  const handleNext = () => {
    const selectedStore = stores.find((store) => store.id === selectedId);

    if (!selectedStore) return;

    setSelectedPlaceId(selectedStore.placeId);
    setStoreName(selectedStore.name);

    onNext?.();
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
        <OnboardingFooterButtons
          onPrev={onPrev}
          onNext={handleNext}
          nextDisabled={!selectedId}
          nextText="다음"
        />
      }
    >
      <div className="relative mt-2 w-full flex-1">
        <div className="absolute inset-0">
          {isLoading && (
            <p className="px-1 pt-2 text-sm font-medium text-gray-400">
              가게 목록을 불러오고 있어요.
            </p>
          )}

          {!isLoading && displayErrorMessage && (
            <p className="px-1 pt-2 text-sm font-medium text-red-500">
              {displayErrorMessage}
            </p>
          )}

          {!isLoading && !displayErrorMessage && stores.length > 0 && (
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
          )}
        </div>

        {stores.length > 0 && <ScrollFadeArrow targetRef={listRef} />}
      </div>
    </OnboardingLayout>
  );
}

export default StoreSelectStep;

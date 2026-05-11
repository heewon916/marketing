import { useEffect, useRef, useState } from 'react';

import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import StoreCard from '../components/StoreCard.jsx';
import ScrollFadeArrow from '../../../../components/common/ScrollFadeArrow.jsx';
import StoreNotFoundModal from '../components/StoreNotFoundModal.jsx';

import { onboardingApi } from '@/features/auth/onboarding/api.js';
import { useOnboardingStore } from '@/features/auth/onboarding/store/onboardingStore.js';

function StoreSelectStep({ onNext, onPrev, onManualInput }) {
  const listRef = useRef(null);

  const storeName = useOnboardingStore((state) => state.storeName);
  const setStoreName = useOnboardingStore((state) => state.setStoreName);
  const setSelectedPlaceId = useOnboardingStore(
    (state) => state.setSelectedPlaceId
  );

  const [stores, setStores] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [isLoading, setIsLoading] = useState(() => !!storeName?.trim());
  const [isModalClosed, setIsModalClosed] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const keyword = storeName?.trim() ?? '';

  useEffect(() => {
    if (!keyword) return;

    const searchStores = async () => {
      try {
        const response = await onboardingApi.searchStores(keyword);
        const result = response.data?.data ?? [];

        const normalizedStores = result.map((store) => ({
          id: store.place_id,
          placeId: store.place_id,
          name: store.name,
          address: store.address,
        }));

        setStores(normalizedStores);
        setErrorMessage('');
      } catch (error) {
        const message =
          error.response?.data?.message ||
          '가게 목록을 불러오지 못했습니다. 다시 시도해 주세요.';

        setStores([]);
        setErrorMessage(message);
      } finally {
        setIsLoading(false);
      }
    };

    void searchStores();
  }, [keyword]);

  const isModalOpen =
    !!keyword &&
    !isLoading &&
    stores.length === 0 &&
    !isModalClosed &&
    !errorMessage;

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

  const handleManualInput = () => {
    setIsModalClosed(true);
    onManualInput?.();
  };

  return (
    <>
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

            {!keyword && (
              <p className="px-1 pt-2 text-sm font-medium text-gray-400">
                상호명 정보가 없어 직접 입력이 필요해요.
              </p>
            )}

            {errorMessage && (
              <p className="px-1 pt-2 text-sm font-medium text-red-500">
                {errorMessage}
              </p>
            )}

            {!isLoading && !errorMessage && stores.length > 0 && (
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

      <StoreNotFoundModal
        isOpen={isModalOpen}
        onManualInput={handleManualInput}
        onGoHome={handleManualInput}
      />
    </>
  );
}

export default StoreSelectStep;

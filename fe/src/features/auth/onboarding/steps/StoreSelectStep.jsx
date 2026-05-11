import { useEffect, useRef, useState } from 'react';

import Modal from '@/components/common/Modal.jsx';
import Button from '@/components/common/Button.jsx';
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
  const [retryCount, setRetryCount] = useState(0);

  const keyword = storeName?.trim() ?? '';
  const isErrorModalOpen = !!errorMessage && !isLoading;

  useEffect(() => {
    if (!keyword) return;

    const searchStores = async () => {
      try {
        setIsLoading(true);

        const response = await onboardingApi.searchStores(keyword);
        const result = response.data?.data ?? [];

        const normalizedStores = result.map((store) => ({
          id: store.place_id,
          placeId: store.place_id,
          name: store.name,
          address: store.address,
        }));

        setStores(normalizedStores);
        setSelectedId('');
        setErrorMessage('');
      } catch (error) {
        const message = error.response?.data?.message;

        setStores([]);
        setSelectedId('');
        setErrorMessage(
          message || '잠시 후 다시 시도하거나,\n직접 입력으로 계속 진행해 주세요.'
        );
      } finally {
        setIsLoading(false);
      }
    };

    void searchStores();
  }, [keyword, retryCount]);

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

  const handleRetry = () => {
    if (!keyword) return;

    setStores([]);
    setSelectedId('');
    setErrorMessage('');
    setIsModalClosed(false);
    setIsLoading(true);
    setRetryCount((prev) => prev + 1);
  };

  const handleManualInput = () => {
    setIsModalClosed(true);
    setErrorMessage('');
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
              <div className="px-1 pt-2">
                <p className="text-sm font-medium text-gray-400">
                  상호명 정보가 없어 직접 입력이 필요해요.
                </p>

                <button
                  type="button"
                  onClick={handleManualInput}
                  className="mt-4 w-full rounded-xl bg-primary-100 py-3 text-sm font-bold text-white"
                >
                  직접 입력하기
                </button>
              </div>
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

    <Modal
      isOpen={isErrorModalOpen}
      onClose={() => setErrorMessage('')}
      showClose={false}
      closeOnBackdrop={false}
    >
      <div className="text-center">
        <h3 className="text-xl font-bold text-gray-900">
          가게 목록을 불러올 수 없어요
        </h3>

        <p className="mt-4 text-base leading-6 text-gray-500 whitespace-pre-line">
          {errorMessage}
        </p>

        <div className="mt-8 flex gap-3">
          <Button
            variant="white"
            size="sm"
            onClick={handleManualInput}
            className="flex-1"
          >
            직접 입력
          </Button>

          <Button
            size="sm"
            onClick={handleRetry}
            className="flex-1"
          >
            다시 시도
          </Button>
        </div>
      </div>
    </Modal>
    </>
  );
}

export default StoreSelectStep;

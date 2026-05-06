import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import StoreCard from '../components/StoreCard.jsx';
import ScrollFadeArrow from '../../../../components/common/ScrollFadeArrow.jsx';
import StoreNotFoundModal from '../components/StoreNotFoundModal.jsx';

function StoreSelectStep({ onNext, onPrev, onManualInput }) {
  const [selectedId, setSelectedId] = useState(null);
  const [isModalClosed, setIsModalClosed] = useState(false);

  const navigate = useNavigate();
  const listRef = useRef(null);

  const [stores] = useState([]);

  const isModalOpen = stores.length === 0 && !isModalClosed;

  const handleManualInput = () => {
    setIsModalClosed(true);
    onManualInput?.();
  };

  const handleGoHome = () => {
    navigate('/');
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
            onNext={onNext}
            nextDisabled={!selectedId}
            nextText="다음"
          />
        }
      >
        <div className="relative mt-2 w-full flex-1">
          <div className="absolute inset-0">
            {stores.length > 0 && (
              <div
                ref={listRef}
                className="flex h-full w-full flex-col gap-3 overflow-y-auto px-1 pb-24 pt-2 [&::-webkit-scrollbar]:hidden"
              >
                {stores.map((store) => (
                  <StoreCard
                    key={store.id}
                    store={store}
                    isSelected={selectedId === store.id}
                    onSelect={setSelectedId}
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
        onGoHome={handleGoHome}
      />
    </>
  );
}

export default StoreSelectStep;

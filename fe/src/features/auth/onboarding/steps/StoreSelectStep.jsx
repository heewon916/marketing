import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import StoreCard from '../components/StoreCard.jsx';
import ScrollFadeArrow from '../components/ScrollFadeArrow.jsx';

import Modal from '../../../../components/common/Modal.jsx';
import Button from '../../../../components/common/Button.jsx';

function StoreSelectStep({ onNext, onPrev }) {
  const [selectedId, setSelectedId] = useState(null);
  const navigate = useNavigate();
  const listRef = useRef(null);

  // 목업 데이터
  // const [stores] = useState([]);
  const [stores] = useState([
  {
    id: 1,
    name: '싸피카페 역삼점',
    address: '서울 강남구 역삼동',
  },
  {
    id: 2,
    name: '클로리스 역삼점',
    address: '서울 강남구 역삼동',
  },
  {
    id: 3,
    name: '바나프레소 역삼점',
    address: '서울 강남구 역삼동',
  },
  {
    id: 4,
    name: '스타벅스 역삼점',
    address: '서울 강남구 역삼동',
  },
  {
    id: 5,
    name: '투썸플레이스 역삼점',
    address: '서울 강남구 역삼동',
  },
]);

  const [isModalClosed, setIsModalClosed] = useState(false);

  const isModalOpen = stores.length === 0 && !isModalClosed;

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
                <span className="text-primary-100 font-extrabold">가게를 선택</span>
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
            nextLabel="다음"
          />
        }
      >
        <div className="relative flex-1 w-full mt-2">

          <div className="absolute inset-0">
            {/* 조건부 렌더링: 가게 목록이 비어있을 때는 메인 콘텐츠 영역을 비워둠 (null) */}
            {stores.length === 0 ? null : (
              <div
                ref={listRef}
                className="flex flex-col gap-3 w-full h-full overflow-y-auto px-1 pt-2 pb-24 [&::-webkit-scrollbar]:hidden"
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

      {/* 모달 컴포넌트 */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalClosed(true)}
        showClose={false}
        closeOnBackdrop={false}
      >
        <div className="flex flex-col items-center text-center mt-2">

          <div className="text-[22px] font-bold text-primary-100 mb-3 whitespace-nowrap">
            가게 정보를 찾을 수 없어요.
          </div>

          <div className="text-[19px] text-[#1D2030] font-semibold leading-snug mb-8">
            네이버 플레이스에 등록되어<br />있는지 확인해 주세요.
          </div>

          <Button
            variant="primary"
            className="!w-full !h-[56px] text-[18px] font-bold rounded-2xl"
            onClick={() => {
              navigate('/');
            }}
          >
            메인으로 돌아가기
          </Button>

        </div>
      </Modal>
    </>
  );
}

export default StoreSelectStep;

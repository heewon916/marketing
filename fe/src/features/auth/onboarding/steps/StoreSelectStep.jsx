import { useState, useRef, useEffect } from 'react';
import OnboardingLayout from '../components/OnboardingLayout.jsx';
import OnboardingHeader from '../components/OnboardingHeader.jsx';
import OnboardingFooterButtons from '../components/OnboardingFooterButtons.jsx';
import StoreCard from '../components/StoreCard.jsx';
import ScrollFadeArrow from '../components/ScrollFadeArrow.jsx';

function StoreSelectStep({ onNext, onPrev }) {
  const [selectedId, setSelectedId] = useState(null);

  const listRef = useRef(null);
  const [showScrollHint, setShowScrollHint] = useState(false);

  // 목업 데이터
  const [stores] = useState([
    { id: 1, name: '싸피카페 역삼점', address: '서울 강남구 역삼동' },
    { id: 2, name: '클로리스 역삼점', address: '서울 강남구 역삼동' },
    { id: 3, name: '바나프레소 역삼점', address: '서울 강남구 역삼동' },
    { id: 4, name: '스타벅스 역삼점', address: '서울 강남구 역삼동' },
    { id: 5, name: '투썸플레이스 역삼점', address: '서울 강남구 역삼동' },
  ]);

  // 스크롤 상태 체크 함수
  const handleScroll = () => {
    const el = listRef.current;
    if (!el) return;
    const isScrollable = el.scrollHeight > el.clientHeight;
    const isBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 10;
    setShowScrollHint(isScrollable && !isBottom);
  };

  // 초기 렌더링 시 높이 계산
  useEffect(() => {
    handleScroll();
    window.addEventListener('resize', handleScroll);
    return () => window.removeEventListener('resize', handleScroll);
  }, [stores]);

  return (
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
          subtitle={
            <div className="flex flex-col gap-1 mt-4">
              <span className="text-gray-900 font-bold text-lg">
                어떤 가게가 사장님 가게인가요?
              </span>
              <span className="text-gray-400 text-md">
                일치하는 매장을 선택해주세요
              </span>
            </div>
          }
        />
      }
      footer={
        <OnboardingFooterButtons
          onPrev={onPrev}
          onNext={onNext}
          nextDisabled={!selectedId}
        />
      }
    >
      <div className="relative flex-1 w-full mt-2">
        
        {/* 리스트 영역을 부모 컨테이너 안에 가두기 */}
        <div className="absolute inset-0">
          <div
            ref={listRef}
            onScroll={handleScroll}
            // 글로우 잘림 방지(px-1 pt-2) 및 하단 여백(pb-24) 추가
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
        </div>

        {/* 블러 + 화살표 컴포넌트 */}
        <ScrollFadeArrow isVisible={showScrollHint} />
      </div>
    </OnboardingLayout>
  );
}

export default StoreSelectStep;
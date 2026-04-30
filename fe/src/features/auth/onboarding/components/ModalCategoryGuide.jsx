import Modal from '@/components/common/Modal.jsx';
import { useState } from 'react';

const pages = [
  [
    {
      title: '식당',
      desc: '식사를 주로 제공하는 매장이에요.\n(한식, 중식, 양식 등)',
    },
    {
      title: '주점',
      desc: '술과 함께 음식을 즐기는 공간이에요.\n(포차, 술집 등)',
    },
  ],
  [
    {
      title: '카페',
      desc: '커피나 음료를 중심으로 운영하는\n매장이에요.',
    },
    {
      title: '제과점',
      desc: '빵, 디저트, 떡 등을 판매하는\n매장이에요.',
    },
  ],
];

export default function ModalCategoryGuide({ isOpen, onClose }) {
  const [page, setPage] = useState(0);
  
  // 스와이프를 위한 터치 좌표 상태 저장
  const [touchStartX, setTouchStartX] = useState(0);

  // 터치 시작 시점의 X 좌표 저장
  const handleTouchStart = (e) => {
    setTouchStartX(e.targetTouches[0].clientX);
  };

  // 터치 종료 시점의 X 좌표를 비교하여 페이지 이동 처리
  const handleTouchEnd = (e) => {
    const touchEndX = e.changedTouches[0].clientX;
    const swipeDistance = touchStartX - touchEndX;

    // 민감도 설정 (50px 이상 움직였을 때만 스와이프 인정)
    const swipeThreshold = 50;

    if (swipeDistance > swipeThreshold && page < pages.length - 1) {
      // 왼쪽으로 밀었을 때 (다음 페이지)
      setPage((prev) => prev + 1);
    } else if (swipeDistance < -swipeThreshold && page > 0) {
      // 오른쪽으로 밀었을 때 (이전 페이지)
      setPage((prev) => prev - 1);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div 
        className="flex flex-col gap-4 mt-4 select-none"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >

        {/* 카드 영역 */}
        {pages[page].map((item) => (
          <div
            key={item.title}
            className="
              rounded-2xl px-5 py-6 text-center bg-surface-100
              h-[130px] flex flex-col items-center justify-center
            "
          >
            <div className="text-primary-100 font-extrabold text-xl mb-2">
              {item.title}
            </div>

            <div className="text-accent-100 text-lg leading-relaxed whitespace-pre-line">
              {item.desc}
            </div>
          </div>
        ))}

        {/* 페이지 인디케이터 */}
        <div className="flex justify-center gap-2 mt-2">
          {pages.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setPage(idx)}
              className={`
                w-2.5 h-2.5 rounded-full transition-all
                ${page === idx ? 'bg-primary-100 w-5' : 'bg-gray-300'}
              `}
            />
          ))}
        </div>

      </div>
    </Modal>
  );
}
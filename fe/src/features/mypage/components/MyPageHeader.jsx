import { useNavigate } from 'react-router-dom';
import { useRef, useEffect, useState } from 'react';

export default function MyPageHeader({
  title,
  subtitle,
  showBackButton = false,
  onBack,
}) {
  const navigate = useNavigate();
  const titleRef = useRef(null);
  const [lineWidth, setLineWidth] = useState(0);

  useEffect(() => {
    if (titleRef.current) {
      setLineWidth(titleRef.current.offsetWidth + 25);
    }
  }, [title]);

  const handleBack = () => {
    if (onBack) {
      onBack();
      return;
    }
    navigate(-1);
  };

  return (
    <header className="sticky top-0 z-50 w-full bg-accent-100/5 backdrop-blur-md transition-all">
      <div className="flex h-14 items-center justify-center px-4 pt-5 relative">
        {showBackButton && (
          <button
            type="button"
            onClick={handleBack}
            className="absolute left-4 top-5 flex h-9 w-9 items-center justify-center rounded-full text-primary-100"
            aria-label="뒤로 가기"
          >
            <span className="material-icons text-[28px]">arrow_back</span>
          </button>
        )}

        <h1
          ref={titleRef}
          className="text-[23px] font-bold tracking-tight text-accent-100"
        >
          {title}
        </h1>
      </div>

      {/* 오렌지 포인트 라인 */}
      <div
        className="mx-auto mt-1 h-[3px] rounded-full bg-primary-100 transition-all duration-300"
        style={{ width: lineWidth }}
      />

      {subtitle && (
        <p className="px-4 pb-2 pt-1 text-[13px] text-gray-400">{subtitle}</p>
      )}
    </header>
  );
}

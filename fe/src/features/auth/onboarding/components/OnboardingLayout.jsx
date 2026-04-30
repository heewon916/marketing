import StepProgress from '@/components/common/StepProgress.jsx';

export default function OnboardingLayout({
  currentStep,
  totalStep = 7,
  header,
  children,
  footer,
  contentAlign = 'center',
}) {
  const alignClass =
    contentAlign === 'left'
      ? 'items-start text-left'
      : 'items-center text-center';

  return (
    <div className="min-h-screen w-full flex flex-col px-4 pt-6 pb-20 bg-white">
      {/* 1. 상단 프로그레스 바 영역 */}
      <div className="mb-10 w-full pt-2">
        <StepProgress current={currentStep} total={totalStep} />
      </div>

      {/* 2. 헤더(제목 및 설명) 영역 */}
      {header && (
        <div className="w-full text-left mb-12 min-h-[140px]">
          {header}
        </div>
      )}

      {/* 3. 메인 콘텐츠 영역 */}
      <div className={`flex-1 min-h-0 flex flex-col w-full ${alignClass}`}>
        {children}
      </div>

      {/* 4. 푸터 영역 */}
      {footer && <div className="mt-auto pt-6 w-full">{footer}</div>}
    </div>
  );
}

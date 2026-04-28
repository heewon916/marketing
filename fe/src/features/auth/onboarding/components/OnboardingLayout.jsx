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
    <div className="min-h-screen flex flex-col px-10 pt-16 pb-18 bg-white">
      {/* 1. 상단 프로그레스 바 영역 */}
      <div className="mb-10">
        <StepProgress current={currentStep} total={totalStep} />
      </div>

      {/* 2. 헤더(제목 및 설명) 영역 */}
      {header && (
        <div className="w-full text-left mb-12">
          {header}
        </div>
      )}

      {/* 3. 메인 콘텐츠 영역 */}
      <div className={`flex-1 flex flex-col w-full ${alignClass}`}>
        {children}
      </div>

      {/* 4. 푸터 영역 */}
      {footer && <div className="mt-auto pt-6 w-full">{footer}</div>}
    </div>
  );
}
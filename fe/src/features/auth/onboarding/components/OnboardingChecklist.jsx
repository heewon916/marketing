export default function OnboardingChecklist({ items = [] }) {
  return (
    <div className="flex flex-col mt-8 mb-10 pl-2">
      {items.map((item, idx) => {
        const isLast = idx === items.length - 1;

        return (
          <div
            key={idx}
            className={`relative flex items-start gap-5 ${isLast ? '' : 'pb-12'}`}
          >
            {!isLast && (
              <div className="absolute left-3 top-4 -bottom-4 w-[1.5px] -translate-x-1/2 bg-primary-100" />
            )}

            <div className="relative z-10 w-6 h-6 mt-1 bg-primary-100 rounded-full shrink-0" />

            {/* 텍스트 영역 */}
            <div className="text-left flex flex-col gap-1 mt-0.5 break-keep">

              {/* 타이틀 */}
              <div className="font-semibold text-xl text-gray-900 tracking-tight">
                {item.title}
              </div>

              {/* 설명 */}
              <div className="text-base text-gray-500 tracking-tight">
                {item.desc}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
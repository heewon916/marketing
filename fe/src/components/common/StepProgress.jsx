export default function StepProgress({
  current = 1,
  total = 5,
  className = '',
}) {
  return (
    <div className={`flex items-center gap-3 w-full ${className}`}>
      {/* 숫자 */}
      <div className="text-sm font-semibold text-accent-500 whitespace-nowrap">
        {current} / {total}
      </div>

      {/* 스텝 바 */}
      <div className="flex gap-2 flex-1">
        {Array.from({ length: total }).map((_, idx) => {
          const isActive = idx < current;
          const isCurrent = idx === current - 1;

          return (
            <div
              key={idx}
              className={`
                flex-1 rounded-full transition-all duration-300
                h-2
                ${
                  isActive
                    ? 'bg-primary-100'
                    : 'bg-gray-200 opacity-50'
                }
              `}
            />
          );
        })}
      </div>
    </div>
  );
}
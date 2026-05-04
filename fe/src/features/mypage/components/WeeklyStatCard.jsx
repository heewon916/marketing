import { useEffect, useState } from 'react';

export default function WeeklyStatCard({
  percent,
  plannedCount,
  achievedCount,
}) {
  const [animatedPercent, setAnimatedPercent] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedPercent(percent), 100);
    return () => clearTimeout(timer);
  }, [percent]);

  const radius = 80;
  const strokeWidth = 16;
  const normalizedRadius = radius - strokeWidth / 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset =
    circumference - (animatedPercent / 100) * circumference;

  return (
    <section className="relative overflow-hidden rounded-[32px] bg-white p-8 shadow-sm ring-1 ring-surface-100">
      {/* 부드러운 테마 배경 장식 */}
      <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-surface-100/60 blur-3xl"></div>

      <div className="relative z-10 flex flex-col items-center">
        <div className="relative flex h-[200px] w-[200px] items-center justify-center">
          <svg
            width="200"
            height="200"
            viewBox="0 0 200 200"
            className="-rotate-90 transform drop-shadow-sm"
            aria-hidden="true"
          >
            <circle
              cx="100"
              cy="100"
              r={normalizedRadius}
              fill="transparent"
              stroke="var(--color-surface-100)"
              strokeWidth={strokeWidth}
            />
            <circle
              cx="100"
              cy="100"
              r={normalizedRadius}
              fill="transparent"
              stroke="var(--color-primary-100)"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-all duration-1000 ease-out"
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center">
            {/* <span className="mb-1 text-[13px] font-bold tracking-widest text-gray-400">
              WEEKLY
            </span> */}
            <strong className="text-[48px] font-extrabold leading-none tracking-tighter text-accent-100">
              {animatedPercent}<span className="text-[24px] text-primary-100">%</span>
            </strong>
          </div>
        </div>

        <div className="mt-8 text-center">
          <h2 className="text-[22px] font-bold tracking-tight text-accent-100">
            주간 포스팅 달성률
          </h2>
          <p className="mt-3 text-[16px] font-medium leading-relaxed text-gray-500">
            지난 7일간 계획한 <strong className="text-primary-100">{plannedCount}개</strong>의 게시물 중<br />
            <strong className="text-primary-100">{achievedCount}개</strong>를 달성했어요!
          </p>
        </div>
      </div>
    </section>
  );
}

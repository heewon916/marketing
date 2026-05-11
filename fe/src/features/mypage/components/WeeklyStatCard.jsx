import { useEffect, useState } from 'react';
import CardShell from './CardShell';

export default function WeeklyStatCard({
  percent,
  plannedCount,
  achievedCount,
}) {
  const [animatedPercent, setAnimatedPercent] = useState(0);

  useEffect(() => {
    const targetPercent = Number(percent);

    if (Number.isNaN(targetPercent)) {
      return;
    }

    let animationFrameId;
    let startTime;

    const duration = 900;

    const animate = (currentTime) => {
      if (!startTime) {
        startTime = currentTime;
      }

      const elapsedTime = currentTime - startTime;
      const progress = Math.min(elapsedTime / duration, 1);
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      const currentPercent = Math.round(targetPercent * easedProgress);

      setAnimatedPercent(currentPercent);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animationFrameId);
  }, [percent]);

  const radius = 85;
  const strokeWidth = 18;
  const normalizedRadius = radius - strokeWidth / 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset =
    circumference - (animatedPercent / 100) * circumference;

  return (
    <CardShell className="flex flex-col items-center justify-center py-6">
      <div className="relative flex h-[190px] w-[190px] items-center justify-center">
        <svg
          width="190"
          height="190"
          viewBox="0 0 190 190"
          className="-rotate-90 transform"
          aria-hidden="true"
        >
          <circle
            cx="95"
            cy="95"
            r={normalizedRadius}
            fill="transparent"
            stroke="var(--color-gray-100)"
            strokeWidth={strokeWidth}
          />
          <circle
            cx="95"
            cy="95"
            r={normalizedRadius}
            fill="transparent"
            stroke="var(--color-primary-100)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
          />
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <strong className="text-[50px] font-semibold tracking-tighter text-accent-100">
            {animatedPercent}
            <span className="ml-1 text-[25px] font-medium text-gray-500">
              %
            </span>
          </strong>
        </div>
      </div>

      <div className="mt-4 text-center">
        <h2 className="text-[24px] font-semibold tracking-tight text-accent-100">
          주간 포스팅 달성률
        </h2>

        <p className="mt-2 text-[17px] font-normal leading-relaxed text-gray-500">
          지난 7일간 계획한{' '}
          <strong className="font-semibold text-primary-100">
            {plannedCount}개
          </strong>
          의 게시물 중
          <br />
          <strong className="font-semibold text-primary-100">
            {achievedCount}개
          </strong>
          를 달성했어요!
        </p>
      </div>
    </CardShell>
  );
}

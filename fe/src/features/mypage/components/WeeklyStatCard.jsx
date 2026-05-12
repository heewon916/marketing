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
      const currentPercent = targetPercent * easedProgress;

      setAnimatedPercent(currentPercent);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animationFrameId);
  }, [percent]);

  const displayPercent = animatedPercent.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });

  const progressPercent = Math.min(animatedPercent, 100);

  const radius = 85;
  const strokeWidth = 18;
  const normalizedRadius = radius - strokeWidth / 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset =
    circumference - (progressPercent / 100) * circumference;

  let statusTitle;
  let statusMessage;

  if (achievedCount === 0) {
    statusTitle = '주간 포스팅 현황';
    statusMessage = (
      <>
        목표 <strong className="font-semibold text-primary-100">{plannedCount}개</strong> 중 현재 <strong className="font-semibold text-primary-100">{achievedCount}개</strong> 달성!
        <br />
        기분 좋게 첫 포스팅을 시작해 볼까요?
      </>
    );
  } else if (achievedCount >= plannedCount) {
    statusTitle = '목표 달성 완료';
    statusMessage = (
      <>
        목표 <strong className="font-semibold text-primary-100">{plannedCount}개</strong> 중 <strong className="font-semibold text-primary-100">{achievedCount}개</strong> 달성!
        <br />
        이번 주 목표를 완벽하게 채우셨네요!
      </>
    );
  } else {
    statusTitle = '이번 주 달성률';
    statusMessage = (
      <>
        목표 <strong className="font-semibold text-primary-100">{plannedCount}개</strong> 중 현재 <strong className="font-semibold text-primary-100">{achievedCount}개</strong> 달성!
        <br />
        목표까지 조금만 더 힘내보세요!
      </>
    );
  }

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
            {displayPercent}
            <span className="ml-1 text-[25px] font-medium text-gray-500">
              %
            </span>
          </strong>
        </div>
      </div>

      <div className="mt-4 text-center">
        <h2 className="text-[24px] font-semibold tracking-tight text-accent-100">
          {statusTitle}
        </h2>

        <p className="mt-2 text-[17px] font-normal leading-relaxed text-gray-500">
          {statusMessage}
        </p>
      </div>
    </CardShell>
  );
}

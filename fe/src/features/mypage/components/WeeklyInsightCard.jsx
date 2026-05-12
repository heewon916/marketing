import { useEffect, useState } from 'react';
import Modal from '@/components/common/Modal';
import CardShell from './CardShell';

const DAY_LABELS = ['일', '월', '화', '수', '목', '금', '토'];

const DESCRIPTION_CONTENT = {
  reach: {
    title: '가게 노출수',
    content: (
      <span className="flex flex-col gap-1">
        <span>지난주 인스타그램 계정의 도달 수예요.</span>
        <span>
          수치가 높을수록 더 많은 사람에게
          <br />
          가게를 알린 거예요.
        </span>
      </span>
    ),
  },
  visitIntent: {
    title: '방문 관심도',
    content: (
      <span className="flex flex-col gap-1">
        <span>
          게시물을 본 사람들이
          <br />
          가게에 관심을 보인 정도예요.
        </span>
        <span>
          저장, 공유 수를 도달 수로 나누어
          <br />
          계산해요.
        </span>
      </span>
    ),
  },
};

const formatWeekRange = (weekStart, weekEnd) => {
  if (!weekStart || !weekEnd) {
    return '';
  }

  const startDate = new Date(weekStart);
  const endDate = new Date(weekEnd);

  if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    return '';
  }

  const startMonth = startDate.getMonth() + 1;
  const startDay = startDate.getDate();
  const startDayLabel = DAY_LABELS[startDate.getDay()];

  const endMonth = endDate.getMonth() + 1;
  const endDay = endDate.getDate();
  const endDayLabel = DAY_LABELS[endDate.getDay()];

  return `${startMonth}월 ${startDay}일 (${startDayLabel}) ~ ${endMonth}월 ${endDay}일 (${endDayLabel})`;
};

function useAnimatedNumber(value) {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    const targetValue = Number(value);

    if (Number.isNaN(targetValue)) {
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
      const currentValue = targetValue * easedProgress;

      setAnimatedValue(currentValue);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animationFrameId);
  }, [value]);

  return animatedValue;
}

function InsightMetricItem({
  title,
  value,
  unit,
  descriptionKey,
  valuePrefix,
  valueColorClassName = 'text-primary-100',
  decimalPlaces = 0,
  onDescriptionOpen,
}) {
  const animatedValue = useAnimatedNumber(value);

  const displayValue = animatedValue.toLocaleString(undefined, {
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces,
  });

  return (
    <div className="flex flex-col items-center gap-3 px-2">
      <div className="flex items-center justify-center gap-1.5">
        <h3 className="text-[20px] font-semibold tracking-tight text-accent-100">
          {title}
        </h3>
        <button
          type="button"
          onClick={() => onDescriptionOpen(descriptionKey)}
          className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-gray-200 text-gray-500 active:scale-95 active:bg-gray-300"
          aria-label={`${title} 설명 보기`}
        >
          <span className="material-icons" style={{ fontSize: '13px' }}>
            question_mark
          </span>
        </button>
      </div>

      {/* 수치 데이터 */}
      <div className="mt-3 flex items-baseline justify-center gap-1">
        {valuePrefix && (
          <span
            className={`text-[18px] font-bold ${valueColorClassName}`}
          >
            {valuePrefix}
          </span>
        )}

        <strong
          className={`text-[36px] font-extrabold tracking-tighter ${valueColorClassName}`}
        >
          {displayValue}
        </strong>

        {unit && (
          <span className={`text-[18px] font-medium ${valueColorClassName}`}>
            {unit}
          </span>
        )}
      </div>
    </div>
  );
}

export default function WeeklyInsightCard({
  weekStart,
  weekEnd,
  reachCount,
  visitIntentScore,
}) {
  const [selectedDescription, setSelectedDescription] = useState(null);

  const weekRangeText = formatWeekRange(weekStart, weekEnd);
  const description = selectedDescription
    ? DESCRIPTION_CONTENT[selectedDescription]
    : null;

  const visitIntentDiffRate = (Number(visitIntentScore) - 1) * 100;
  const visitIntentPrefix =
    visitIntentDiffRate > 0 ? '▲' : visitIntentDiffRate < 0 ? '▼' : '';
  const visitIntentValue = Math.abs(visitIntentDiffRate);
  const visitIntentColorClassName =
    visitIntentDiffRate < 0 ? 'text-gray-500' : 'text-primary-100';

  return (
    <>
      <CardShell className="flex flex-col p-6">
        {/* 상단 날짜 뱃지 */}
        {weekRangeText && (
          <div className="mb-2 text-center">
            <span className="inline-block rounded-full bg-surface-100 px-3.5 py-1.5 text-[14px] font-semibold tracking-tight text-primary-100">
              {weekRangeText}
            </span>
          </div>
        )}

        {/* 지표 영역 */}
        <div className="mt-4 flex flex-col items-center gap-6">
          <InsightMetricItem
            title="가게 노출수"
            value={reachCount}
            unit="회"
            descriptionKey="reach"
            valueColorClassName="text-accent-100"
            onDescriptionOpen={setSelectedDescription}
          />

          {/* 구분선 */}
          <div className="w-full border-t border-gray-100" />

          <InsightMetricItem
            title="방문 관심도"
            value={visitIntentValue}
            valuePrefix={visitIntentPrefix}
            unit="%"
            descriptionKey="visitIntent"
            decimalPlaces={0}
            valueColorClassName={visitIntentColorClassName}
            onDescriptionOpen={setSelectedDescription}
          />
        </div>
      </CardShell>

      {/* 모달 */}
      {description && (
        <Modal
          isOpen={Boolean(selectedDescription)}
          onClose={() => setSelectedDescription(null)}
        >
          <div className="flex flex-col items-center text-center p-2">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-surface-100 text-primary-100">
              <span className="material-icons text-[24px]">info</span>
            </div>

            <h3 className="text-[24px] font-extrabold leading-snug text-accent-100">
              {description.title}
            </h3>

            <div className="mt-4 text-[17px] font-medium leading-relaxed text-gray-500">
              {description.content}
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}

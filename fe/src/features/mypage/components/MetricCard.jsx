import { useEffect, useState } from 'react';
import Modal from '@/components/common/Modal';
import CardShell from './CardShell';

export default function MetricCard({
  title,
  modalTitle,
  value,
  unit,
  description,
}) {
  const [isDescriptionOpen, setIsDescriptionOpen] = useState(false);
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
      const currentValue = Math.round(targetValue * easedProgress);

      setAnimatedValue(currentValue);

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    animationFrameId = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(animationFrameId);
  }, [value]);

  return (
    <>
      <CardShell className="relative flex min-h-[160px] min-w-0 flex-col justify-between p-5">
        <div className="flex items-start justify-between gap-1">
          <h3 className="pr-7 text-[18px] font-bold leading-snug text-accent-100">
            {title}
          </h3>

          {description && (
            <button
              type="button"
              onClick={() => setIsDescriptionOpen(true)}
              className="absolute right-4 top-4 flex h-6 w-6 items-center justify-center rounded-full bg-gray-100 text-gray-500"
              aria-label={`${modalTitle || '지표'} 설명 보기`}
            >
              <span className="material-icons" style={{ fontSize: '16px' }}>
                question_mark
              </span>
            </button>
          )}
        </div>

        <div className="flex w-full items-baseline justify-end gap-1.5 text-right">
          <strong className="text-[38px] font-semibold tracking-tight text-accent-100">
            {animatedValue.toLocaleString()}
          </strong>

          {unit && (
            <span className="text-[16px] font-medium text-gray-400">
              {unit}
            </span>
          )}
        </div>
      </CardShell>

      {description && (
        <Modal
          isOpen={isDescriptionOpen}
          onClose={() => setIsDescriptionOpen(false)}
        >
          <div className="text-center">
            <h3 className="text-[28px] font-extrabold leading-snug text-primary-100">
              {modalTitle || title}
            </h3>

            <div className="mt-5 text-[18px] font-medium leading-relaxed text-gray-600">
              {description}
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}

import DayTimeRow from '@/features/auth/onboarding/components/DayTimeRow';
import Button from '@/components/common/Button';
import CardShell from './CardShell';

export default function OperatingHoursEdit({
  hours,
  onChange,
  onCancel,
  onSave,
}) {
  const updateDay = (index, key, value) => {
    const updatedHours = hours.map((item, currentIndex) => {
      if (currentIndex !== index) return item;

      return {
        ...item,
        [key]: value,
      };
    });

    onChange(updatedHours);
  };

  return (
    <CardShell className="flex flex-col gap-6 px-7 py-8">
      <h2 className="text-[15px] font-semibold text-gray-400">영업시간</h2>

      <div className="flex flex-col gap-3">
        {hours.map((item, index) => (
          <DayTimeRow
            key={item.day}
            day={item.day}
            isOpen={item.isOpen}
            startTime={item.startTime}
            endTime={item.endTime}
            onToggle={() => updateDay(index, 'isOpen', !item.isOpen)}
            onStartTimeChange={(value) => updateDay(index, 'startTime', value)}
            onEndTimeChange={(value) => updateDay(index, 'endTime', value)}
          />
        ))}
      </div>

      <div className="mt-2 flex justify-center gap-3">
        <Button
          size="sm"
          variant="white"
          onClick={onCancel}
          className="text-[18px] font-bold"
        >
          취소
        </Button>

        <Button
          size="sm"
          variant="primary"
          onClick={onSave}
          className="text-[18px] font-bold"
        >
          저장하기
        </Button>
      </div>
    </CardShell>
  );
}

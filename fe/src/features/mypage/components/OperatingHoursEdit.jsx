import DayTimeRow from '@/features/auth/onboarding/components/DayTimeRow';
import CardShell from './CardShell';

export default function OperatingHoursEdit({ hours, onChange }) {
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
    </CardShell>
  );
}

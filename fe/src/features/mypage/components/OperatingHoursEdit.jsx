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
    <CardShell className="flex flex-col gap-3 p-5">
      {hours.map((item, index) => (
        <DayTimeRow
          key={item.day}
          day={item.day}
          isOpen={item.isOpen}
          startTime={item.startTime}
          endTime={item.endTime}
          onToggle={() => updateDay(index, 'isOpen', !item.isOpen)}
          onStartTimeChange={(value) =>
            updateDay(index, 'startTime', value)
          }
          onEndTimeChange={(value) =>
            updateDay(index, 'endTime', value)
          }
        />
      ))}
    </CardShell>
  );
}

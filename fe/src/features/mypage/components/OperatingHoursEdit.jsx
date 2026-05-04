import DayTimeRow from '@/features/auth/onboarding/components/DayTimeRow';

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
    <div className="flex flex-col gap-3">
      {hours.map((item, index) => (
        <DayTimeRow
          key={item.day}
          dayData={item}
          onChange={(key, value) => updateDay(index, key, value)}
        />
      ))}
    </div>
  );
}

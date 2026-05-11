import { useState } from 'react';
import DayTimeRow from '@/features/auth/onboarding/components/DayTimeRow';
import Button from '@/components/common/Button';
import CardShell from './CardShell';
import {
  convertApiCloseTimeToDisplayTime,
  convertDisplayCloseTimeToApiTime,
} from '@/utils/operatingHours.js';

const convertHoursToDisplayHours = (hours) =>
  hours.map((item) => ({
    ...item,
    endTime: convertApiCloseTimeToDisplayTime(item.endTime),
  }));

const convertHoursToApiHours = (hours) =>
  hours.map((item) => ({
    ...item,
    endTime: item.isOpen
      ? convertDisplayCloseTimeToApiTime(item.startTime, item.endTime)
      : null,
  }));

export default function OperatingHoursEdit({
  hours,
  onChange,
  onCancel,
  onSave,
}) {
  const [editableHours, setEditableHours] = useState(() =>
    convertHoursToDisplayHours(hours)
  );

  const updateDay = (index, key, value) => {
    setEditableHours((prev) => {
      const updatedHours = prev.map((item, currentIndex) => {
        if (currentIndex !== index) return item;

        return {
          ...item,
          [key]: value,
        };
      });

      onChange?.(updatedHours);

      return updatedHours;
    });
  };

  const handleSave = () => {
    const apiHours = convertHoursToApiHours(editableHours);

    onChange?.(apiHours);
    onSave?.(apiHours);
  };

  return (
    <CardShell className="flex flex-col gap-6 px-7 py-8">
      <h2 className="text-[15px] font-semibold text-gray-400">영업시간</h2>

      <div className="flex flex-col gap-3">
        {editableHours.map((item, index) => (
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
          onClick={handleSave}
          className="text-[18px] font-bold"
        >
          저장하기
        </Button>
      </div>
    </CardShell>
  );
}

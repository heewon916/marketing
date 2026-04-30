import ToggleSwitch from './ToggleSwitch.jsx';
import TimeInput from './TimeInput.jsx';

export default function DayTimeRow({
  day,
  isOpen,
  startTime,
  endTime,
  onToggle,
  onStartTimeChange,
  onEndTimeChange,
}) {
  return (
    <div className="grid grid-cols-[70px_36px_1fr] items-center w-full py-1.5 gap-2">
      {/* 1. 요일 */}
      <div className="whitespace-nowrap">
        <span
          className={`text-[20px] font-bold ${
            isOpen ? 'text-gray-900' : 'text-gray-400'
          }`}
        >
          {day}요일
        </span>
      </div>

      {/* 2. 토글 */}
      <div className="flex justify-center">
        <ToggleSwitch checked={isOpen} onChange={onToggle} />
      </div>

      {/* 3. 시간 */}
      <div className="flex items-center justify-end gap-2 min-w-0">
        <TimeInput
          value={startTime}
          onChange={onStartTimeChange}
          disabled={!isOpen}
        />
        <span className="text-gray-400 font-medium">-</span>
        <TimeInput
          value={endTime}
          onChange={onEndTimeChange}
          disabled={!isOpen}
        />
      </div>
    </div>
  );
}

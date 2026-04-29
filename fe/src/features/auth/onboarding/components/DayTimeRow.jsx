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
    <div className="flex items-center w-full py-1.5">
      
      {/* 1. 요일 */}
      <div className="w-[60px] shrink-0">
        <span
          className={`text-[17px] font-bold ${
            isOpen ? 'text-gray-900' : 'text-gray-400'
          }`}
        >
          {day}요일
        </span>
      </div>

      {/* 2. 토글 */}
      <div className="flex-1 flex justify-start pl-2">
        <ToggleSwitch checked={isOpen} onChange={onToggle} />
      </div>

      {/* 3. 시간 */}
      <div className="flex items-center gap-1.5 shrink-0">
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
import Button from '@/components/common/Button';
import CardShell from '../components/CardShell';

export default function OperatingHoursList({ hours, onEdit }) {
  return (
    <CardShell className="flex flex-col px-7 py-8">
      <h3 className="text-[15px] font-semibold text-gray-400">영업시간</h3>

      <ul className="mt-6 flex flex-col gap-4">
        {hours.map(({ day, isOpen, startTime, endTime }) => (
          <li
            key={day}
            className="grid grid-cols-[80px_1fr] items-center text-[18px] font-bold text-accent-100"
          >
            <span>{day}요일</span>
            <span className="text-right">
              {isOpen ? `${startTime} - ${endTime}` : '휴무'}
            </span>
          </li>
        ))}
      </ul>

      <Button
        size="lg"
        variant="primary"
        onClick={onEdit}
        className="mt-8 w-full text-[18px] font-bold"
      >
        수정하기
      </Button>
    </CardShell>
  );
}

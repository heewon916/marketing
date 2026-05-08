import CardShell from './CardShell';

export default function OperatingHoursList({ hours }) {
  return (
    <CardShell className="flex flex-col gap-8 px-7 py-8">
      <h2 className="text-[15px] font-semibold text-gray-400">영업시간</h2>

      <div className="flex flex-col gap-5">
        {hours.map((item) => (
          <div
            key={item.day}
            className="grid grid-cols-[80px_1fr] items-center text-[18px]"
          >
            <span className="font-bold text-accent-100">{item.day}요일</span>

            <span className="text-right font-medium text-accent-100">
              {item.isOpen ? `${item.startTime} - ${item.endTime}` : '휴무'}
            </span>
          </div>
        ))}
      </div>
    </CardShell>
  );
}

import CardShell from './CardShell';

export default function OperatingHoursList({ hours }) {
  return (
    <CardShell className="flex flex-col gap-5 p-5">
      {hours.map((item) => (
        <div
          key={item.day}
          className="grid grid-cols-[72px_1fr] items-center border-b border-gray-100 pb-5 last:border-b-0 last:pb-0"
        >
          <span className="text-[18px] font-bold text-accent-100">
            {item.day}요일
          </span>

          <span className="text-right text-[18px] font-semibold text-accent-100">
            {item.isOpen
              ? `${item.startTime} - ${item.endTime}`
              : '휴무'}
          </span>
        </div>
      ))}
    </CardShell>
  );
}

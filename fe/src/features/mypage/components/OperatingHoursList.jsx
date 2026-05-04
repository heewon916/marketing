export default function OperatingHoursList({ hours }) {
  return (
    <div className="flex flex-col gap-7 px-3">
      {hours.map((item) => (
        <div
          key={item.day}
          className="grid grid-cols-[90px_1fr] items-center"
        >
          <span className="text-[22px] font-extrabold text-accent-100">
            {item.day}요일
          </span>

          <span className="text-right text-[22px] font-semibold text-accent-100">
            {item.isOpen
              ? `${item.startTime} - ${item.endTime}`
              : '휴무'}
          </span>
        </div>
      ))}
    </div>
  );
}

const TIME_LIMIT = {
  hour: 24,
  minute: 60,
};

const formatTime = (numbers) => {
  if (numbers.length <= 2) return numbers;
  return `${numbers.slice(0, 2)}:${numbers.slice(2)}`;
};

const isValidTime = (formatted, limit = TIME_LIMIT) => {
  const [h, m] = formatted.split(':');

  if (!h) return true;

  const hour = Number(h);
  const minute = m ? Number(m) : null;

  if (hour === 24 && minute === 0) return true;

  if (hour >= limit.hour) return false;
  if (minute !== null && minute >= limit.minute) return false;

  return true;
};

export default function TimeInput({
  value,
  onChange,
  disabled,
  ...props
}) {
  const handleChange = (e) => {
    const raw = e.target.value;

    // 숫자만
    const numbers = raw.replace(/\D/g, '').slice(0, 4);

    const formatted = formatTime(numbers);

    if (!isValidTime(formatted)) return;

    onChange?.(formatted);
  };

  return (
    <input
      type="text"
      inputMode="numeric"
      value={value}
      onChange={handleChange}
      disabled={disabled}
      placeholder="00:00"
      className="
        w-[88px] px-2 py-2 text-center
        text-lg font-semibold
        border border-gray-200 rounded-xl
        outline-none transition-all

        focus:border-primary-100
        focus:ring-4 focus:ring-primary-100/10

        disabled:bg-gray-100
        disabled:text-gray-400
        disabled:border-transparent
      "
      {...props}
    />
  );
}
export default function MetricCard({ title, value, unit = '%', isUp = true }) {
  return (
    <section className="flex min-h-[150px] flex-1 flex-col items-center justify-center rounded-3xl border border-gray-100 bg-white px-4 py-6 shadow-sm">
      <h3 className="text-center text-[19px] font-extrabold leading-snug text-accent-100">
        {title}
      </h3>

      <div className="mt-5 flex items-center gap-1 text-primary-100">
        <strong className="text-[32px] font-extrabold leading-none">
          {value}
          {unit}
        </strong>
        <span className="text-[27px] font-extrabold leading-none">
          {isUp ? '↑' : '↓'}
        </span>
      </div>
    </section>
  );
}

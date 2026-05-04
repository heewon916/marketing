export default function InfoItem({ label, value }) {
  return (
    <div className="border-b border-gray-100 pb-5 last:border-b-0 last:pb-0">
      <dt className="text-[15px] font-semibold text-gray-400">
        {label}
      </dt>

      <dd className="mt-2 whitespace-pre-line text-[20px] font-bold leading-relaxed text-accent-100">
        {value}
      </dd>
    </div>
  );
}

export default function InfoItem({ label, value }) {
  return (
    <div>
      <dt className="text-[18px] font-bold text-gray-500">
        {label}
      </dt>

      <dd className="mt-5 whitespace-pre-line pl-3 text-[22px] font-bold leading-relaxed text-black">
        {value}
      </dd>
    </div>
  );
}

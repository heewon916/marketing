export default function AccountProfile({
  storeName,
  instagramUsername,
}) {
  return (
    <section className="flex flex-col items-center">
      <strong className="mt-4 text-[24px] font-extrabold leading-tight text-accent-100">
        {storeName}
      </strong>

      <span className="mt-1 text-[20px] font-bold leading-tight text-gray-500">
        {instagramUsername}
      </span>
    </section>
  );
}

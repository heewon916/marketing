import CardShell from './CardShell';

export default function AccountProfile({ storeName, instagramUsername }) {
  return (
    <CardShell className="flex flex-col items-center justify-center p-6 text-center">
      <strong className="text-[24px] font-extrabold tracking-tight text-accent-100">
        {storeName}
      </strong>

      <span className="mt-1 text-[17px] font-medium text-gray-500">
        {instagramUsername}
      </span>
    </CardShell>
  );
}

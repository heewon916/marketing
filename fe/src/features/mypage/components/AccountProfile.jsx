// import defaultProfileImage from '@/assets/character/CharacterDdabong.png';

export default function AccountProfile({
  // imageSrc = defaultProfileImage,
  storeName,
  instagramUsername,
}) {
  return (
    <section className="flex flex-col items-center">
      {/* <div className="h-[104px] w-[104px] overflow-hidden rounded-full border-4 border-white bg-surface-100 shadow-lg">
        <img
          src={imageSrc}
          alt={`${storeName} 프로필 이미지`}
          className="h-full w-full object-cover"
        />
      </div> */}

      <strong className="mt-4 text-[24px] font-extrabold leading-tight text-accent-100">
        {storeName}
      </strong>

      <span className="mt-1 text-[20px] font-bold leading-tight text-gray-500">
        {instagramUsername}
      </span>
    </section>
  );
}

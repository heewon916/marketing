export default function MyPageHeader({ title = '내 정보'}) {

  return (
    <header className="sticky top-0 z-50 flex h-14 w-full items-center justify-center px-4 pt-5 backdrop-blur-md transition-all">
      <h1 className="text-[19px] font-bold tracking-tight text-accent-100">
        {title}
      </h1>
    </header>
  );
}

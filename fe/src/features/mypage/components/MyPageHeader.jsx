import { useNavigate } from 'react-router-dom';

export default function MyPageHeader({ title = '내 정보'}) {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-50 flex h-14 w-full items-center justify-center bg-surface-200/80 px-4 backdrop-blur-md transition-all">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="absolute left-4 flex h-10 w-10 items-center justify-center rounded-full bg-white text-accent-100 shadow-sm transition-colors hover:bg-surface-100 active:scale-95"
        aria-label="뒤로가기"
      >
        <span className="material-icons text-[26px]">arrow_back</span>
      </button>

      <h1 className="text-[19px] font-bold tracking-tight text-accent-100">
        {title}
      </h1>
    </header>
  );
}

import { useNavigate } from 'react-router-dom';

export default function AccountHeader({ title = '계정 정보' }) {
  const navigate = useNavigate();

  return (
    <header className="relative flex h-14 w-full items-center justify-center">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="absolute left-0 flex h-11 w-11 items-center justify-center rounded-2xl bg-gray-100 text-accent-100"
        aria-label="뒤로가기"
      >
        <span className="material-icons text-[28px]">arrow_back</span>
      </button>

      <h1 className="text-[22px] font-extrabold text-accent-100">
        {title}
      </h1>
    </header>
  );
}

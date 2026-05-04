import { useNavigate } from 'react-router-dom';

export default function AccountHeader({
  title = '계정 정보',
  hideBackButton = false,
}) {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-50 flex h-14 w-full items-center justify-center px-4 pt-5 backdrop-blur-md transition-all">
      {!hideBackButton && (
        <button
          type="button"
          onClick={() => navigate('/mypage')}
          className="absolute left-4 top-5 flex h-9 w-9 items-center justify-center rounded-full text-accent-100"
          aria-label="마이페이지로 이동"
        >
          <span className="material-icons text-[28px]">arrow_back</span>
        </button>
      )}

      <h1 className="text-[19px] font-bold tracking-tight text-accent-100">
        {title}
      </h1>
    </header>
  );
}

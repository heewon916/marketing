import { useNavigate, useLocation } from 'react-router-dom';
import { GoHomeFill } from 'react-icons/go';
import { IoPerson } from 'react-icons/io5';

function BottomTab({ fixed = true }) {
  const navigate = useNavigate();
  const location = useLocation();

  const currentPath = location.pathname;

  const isHome =
    currentPath.startsWith('/home') ||
    currentPath.startsWith('/post-create');

  const isMyPage = currentPath.startsWith('/mypage');

  return (
    <div
      className={[
        'w-full max-w-md bg-white border-t border-gray-200',
        fixed
          ? 'fixed bottom-0 left-1/2 -translate-x-1/2'
          : 'mx-auto shrink-0',
      ].join(' ')}
    >
      <div className="flex h-20">
        {/* 홈 */}
        <button
          type="button"
          onClick={() => {
            if (currentPath !== '/home') {
              navigate('/home');
            }
          }}
          className="flex-1 flex flex-col items-center justify-center"
        >
          <GoHomeFill
            className={`text-[32px] ${
              isHome
                ? 'text-[var(--color-primary-100)]'
                : 'text-gray-400'
            }`}
          />

          <span
            className={
              isHome
                ? 'text-[var(--color-primary-100)] text-lg font-medium'
                : 'text-gray-400 text-lg'
            }
          >
            홈
          </span>
        </button>

        {/* 내 정보 */}
        <button
          type="button"
          onClick={() => {
            if (currentPath !== '/mypage') {
              navigate('/mypage');
            }
          }}
          className="flex-1 flex flex-col items-center justify-center"
        >
          <IoPerson
            className={`text-[32px] ${
              isMyPage
                ? 'text-[var(--color-primary-100)]'
                : 'text-gray-400'
            }`}
          />

          <span
            className={
              isMyPage
                ? 'text-[var(--color-primary-100)] text-lg font-medium'
                : 'text-gray-400 text-lg'
            }
          >
            내 정보
          </span>
        </button>
      </div>
    </div>
  );
}

export default BottomTab;

import { useNavigate, useLocation } from 'react-router-dom';

function BottomTab() {
  const navigate = useNavigate();
  const location = useLocation();

  const currentPath = location.pathname;

  return (
    <div className="fixed bottom-0 left-1/2 -translate-x-1/2 w-full max-w-md bg-white border-t border-gray-200">
      
      <div className="flex h-20">

        {/* 홈 */}
        <button
          onClick={() => navigate('/home')}
          className="flex-1 flex flex-col items-center justify-center"
        >
          <span
            className={`material-icons text-5xl scale-150 ${
              currentPath === '/home'
                ? 'text-[var(--color-primary-100)]'
                : 'text-gray-400'
            }`}
          >
            home
          </span>

          <span
            className={
              currentPath === '/home'
                ? 'text-[var(--color-primary-100)] text-lg font-medium'
                : 'text-gray-400 text-lg'
            }
          >
            홈
          </span>
        </button>

        {/* 내 정보 */}
        <button
          onClick={() => navigate('/mypage')}
          className="flex-1 flex flex-col items-center justify-center"
        >
          <span
            className={`material-icons text-5xl scale-150 ${
              currentPath === '/mypage'
                ? 'text-[var(--color-primary-100)]'
                : 'text-gray-400'
            }`}
          >
            person
          </span>

          <span
            className={
              currentPath === '/mypage'
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

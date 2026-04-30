import { useNavigate } from 'react-router-dom';
import Button from '@/components/common/Button.jsx';
import Character from '@/assets/character/CharacterDdabong.png';

function LandingPage() {
  const navigate = useNavigate();

  const handleOnboarding = () => {
    navigate('/auth/onboarding');
  };
  
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
      
      {/* 상단 뱃지 */}
      <div className="mb-4 px-5 py-1.5 bg-surface-100 rounded-full text-base font-medium text-gray-500">
        사장님의 든든한 AI 손녀딸
      </div>

      {/* 메인 텍스트 */}
      <h1 className="text-4xl font-extrabold text-accent-100 mb-2 tracking-tight">
        이제 맡겨주세요
      </h1>

      <h2 className="text-6xl font-extrabold text-primary-100 mb-8 tracking-tight">
        맡케팅
      </h2>

      {/* 캐릭터 */}
      <img
        src={Character}
        alt="character"
        className="w-full max-w-[340px] mb-12"
      />

      {/* TODO: 인스타그램 OAuth API 연동 */}
      <Button className="w-full max-w-[340px] font-bold shadow-lg shadow-primary-100/40 mb-6">
        인스타그램으로 로그인
      </Button>

      <button
        onClick={handleOnboarding}
        className="text-gray-400 text-lg font-medium"
      >
        처음이세요? 제가 도와드릴게요
      </button>

    </main>
  );
}

export default LandingPage;
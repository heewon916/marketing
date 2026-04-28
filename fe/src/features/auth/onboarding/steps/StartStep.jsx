import Button from '@/components/common/Button.jsx';
import Character from '@/assets/character/CharacterDdabong.png';

function StartStep({ onNext }) {
  return (
    <div className="flex flex-col items-center text-center px-6">
      
      {/* 캐릭터 */}
      <img
        src={Character}
        alt="character"
        className="w-full max-w-[280px] mb-8"
      />

      {/* 텍스트 */}
      <h1 className="text-2xl font-bold text-accent-100 mb-2">
        반가워요 사장님!
      </h1>

      <p className="text-gray-500 text-base mb-10">
        맡케팅 시작을 위해<br />
        몇 가지만 설정해볼게요
      </p>

      {/* 버튼 */}
      <Button
        onClick={onNext}
        className="w-full max-w-[340px] font-bold shadow-lg shadow-primary-100/40"
      >
        시작하기
      </Button>

    </div>
  );
}

export default StartStep;
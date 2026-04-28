import Button from '@/components/common/Button.jsx';
import Character from '@/assets/character/CharacterDdabong.png';

function InstagramConnectStep({ onNext, onPrev }) {
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
        인스타그램 계정을 연결해주세요
      </h1>

      <p className="text-gray-500 text-base mb-10">
        마케팅 자동화를 위해<br />
        인스타그램 계정 연결이 필요해요
      </p>

      {/* 인스타 연결 버튼 */}
      <Button
        onClick={onNext}
        className="w-full max-w-[340px] font-bold shadow-lg shadow-primary-100/40 mb-4"
      >
        인스타그램 연결하기
      </Button>

      {/* 뒤로가기 */}
      <button
        onClick={onPrev}
        className="text-gray-400 text-sm"
      >
        이전으로
      </button>

    </div>
  );
}

export default InstagramConnectStep;
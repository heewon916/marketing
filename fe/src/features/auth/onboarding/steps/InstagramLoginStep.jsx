function InstagramLoginStep({ onNext, onPrev }) {
  return (
    <div className="flex flex-col items-center text-center px-6">
      <h1 className="text-xl font-bold mb-4">인스타그램 로그인 진행</h1>

      <button
        onClick={onNext}
        className="mb-4 px-4 py-2 bg-black text-white rounded"
      >
        로그인 완료 (다음)
      </button>

      <button
        onClick={onPrev}
        className="text-gray-400 text-sm"
      >
        이전
      </button>
    </div>
  );
}

export default InstagramLoginStep;
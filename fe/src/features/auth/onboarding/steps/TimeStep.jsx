function TimeStep({ onNext, onPrev }) {
  return (
    <div className="flex flex-col items-center text-center px-6">
      <h1 className="text-xl font-bold mb-4">영업시간을 설정해주세요</h1>

      <input
        type="text"
        placeholder="예: 09:00 ~ 21:00"
        className="mb-4 border px-3 py-2 rounded"
      />

      <button
        onClick={onNext}
        className="mb-4 px-4 py-2 bg-black text-white rounded"
      >
        다음
      </button>

      <button onClick={onPrev} className="text-gray-400 text-sm">
        이전
      </button>
    </div>
  );
}

export default TimeStep;
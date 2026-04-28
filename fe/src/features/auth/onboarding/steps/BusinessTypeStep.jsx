function BusinessTypeStep({ onNext, onPrev }) {
  return (
    <div className="flex flex-col items-center text-center px-6">
      <h1 className="text-xl font-bold mb-4">업종을 선택해주세요</h1>

      <button className="mb-2 px-4 py-2 border rounded">카페</button>
      <button className="mb-4 px-4 py-2 border rounded">음식점</button>

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

export default BusinessTypeStep;
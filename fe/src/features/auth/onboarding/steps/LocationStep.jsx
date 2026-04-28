function LocationStep({ onNext, onPrev }) {
  return (
    <div className="flex flex-col items-center text-center px-6">
      <h1 className="text-xl font-bold mb-4">매장 위치를 입력해주세요</h1>

      <input
        type="text"
        placeholder="주소 입력"
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

export default LocationStep;
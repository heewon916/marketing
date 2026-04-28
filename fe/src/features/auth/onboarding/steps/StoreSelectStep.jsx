function StoreSelectStep({ onNext, onPrev }) {
  return (
    <div className="flex flex-col items-center text-center px-6">
      <h1 className="text-xl font-bold mb-4">매장을 선택해주세요</h1>

      <button className="mb-4 px-4 py-2 border rounded">
        매장 1
      </button>

      <button
        onClick={onNext}
        className="mb-4 px-4 py-2 bg-black text-white rounded"
      >
        선택 완료 (다음)
      </button>

      <button onClick={onPrev} className="text-gray-400 text-sm">
        이전
      </button>
    </div>
  );
}

export default StoreSelectStep;
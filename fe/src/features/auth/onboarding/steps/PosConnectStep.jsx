function PosConnectStep({ onNext, onPrev }) {
  return (
    <div className="flex flex-col items-center text-center px-6">
      <h1 className="text-xl font-bold mb-4">POS 연동이 필요해요</h1>

      <button
        onClick={onNext}
        className="mb-4 px-4 py-2 bg-black text-white rounded"
      >
        POS 연결하기 (다음)
      </button>

      <button onClick={onPrev} className="text-gray-400 text-sm">
        이전
      </button>
    </div>
  );
}

export default PosConnectStep;
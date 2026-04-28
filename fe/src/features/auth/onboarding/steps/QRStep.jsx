function QRStep({ onNext, onPrev }) {
  return (
    <div className="flex flex-col items-center text-center px-6">
      <h1 className="text-xl font-bold mb-4">QR을 스캔해주세요</h1>

      <div className="w-[200px] h-[200px] bg-gray-200 mb-4 flex items-center justify-center">
        QR 영역
      </div>

      <button
        onClick={onNext}
        className="mb-4 px-4 py-2 bg-black text-white rounded"
      >
        스캔 완료 (다음)
      </button>

      <button onClick={onPrev} className="text-gray-400 text-sm">
        이전
      </button>
    </div>
  );
}

export default QRStep;
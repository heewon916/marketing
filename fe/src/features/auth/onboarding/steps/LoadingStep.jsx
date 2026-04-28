function LoadingStep({ onNext }) {
  return (
    <div className="flex flex-col items-center text-center px-6">
      <h1 className="text-xl font-bold mb-4">연동 중입니다...</h1>

      <div className="mb-6">⏳ 로딩중</div>

      <button
        onClick={onNext}
        className="px-4 py-2 bg-black text-white rounded"
      >
        다음
      </button>
    </div>
  );
}

export default LoadingStep;
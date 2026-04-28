function InstagramSuccessStep({ onNext }) {
  return (
    <div className="flex flex-col items-center text-center px-6">
      <h1 className="text-xl font-bold mb-4">인스타그램 연결 완료</h1>

      <button
        onClick={onNext}
        className="px-4 py-2 bg-black text-white rounded"
      >
        다음
      </button>
    </div>
  );
}

export default InstagramSuccessStep;

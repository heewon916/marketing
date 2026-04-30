export default function StaticMap({
  storeName,
  position = { x: '50%', y: '50%' },
}) {
  return (
    <div className="relative w-full h-[320px] bg-[#F2F4F2] rounded-2xl border border-gray-200 overflow-hidden mt-4">
      
      {/* 배경 */}
      <div className="absolute inset-0 opacity-50">
        <div className="absolute top-1/2 w-full h-4 bg-white -translate-y-1/2"></div>
        <div className="absolute left-2/3 w-4 h-full bg-white -translate-x-1/2"></div>
      </div>

      {/* 마커 */}
      <div
        className="absolute flex flex-col items-center -translate-x-1/2 -translate-y-[40px]"
        style={{ top: position.y, left: position.x }}
      >
        <span className="material-icons text-[48px] text-primary-100 drop-shadow-md">
          location_on
        </span>

        <div className="mt-1 px-3 py-1.5 bg-white rounded-full shadow-md text-[13px] font-bold text-gray-800 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-primary-100"></span>
          {storeName || '가게 위치'}
        </div>
      </div>
    </div>
  );
}
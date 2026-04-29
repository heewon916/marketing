import { memo } from 'react';

function StoreCard({ store, isSelected, onSelect }) {
  return (
    <div
      onClick={() => onSelect(store.id)}
      className={`
        px-5 py-4 rounded-2xl border cursor-pointer transition-all flex justify-between items-center
        ${isSelected
          ? 'border-primary-100 bg-white ring-4 ring-primary-100/20'
          : 'border-gray-200 bg-white'}
      `}
    >
      {/* 텍스트 */}
      <div>
        <div className="font-bold text-gray-900 text-[17px]">
          {store.name}
        </div>
        <div className="text-[14px] text-gray-400 mt-0.5">
          {store.address}
        </div>
      </div>

      {/* 체크 UI */}
      <div
        className={`
          w-5 h-5 rounded-[6px] border flex items-center justify-center transition-colors
          ${isSelected
            ? 'bg-primary-100 border-primary-100 text-white'
            : 'border-gray-300 bg-white'}
        `}
      >
        {isSelected && (
          <span className="material-icons text-xs scale-[0.7]">
            check
          </span>
        )}
      </div>
    </div>
  );
}

export default memo(StoreCard);
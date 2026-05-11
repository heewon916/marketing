const tabs = [
  { key: 'stats', label: '통계' },
  { key: 'info', label: '기본정보' },
  { key: 'hours', label: '영업시간' },
];

export default function MyPageTabSwitcher({ activeTab, onChange }) {
  return (
    <nav className="border-b border-gray-200 bg-white">
      <div className="mx-auto grid h-10 w-full max-w-[430px] grid-cols-3">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;

          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => onChange(tab.key)}
              className={[
                'relative flex items-center justify-center text-[16px] transition-colors',
                isActive ? 'font-bold text-black' : 'font-medium text-gray-400',
              ].join(' ')}
            >
              {tab.label}

              {isActive && (
                <span className="absolute bottom-[-1px] left-1/2 h-[2px] w-20 -translate-x-1/2 rounded-full bg-black" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

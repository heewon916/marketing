const tabs = [
  { key: 'info', label: '기본정보' },
  { key: 'hours', label: '영업시간' },
];

export default function AccountTabSwitcher({ activeTab, onChange }) {
  return (
    <div className="grid h-13 w-full grid-cols-2 rounded-[20px] border border-gray-200 bg-white p-1">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;

        return (
          <button
            key={tab.key}
            type="button"
            onClick={() => onChange(tab.key)}
            className={[
              'flex items-center justify-center rounded-[16px] text-[17px] font-bold transition-colors',
              isActive
                ? 'bg-accent-100 text-white'
                : 'bg-transparent text-gray-500',
            ].join(' ')}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

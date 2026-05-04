const tabs = [
  { key: 'info', label: '기본정보' },
  { key: 'hours', label: '영업시간' },
];

export default function AccountTabSwitcher({ activeTab, onChange }) {
  return (
    <div className="grid h-14 w-full grid-cols-2 rounded-2xl bg-gray-100 p-0">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;

        return (
          <button
            key={tab.key}
            type="button"
            onClick={() => onChange(tab.key)}
            className={[
              'flex items-center justify-center rounded-2xl text-[18px] font-extrabold transition-colors',
              isActive
                ? 'bg-accent-100 text-white'
                : 'bg-transparent text-accent-100',
            ].join(' ')}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export default function OnboardingChecklist({ items = [] }) {
  return (
    <div className="flex flex-col mt-8 mb-10 pl-1">
      {items.map((item, idx) => {
        const number = idx + 1;

        return (
          <div
            key={idx}
            className="relative flex items-start gap-5 pb-8 last:pb-0"
          >
            <div className="relative z-10 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary-100/15">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-100 text-base font-bold leading-none text-white pb-[1px]">
                {number}
              </div>
            </div>

            <div className="flex flex-col gap-1 pt-0.5 text-left break-keep">
              <div className="text-xl font-bold tracking-tight text-gray-900">
                {item.title}
              </div>

              <div className="text-base font-small tracking-tight text-gray-500">
                {item.desc}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

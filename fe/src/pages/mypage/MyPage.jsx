import { useState } from 'react';
import BottomTab from '@/components/common/BottomTab';
import MyPageHeader from '@/features/mypage/components/MyPageHeader';
import MyPageTabSwitcher from '@/features/mypage/components/MyPageTabSwitcher';
import MyPageStatsSection from '@/features/mypage/sections/MyPageStatsSection';
import AccountInfoSection from '@/features/mypage/sections/AccountInfoSection';
import OperatingHoursSection from '@/features/mypage/sections/OperatingHoursSection';

const myPageMockData = {
  storeName: '싸피 카페',
  instagramUsername: '@ssafy_cafe',
  weeklyPostAchievementRate: 25,
  targetPostCount: 4,
  achievedPostCount: 1,
  weeklyReachCount: 17,
  weeklyVisitIntentScore: 29,
};

export default function MyPage() {
  const [activeTab, setActiveTab] = useState('stats');

  const handleLogout = () => {
    // TODO: 실제 로그아웃 로직 연결
    console.log('로그아웃');
  };

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-[#f4f4f6]">
      <MyPageHeader
        storeName={myPageMockData.storeName}
        instagramUsername={myPageMockData.instagramUsername}
        onLogout={handleLogout}
      />

      <MyPageTabSwitcher activeTab={activeTab} onChange={setActiveTab} />

      <main className="mx-auto flex w-full max-w-[430px] flex-1 flex-col gap-2 overflow-y-auto px-5 pt-4 pb-[100px]">
        {activeTab === 'stats' && (
          <MyPageStatsSection
            weeklyPostAchievementRate={myPageMockData.weeklyPostAchievementRate}
            targetPostCount={myPageMockData.targetPostCount}
            achievedPostCount={myPageMockData.achievedPostCount}
            weeklyReachCount={myPageMockData.weeklyReachCount}
            weeklyVisitIntentScore={myPageMockData.weeklyVisitIntentScore}
          />
        )}

        {activeTab === 'info' && <AccountInfoSection />}

        {activeTab === 'hours' && <OperatingHoursSection />}
      </main>

      <BottomTab />
    </div>
  );
}

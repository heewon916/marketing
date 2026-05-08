import { useState } from 'react';
import BottomTab from '@/components/common/BottomTab';
import MyPageHeader from '../components/MyPageHeader';
import AccountTabSwitcher from '../components/AccountTabSwitcher';
import WeeklyStatCard from '../components/WeeklyStatCard';
import MetricCard from '../components/MetricCard';
import AccountInfoSection from './AccountInfoSection';
import OperatingHoursSection from './OperatingHoursSection';

const myPageMockData = {
  storeName: '싸피 카페',
  instagramUsername: '@ssafy_cafe',
  weeklyPostAchievementRate: 25,
  targetPostCount: 4,
  achievedPostCount: 1,
  weeklyReachCount: 17,
  weeklyVisitIntentScore: 29,
};

export default function MyPageMainSection() {
  const [activeTab, setActiveTab] = useState('stats');

  const {
    storeName,
    instagramUsername,
    weeklyPostAchievementRate,
    targetPostCount,
    achievedPostCount,
    weeklyReachCount,
    weeklyVisitIntentScore,
  } = myPageMockData;

  const handleLogout = () => {
    // TODO: 실제 로그아웃 로직 연결
    console.log('로그아웃');
  };

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-[#f4f4f6]">
      <MyPageHeader
        storeName={storeName}
        instagramUsername={instagramUsername}
        onLogout={handleLogout}
      />

      <AccountTabSwitcher activeTab={activeTab} onChange={setActiveTab} />

      <main className="mx-auto flex w-full max-w-[430px] flex-1 flex-col gap-2 overflow-y-auto px-5 pt-5 pb-[100px]">
        {activeTab === 'stats' && (
          <>
            <WeeklyStatCard
              percent={weeklyPostAchievementRate}
              plannedCount={targetPostCount}
              achievedCount={achievedPostCount}
            />

            <div className="grid grid-cols-2 gap-4">
              <MetricCard
                title={
                  <>
                    주간
                    <br />
                    가게 노출 수
                  </>
                }
                modalTitle="가게 노출 수"
                value={weeklyReachCount}
                unit="%↑"
                description={
                  <span className="flex flex-col gap-1">
                    <span>인스타그램 게시물 노출 횟수예요.</span>
                    <span>
                      수치가 높을수록 더 많은 사람에게
                      <br />
                      가게를 알린 거예요.
                    </span>
                  </span>
                }
              />

              <MetricCard
                title={
                  <>
                    주간
                    <br />
                    방문 관심도
                  </>
                }
                modalTitle="방문 관심도"
                value={weeklyVisitIntentScore}
                unit="%↑"
                description={
                  <span className="flex flex-col gap-1">
                    <span>
                      게시물을 본 사람들이
                      <br />
                      가게에 관심을 보인 정도예요.
                    </span>
                    <span>
                      프로필 방문, 게시물 저장, 클릭 등의
                      <br />
                      행동을 바탕으로 계산해요.
                    </span>
                  </span>
                }
              />
            </div>
          </>
        )}

        {activeTab === 'info' && <AccountInfoSection isEmbedded />}

        {activeTab === 'hours' && <OperatingHoursSection isEmbedded />}
      </main>

      <BottomTab />
    </div>
  );
}

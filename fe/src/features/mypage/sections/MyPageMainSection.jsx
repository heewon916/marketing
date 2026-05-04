import { useNavigate } from 'react-router-dom';
import BottomTab from '@/components/common/BottomTab';
import MyPageHeader from '../components/MyPageHeader';
import ProfileCard from '../components/ProfileCard';
import WeeklyStatCard from '../components/WeeklyStatCard';
import MetricCard from '../components/MetricCard';

const myPageMockData = {
  storeName: '싸피 카페',
  instagramUsername: '@ssafy_cafe',
  weeklyPostAchievementRate: 75,
  targetPostCount: 4,
  achievedPostCount: 3,
  weeklyReachRate: 15,
  weeklyVisitIntentRate: 37,
};

export default function MyPageMainSection() {
  const navigate = useNavigate();

  const {
    storeName,
    instagramUsername,
    weeklyPostAchievementRate,
    targetPostCount,
    achievedPostCount,
    weeklyReachRate,
    weeklyVisitIntentRate,
  } = myPageMockData;

  const handleProfileClick = () => {
    navigate('/mypage/account');
  };

  const handleSettingClick = () => {
    navigate('/mypage/account');
  };

  return (
    // 배경을 surface-200으로 설정하여 따뜻한 톤 유지
    <div className="min-h-screen bg-surface-200 pb-28 font-sans selection:bg-primary-100/20">
      <MyPageHeader
        title="내 정보"
        onSettingClick={handleSettingClick}
      />

      <main className="mx-auto flex w-full max-w-[430px] flex-col px-5 pt-4">
        <div className="animate-fade-in-up">
          <ProfileCard
            storeName={storeName}
            instagramUsername={instagramUsername}
            onClick={handleProfileClick}
          />
        </div>

        <div className="mt-6 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
          <WeeklyStatCard
            percent={weeklyPostAchievementRate}
            plannedCount={targetPostCount}
            achievedCount={achievedPostCount}
          />
        </div>

        <div className="mt-5 grid grid-cols-2 gap-4 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
          <MetricCard
            title={
              <>
                주간 가게<br />노출수
              </>
            }
            value={weeklyReachRate}
            isUp={true}
          />

          <MetricCard
            title={
              <>
                주간 실제<br />방문 의사 지수
              </>
            }
            value={weeklyVisitIntentRate}
            isUp={false}
          />
        </div>
      </main>

      <BottomTab />
    </div>
  );
}

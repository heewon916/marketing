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
  weeklyReachCount: 4200,
  weeklyVisitIntentScore: 285,
};

export default function MyPageMainSection() {
  const navigate = useNavigate();

  const {
    storeName,
    instagramUsername,
    weeklyPostAchievementRate,
    targetPostCount,
    achievedPostCount,
    weeklyReachCount,
    weeklyVisitIntentScore,
  } = myPageMockData;

  return (
    <div className="min-h-screen bg-accent-100/5 pb-28">
      <MyPageHeader
        title="내 정보"
        onSettingClick={() => navigate('/mypage/account')}
      />

      <main className="mx-auto flex w-full max-w-[430px] flex-col gap-4 px-5 pt-4">
        <ProfileCard
          storeName={storeName}
          instagramUsername={instagramUsername}
          onClick={() => navigate('/mypage/account')}
        />

        <WeeklyStatCard
          percent={weeklyPostAchievementRate}
          plannedCount={targetPostCount}
          achievedCount={achievedPostCount}
        />

        <div className="grid grid-cols-2 gap-4">
          <MetricCard
            title={
              <>
                주간 가게 노출 수
              </>
            }
            value={weeklyReachCount}
            unit="회"
            description={`인스타그램 게시물 노출 횟수예요.

          수치가 높을수록 더 많은 사람에게
          가게를 알린 거예요.`}
          />

          <MetricCard
            title={
              <>
                주간 방문 관심도
              </>
            }
            value={weeklyVisitIntentScore}
            unit="점"
            description={`게시물을 본 사람들이
          가게에 관심을 보인 정도예요.

          프로필 방문, 게시물 저장,
          길찾기나 전화 클릭 같은 행동을
          바탕으로 계산해요.`}
          />
        </div>
      </main>

      <BottomTab />
    </div>
    );
}

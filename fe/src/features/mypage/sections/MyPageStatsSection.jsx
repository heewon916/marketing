import WeeklyStatCard from '../components/WeeklyStatCard';
import MetricCard from '../components/MetricCard';

export default function MyPageStatsSection({
  weeklyPostAchievementRate,
  targetPostCount,
  achievedPostCount,
  weeklyReachCount,
  weeklyVisitIntentScore,
}) {
  return (
    <section className="flex flex-col gap-4">
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
    </section>
  );
}

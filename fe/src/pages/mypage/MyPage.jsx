import { useEffect, useState } from 'react';
import BottomTab from '@/components/common/BottomTab';
import MyPageHeader from '@/features/mypage/components/MyPageHeader';
import MyPageTabSwitcher from '@/features/mypage/components/MyPageTabSwitcher';
import MyPageStatsSection from '@/features/mypage/sections/MyPageStatsSection';
import AccountInfoSection from '@/features/mypage/sections/AccountInfoSection';
import OperatingHoursSection from '@/features/mypage/sections/OperatingHoursSection';
import { mypageApi } from '@/features/mypage/api';

const myPageMockData = {
  weeklyPostAchievementRate: 25,
  targetPostCount: 4,
  achievedPostCount: 1,
  weeklyReachCount: 17,
  weeklyVisitIntentScore: -29,
};

export default function MyPage() {
  const [activeTab, setActiveTab] = useState('stats');
  const [myInfo, setMyInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMyInfo = async () => {
    try {
      const response = await mypageApi.getMyInfo();

      console.log('마이페이지 정보:', response.data);

      setMyInfo(response.data);
    } catch (error) {
      console.error('마이페이지 정보 조회 실패:', error);
    }
  };

  useEffect(() => {
    let isMounted = true;

    const loadMyInfo = async () => {
      try {
        const response = await mypageApi.getMyInfo();

        console.log('마이페이지 정보:', response.data);

        if (isMounted) {
          setMyInfo(response.data);
        }
      } catch (error) {
        console.error('마이페이지 정보 조회 실패:', error);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadMyInfo();

    return () => {
      isMounted = false;
    };
  }, []);

  const user = myInfo?.user;
  const store = myInfo?.store;

  const storeName = store?.storeName ?? '매장명 없음';

  const instagramUsername = user?.instagramUsername
    ? `@${user.instagramUsername}`
    : '@instagram';

  const handleLogout = () => {
    // TODO: 실제 로그아웃 로직 연결
    console.log('로그아웃');
  };

  if (isLoading) {
    return (
      <div className="flex h-dvh items-center justify-center bg-[#f4f4f6] text-base text-gray-500">
        마이페이지 정보를 불러오는 중입니다.
      </div>
    );
  }

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-[#f4f4f6]">
      <MyPageHeader
        storeName={storeName}
        instagramUsername={instagramUsername}
      />

      <MyPageTabSwitcher activeTab={activeTab} onChange={setActiveTab} />

      <main className="mx-auto flex min-h-0 w-full max-w-[430px] flex-1 flex-col gap-2 overflow-y-auto px-5 pt-4 pb-5">
        {activeTab === 'stats' && (
          <MyPageStatsSection
            weeklyPostAchievementRate={myPageMockData.weeklyPostAchievementRate}
            targetPostCount={myPageMockData.targetPostCount}
            achievedPostCount={myPageMockData.achievedPostCount}
            weeklyReachCount={myPageMockData.weeklyReachCount}
            weeklyVisitIntentScore={myPageMockData.weeklyVisitIntentScore}
          />
        )}

        {activeTab === 'info' && (
          <AccountInfoSection
            store={store}
            onLogout={handleLogout}
            onRefresh={fetchMyInfo}
          />
        )}

        {activeTab === 'hours' && (
          <OperatingHoursSection
            operatingHours={store?.operatingHours}
            onRefresh={fetchMyInfo}
          />
        )}
      </main>

      <BottomTab fixed={false} />
    </div>
  );
}

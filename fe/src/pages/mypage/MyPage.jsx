import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BottomTab from '@/components/common/BottomTab';
import MyPageHeader from '@/features/mypage/components/MyPageHeader';
import MyPageTabSwitcher from '@/features/mypage/components/MyPageTabSwitcher';
import MyPageStatsSection from '@/features/mypage/sections/MyPageStatsSection';
import AccountInfoSection from '@/features/mypage/sections/AccountInfoSection';
import OperatingHoursSection from '@/features/mypage/sections/OperatingHoursSection';
import { mypageApi } from '@/features/mypage/api';
import { authApi } from '@/features/auth/api';

const myPageMockData = {
  weeklyPostAchievementRate: 25,
  targetPostCount: 4,
  achievedPostCount: 1,
  weeklyReachCount: 17,
  weeklyVisitIntentScore: -29,
};

const clearAuthStorage = () => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  sessionStorage.removeItem('instagramAuthPurpose');
};

export default function MyPage() {
  const navigate = useNavigate();

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

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('로그아웃 API 호출 실패:', error);
    } finally {
      clearAuthStorage();
      navigate('/', { replace: true });
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await authApi.deleteAccount();
    } catch (error) {
      console.error('회원탈퇴 API 호출 실패:', error);
      throw error;
    }

    clearAuthStorage();
    navigate('/', { replace: true });
  };

  const handleInstagramUpdate = async () => {
    try {
      const response = await mypageApi.syncInstagramProfile();
      const syncedProfile = response.data.data;

      setMyInfo((prev) => ({
        ...prev,
        user: {
          ...prev.user,
          instagramUserId: syncedProfile.instagramUserId,
          instagramUsername: syncedProfile.instagramUsername,
          profileImageUrl: syncedProfile.profileImageUrl,
        },
      }));
    } catch (error) {
      console.error('인스타그램 프로필 동기화 실패:', error);
      throw error;
    }
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
        profileImageUrl={user?.profileImageUrl}
        onInstagramUpdate={handleInstagramUpdate}
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
            onDeleteAccount={handleDeleteAccount}
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

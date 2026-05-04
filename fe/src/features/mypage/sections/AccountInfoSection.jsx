import { useNavigate } from 'react-router-dom';
import AccountHeader from '../components/AccountHeader';
import AccountProfile from '../components/AccountProfile';
import AccountTabSwitcher from '../components/AccountTabSwitcher';
import InfoItem from '../components/InfoItem';
import BottomTab from '@/components/common/BottomTab';

const accountMockData = {
  storeName: '싸피 카페',
  instagramUsername: '@ssafy_cafe',
  businessName: '싸피 카페',
  category: '카페',
  address: '서울시 강남구 역삼대로 123',
};

export default function AccountInfoSection({ onTabChange }) {
  const navigate = useNavigate();

  const {
    storeName,
    instagramUsername,
    businessName,
    category,
    address,
  } = accountMockData;

  const handleTabChange = (tab) => {
    if (tab === 'hours') {
      if (onTabChange) {
        onTabChange(tab);
        return;
      }

      navigate('/mypage/account/hours');
    }
  };

  const handleEditClick = () => {
    navigate('/mypage/account/edit');
  };

  return (
    <div className="min-h-screen bg-white pb-24">
      <main className="mx-auto flex min-h-screen w-full max-w-[430px] flex-col px-6 pt-6">
        <AccountHeader title="계정 정보" />

        <div className="mt-11">
          <AccountProfile
            storeName={storeName}
            instagramUsername={instagramUsername}
          />
        </div>

        <div className="mt-11 px-4">
          <AccountTabSwitcher
            activeTab="info"
            onChange={handleTabChange}
          />
        </div>

        <dl className="mt-16 flex flex-col gap-9">
          <InfoItem label="상호명" value={businessName} />
          <InfoItem label="업종" value={category} />
          <InfoItem label="위치" value={address} />
        </dl>

        <button
          type="button"
          onClick={handleEditClick}
          className="mt-auto mb-5 h-14 w-full rounded-xl bg-primary-100 text-[20px] font-extrabold text-white"
        >
          수정하기
        </button>
      </main>

      <BottomTab />
    </div>
  );
}

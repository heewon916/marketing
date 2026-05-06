import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MyPageHeader from '../components/MyPageHeader';
import AccountProfile from '../components/AccountProfile';
import AccountTabSwitcher from '../components/AccountTabSwitcher';
import AccountInfoEdit from '../components/AccountInfoEdit';
import InfoItem from '../components/InfoItem';
import CardShell from '../components/CardShell';
import BottomTab from '@/components/common/BottomTab';
import Button from '@/components/common/Button';

const accountMockData = {
  storeName: '싸피 카페',
  instagramUsername: '@ssafy_cafe',
  businessName: '싸피 카페',
  category: '카페',
  address: '서울시 강남구 역삼대로 123',
};

export default function AccountInfoSection({ onTabChange }) {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState(accountMockData);

  const {
    storeName,
    instagramUsername,
    businessName,
    category,
    address,
  } = formData;

  const handleTabChange = (tab) => {
    if (isEditing) return;

    if (tab === 'hours') {
      if (onTabChange) {
        onTabChange(tab);
        return;
      }

      navigate('/mypage/account/hours');
    }
  };

  const handleEditClick = () => {
    setIsEditing(true);
  };

  const handleCancelClick = () => {
    setFormData(accountMockData);
    setIsEditing(false);
  };

  const handleSaveClick = () => {
    // TODO: 계정 기본정보 수정 API 연결
    setIsEditing(false);
  };

  const handleBack = () => {
    navigate('/mypage');
  };

  return (
    <div className="min-h-screen bg-accent-100/5 pb-28">
      <MyPageHeader
        title="계정 정보"
        showBackButton={!isEditing}
        onBack={handleBack}
      />

      <main className="mx-auto flex w-full max-w-[430px] flex-col gap-4 px-5 pt-4">
        <AccountProfile
          storeName={storeName}
          instagramUsername={instagramUsername}
        />

        <AccountTabSwitcher
          activeTab="info"
          onChange={handleTabChange}
        />

        {isEditing ? (
          <AccountInfoEdit
            formData={formData}
            onChange={setFormData}
          />
        ) : (
          <CardShell as="dl" className="flex flex-col gap-5 p-5">
            <InfoItem label="상호명" value={businessName} />
            <InfoItem label="업종" value={category} />
            <InfoItem label="위치" value={address} />
          </CardShell>
        )}

        {isEditing ? (
          <div className="mt-2 flex justify-center gap-3">
            <Button
              size="sm"
              variant="white"
              onClick={handleCancelClick}
              className="text-[18px] font-bold"
            >
              취소
            </Button>

            <Button
              size="sm"
              variant="primary"
              onClick={handleSaveClick}
              className="text-[18px] font-bold"
            >
              저장하기
            </Button>
          </div>
        ) : (
          <div className="mt-2 flex justify-center">
            <Button
              size="lg"
              variant="primary"
              onClick={handleEditClick}
              className="text-[18px] font-bold"
            >
              수정하기
            </Button>
          </div>
        )}
      </main>

      <BottomTab />
    </div>
  );
}

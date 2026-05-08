import { useState } from 'react';
import AccountInfoEdit from '../components/AccountInfoEdit';
import InfoItem from '../components/InfoItem';
import CardShell from '../components/CardShell';
import Button from '@/components/common/Button';

const accountMockData = {
  storeName: '싸피 카페',
  instagramUsername: '@ssafy_cafe',
  businessName: '김가네',
  category: '카페',
  address: '서울시 강남구 역삼대로 123',
};

export default function AccountInfoSection() {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState(accountMockData);

  const { businessName, category, address } = formData;

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

  return (
    <section className="flex flex-col gap-4">
      {isEditing ? (
        <AccountInfoEdit formData={formData} onChange={setFormData} />
      ) : (
        <CardShell as="dl" className="flex flex-col gap-7 px-7 py-8">
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
            className="w-full text-[18px] font-bold"
          >
            수정하기
          </Button>
        </div>
      )}
    </section>
  );
}

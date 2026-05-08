import { useState } from 'react';
import AccountInfoEdit from '../components/AccountInfoEdit';
import InfoItem from '../components/InfoItem';
import CardShell from '../components/CardShell';
import Button from '@/components/common/Button';

const accountMockData = {
  storeName: '바나프레소',
  instagramUsername: '@banapresso_official',
  businessName: '바나프레소',
  category: '카페',
  address: '서울시 강남구 테헤란로 208 1층 (역삼동)',
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
        <AccountInfoEdit
          formData={formData}
          onChange={setFormData}
          onCancel={handleCancelClick}
          onSave={handleSaveClick}
        />
      ) : (
        <CardShell as="div" className="flex flex-col px-7 py-8">
          <dl className="flex flex-col">
            <InfoItem label="상호명" value={businessName} />
            <InfoItem label="업종" value={category} />
            <InfoItem label="위치" value={address} />
          </dl>

          <Button
            size="lg"
            variant="primary"
            onClick={handleEditClick}
            className="mt-6 w-full text-[18px] font-bold"
          >
            수정하기
          </Button>
        </CardShell>
      )}
    </section>
  );
}

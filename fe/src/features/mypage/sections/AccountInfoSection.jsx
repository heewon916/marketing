import { useState } from 'react';
import AccountInfoEdit from '../components/AccountInfoEdit';
import InfoItem from '../components/InfoItem';
import CardShell from '../components/CardShell';
import Button from '@/components/common/Button';
import Modal from '@/components/common/Modal';
import { mypageApi } from '@/features/mypage/api';

const createFormDataFromStore = (store) => ({
  businessName: store?.storeName ?? '매장명 없음',
  category: store?.category ?? '',
  address: store?.address ?? '',
});

export default function AccountInfoSection({ store, onLogout, onRefresh }) {
  const [isEditing, setIsEditing] = useState(false);
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const [formData, setFormData] = useState(() =>
    createFormDataFromStore(store)
  );
  const [isSaving, setIsSaving] = useState(false);

  const displayData = createFormDataFromStore(store);

  const { businessName, category, address } = isEditing
    ? formData
    : displayData;

  const handleEditClick = () => {
    setFormData(createFormDataFromStore(store));
    setIsEditing(true);
  };

  const handleCancelClick = () => {
    setFormData(createFormDataFromStore(store));
    setIsEditing(false);
  };

  const handleSaveClick = async () => {
    const requestBody = {
      category: formData.category,
      address: formData.address,
    };

    try {
      setIsSaving(true);

      console.log('내정보 수정 요청:', requestBody);

      await mypageApi.updateMyInfo(requestBody);

      if (onRefresh) {
        await onRefresh();
      }

      setIsEditing(false);
    } catch (error) {
      console.error('내정보 수정 실패:', error);
      alert('매장 정보를 수정하지 못했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogoutClick = () => {
    setIsLogoutModalOpen(true);
  };

  const handleCancelLogout = () => {
    setIsLogoutModalOpen(false);
  };

  const handleConfirmLogout = () => {
    setIsLogoutModalOpen(false);

    if (onLogout) {
      onLogout();
    }
  };

  return (
    <>
      <section className="flex flex-col gap-4">
        {isEditing ? (
          <AccountInfoEdit
            formData={formData}
            onChange={setFormData}
            onCancel={handleCancelClick}
            onSave={handleSaveClick}
            isSaving={isSaving}
          />
        ) : (
          <CardShell as="div" className="flex flex-col px-7 py-8">
            <dl className="flex flex-col">
              <InfoItem label="상호명" value={businessName} />
              <InfoItem label="업종" value={category || '업종 없음'} />
              <InfoItem label="위치" value={address || '주소 없음'} />
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

        {!isEditing && (
          <button
            type="button"
            onClick={handleLogoutClick}
            className="mx-auto mt-1 text-[15px] font-medium text-red-500 underline underline-offset-2 active:brightness-90"
          >
            로그아웃
          </button>
        )}
      </section>

      {isLogoutModalOpen && (
        <Modal
          isOpen={isLogoutModalOpen}
          onClose={handleCancelLogout}
          showClose={false}
          closeOnBackdrop
        >
          <div className="text-center">
            <h2 className="text-[22px] font-bold text-accent-100">
              로그아웃할까요?
            </h2>

            <p className="mt-3 text-[18px] leading-relaxed text-gray-500">
              다시 이용하려면 로그인이 필요합니다.
            </p>

            <div className="mt-7 flex justify-center gap-3">
              <Button
                size="sm"
                variant="white"
                onClick={handleCancelLogout}
                className="text-[18px] font-bold"
              >
                취소
              </Button>

              <Button
                size="sm"
                variant="danger"
                onClick={handleConfirmLogout}
                className="text-[18px] font-bold"
              >
                로그아웃
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}

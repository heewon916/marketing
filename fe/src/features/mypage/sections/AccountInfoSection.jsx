import { useState } from 'react';
import AccountInfoEdit from '../components/AccountInfoEdit';
import InfoItem from '../components/InfoItem';
import CardShell from '../components/CardShell';
import Button from '@/components/common/Button';
import Modal from '@/components/common/Modal';
import { mypageApi } from '@/features/mypage/api';

const createFormDataFromStore = (store) => ({
  businessName: store?.storeName ?? '',
  category: store?.category ?? '',
  address: store?.address ?? '',
  latitude: store?.latitude ?? null,
  longitude: store?.longitude ?? null,
});

export default function AccountInfoSection({
  store,
  onLogout,
  onRefresh,
  onDeleteAccount,
  onEditingChange,
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const [isDeleteConfirmModalOpen, setIsDeleteConfirmModalOpen] =
    useState(false);
  const [isDeleteWarningModalOpen, setIsDeleteWarningModalOpen] =
    useState(false);

  const [formData, setFormData] = useState(() =>
    createFormDataFromStore(store)
  );
  const [isSaving, setIsSaving] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);

  const displayData = createFormDataFromStore(store);

  const { businessName, category, address } = isEditing
    ? formData
    : displayData;

  const handleEditClick = () => {
    setFormData(createFormDataFromStore(store));
    setIsEditing(true);
    onEditingChange?.(true);
  };

  const handleCancelClick = () => {
    setFormData(createFormDataFromStore(store));
    setIsEditing(false);
    onEditingChange?.(false);
  };

  const handleSaveClick = async () => {
    const requestBody = {
      category: formData.category,
      address: formData.address,
    };

    try {
      setIsSaving(true);

      await mypageApi.updateMyInfo(requestBody);

      if (onRefresh) {
        await onRefresh();
      }

      setIsEditing(false);
      onEditingChange?.(false);
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
    if (isLoggingOut) return;

    setIsLogoutModalOpen(false);
  };

  const handleConfirmLogout = async () => {
    if (isLoggingOut) return;

    try {
      setIsLoggingOut(true);

      if (onLogout) {
        await onLogout();
      }

      setIsLogoutModalOpen(false);
    } catch (error) {
      console.error('로그아웃 실패:', error);
      alert('로그아웃하지 못했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleDeleteAccountClick = () => {
    setIsDeleteConfirmModalOpen(true);
  };

  const handleCancelDeleteConfirm = () => {
    if (isDeletingAccount) return;

    setIsDeleteConfirmModalOpen(false);
  };

  const handleOpenDeleteWarning = () => {
    setIsDeleteConfirmModalOpen(false);
    setIsDeleteWarningModalOpen(true);
  };

  const handleCancelDeleteWarning = () => {
    if (isDeletingAccount) return;

    setIsDeleteWarningModalOpen(false);
  };

  const handleConfirmDeleteAccount = async () => {
    if (isDeletingAccount) return;

    try {
      setIsDeletingAccount(true);

      if (onDeleteAccount) {
        await onDeleteAccount();
      } else {
        console.log('회원탈퇴');
      }

      setIsDeleteWarningModalOpen(false);
    } catch (error) {
      console.error('회원탈퇴 실패:', error);
      alert('회원탈퇴하지 못했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setIsDeletingAccount(false);
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
              <InfoItem label="상호명" value={businessName || '상호명 없음'} />
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
          <div className="mt-1 flex justify-center gap-4">
            <button
              type="button"
              onClick={handleLogoutClick}
              className="text-[15px] font-medium text-red-500 underline underline-offset-2"
            >
              로그아웃
            </button>

            <button
              type="button"
              onClick={handleDeleteAccountClick}
              className="text-[15px] font-medium text-gray-400 underline underline-offset-2"
            >
              회원탈퇴
            </button>
          </div>
        )}
      </section>

      {/* 로그아웃 모달 */}
      {isLogoutModalOpen && (
        <Modal
          isOpen={isLogoutModalOpen}
          onClose={handleCancelLogout}
          showClose={false}
          closeOnBackdrop={!isLoggingOut}
          title="로그아웃할까요?"
          description="다시 이용하려면 로그인이 필요합니다."
          cancelText="취소"
          confirmText={isLoggingOut ? '로그아웃 중' : '로그아웃'}
          variant="danger"
          confirmVariant="danger"
          cancelDisabled={isLoggingOut}
          confirmDisabled={isLoggingOut}
          onCancel={handleCancelLogout}
          onConfirm={handleConfirmLogout}
        />
      )}

      {/* 회원탈퇴 확인 모달 */}
      {isDeleteConfirmModalOpen && (
        <Modal
          isOpen={isDeleteConfirmModalOpen}
          onClose={handleCancelDeleteConfirm}
          showClose={false}
          closeOnBackdrop={!isDeletingAccount}
          variant="danger"
          title="회원탈퇴할까요?"
          description="맡케팅 이용을 그만두시겠어요?"
          cancelText="취소"
          confirmText="확인"
          confirmVariant="danger"
          cancelDisabled={isDeletingAccount}
          confirmDisabled={isDeletingAccount}
          onCancel={handleCancelDeleteConfirm}
          onConfirm={handleOpenDeleteWarning}
        />
      )}

      {/* 회원탈퇴 경고 모달 */}
      {isDeleteWarningModalOpen && (
        <Modal
          isOpen={isDeleteWarningModalOpen}
          onClose={handleCancelDeleteWarning}
          showClose={false}
          closeOnBackdrop={!isDeletingAccount}
          variant="danger"
          title="정말 탈퇴하시겠어요?"
          description={`탈퇴하면 계정, 매장 정보,\n마케팅 기록 등 모든 정보가 사라져요.`}
          cancelText="취소"
          confirmText={isDeletingAccount ? '탈퇴 중' : '탈퇴'}
          titleColor="danger"
          confirmVariant="danger"
          cancelDisabled={isDeletingAccount}
          confirmDisabled={isDeletingAccount}
          onCancel={handleCancelDeleteWarning}
          onConfirm={handleConfirmDeleteAccount}
        >
          <p className="mt-2 text-center text-[15px] leading-relaxed text-red-400">
            삭제된 정보는 다시 복구할 수 없습니다.
          </p>
        </Modal>
      )}
    </>
  );
}

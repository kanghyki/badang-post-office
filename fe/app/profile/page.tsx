'use client';
import styles from './profile.module.scss';
import Header from '@/app/components/Header';
import { useRouter } from 'next/navigation';
import { useState, useEffect } from 'react';
import { authUtils } from '@/lib/utils/auth';
import { useAuth } from '@/hooks/useAuth';
import { useNotification } from '@/app/context/NotificationContext';
import { ROUTES } from '@/lib/constants/urls';
import { authApi, UserProfile, UpdateProfileRequest } from '@/lib/api/auth';

export default function Profile() {
  useAuth(); // 인증 체크
  const router = useRouter();
  const { showModal, showToast } = useNotification();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isResendingEmail, setIsResendingEmail] = useState(false);

  useEffect(() => {
    loadProfile();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadProfile = async () => {
    try {
      const data = await authApi.getUserProfile();
      setProfile(data);
      setName(data.name);
    } catch {
      showToast({
        message: '프로필 정보를 불러올 수 없습니다.',
        type: 'error',
      });
      router.push(ROUTES.MAIN);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    const confirmed = await showModal({
      title: '로그아웃',
      message: '로그아웃 하시겠습니까?',
      type: 'confirm',
      confirmText: '로그아웃',
      cancelText: '취소',
    });

    if (confirmed) {
      authUtils.removeToken();
      router.push(ROUTES.LOGIN);
    }
  };

  const handleDeleteAccount = async () => {
    const confirmed = await showModal({
      title: '회원 탈퇴',
      message: '정말 탈퇴하시겠습니까? 이 작업은 되돌릴 수 없습니다.',
      type: 'confirm',
      confirmText: '탈퇴',
      cancelText: '취소',
    });

    if (confirmed) {
      try {
        await authApi.deleteAccount();
        authUtils.removeToken();
        await showModal({
          title: '탈퇴 완료',
          message: '회원 탈퇴가 완료되었습니다.',
          type: 'alert',
        });
        router.push(ROUTES.LOGIN);
      } catch {
        await showModal({
          title: '오류',
          message: '회원 탈퇴 중 오류가 발생했습니다.',
          type: 'alert',
        });
      }
    }
  };

  const handleUpdateProfile = async () => {
    if (!name.trim()) {
      showToast({ message: '이름을 입력해주세요.', type: 'error' });
      return;
    }

    if (newPassword && newPassword !== confirmPassword) {
      showToast({
        message: '새 비밀번호가 일치하지 않습니다.',
        type: 'error',
      });
      return;
    }

    try {
      const updateData: UpdateProfileRequest = {
        name: name !== profile?.name ? name : undefined,
      };

      if (newPassword) {
        updateData.password = newPassword;
      }

      const updatedProfile = await authApi.updateUserProfile(updateData);
      setProfile(updatedProfile);
      setName(updatedProfile.name);
      setIsEditing(false);
      setNewPassword('');
      setConfirmPassword('');
      showToast({
        message: '프로필이 업데이트되었습니다.',
        type: 'success',
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error && 'response' in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
            '프로필 업데이트 중 오류가 발생했습니다.'
          : '프로필 업데이트 중 오류가 발생했습니다.';
      showToast({ message: errorMessage, type: 'error' });
    }
  };

  const handleCancelEdit = () => {
    setName(profile?.name || '');
    setNewPassword('');
    setConfirmPassword('');
    setIsEditing(false);
  };

  const handleResendVerification = async () => {
    if (isResendingEmail) return;

    setIsResendingEmail(true);
    try {
      await authApi.resendVerificationEmail();
      showToast({
        message: '인증 메일이 재발송되었습니다. 이메일을 확인해주세요.',
        type: 'success',
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error && 'response' in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail ||
            '인증 메일 재발송 중 오류가 발생했습니다.'
          : '인증 메일 재발송 중 오류가 발생했습니다.';
      showToast({ message: errorMessage, type: 'error' });
    } finally {
      setIsResendingEmail(false);
    }
  };

  if (isLoading) {
    return (
      <>
        <div className="hdrWrap">
          <Header
            title="내 정보"
            showUserMenu={true}
            userName={profile?.name}
            onLogout={handleLogout}
            onDeleteAccount={handleDeleteAccount}
          />
        </div>
        <div className="container">
          <main className={styles.profileMain}></main>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="hdrWrap">
        <Header
          title="내 정보"
          showUserMenu={true}
          userName={profile?.name}
          onLogout={handleLogout}
          onDeleteAccount={handleDeleteAccount}
        />
      </div>
      <div className="container">
        <main className={styles.profileMain}>
          <div className={styles.infoSection}>
            <div className={styles.infoItem}>
              <span className={styles.label}>이메일</span>
              <span
                className={styles.value}
                style={{
                  color: profile?.is_email_verified ? '#4CAF50' : '#ff9800',
                }}
              >
                {profile?.email}
              </span>
            </div>

            {profile?.is_email_verified || (
              <div className={styles.infoItem}>
                <span className={styles.label}>이메일 상태</span>
                <span className={styles.value}>
                  {profile?.is_email_verified ? (
                    <span style={{ color: '#4CAF50' }}>인증됨</span>
                  ) : (
                    <>
                      <span style={{ color: '#ff9800' }}>미인증</span>
                      <button
                        onClick={handleResendVerification}
                        disabled={isResendingEmail}
                        style={{
                          marginLeft: '10px',
                          padding: '4px 12px',
                          fontSize: '12px',
                          backgroundColor: '#4CAF50',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: isResendingEmail ? 'not-allowed' : 'pointer',
                          opacity: isResendingEmail ? 0.6 : 1,
                        }}
                      >
                        {isResendingEmail ? '발송 중...' : '인증 메일 재발송'}
                      </button>
                    </>
                  )}
                </span>
              </div>
            )}

            <div className={styles.infoItem}>
              <span className={styles.label}>가입일</span>
              <span className={styles.value}>
                {profile?.created_at ? new Date(profile.created_at).toLocaleDateString('ko-KR') : ''}
              </span>
            </div>
          </div>

          <div className={styles.editSection}>
            <div className={styles.formGroup}>
              <label>이름</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                disabled={!isEditing}
                placeholder="이름을 입력하세요"
              />
            </div>

            {isEditing && (
              <>
                <div className={styles.formGroup}>
                  <label>새 비밀번호</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    placeholder="변경할 경우만 입력"
                  />
                </div>

                <div className={styles.formGroup}>
                  <label>비밀번호 확인</label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    placeholder="비밀번호 재입력"
                  />
                </div>
              </>
            )}

            <div className={styles.buttonGroup}>
              {!isEditing ? (
                <button onClick={() => setIsEditing(true)} className={styles.editBtn}>
                  정보 수정
                </button>
              ) : (
                <>
                  <button onClick={handleCancelEdit} className={styles.cancelBtn}>
                    취소
                  </button>
                  <button onClick={handleUpdateProfile} className={styles.saveBtn}>
                    저장
                  </button>
                </>
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}

'use client';
import styles from './home.module.scss';
import Header from '@/app/components/Header';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { TbEdit } from 'react-icons/tb';
import { authUtils } from '@/lib/utils/auth';
import { useAuth } from '@/hooks/useAuth';
import { observer } from 'mobx-react-lite';
import { useStore } from '@/store/StoreProvider';
import { useNotification } from '@/app/context/NotificationContext';
import { ROUTES } from '@/lib/constants/urls';
import { authApi } from '@/lib/api/auth';
import { useState } from 'react';

const User = observer(() => {
  useAuth(); // 인증 체크
  const router = useRouter();
  const { postcardStore } = useStore();
  const { showModal } = useNotification();
  const [userName, setUserName] = useState<string>('');

  useEffect(() => {
    postcardStore.fetchPostcards();
    loadUserProfile();
  }, [postcardStore]);

  const loadUserProfile = async () => {
    try {
      const profile = await authApi.getUserProfile();
      setUserName(profile.name);
    } catch {
      // 조용히 실패 처리
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

  return (
    <>
      <div className="hdrWrap">
        <Header
          title=""
          showUserMenu={true}
          userName={userName}
          onLogout={handleLogout}
          onDeleteAccount={handleDeleteAccount}
        />
      </div>
      <div className={styles.homeContainer}>
        <main className={styles.userMain}>
          <div className={styles.inputBox}>
            <button
              className={styles.menuItem}
              onClick={() => router.push(ROUTES.LIST)}
            >
              <span className={styles.boxTxt}>
                <b>엽서목록보기</b>
              </span>
              <span>
                <b>{postcardStore.postcardsCount}</b>
                <i>개</i>
              </span>
            </button>

            <button
              className={styles.menuItem}
              onClick={() => router.push(ROUTES.WRITE)}
            >
              <span className={styles.boxTxt}>
                <b>엽서작성하기</b>
              </span>
              <span className={styles.boxCnt}>
                <TbEdit />
              </span>
            </button>
          </div>
        </main>
      </div>
    </>
  );
});

export default User;

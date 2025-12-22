'use client';

import Header from '@/app/components/Header';
import PostcardItem from '@/app/components/PostcardItem';
import PostcardImageModal from '@/app/components/PostcardImageModal';
import LoadingSkeleton from '@/app/components/LoadingSkeleton';
import styles from './list.module.scss';
import { useEffect, useState } from 'react';
import {
  postcardsApi,
  PostcardResponse,
  PostcardStatus,
} from '@/lib/api/postcards';
import { useAuth } from '@/hooks/useAuth';
import { useNotification } from '@/app/context/NotificationContext';
import { ROUTES } from '@/lib/constants/urls';
import { authUtils } from '@/lib/utils/auth';
import { authApi } from '@/lib/api/auth';
import { useRouter } from 'next/navigation';

type FilterType = 'all' | PostcardStatus;

const STATUS_LABELS: Record<FilterType, string> = {
  all: '전체',
  writing: '작성중',
  pending: '예약됨',
  processing: '발송중',
  sent: '발송완료',
  failed: '실패',
};

export default function List() {
  useAuth(); // 인증 체크
  const router = useRouter();
  const { showModal, showToast } = useNotification();
  const [postcards, setPostcards] = useState<PostcardResponse[]>([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [filterLoading, setFilterLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [userName, setUserName] = useState<string>('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedPostcard, setSelectedPostcard] =
    useState<PostcardResponse | null>(null);

  const fetchPostcards = async (status?: PostcardStatus, isInitial = false) => {
    try {
      if (isInitial) {
        setInitialLoading(true);
      } else {
        setFilterLoading(true);
      }
      const data = await postcardsApi.getList(status);
      setPostcards(data);
    } catch (err) {
      console.error('편지 목록 조회 실패:', err);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('편지 목록을 불러올 수 없습니다.');
      }
    } finally {
      if (isInitial) {
        setInitialLoading(false);
      } else {
        setFilterLoading(false);
      }
    }
  };

  useEffect(() => {
    const isInitial = initialLoading;
    if (activeFilter === 'all') {
      fetchPostcards(undefined, isInitial);
    } else {
      fetchPostcards(activeFilter, isInitial);
    }
    if (isInitial) {
      loadUserProfile();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeFilter]);

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

  const handleFilterChange = (filter: FilterType) => {
    setActiveFilter(filter);
  };

  const handlePostcardClick = (postcard: PostcardResponse) => {
    setSelectedPostcard(postcard);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedPostcard(null);
  };

  const handleStatusUpdate = async () => {
    // 발송 완료 시 목록 새로고침
    if (activeFilter === 'all') {
      fetchPostcards();
    } else {
      fetchPostcards(activeFilter);
    }
  };

  const handleCancel = async (id: string) => {
    const confirmed = await showModal({
      title: '예약 취소',
      message:
        '예약된 발송을 취소하시겠습니까?\n취소된 편지는 목록에서 확인할 수 있습니다.',
      type: 'confirm',
      confirmText: '예약 취소',
      cancelText: '돌아가기',
    });

    if (!confirmed) return;

    try {
      await postcardsApi.cancel(id);
      // 현재 필터 상태를 유지하며 목록 새로고침
      if (activeFilter === 'all') {
        fetchPostcards();
      } else {
        fetchPostcards(activeFilter);
      }
      showToast({ message: '예약이 취소되었습니다.', type: 'success' });
    } catch (error) {
      console.error('예약 취소 실패:', error);
      if (error instanceof Error) {
        showToast({
          message: `예약 취소 실패: ${error.message}`,
          type: 'error',
        });
      } else {
        showToast({
          message: '예약 취소 중 오류가 발생했습니다.',
          type: 'error',
        });
      }
    }
  };

  const handleDelete = async (id: string) => {
    const confirmed = await showModal({
      title: '편지 삭제',
      message: '이 편지를 삭제하시겠습니까?\n삭제된 편지는 복구할 수 없습니다.',
      type: 'confirm',
      confirmText: '삭제',
      cancelText: '취소',
    });

    if (!confirmed) return;

    try {
      await postcardsApi.delete(id);
      // 현재 필터 상태를 유지하며 목록 새로고침
      if (activeFilter === 'all') {
        fetchPostcards();
      } else {
        fetchPostcards(activeFilter);
      }
      showToast({ message: '편지가 삭제되었습니다.', type: 'success' });
    } catch (error) {
      console.error('삭제 실패:', error);
      if (error instanceof Error) {
        showToast({
          message: `삭제 실패: ${error.message}`,
          type: 'error',
        });
      } else {
        showToast({
          message: '삭제 중 오류가 발생했습니다.',
          type: 'error',
        });
      }
    }
  };

  const handleRetry = async (id: string) => {
    const confirmed = await showModal({
      title: '편지 재발송',
      message: '이 편지를 다시 발송하시겠습니까?',
      type: 'confirm',
      confirmText: '재발송',
      cancelText: '취소',
    });

    if (!confirmed) return;

    try {
      await postcardsApi.send(id);
      // 현재 필터 상태를 유지하며 목록 새로고침
      if (activeFilter === 'all') {
        fetchPostcards();
      } else {
        fetchPostcards(activeFilter);
      }
      showToast({ message: '편지 재발송이 시작되었습니다.', type: 'success' });
    } catch (error) {
      console.error('재발송 실패:', error);
      if (error instanceof Error) {
        showToast({
          message: `재발송 실패: ${error.message}`,
          type: 'error',
        });
      } else {
        showToast({
          message: '재발송 중 오류가 발생했습니다.',
          type: 'error',
        });
      }
    }
  };

  if (initialLoading) {
    return (
      <>
        <div className="hdrWrap">
          <Header
            showUserMenu={true}
            userName={userName}
            onLogout={handleLogout}
            onDeleteAccount={handleDeleteAccount}
          />
        </div>
        <div className="container"></div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <div className="hdrWrap">
          <Header
            showUserMenu={true}
            userName={userName}
            onLogout={handleLogout}
            onDeleteAccount={handleDeleteAccount}
          />
        </div>
        <div className="container">
          <div
            style={{
              textAlign: 'center',
              padding: '50px',
              color: 'red',
            }}
          >
            {error}
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="hdWrap">
        <Header
          showUserMenu={true}
          userName={userName}
          onLogout={handleLogout}
          onDeleteAccount={handleDeleteAccount}
        />
      </div>

      <div className="container">
        <div className={styles.filterContainer}>
          {(Object.keys(STATUS_LABELS) as FilterType[]).map((filter) => (
            <button
              key={filter}
              className={`${styles.filterButton} ${activeFilter === filter ? styles.active : ''}`}
              onClick={() => handleFilterChange(filter)}
            >
              {STATUS_LABELS[filter]}
            </button>
          ))}
        </div>
        <main className={styles.listMain}>
          <div className={styles.postcardBox}>
            {filterLoading ? (
              <LoadingSkeleton />
            ) : postcards.length === 0 ? (
              <div className={styles.emptyState}>
                <div className={styles.emptyText}>
                  아직 작성한 편지가 없어요
                </div>
              </div>
            ) : (
              postcards.map((item, index) => (
                <PostcardItem
                  key={item.id}
                  data={item}
                  index={index}
                  onCancel={handleCancel}
                  onDelete={handleDelete}
                  onRetry={handleRetry}
                  onClick={handlePostcardClick}
                  onStatusUpdate={handleStatusUpdate}
                />
              ))
            )}
          </div>
        </main>
      </div>

      <PostcardImageModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        postcardPath={selectedPostcard?.postcard_path || null}
      />
    </>
  );
}

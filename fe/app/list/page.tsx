"use client";

import Link from "next/link";
import Header from "@/app/components/Header";
import PostcardItem from "@/app/components/PostcardItem";
import styles from "./list.module.scss";
import { useEffect, useState } from "react";
import {
  postcardsApi,
  PostcardResponse,
  PostcardStatus,
} from "@/lib/api/postcards";
import { useAuth } from "@/hooks/useAuth";
import { useNotification } from "@/app/context/NotificationContext";
import { ROUTES } from "@/lib/constants/urls";
import { authUtils } from "@/lib/utils/auth";
import { authApi } from "@/lib/api/auth";
import { useRouter } from "next/navigation";

type FilterType = "all" | PostcardStatus;

const STATUS_LABELS: Record<FilterType, string> = {
  all: "전체",
  writing: "작성중",
  pending: "예약됨",
  sent: "발송완료",
  failed: "실패",
  cancelled: "취소됨",
};

export default function List() {
  useAuth(); // 인증 체크
  const router = useRouter();
  const { showModal, showToast } = useNotification();
  const [postcards, setPostcards] = useState<PostcardResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterType>("all");
  const [userName, setUserName] = useState<string>("");

  const fetchPostcards = async (status?: PostcardStatus) => {
    try {
      setLoading(true);
      const data = await postcardsApi.getList(status);
      setPostcards(data);
    } catch (err) {
      console.error("엽서 목록 조회 실패:", err);
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("엽서 목록을 불러올 수 없습니다.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeFilter === "all") {
      fetchPostcards();
    } else {
      fetchPostcards(activeFilter);
    }
    loadUserProfile();
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
      title: "로그아웃",
      message: "로그아웃 하시겠습니까?",
      type: "confirm",
      confirmText: "로그아웃",
      cancelText: "취소",
    });

    if (confirmed) {
      authUtils.removeToken();
      router.push(ROUTES.LOGIN);
    }
  };

  const handleDeleteAccount = async () => {
    const confirmed = await showModal({
      title: "회원 탈퇴",
      message: "정말 탈퇴하시겠습니까? 이 작업은 되돌릴 수 없습니다.",
      type: "confirm",
      confirmText: "탈퇴",
      cancelText: "취소",
    });

    if (confirmed) {
      try {
        await authApi.deleteAccount();
        authUtils.removeToken();
        await showModal({
          title: "탈퇴 완료",
          message: "회원 탈퇴가 완료되었습니다.",
          type: "alert",
        });
        router.push(ROUTES.LOGIN);
      } catch {
        await showModal({
          title: "오류",
          message: "회원 탈퇴 중 오류가 발생했습니다.",
          type: "alert",
        });
      }
    }
  };

  const handleFilterChange = (filter: FilterType) => {
    setActiveFilter(filter);
  };

  const handleDelete = async (id: string) => {
    const confirmed = await showModal({
      title: "엽서 삭제",
      message: "정말로 삭제하시겠습니까?",
      type: "confirm",
      confirmText: "삭제",
      cancelText: "취소",
    });

    if (!confirmed) return;

    try {
      await postcardsApi.delete(id);
      // 현재 필터 상태를 유지하며 목록 새로고침
      if (activeFilter === "all") {
        fetchPostcards();
      } else {
        fetchPostcards(activeFilter);
      }
    } catch (error) {
      console.error("삭제 실패:", error);
      if (error instanceof Error) {
        showToast({ message: `삭제 실패: ${error.message}`, type: "error" });
      } else {
        showToast({ message: "삭제 중 오류가 발생했습니다.", type: "error" });
      }
    }
  };

  if (loading) {
    return (
      <>
        <div className="hdrWrap">
          <Header
            title="예약엽서목록"
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
            title="예약엽서목록"
            showUserMenu={true}
            userName={userName}
            onLogout={handleLogout}
            onDeleteAccount={handleDeleteAccount}
          />
        </div>
        <div className="container">
          <div style={{ textAlign: "center", padding: "50px", color: "red" }}>
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
          title="예약엽서목록"
          showUserMenu={true}
          userName={userName}
          onLogout={handleLogout}
          onDeleteAccount={handleDeleteAccount}
        />
      </div>

      <div className="container">
        <div className={styles.postCopy}>
          오늘도 해 넘어가는 들녘
          <br />
          바라보멍 너 생각에 웃음 나불어
          <br />이 정 담은 편지를 살그마니 보낸다게
        </div>
        <div className={styles.filterContainer}>
          {(Object.keys(STATUS_LABELS) as FilterType[]).map((filter) => (
            <button
              key={filter}
              className={`${styles.filterButton} ${
                activeFilter === filter ? styles.active : ""
              }`}
              onClick={() => handleFilterChange(filter)}
            >
              {STATUS_LABELS[filter]}
            </button>
          ))}
        </div>
        <main className={styles.listMain}>
          <div className={styles.postcardBox}>
            {postcards.length === 0 ? (
              <div className={styles.emptyState}>
                <div className={styles.emptyText}>
                  아직 작성한 엽서가 없어요
                </div>
              </div>
            ) : (
              postcards.map((item, index) => (
                <PostcardItem
                  key={item.id}
                  data={item}
                  index={index}
                  onDelete={handleDelete}
                />
              ))
            )}
          </div>
          <div className={styles.buttonSection}>
            <Link
              href={ROUTES.WRITE}
              className={"btnBig"}
              style={{ color: "#FFF" }}
            >
              엽서 작성하기
            </Link>
          </div>
        </main>
      </div>
    </>
  );
}

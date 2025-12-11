"use client";

import Link from "next/link";
import Header from "../components/Header";
import PostcardItem from "../components/PostcardItem";
import styles from "./list.module.scss";
import { useEffect, useState } from "react";
import { postcardsApi, PostcardResponse } from "@/lib/api/postcards";
import { useAuth } from "@/hooks/useAuth";
import { useNotification } from "../context/NotificationContext";

export default function List() {
  useAuth(); // 인증 체크
  const { showModal, showToast } = useNotification();
  const [postcards, setPostcards] = useState<PostcardResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPostcards = async () => {
    try {
      setLoading(true);
      const data = await postcardsApi.getList();
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
    fetchPostcards();
  }, []);

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
      // 목록 새로고침
      fetchPostcards();
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
        <div className="hdWrap">
          <Header title="예약엽서목록" path="/user" />
        </div>
        <div className="container">
          <div style={{ textAlign: "center", padding: "50px" }}>로딩 중...</div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <div className="hdWrap">
          <Header title="예약엽서목록" path="/user" />
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
        <Header title="예약엽서목록" path="/user" />
      </div>

      <div className="container">
        <div className={styles.postCopy}>
          오늘도 해 넘어가는 들녘
          <br />
          바라보멍 너 생각에 웃음 나불어
          <br />이 정 담은 편지를 살그마니 보낸다게
        </div>
        <main className={styles.listMain}>
          <div className={styles.postcardBox}>
            {postcards.length === 0 ? (
              <div style={{ textAlign: "center", padding: "50px" }}>
                작성한 엽서가 없습니다.
              </div>
            ) : (
              postcards.map((item) => (
                <PostcardItem
                  key={item.id}
                  data={item}
                  onDelete={handleDelete}
                />
              ))
            )}
          </div>
          <div className={styles.buttonSection}>
            <Link href="/write" className={"btnBig"} style={{ color: "#FFF" }}>
              엽서 작성하기
            </Link>
          </div>
        </main>
      </div>
    </>
  );
}

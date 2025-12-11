"use client";
import styles from "./user.module.scss";
import Header from "../components/Header";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { TbEdit } from "react-icons/tb";
import { authUtils } from "@/lib/utils/auth";
import { useAuth } from "@/hooks/useAuth";
import { observer } from "mobx-react-lite";
import { useStore } from "@/store/StoreProvider";
import { useNotification } from "../context/NotificationContext";

import Logo from "../components/LogoBox";

const User = observer(() => {
  useAuth(); // 인증 체크
  const router = useRouter();
  const { postcardStore } = useStore();
  const { showModal } = useNotification();

  useEffect(() => {
    postcardStore.fetchPostcards();
  }, [postcardStore]);

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
      router.push("/login");
    }
  };

  return (
    <>
      <div className="hdrWrap">
        <Header
          title="사용자"
          path="/user"
          showLogout={true}
          onLogout={handleLogout}
        />
      </div>
      <div className="container">
        <main className={styles.userMain}>
          <Logo c_value="#f61" bg_value="#fff" />
          <div className={styles.inputBox}>
            <button
              className={styles.menuItem}
              onClick={() => router.push("/list")}
            >
              <span className={styles.boxTxt}>
                <b>엽서목록보기</b>
                <i>제주방언엽서 목록 확인하기</i>
              </span>
              <span>
                <b>{postcardStore.postcardsCount}</b>
                <i>개</i>
              </span>
            </button>

            <button
              className={styles.menuItem}
              onClick={() => router.push("/write")}
            >
              <span className={styles.boxTxt}>
                <b>엽서작성하기</b>
                <i>제주방언엽서 미래로 보내기</i>
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

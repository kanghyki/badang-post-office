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
import { ROUTES } from "@/lib/constants/urls";
import { authApi } from "@/lib/api/auth";

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
      } catch (error) {
        await showModal({
          title: "오류",
          message: "회원 탈퇴 중 오류가 발생했습니다.",
          type: "alert",
        });
      }
    }
  };

  return (
    <>
      <div className="hdrWrap">
        <Header
          title="사용자"
          path={ROUTES.USER}
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

          <button className={styles.deleteButton} onClick={handleDeleteAccount}>
            회원 탈퇴
          </button>
        </main>
      </div>
    </>
  );
});

export default User;

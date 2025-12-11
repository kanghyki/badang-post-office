"use client";
import Image from "next/image";
import Link from "next/link";
import styles from "./user.module.scss";
import Header from "../components/Header";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { FaRegCircle, FaCircleCheck } from "react-icons/fa6";
import { TbEdit } from "react-icons/tb";
import { authUtils } from "@/lib/utils/auth";
import { useAuth } from "@/hooks/useAuth";
import { observer } from "mobx-react-lite";
import { useStore } from "@/store/StoreProvider";

import Logo from "../components/LogoBox";

const User = observer(() => {
  useAuth(); // 인증 체크
  const router = useRouter();
  const { postcardStore } = useStore();
  const [selectedPage, setSelectedPage] = useState("");

  useEffect(() => {
    postcardStore.fetchPostcards();
  }, [postcardStore]);
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedPage(e.target.id);
  };

  const handleSubmit = () => {
    if (!selectedPage) {
      alert("메뉴를 선택해 주세요.");
      return;
    }

    if (selectedPage === "list") router.push("/list");
    if (selectedPage === "write") router.push("/write");
  };

  const handleLogout = () => {
    if (confirm("로그아웃 하시겠습니까?")) {
      authUtils.removeToken();
      alert("로그아웃 되었습니다.");
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
            <input
              type="radio"
              name="postcard"
              id="list"
              onChange={handleChange}
            />
            <label htmlFor="list">
              <span className={styles.radioBox}>
                <FaRegCircle />
                <FaCircleCheck />

                <span className={styles.boxTxt}>
                  <b>엽서목록보기</b>
                  <i>제주방언엽서 목록 확인하기</i>
                </span>
              </span>
              <span>
                <b>{postcardStore.postcardsCount}</b>
                <i>개</i>
              </span>
            </label>

            <input
              type="radio"
              name="postcard"
              id="write"
              onChange={handleChange}
            />
            <label htmlFor="write">
              <span className={styles.radioBox}>
                <FaRegCircle />
                <FaCircleCheck />

                <span className={styles.boxTxt}>
                  <b>엽서작성하기</b>
                  <i>제주방언엽서 미래로 보내기</i>
                </span>
              </span>
              <span className={styles.boxCnt}>
                <TbEdit />
              </span>
            </label>
          </div>

          <div className={styles.buttonSection}>
            <button className={styles.sendBtn} onClick={handleSubmit}>
              이동하기
            </button>
          </div>
        </main>
      </div>
    </>
  );
});

export default User;

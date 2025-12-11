"use client";
import Image from "next/image";
import Link from "next/link";
import styles from "./user.module.scss";
import Header from "../Components/Header";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { FaRegCircle, FaCircleCheck } from "react-icons/fa6";
import { TbEdit } from "react-icons/tb";
import { authUtils } from "../utils/auth";
import { useAuth } from "../hooks/useAuth";

import Logo from "../Components/LogoBox";

export default function User() {
  useAuth(); // 인증 체크
  const router = useRouter();
  const [selectedPage, setSelectedPage] = useState("");
  const postcards = [
    { id: 1, title: "..." },
    { id: 2, title: "..." },
    { id: 3, title: "..." },
    { id: 4, title: "..." },
    { id: 5, title: "..." },
    { id: 6, title: "..." },
    { id: 7, title: "..." },
  ];
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
        <Header title="사용자"  path="/user"/>
      </div>
      <div className="container">
        <main className={styles.userMain}>
          <div style={{ textAlign: "right", marginBottom: "10px" }}>
            <button
              onClick={handleLogout}
              style={{
                padding: "8px 16px",
                background: "#f44336",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "14px"
              }}
            >
              로그아웃
            </button>
          </div>
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
              <span><b>{postcards.length}</b><i>개</i></span>
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
              <span className={styles.boxCnt}><TbEdit /></span>
            </label>
          </div>

          <div className={styles.buttonSection}>
            <button className={styles.sendBtn} onClick={handleSubmit}>이동하기</button>
          </div>
        </main>
      </div>
    </>
  );
}
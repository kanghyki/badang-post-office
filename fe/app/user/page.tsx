"use client";
import Image from "next/image";
import Link from "next/link";
import styles from "./user.module.scss";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { FaRegCircle, FaCircleCheck } from "react-icons/fa6";

export default function User() {
  const pageTitle = "사용자";
  const router = useRouter();
  const [selectedPage, setSelectedPage] = useState("");

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

  return (
    <>
      <div className="hdrWrap"></div>
      <div className="container">
        <main className={styles.userMain}>
          <div className={styles.logoImg}></div>
          <h1 className={styles.logoTitle}>제주헌디</h1>
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
              <span className={styles.boxCnt}><b>{"7"}</b><i>개</i></span>
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
              <span className={styles.boxCnt}><b>1</b><i>day</i></span>
            </label>

            <div className={styles.submitWrap}>
              <button onClick={handleSubmit} className="btnBig">
                이동하기
              </button>
            </div>

          </div>
        </main>
      </div>
    </>
  );
}
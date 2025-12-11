"use client";
import styles from "./home.module.scss";
import Link from "next/link";
import Logo from "../components/LogoBox";
import { useEffect } from "react";
export default function Home() {
  const pageTitle = "시작";
  useEffect(() => {
    document.body.style.backgroundColor = "#FE6716"; // 시작화면 배경색

    return () => {
      document.body.style.backgroundColor = ""; // 나갈 때 초기화
    };
  }, []);
  return (
    <>
      <div className="hdWrap"></div>
      <div className="container">
        <main className={styles.homeMain}>
          <Logo c_value="#FFF" bg_value="#fff"/>
          <p className={styles.headCopy}>
            시간을 담아 보내는<br />제주방언 느영나영 편지,<br />미래에 도착해서 만나.</p>
          <div className={styles.buttonSection}>
            <Link href="/login" className={`${styles.moveBtn} btnBig`}>
              START
            </Link>
          </div>
        </main>
      </div>
    </>
  );
}
"use client";
import styles from "./home.module.scss";
import Link from "next/link";
import Logo from "@/app/components/LogoBox";
import { ROUTES } from "@/lib/constants/urls";
import { useEffect, useState } from "react";

export default function Home() {
  const [targetRoute, setTargetRoute] = useState(ROUTES.LOGIN);

  useEffect(() => {
    document.body.style.backgroundColor = "#FE6716"; // 시작화면 배경색

    // 온보딩을 본 적이 없으면 온보딩으로, 봤으면 로그인으로
    const hasSeenOnboarding = localStorage.getItem("hasSeenOnboarding");
    if (!hasSeenOnboarding) {
      setTargetRoute(ROUTES.ONBOARDING);
    }

    return () => {
      document.body.style.backgroundColor = ""; // 나갈 때 초기화
    };
  }, []);

  return (
    <>
      <main className={styles.homeMain}>
        <Logo c_value="#FFF" bg_value="#fff" />
        <p className={styles.headCopy}>
          시간을 담아 보내는
          <br />
          제주방언 느영나영 편지,
          <br />
          미래에 도착해서 만나.
        </p>
        <div className={styles.buttonSection}>
          <Link href={targetRoute} className={styles.moveBtn}>
            문 열고 들어가기
          </Link>
        </div>
      </main>
    </>
  );
}

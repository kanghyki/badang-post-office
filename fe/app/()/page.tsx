"use client";
import styles from "./home.module.scss";
import Link from "next/link";
import Logo from "@/app/components/LogoBox";
import { ROUTES } from "@/lib/constants/urls";
import { useEffect, useState } from "react";

export default function Home() {
  const [targetRoute, setTargetRoute] = useState<string>(ROUTES.LOGIN);

  useEffect(() => {
    // 온보딩을 본 적이 없으면 온보딩으로, 봤으면 로그인으로
    const hasSeenOnboarding = localStorage.getItem("hasSeenOnboarding");
    if (!hasSeenOnboarding) {
      setTargetRoute(ROUTES.ONBOARDING);
    }
  }, []);

  return (
    <>
      <main className={styles.homeMain}>
        <div className={styles.logoWrapper}>
          <Logo c_value="#FFF" bg_value="#fff" />
        </div>
        <p className={styles.headCopy}>
          작은 마음 담은 엽서 한 통
          <br />
          바당우체국이 전해드려요
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

'use client';
import styles from './home.module.scss';
import Link from 'next/link';
import Logo from '@/app/components/LogoBox';
import { ROUTES } from '@/lib/constants/urls';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authUtils } from '@/lib/utils/auth';

export default function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 로그인 상태면 메인으로 리다이렉트
    if (authUtils.getToken()) {
      router.replace(ROUTES.MAIN);
      return;
    }
    setIsLoading(false);
  }, [router]);

  useEffect(() => {
    document.body.style.backgroundColor = '#FE6716'; // 시작화면 배경색

    return () => {
      document.body.style.backgroundColor = ''; // 나갈 때 초기화
    };
  }, []);

  if (isLoading) {
    return null; // 로딩 중에는 아무것도 표시하지 않음
  }

  return (
    <>
      <main className={styles.homeMain}>
        <Logo />
        <p className={styles.headCopy}>
          시간을 담아 보내는
          <br />
          제주방언 느영나영 편지,
          <br />
          미래에 도착해서 만나.
        </p>
        <div className={styles.buttonSection}>
          <Link href={ROUTES.ONBOARDING} className={styles.moveBtn}>
            문 열고 들어가기
          </Link>
        </div>
      </main>
    </>
  );
}

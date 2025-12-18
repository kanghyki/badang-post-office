'use client';

import Link from 'next/link';
import styles from './login.module.scss';
import Logo from '@/app/components/LogoBox';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api/auth';
import { authUtils } from '@/lib/utils/auth';
import { useNotification } from '@/app/context/NotificationContext';
import { ROUTES } from '@/lib/constants/urls';

export default function Login() {
  const router = useRouter();
  const { showToast } = useNotification();

  const [email, setEmail] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('rememberedEmail') || '';
    }
    return '';
  });
  const [password, setPassword] = useState('');
  const [rememberEmail, setRememberEmail] = useState(() => {
    if (typeof window !== 'undefined') {
      return !!localStorage.getItem('rememberedEmail');
    }
    return false;
  });

  // 컴포넌트 마운트 시 로그인 상태 확인
  useEffect(() => {
    // 이미 로그인되어 있으면 홈으로 리다이렉트
    if (authUtils.getToken()) {
      router.replace(ROUTES.MAIN);
    }
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await authApi.login({ email, password });

      console.log('로그인 응답:', response);

      if (response.access_token) {
        authUtils.setToken(response.access_token);

        // 아이디 기억하기 처리
        if (rememberEmail) {
          localStorage.setItem('rememberedEmail', email);
        } else {
          localStorage.removeItem('rememberedEmail');
        }

        router.push(ROUTES.MAIN);
      }
    } catch (error) {
      console.error('로그인 에러:', error);
      if (error instanceof Error) {
        showToast({ message: `로그인 실패: ${error.message}`, type: 'error' });
      } else {
        showToast({ message: '서버에 연결할 수 없습니다.', type: 'error' });
      }
    }
  };

  return (
    <>
      <div className="container">
        <main className={styles.loginMain}>
          <Logo c_value="#f61" bg_value="#fff" />

          <div className={styles.loginBox}>
            <form onSubmit={handleLogin}>
              <label>
                <span>이메일</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="이메일을 입력하세요"
                  required
                />
              </label>

              <label>
                <span>비밀번호</span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="비밀번호를 입력하세요"
                  required
                />
              </label>

              <label className={styles.rememberEmail}>
                <input
                  type="checkbox"
                  checked={rememberEmail}
                  onChange={(e) => setRememberEmail(e.target.checked)}
                />
                <span>이메일 기억하기</span>
              </label>

              <button type="submit" className="btnBig">
                로그인
              </button>
            </form>
          </div>

          <div className={styles.signupLink}>
            <span>계정이 없으신가요?</span>
            <Link href={ROUTES.SIGNUP}>회원가입</Link>
          </div>
        </main>
      </div>
    </>
  );
}

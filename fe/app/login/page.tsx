"use client";

import Link from "next/link";
import styles from "./login.module.scss";
import Header from "../components/Header";
import Logo from "../components/LogoBox";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api/auth";
import { authUtils } from "@/lib/utils/auth";
import { useNotification } from "../context/NotificationContext";
import { ROUTES } from "@/lib/constants/urls";

export default function Login() {
  const router = useRouter();
  const { showToast } = useNotification();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberEmail, setRememberEmail] = useState(false);

  // 컴포넌트 마운트 시 저장된 이메일 불러오기
  useEffect(() => {
    const savedEmail = localStorage.getItem("rememberedEmail");
    if (savedEmail) {
      setEmail(savedEmail);
      setRememberEmail(true);
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await authApi.login({ email, password });

      console.log("로그인 응답:", response);

      if (response.access_token) {
        authUtils.setToken(response.access_token);

        // 아이디 기억하기 처리
        if (rememberEmail) {
          localStorage.setItem("rememberedEmail", email);
        } else {
          localStorage.removeItem("rememberedEmail");
        }

        router.push(ROUTES.MAIN);
      }
    } catch (error) {
      console.error("로그인 에러:", error);
      if (error instanceof Error) {
        showToast({ message: `로그인 실패: ${error.message}`, type: "error" });
      } else {
        showToast({ message: "서버에 연결할 수 없습니다.", type: "error" });
      }
    }
  };

  return (
    <>
      <div className="hdWrap">
        <Header title="로그인" />
      </div>

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

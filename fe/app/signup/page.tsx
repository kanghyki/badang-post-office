"use client";

import Link from "next/link";
import styles from "./signup.module.scss";
import Logo from "../components/LogoBox";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api/auth";
import { useNotification } from "../context/NotificationContext";
import { ROUTES } from "@/lib/constants/urls";

export default function Signup() {
  const { showToast } = useNotification();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await authApi.signup({ email, name, password });

      console.log("회원가입 성공:", response);

      router.push(ROUTES.LOGIN);
    } catch (error) {
      console.error("회원가입 에러:", error);
      if (error instanceof Error) {
        showToast({
          message: `회원가입 실패: ${error.message}`,
          type: "error",
        });
      } else {
        showToast({ message: "서버에 연결할 수 없습니다.", type: "error" });
      }
    }
  };

  return (
    <>
      <div className="container">
        <main className={styles.signupMain}>
          <Logo c_value="#f61" bg_value="#fff" />

          <div className={styles.signupBox}>
            <form onSubmit={handleSubmit}>
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
                <span>닉네임</span>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="닉네임을 입력하세요"
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

              <button type="submit" className="btnBig">
                회원가입
              </button>
            </form>
          </div>

          <div className={styles.loginLink}>
            <span>이미 계정이 있으신가요?</span>
            <Link href={ROUTES.LOGIN}>로그인</Link>
          </div>
        </main>
      </div>
    </>
  );
}

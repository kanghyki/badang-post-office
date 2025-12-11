"use client";

import Link from "next/link";
import styles from "./login.module.scss";
import Header from "../Components/Header";
import Logo from "../Components/LogoBox";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/app/api/auth";
import { authUtils } from "../utils/auth";

export default function Login() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await authApi.login({ email, password });

      console.log("로그인 응답:", response);

      if (response.access_token) {
        authUtils.setToken(response.access_token);
        alert("로그인 성공!");
        router.push("/user");
      }
    } catch (error) {
      console.error("로그인 에러:", error);
      if (error instanceof Error) {
        alert(`로그인 실패: ${error.message}`);
      } else {
        alert("서버에 연결할 수 없습니다.");
      }
    }
  };

  return (
    <>
      <div className="hdWrap">
        <Header title="로그인" path="/" />
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
            </form>
          </div>

          <div className={styles.buttonGroup}>
            <button className="btnBig" onClick={handleLogin}>
              로그인
            </button>
            <Link href="/signup" className="btnBig btnSecondary">
              회원가입하기
            </Link>
          </div>
        </main>
      </div>
    </>
  );
}

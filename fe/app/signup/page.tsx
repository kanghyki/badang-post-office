"use client";

import Link from "next/link";
import styles from "./signup.module.scss";
import Header from "../Components/Header";
import Logo from "../Components/LogoBox";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/app/api/auth";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await authApi.signup({ email, name, password });

      console.log("회원가입 성공:", response);

      alert("회원가입이 완료되었습니다!");
      router.push("/login");
    } catch (error) {
      console.error("회원가입 에러:", error);
      if (error instanceof Error) {
        alert(`회원가입 실패: ${error.message}`);
      } else {
        alert("서버에 연결할 수 없습니다.");
      }
    }
  };

  return (
    <>
      <div className="hdWrap">
        <Header title="회원가입" path="/login" />
      </div>

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
            </form>
          </div>

          <div className={styles.buttonGroup}>
            <button className="btnBig" onClick={handleSubmit}>
              회원가입
            </button>
            <Link href="/login" className="btnBig btnSecondary">
              로그인하기
            </Link>
          </div>
        </main>
      </div>
    </>
  );
}

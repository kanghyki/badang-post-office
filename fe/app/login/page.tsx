"use client";

import Image from "next/image";
import Link from "next/link";
import styles from "./login.module.scss";
import Header from "../Components/Header";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Login() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    const reqBody = {
      email,
      password,
    };

    try {
      const res = await fetch("https://jeju-be.hyki.me/docs/v1/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(reqBody),
      });

      const data = await res.json();

      console.log("로그인 응답:", data);

      if (!res.ok) {
        alert(`로그인 실패: ${data.message || "아이디 또는 비밀번호가 올바르지 않습니다."}`);
        return;
      }

      alert("로그인 성공!");

      // 🔥 accessToken 저장 (백엔드에서 어떤 키로 주는지 확인 필요)
      if (data?.data?.accessToken) {
        localStorage.setItem("accessToken", data.data.accessToken);
      }

      // 로그인 후 이동
      router.push("/user");

    } catch (error) {
      console.error("로그인 에러:", error);
      alert("서버에 연결할 수 없습니다.");
    }
  };

  return (
    <>
      <div className="hdWrap">
        <Header title="로그인" path="/user"/>
      </div>

      <div className="container">
        <main className={styles.loginMain}>
          <div className={styles.loginImg}>
            <Image
              src="/images/alyak.png"
              alt=""
              width={200}
              height={320}
            />
          </div>

          <div className={styles.loginBox}>
            <form onSubmit={handleLogin}>
              <label>
                <span>이메일</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </label>

              <label>
                <span>비밀번호</span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </label>

              <label>
                <button type="submit">로그인</button>
              </label>
            </form>
          </div>

          <Link href="/signup">회원가입하기</Link>
        </main>
      </div>
    </>
  );
}
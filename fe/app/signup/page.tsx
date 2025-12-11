"use client";

import styles from "./signup.module.scss";
import Header from "../Components/Header";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Signup() {
    const [email, setEmail] = useState("");
    const [name, setName] = useState("");
    const [password, setPassword] = useState("");
    const router = useRouter();
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const reqBody = {
            email,
            name,
            password,
        };

        try {
            const res = await fetch("https://jeju-be.hyki.me/v1/auth/signup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(reqBody),
            });

            if (!res.ok) {
                const errorData = await res.json();
                alert(`회원가입 실패: ${errorData.message || "오류 발생"}`);
                return;
            }

            const data = await res.json();
            console.log("회원가입 성공:", data);

            alert("회원가입이 완료되었습니다!");
            // 회원가입 완료 후 필요한 페이지로 이동 가능
            router.push("/login");
        } catch (error) {
            console.error(error);
            alert("서버에 연결할 수 없습니다.");
        }
    };

    return (
        <>
            <div className="hdWrap">
                <Header title="회원가입" path="/login" />
            </div>

            <div className="container">
                <main className={styles.signupMain}>
                    <form onSubmit={handleSubmit}>
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
                            <span>닉네임</span>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
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

                        <button type="submit" className={styles.signupBtn}>
                            회원가입
                        </button>
                    </form>
                </main>
            </div>
        </>
    );
}

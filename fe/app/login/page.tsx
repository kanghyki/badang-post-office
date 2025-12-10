import Link from "next/link";
import styles from "./login.module.scss";

const KAKAO_CLIENT_ID = process.env.NEXT_PUBLIC_KAKAO_CLIENT_ID;
const REDIRECT_URI = "http://localhost:3000/api/auth/kakao/callback";

export default function Login() {
  const kakaoLoginUrl = `https://kauth.kakao.com/oauth/authorize?client_id=${KAKAO_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=code`;

  return (
    <>
      <div className="hdWrap"></div>
      <div className="container">
        <main className={styles.loginMain}>
          <div className={styles.loginImg}></div>
          <div className={styles.loginBox}>
            <Link href="./user" className="btnBig">
              GOOGLE LOGIN
            </Link>

            <Link href={kakaoLoginUrl} className="btnBig">
              KAKAO LOGIN
            </Link>

            <Link href="" className="btnBig">
              LINE LOGIN
            </Link>
          </div>
        </main>
      </div>
    </>
  );
}
import Image from "next/image";
import styles from "./home.module.scss";
import Link from "next/link";
export default function Home() {
  const pageTitle = "시작";
  return (
    <>
      <div className="hdWrap"></div>
      <div className="container">
        <main className={styles.homeMain}>
          <div className={styles.logoImg}></div>
          <h1 className={styles.logoTitle}>제주헌디</h1>
          <p className={styles.headCopy}>"시간을 담아 보내는 제주방언 느영나영 편지,<br/> 미래에 도착해서 만나.</p>
          <div className={"btnBox"}>
            <Link href="/login" className={"btnBig"}>
              START
            </Link>
          </div>
        </main>
      </div>
    </>
  );
}
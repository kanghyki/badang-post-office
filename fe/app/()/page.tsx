import Image from "next/image";
import styles from "./home.module.scss";
import Link from "next/link";
export default function Home() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Start</h1>
      </header>
      <main className={styles.mnView}>
        <div className={"btnBox"}>
          <Link href="/login" className={styles.btns}>
            START
          </Link>
        </div>
      </main>
    </div>
  );
}
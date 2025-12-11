import Image from "next/image";
import styles from "../()/home.module.scss";
import Link from "next/link";
export default function Home() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1>Start</h1>
      </header>
      <main className={styles.mnView}>
        <form action="">
          <input type="text" placeholder="Title" />
          <textarea placeholder="Content" />

          <input type="email" placeholder="Email" />
          <input type="date" placeholder="Date" />
          <button type="submit">SAVE</button>
        </form>
      </main>
    </div>
  );
}

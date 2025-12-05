import Image from "next/image";
import Link from "next/link";
import styles from "./user.module.scss";
export default function Home() {
  return (
    <div className="">
      <header className="header">
        <h1>USER</h1>
      </header>
      <main className="">
        <div className="btnBox">
          <Link href="./write" className={""}>
            WRITE
          </Link>
          <Link href="./list" className={""}>
            LIST
          </Link>
        </div>
      </main>
    </div>
  );
}
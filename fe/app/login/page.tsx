import Image from "next/image";
import Link from "next/link";

export default function Home() {
  return (
    <div className="">
      <header className="header">
        <h1>LOGIN</h1>
      </header>
      <main className="btnBox">
        <div>
        <Link href="./user" className={""}>
          GOOGLE LOGIN
        </Link>
        <Link href="" className={""}>
          KAKAO LOGIN
        </Link>
        <Link href="" className={""}>
          LINE LOGIN
        </Link>
        </div>
      </main>
    </div>
  );
}
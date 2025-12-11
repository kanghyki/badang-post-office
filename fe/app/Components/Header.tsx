import Link from "next/link";
import styles from "./header.module.scss";
import { IoArrowBackCircleOutline } from "react-icons/io5";
interface LoginProps {
  title: string;
  path: string;
}
export default function Header({ title, path }: LoginProps) {
  return (
    <header className={styles.header}>
      <div className={styles.headerBtn}><Link href={path}><IoArrowBackCircleOutline/></Link></div>
      <h2 className={styles.pageTitle}>{title}</h2>
      <div className={styles.headerBtn}><Link href={"/user"}></Link></div>
    </header>
  );
}
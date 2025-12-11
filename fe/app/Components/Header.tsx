import Link from "next/link";
import styles from "./header.module.scss";
import { IoArrowBackCircleOutline } from "react-icons/io5";
import { IoLogOutOutline } from "react-icons/io5";

interface LoginProps {
  title: string;
  path: string;
  showLogout?: boolean;
  onLogout?: () => void;
}
export default function Header({ title, path, showLogout, onLogout }: LoginProps) {
  return (
    <header className={styles.header}>
      <div className={styles.headerBtn}><Link href={path}><IoArrowBackCircleOutline/></Link></div>
      <h2 className={styles.pageTitle}>{title}</h2>
      <div className={styles.headerBtn}>
        {showLogout && onLogout ? (
          <button onClick={onLogout} className={styles.logoutBtn}>
            <IoLogOutOutline />
          </button>
        ) : (
          <Link href={"/user"}></Link>
        )}
      </div>
    </header>
  );
}
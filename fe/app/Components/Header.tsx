import styles from "./header.module.scss";
import { IoLogOutOutline } from "react-icons/io5";

interface LoginProps {
  title: string;
  showLogout?: boolean;
  onLogout?: () => void;
}
export default function Header({ title, showLogout, onLogout }: LoginProps) {
  return (
    <header className={styles.header}>
      <h2 className={styles.pageTitle}>{title}</h2>
      {showLogout && onLogout && (
        <button onClick={onLogout} className={styles.logoutBtn}>
          <IoLogOutOutline />
        </button>
      )}
    </header>
  );
}

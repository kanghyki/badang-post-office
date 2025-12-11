import styles from "./header.module.scss";
import { IoLogOutOutline, IoChevronBack } from "react-icons/io5";
import { useRouter } from "next/navigation";

interface LoginProps {
  title: string;
  showLogout?: boolean;
  onLogout?: () => void;
  path?: string;
  onBackClick?: () => void;
}
export default function Header({
  title,
  showLogout,
  onLogout,
  path,
  onBackClick,
}: LoginProps) {
  const router = useRouter();

  const handleBack = () => {
    if (onBackClick) {
      onBackClick();
    } else if (path) {
      router.push(path);
    }
  };

  return (
    <header className={styles.header}>
      {path && (
        <button onClick={handleBack} className={styles.backBtn}>
          <IoChevronBack />
        </button>
      )}
      <h2 className={styles.pageTitle}>{title}</h2>
      {showLogout && onLogout && (
        <button onClick={onLogout} className={styles.logoutBtn}>
          <IoLogOutOutline />
        </button>
      )}
    </header>
  );
}

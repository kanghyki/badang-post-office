import styles from "./footer.module.scss";
import Link from "next/link";
import { ROUTES } from "@/lib/constants/urls";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.content}>
        <Link href={ROUTES.HOME} className={styles.link}>
          제주바당우체국
        </Link>
        <div className={styles.divider} />
        <Link href={ROUTES.LICENSE} className={styles.link}>
          License
        </Link>
      </div>
    </footer>
  );
}

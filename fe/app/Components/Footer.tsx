import styles from "./footer.module.scss";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.content}>
        <a href="/" className={styles.link}>
          제주바당우체국
        </a>
        <div className={styles.divider} />
        <a href="/license" className={styles.link}>
          License
        </a>
      </div>
    </footer>
  );
}

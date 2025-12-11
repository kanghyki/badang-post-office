import styles from "./license.module.scss";
import Link from "next/link";
import { IoArrowBack } from "react-icons/io5";

export default function LicensePage() {
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <Link href="/" className={styles.backButton}>
          <IoArrowBack />
        </Link>
        <h1>License</h1>
      </header>

      <main className={styles.content}>
        <div className={styles.fontCard}>
          <div className={styles.fontHeader}>
            <h3>Pretendard</h3>
            <span className={styles.badge}>SIL OFL 1.1</span>
          </div>
          <p className={styles.creator}>제작 길형진 (orioncactus)</p>
          <p className={styles.description}>
            글꼴 단독 판매를 제외한 모든 상업적 행위 및 수정, 재배포가
            가능합니다.
          </p>
          <a
            href="https://noonnu.cc/font_page/694"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.link}
          >
            자세히 보기 →
          </a>
        </div>

        <div className={styles.fontCard}>
          <div className={styles.fontHeader}>
            <h3>규리의 일기</h3>
            <span className={styles.badge}>네이버 나눔글꼴</span>
          </div>
          <p className={styles.creator}>제작 네이버</p>
          <p className={styles.description}>
            이 페이지에는 네이버에서 제공한 나눔글꼴이 적용되어 있습니다.
          </p>
          <a
            href="https://noonnu.cc/font_page/565"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.link}
          >
            자세히 보기 →
          </a>
        </div>
      </main>
    </div>
  );
}

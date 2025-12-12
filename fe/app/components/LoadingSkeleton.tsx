import styles from './LoadingSkeleton.module.scss';

export default function LoadingSkeleton() {
  return (
    <div className={styles.container}>
      <div className={styles.spinner}></div>
    </div>
  );
}

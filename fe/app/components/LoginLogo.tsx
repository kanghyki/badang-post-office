import Image from 'next/image';
import styles from './loginLogo.module.scss';

export default function LoginLogo() {
  return (
    <>
      <div className={styles.logoBox}>
        <div className={styles.logoImage} style={{ backgroundColor: 'transparent' }}>
          <Image
            src="/images/logoImg3.png"
            alt="바당우체국 로고"
            fill
            style={{
              objectFit: 'contain',
            }}
            unoptimized
          />
        </div>
        <h1 className={styles.logoTitle} style={{ color: '#f61' }}>
          바당우체국
        </h1>
      </div>
    </>
  );
}

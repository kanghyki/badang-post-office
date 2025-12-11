import Image from "next/image";
import styles from "./logoBox.module.scss";
import Link from "next/link";

interface LogoBoxProps {
  c_value: string;
  bg_value: string;
}

export default function LogoBox({ c_value, bg_value }: LogoBoxProps) {
  return (
    <>
      <div className={styles.logoBox}>
        <figure style={{backgroundColor:bg_value}}>
          <Image
            src="/images/logoImg.png"
            alt="샘플 이미지"
            width={160}
            height={120}
          />
        </figure>
        <h1 className={styles.logoTitle} style={{color:c_value}}>바당우체국</h1>
      </div>
    </>
  );
}
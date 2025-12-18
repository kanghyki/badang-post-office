import Image from "next/image";
import styles from "./logoBox.module.scss";

interface LogoBoxProps {
    c_value: string;
    bg_value: string;
}

export default function LogoBox({ c_value, bg_value }: LogoBoxProps) {
    return (
        <>
            <div className={styles.logoBox}>
                <div className={styles.logoImage}>
                    <Image
                        src="/images/logoImg2.png"
                        alt="바당우체국 로고"
                        fill
                        style={{
                            objectFit: "contain",
                            padding: "2rem",
                        }}
                        unoptimized
                    />
                </div>
                <h1 className={styles.logoTitle} style={{ color: c_value }}>
                    바당우체국
                </h1>
            </div>
        </>
    );
}

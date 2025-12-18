'use client';
import styles from './header.module.scss';
import { useRouter } from 'next/navigation';
import { useState, useRef, useEffect } from 'react';
import { ROUTES } from '@/lib/constants/urls';
import Image from 'next/image';

interface LoginProps {
  showUserMenu?: boolean;
  userName?: string;
  onLogout?: () => void;
  onDeleteAccount?: () => void;
}
export default function Header({
  showUserMenu,
  userName,
  onLogout,
  onDeleteAccount,
}: LoginProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  const handleProfileClick = () => {
    router.push(ROUTES.PROFILE);
    setIsDropdownOpen(false);
  };

  const handleLogoutClick = () => {
    setIsDropdownOpen(false);
    onLogout?.();
  };

  const handleDeleteClick = () => {
    setIsDropdownOpen(false);
    onDeleteAccount?.();
  };

  const handleLogoClick = () => {
    router.push(ROUTES.MAIN);
  };

  return (
    <header className={styles.header}>
      <button onClick={handleLogoClick} className={styles.logoBtn}>
        <div className={styles.logoImageWrapper}>
          <Image
            src="/images/logoImg2.png"
            alt="바당우체국"
            fill
            style={{ objectFit: 'contain' }}
            priority
            unoptimized
          />
        </div>
        <span className={styles.logoText}>바당우체국</span>
      </button>
      {showUserMenu && (
        <div className={styles.userMenuWrapper} ref={dropdownRef}>
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className={styles.userMenuBtn}
          >
            {userName && <span className={styles.userName}>{userName}</span>}
            <div className={styles.profileImageWrapper}>
              <Image
                src="/images/profile.png"
                alt="프로필"
                width={40}
                height={40}
                style={{
                  objectFit: 'cover',
                  borderRadius: '50%',
                }}
                priority
              />
            </div>
          </button>
          {isDropdownOpen && (
            <div className={styles.dropdown}>
              <button
                onClick={handleProfileClick}
                className={styles.dropdownItem}
              >
                내 정보
              </button>
              <button
                onClick={handleLogoutClick}
                className={styles.dropdownItem}
              >
                로그아웃
              </button>
              <button
                onClick={handleDeleteClick}
                className={`${styles.dropdownItem} ${styles.danger}`}
              >
                회원탈퇴
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  );
}

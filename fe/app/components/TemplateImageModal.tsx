'use client';

import { useEffect } from 'react';
import styles from './PostcardImageModal.module.scss';

interface TemplateImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  templateImageUrl: string | null;
}

export default function TemplateImageModal({ isOpen, onClose, templateImageUrl }: TemplateImageModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className={styles.modalBackdrop} onClick={handleBackdropClick}>
      <div className={styles.modalContent}>
        <button className={styles.closeButton} onClick={onClose}>
          ✕
        </button>
        {templateImageUrl ? (
          <div className={styles.imageContainer}>
            <img src={templateImageUrl} alt="템플릿" className={styles.postcardImage} />
          </div>
        ) : (
          <div className={styles.noImageContainer}>
            <p className={styles.noImageText}>템플릿 이미지를 불러올 수 없습니다</p>
          </div>
        )}
      </div>
    </div>
  );
}

"use client";

import { useEffect } from "react";
import styles from "./Modal.module.scss";

interface ModalProps {
  title: string;
  message: string;
  type?: "confirm" | "alert";
  onConfirm: () => void;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
}

export default function Modal({
  title,
  message,
  type = "alert",
  onConfirm,
  onCancel,
  confirmText = "확인",
  cancelText = "취소",
}: ModalProps) {
  useEffect(() => {
    // 모달이 열릴 때 body 스크롤 방지
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "unset";
    };
  }, []);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && onCancel) {
      onCancel();
    }
  };

  return (
    <div className={styles.modalBackdrop} onClick={handleBackdropClick}>
      <div className={styles.modalContent}>
        <h3 className={styles.modalTitle}>{title}</h3>
        <p className={styles.modalMessage}>{message}</p>
        <div className={styles.modalButtons}>
          {type === "confirm" && onCancel && (
            <button className={styles.cancelBtn} onClick={onCancel}>
              {cancelText}
            </button>
          )}
          <button className={styles.confirmBtn} onClick={onConfirm}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

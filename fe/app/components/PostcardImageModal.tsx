"use client";

import { useEffect, useState } from "react";
import styles from "./PostcardImageModal.module.scss";
import { API_BASE_URL } from "@/lib/constants/urls";

interface PostcardImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  postcardPath: string | null;
}

export default function PostcardImageModal({
  isOpen,
  onClose,
  postcardPath,
}: PostcardImageModalProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  useEffect(() => {
    const fetchImage = async () => {
      if (!postcardPath) return;

      setLoading(true);
      setError(false);

      try {
        const token = localStorage.getItem("accessToken");
        const fullUrl = postcardPath.startsWith("http")
          ? postcardPath
          : `${API_BASE_URL}${postcardPath}`;

        const response = await fetch(fullUrl, {
          headers: {
            ...(token && { Authorization: `Bearer ${token}` }),
          },
        });

        if (!response.ok) {
          throw new Error("이미지를 불러오는데 실패했습니다");
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setImageUrl(url);
      } catch (err) {
        console.error("이미지 로드 실패:", err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen && postcardPath) {
      fetchImage();
    }

    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [isOpen, postcardPath]);

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
        {loading ? (
          <div className={styles.loadingContainer}>
            <p className={styles.loadingText}>이미지를 불러오는 중...</p>
          </div>
        ) : error ? (
          <div className={styles.noImageContainer}>
            <p className={styles.noImageText}>
              이미지를 불러오는데 실패했습니다
            </p>
          </div>
        ) : postcardPath && imageUrl ? (
          <div className={styles.imageContainer}>
            <img
              src={imageUrl}
              alt="생성된 엽서"
              className={styles.postcardImage}
            />
          </div>
        ) : (
          <div className={styles.noImageContainer}>
            <p className={styles.noImageText}>아직 엽서가 생성되지 않았습니다</p>
          </div>
        )}
      </div>
    </div>
  );
}

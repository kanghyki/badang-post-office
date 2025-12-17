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

  const handleDownload = async () => {
    if (!imageUrl) return;

    try {
      // Blob URL에서 다운로드
      const response = await fetch(imageUrl);
      const blob = await response.blob();

      // 다운로드 링크 생성
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `jeju-postcard-${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("다운로드 실패:", error);
      alert("다운로드에 실패했습니다.");
    }
  };

  return (
    <div className={styles.modalBackdrop} onClick={handleBackdropClick}>
      <div className={styles.modalContent}>
        <button className={styles.closeButton} onClick={onClose}>
          ✕
        </button>
        {postcardPath && imageUrl && !loading && !error && (
          <button
            className={styles.downloadButton}
            onClick={handleDownload}
            aria-label="엽서 사진 저장"
          >
            ⬇ 저장
          </button>
        )}
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
            <img src={imageUrl} alt="엽서" className={styles.postcardImage} />
          </div>
        ) : (
          <div className={styles.noImageContainer}>
            <p className={styles.noImageText}>
              엽서는 접수 후에 만들어져요! 🍊
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

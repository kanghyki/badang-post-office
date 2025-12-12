import Link from "next/link";
import { FaEdit, FaTrashAlt, FaEllipsisV } from "react-icons/fa";
import styles from "./PostcardItem.module.scss";
import { PostcardResponse } from "@/lib/api/postcards";
import { ROUTES } from "@/lib/constants/urls";
import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";

interface PostcardItemProps {
  data: PostcardResponse;
  index: number;
  onDelete?: (id: string) => void;
  onClick?: (data: PostcardResponse) => void;
}

const STATUS_LABELS: Record<string, string> = {
  writing: "작성중",
  pending: "예약됨",
  sent: "발송완료",
  failed: "실패",
  cancelled: "취소됨",
};

export default function PostcardItem({
  data,
  index,
  onDelete,
  onClick,
}: PostcardItemProps) {
  const router = useRouter();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

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
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isDropdownOpen]);

  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDropdownOpen(false);
    onDelete?.(data.id);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDropdownOpen(false);
    router.push(ROUTES.MODIFY(data.id));
  };

  const handleMenuToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleClick = () => {
    onClick?.(data);
  };

  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate);
    return date.toISOString().split("T")[0].replace(/-/g, ".");
  };

  const getScheduledDateText = () => {
    if (data.scheduled_at) {
      return formatDate(data.scheduled_at);
    }
    if (data.status === "sent" && data.sent_at) {
      return formatDate(data.sent_at);
    }
    return "바로 전달";
  };
  const relativeDate = (isoDate: string) => {
    // UTC 시간을 한국 시간(KST)으로 변환
    const date = new Date(isoDate);
    const kstDate = new Date(date.getTime() + (9 * 60 * 60 * 1000));
    const now = new Date();
    const diffTime = now.getTime() - kstDate.getTime();
    const diffSeconds = Math.floor(diffTime / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSeconds < 60) return "방금 전";
    if (diffMinutes < 60) return `${diffMinutes}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays === 1) return "하루 전";
    if (diffDays < 7) return `${diffDays}일 전`;
    if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7);
      return weeks === 1 ? "일주일 전" : `${weeks}주 전`;
    }
    if (diffDays < 365) {
      const months = Math.floor(diffDays / 30);
      return months === 1 ? "한 달 전" : `${months}달 전`;
    }
    const years = Math.floor(diffDays / 365);
    return years === 1 ? "1년 전" : `${years}년 전`;
  };

  return (
    <div className={styles.postcardItem} onClick={handleClick}>
      <div className={styles.listBullet}>{index + 1}</div>

      <div className={styles.listBox}>
        <div className={styles.postcardDate}>
          <div className={styles.statusBadge} data-status={data.status}>
            <span className={styles.statusLabel}>
              {STATUS_LABELS[data.status]}
            </span>
          </div>
          <div className={styles.dateRight}>
            <div className={styles.writeDate}>
              {relativeDate(data.created_at)}
            </div>
            {(data.status === "writing" || data.status === "pending") && (
              <div className={styles.menuWrapper} ref={dropdownRef}>
                <button onClick={handleMenuToggle} className={styles.menuBtn}>
                  <FaEllipsisV />
                </button>
                {isDropdownOpen && (
                  <div className={styles.dropdown}>
                    <button onClick={handleEdit} className={styles.dropdownItem}>
                      수정
                    </button>
                    <button
                      onClick={handleDelete}
                      className={`${styles.dropdownItem} ${styles.danger}`}
                    >
                      삭제
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        <div className={styles.recipient}>
          <span className={styles.label}>받는 분</span>
          <span className={styles.value}>
            {data.recipient_name || "이름 없음"}
            {data.recipient_email && ` (${data.recipient_email})`}
          </span>
        </div>
        {data.sender_name && (
          <div className={styles.title}>
            <span className={styles.label}>보내는 분</span>
            <span className={styles.value}>{data.sender_name}</span>
          </div>
        )}
        <div className={styles.content}>
          <p>{data.text || data.original_text || "내용 없음"}</p>
        </div>
      </div>
    </div>
  );
}

import Link from "next/link";
import { FaEdit, FaTrashAlt } from "react-icons/fa";
import styles from "./PostcardItem.module.scss";
import { PostcardResponse } from "@/lib/api/postcards";

interface PostcardItemProps {
  data: PostcardResponse;
  onDelete?: (id: string) => void;
}

export default function PostcardItem({ data, onDelete }: PostcardItemProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    if (confirm("정말 삭제하시겠습니까?")) {
      onDelete?.(data.id);
    }
  };

  const formatDate = (isoDate: string) => {
    const date = new Date(isoDate);
    return date.toISOString().split("T")[0].replace(/-/g, ".");
  };
  const relativeDate = (isoDate: string) => {
    const date = new Date(isoDate);
    const now = new Date();
    const d1 = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const d2 = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffTime = d2.getTime() - d1.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    const formatted = `${y}.${m}.${d}`;
    if (diffDays === 0) return formatted;
    if (diffDays === 1) return "1 day after";
    if (diffDays < 30) return `${diffDays} days after`;
    const diffMonths = Math.floor(diffDays / 30);
    if (diffMonths === 1) return "1 month after";
    if (diffMonths < 12) return `${diffMonths} months after`;
    const diffYears = Math.floor(diffMonths / 12);
    if (diffYears === 1) return "1 year after";

    return `${diffYears} years after`;
  };
  return (
    <div className={styles.postcardItem}>
      <div className={styles.listBullet}>1</div>

      <div className={styles.listBox}>
        <div className={styles.postcardDate}>
          <div className={styles.reservDate}>
            <span>
              {data.scheduled_at ? formatDate(data.scheduled_at) : "미정"}
            </span>
          </div>
          <div className={styles.dateRight}>
            <div className={styles.writeDate}>
              {relativeDate(data.created_at)}
            </div>
            {(data.status === "writing" || data.status === "pending") && (
              <div className={styles.actionButtons}>
                <Link href={`/modify?id=${data.id}`} className={styles.iconBtn}>
                  <FaEdit />
                </Link>
                <button onClick={handleDelete} className={styles.iconBtn}>
                  <FaTrashAlt />
                </button>
              </div>
            )}
          </div>
        </div>
        <div className={styles.recipient}>
          <span className={styles.label}>받는 사람</span>
          <span className={styles.value}>{data.recipient_email || "미정"}</span>
        </div>
        <div className={styles.title}>
          <span className={styles.label}>제목</span>
          <span className={styles.value}>
            {data.recipient_name || "제목 없음"}
          </span>
        </div>
        <div className={styles.content}>
          <p>{data.text || data.original_text || "내용 없음"}</p>
        </div>
      </div>
    </div>
  );
}

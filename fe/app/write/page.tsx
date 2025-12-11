"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "./write.module.scss";
import Header from "../components/Header";
import { postcardsApi } from "@/lib/api/postcards";
import { useAuth } from "@/hooks/useAuth";
import { useNotification } from "../context/NotificationContext";

export default function Write() {
  useAuth(); // 인증 체크
  const router = useRouter();
  const { showToast, showModal } = useNotification();
  const [postcardId, setPostcardId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [translatedText, setTranslatedText] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [recipientEmail, setRecipientEmail] = useState("");
  const [senderName, setSenderName] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");

  // 페이지 진입 시 빈 엽서 생성
  useEffect(() => {
    const createPostcard = async () => {
      try {
        const postcard = await postcardsApi.create();
        setPostcardId(postcard.id);
        console.log("엽서 생성 완료:", postcard.id);
      } catch (error) {
        console.error("엽서 생성 실패:", error);
        await showModal({
          title: "오류",
          message: "엽서 생성에 실패했습니다.",
          type: "alert",
        });
        router.push("/list");
      }
    };

    createPostcard();
  }, [router, showModal]);

  // 텍스트 입력 시 번역 (디바운스)
  useEffect(() => {
    if (!text.trim()) {
      setTranslatedText("");
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const result = await postcardsApi.translate(text);
        setTranslatedText(result.translated_text);
      } catch (error) {
        console.error("번역 실패:", error);
      }
    }, 500); // 500ms 디바운스

    return () => clearTimeout(timer);
  }, [text]);

  // 이미지 파일 선택
  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImage(file);

    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  // 폼 제출
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!postcardId) {
      await showModal({
        title: "오류",
        message: "엽서 ID가 없습니다. 페이지를 새로고침해주세요.",
        type: "alert",
      });
      return;
    }

    setLoading(true);

    try {
      // 1. 엽서 내용 업데이트
      await postcardsApi.update(postcardId, {
        text,
        recipient_email: recipientEmail,
        recipient_name: recipientName,
        sender_name: senderName,
        scheduled_at: scheduledAt
          ? new Date(scheduledAt).toISOString()
          : undefined,
        image: image || undefined,
      });

      // 2. 엽서 발송
      await postcardsApi.send(postcardId);

      router.push("/list");
    } catch (error) {
      console.error("엽서 전송 실패:", error);
      if (error instanceof Error) {
        showToast({ message: `전송 실패: ${error.message}`, type: "error" });
      } else {
        showToast({ message: "요청 중 오류가 발생했습니다.", type: "error" });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="hdrWrap">
        <Header title="엽서 작성하기" path="/list" />
      </div>

      <div className="container">
        <main className={styles.writeMain}>
          <form onSubmit={handleSubmit} id="postcardForm">
            {/* 엽서 내용 섹션 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>엽서 내용</h3>
              <div className={styles.textBox}>
                <div className={styles.textareaWrapper}>
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="마음을 담아 메시지를 작성해주세요..."
                    maxLength={120}
                    className={styles.textarea}
                    required
                  />
                  <span className={styles.charCount}>{text.length} / 120</span>
                </div>
                <div className={styles.translationBox}>
                  <div className={styles.translationLabel}>
                    <span className={styles.icon}>🌴</span>
                    <span>미리보기</span>
                  </div>
                  <div className={styles.translatedText}>
                    {translatedText || ""}
                  </div>
                </div>
              </div>
            </div>

            {/* 이미지 업로드 섹션 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>사진 첨부</h3>
              <div className={styles.fileInputWrapper}>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  className={styles.fileInput}
                  id="imageInput"
                />
                <label htmlFor="imageInput" className={styles.fileLabel}>
                  <span className={styles.icon}>📷</span>
                  <span>{image ? image.name : "사진을 선택해주세요"}</span>
                </label>
              </div>

              {imagePreview && (
                <div className={styles.previewBox}>
                  <img
                    src={imagePreview}
                    alt="preview"
                    className={styles.previewImg}
                  />
                </div>
              )}
            </div>

            {/* 보내는 사람 섹션 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>보내는 사람</h3>
              <div className={styles.inputGroup}>
                <label className={styles.inputLabel}>
                  <span className={styles.icon}>✍️</span>
                  <input
                    type="text"
                    value={senderName}
                    onChange={(e) => setSenderName(e.target.value)}
                    placeholder="이름을 입력해주세요"
                    className={styles.input}
                  />
                </label>
              </div>
            </div>

            {/* 받는 사람 정보 섹션 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>받는 사람</h3>
              <div className={styles.inputGroup}>
                <label className={styles.inputLabel}>
                  <span className={styles.icon}>👤</span>
                  <input
                    type="text"
                    value={recipientName}
                    onChange={(e) => setRecipientName(e.target.value)}
                    placeholder="이름을 입력해주세요"
                    className={styles.input}
                    required
                  />
                </label>
              </div>

              <div className={styles.inputGroup}>
                <label className={styles.inputLabel}>
                  <span className={styles.icon}>📧</span>
                  <input
                    type="email"
                    value={recipientEmail}
                    onChange={(e) => setRecipientEmail(e.target.value)}
                    placeholder="이메일 주소"
                    className={styles.input}
                    required
                  />
                </label>
              </div>
            </div>

            {/* 발송 시간 섹션 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>발송 예약</h3>
              <div className={styles.inputGroup}>
                <label className={styles.inputLabel}>
                  <span className={styles.icon}>📅</span>
                  <input
                    id="scheduled_at"
                    type="datetime-local"
                    value={scheduledAt}
                    onChange={(e) => setScheduledAt(e.target.value)}
                    className={styles.input}
                    required
                  />
                </label>
              </div>
            </div>
          </form>

          <div className={styles.buttonSection}>
            <button
              className={styles.sendBtn}
              type="submit"
              form="postcardForm"
              disabled={loading || !postcardId}
            >
              {loading ? (
                <>
                  <span className={styles.spinner}></span>
                  <span>보내는 중...</span>
                </>
              ) : (
                <>
                  <span>✉️</span>
                  <span>엽서 보내기</span>
                </>
              )}
            </button>
          </div>
        </main>
      </div>
    </>
  );
}

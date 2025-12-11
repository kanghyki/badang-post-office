"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "./write.module.scss";
import Header from "../components/Header";
import { postcardsApi } from "@/lib/api/postcards";
import { useAuth } from "@/hooks/useAuth";
import { useNotification } from "../context/NotificationContext";
import { ROUTES } from "@/lib/constants/urls";

export default function Write() {
  useAuth(); // 인증 체크
  const router = useRouter();
  const { showToast, showModal } = useNotification();
  const [postcardId, setPostcardId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [translatedText, setTranslatedText] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [emailLocalPart, setEmailLocalPart] = useState("");
  const [emailDomain, setEmailDomain] = useState("");
  const [senderName, setSenderName] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // 입력값 변경 감지
  useEffect(() => {
    if (
      text ||
      recipientName ||
      emailLocalPart ||
      emailDomain ||
      senderName ||
      scheduledAt ||
      image
    ) {
      setHasUnsavedChanges(true);
    }
  }, [
    text,
    recipientName,
    emailLocalPart,
    emailDomain,
    senderName,
    scheduledAt,
    image,
  ]);

  // 뒤로가기 시 경고
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = "";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [hasUnsavedChanges]);

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

  // 임시 저장 (create + update 또는 update만 호출)
  const handleSave = async () => {
    // 이메일 validation
    if (emailLocalPart || emailDomain) {
      if (!emailLocalPart || !emailDomain) {
        showToast({ message: "이메일 주소를 완성해주세요.", type: "error" });
        return;
      }
      if (!/^[a-zA-Z0-9._-]+$/.test(emailLocalPart)) {
        showToast({ message: "유효한 이메일 형식이 아닙니다.", type: "error" });
        return;
      }
      if (!/^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(emailDomain)) {
        showToast({ message: "유효한 도메인 형식이 아닙니다.", type: "error" });
        return;
      }
    }

    setLoading(true);

    try {
      let currentPostcardId = postcardId;

      // postcardId가 없으면 먼저 생성
      if (!currentPostcardId) {
        const newPostcard = await postcardsApi.create();
        currentPostcardId = newPostcard.id;
        setPostcardId(currentPostcardId);
        console.log("엽서 생성 완료:", currentPostcardId);
      }

      // 이메일 주소 조합
      const recipientEmail =
        emailLocalPart && emailDomain
          ? `${emailLocalPart}@${emailDomain}`
          : undefined;

      // 엽서 내용 업데이트
      const updatedPostcard = await postcardsApi.update(currentPostcardId, {
        text,
        recipient_email: recipientEmail,
        recipient_name: recipientName,
        sender_name: senderName,
        scheduled_at: scheduledAt
          ? new Date(scheduledAt).toISOString()
          : undefined,
        image: image || undefined,
      });

      // 서버에서 번역된 텍스트를 미리보기에 표시
      if (updatedPostcard.text) {
        setTranslatedText(updatedPostcard.text);
      }

      setHasUnsavedChanges(false);
      showToast({ message: "임시 저장되었습니다.", type: "success" });
    } catch (error) {
      console.error("저장 실패:", error);
      if (error instanceof Error) {
        showToast({ message: `저장 실패: ${error.message}`, type: "error" });
      } else {
        showToast({ message: "저장 중 오류가 발생했습니다.", type: "error" });
      }
    } finally {
      setLoading(false);
    }
  };

  // 접수하기 (update + send 호출)
  const handleSend = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // 이메일 validation
    if (!emailLocalPart || !emailDomain) {
      showToast({ message: "이메일 주소를 입력해주세요.", type: "error" });
      return;
    }
    if (!/^[a-zA-Z0-9._-]+$/.test(emailLocalPart)) {
      showToast({ message: "유효한 이메일 형식이 아닙니다.", type: "error" });
      return;
    }
    if (!/^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(emailDomain)) {
      showToast({ message: "유효한 도메인 형식이 아닙니다.", type: "error" });
      return;
    }

    setLoading(true);

    try {
      let currentPostcardId = postcardId;

      // postcardId가 없으면 먼저 생성
      if (!currentPostcardId) {
        const newPostcard = await postcardsApi.create();
        currentPostcardId = newPostcard.id;
        setPostcardId(currentPostcardId);
        console.log("엽서 생성 완료:", currentPostcardId);
      }

      // 이메일 주소 조합
      const recipientEmail = `${emailLocalPart}@${emailDomain}`;

      // 1. 엽서 내용 업데이트
      await postcardsApi.update(currentPostcardId, {
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
      await postcardsApi.send(currentPostcardId);

      setHasUnsavedChanges(false);
      router.push(ROUTES.LIST);
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
        <Header
          title="엽서 작성하기"
        />
      </div>

      <div className="container">
        <main className={styles.writeMain}>
          <form onSubmit={handleSend} id="postcardForm">
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
                  <div className={styles.emailInputWrapper}>
                    <input
                      type="text"
                      value={emailLocalPart}
                      onChange={(e) => setEmailLocalPart(e.target.value)}
                      placeholder="이메일 아이디"
                      className={styles.emailInput}
                      required
                    />
                    <span className={styles.atSymbol}>@</span>
                    <input
                      type="text"
                      value={emailDomain}
                      onChange={(e) => setEmailDomain(e.target.value)}
                      placeholder="example.com"
                      className={styles.emailInput}
                      required
                    />
                  </div>
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
              className={styles.backBtn}
              type="button"
              onClick={async () => {
                if (hasUnsavedChanges) {
                  const confirmed = await showModal({
                    title: "작성 중인 내용이 있습니다",
                    message: "저장하지 않은 내용은 사라집니다. 나가시겠습니까?",
                    type: "confirm",
                  });
                  if (confirmed) {
                    router.push(ROUTES.LIST);
                  }
                } else {
                  router.push(ROUTES.LIST);
                }
              }}
              disabled={loading}
            >
              <span>←</span>
              <span>나가기</span>
            </button>
            <button
              className={styles.saveBtn}
              type="button"
              onClick={handleSave}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className={styles.spinner}></span>
                  <span>저장 중...</span>
                </>
              ) : (
                <span>임시저장</span>
              )}
            </button>
            <button
              className={styles.sendBtn}
              type="submit"
              form="postcardForm"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className={styles.spinner}></span>
                  <span>보내는 중...</span>
                </>
              ) : (
                <span>접수하기</span>
              )}
            </button>
          </div>
        </main>
      </div>
    </>
  );
}

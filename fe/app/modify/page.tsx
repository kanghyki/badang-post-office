"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import styles from "../write/write.module.scss";
import Header from "@/app/components/Header";
import { postcardsApi } from "@/lib/api/postcards";
import { useAuth } from "@/hooks/useAuth";
import { useNotification } from "@/app/context/NotificationContext";
import { ROUTES, API_BASE_URL } from "@/lib/constants/urls";

function ModifyContent() {
  useAuth(); // 인증 체크
  const router = useRouter();
  const { showToast, showModal } = useNotification();
  const searchParams = useSearchParams();
  const postcardId = searchParams.get("id");

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [text, setText] = useState("");
  const [translatedText, setTranslatedText] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [emailLocalPart, setEmailLocalPart] = useState("");
  const [emailDomain, setEmailDomain] = useState("");
  const [senderName, setSenderName] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [sendType, setSendType] = useState<"immediate" | "scheduled">(
    "immediate"
  );
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

  // 기존 엽서 데이터 로드
  useEffect(() => {
    if (!postcardId) {
      showModal({
        title: "오류",
        message: "엽서 ID가 없습니다.",
        type: "alert",
      }).then(() => {
        router.push(ROUTES.LIST);
      });
      return;
    }

    const loadPostcard = async () => {
      try {
        setInitialLoading(true);
        const postcard = await postcardsApi.getById(postcardId);

        // 상태가 writing이나 pending일 때만 수정 가능
        if (postcard.status !== "writing" && postcard.status !== "pending") {
          await showModal({
            title: "수정 불가",
            message: "이미 발송되었거나 발송 중인 엽서는 수정할 수 없습니다.",
            type: "alert",
          });
          router.push(ROUTES.LIST);
          return;
        }

        setText(postcard.original_text || "");
        setTranslatedText(postcard.text || "");
        setRecipientName(postcard.recipient_name || "");

        // 이메일을 @ 기준으로 분리
        if (postcard.recipient_email) {
          const [local, domain] = postcard.recipient_email.split("@");
          setEmailLocalPart(local || "");
          setEmailDomain(domain || "");
        }

        setSenderName(postcard.sender_name || "");

        if (postcard.scheduled_at) {
          // ISO 8601을 datetime-local 형식으로 변환
          const date = new Date(postcard.scheduled_at);
          const localDateTime = new Date(
            date.getTime() - date.getTimezoneOffset() * 60000
          )
            .toISOString()
            .slice(0, 16);
          setScheduledAt(localDateTime);
          setSendType("scheduled");
        } else {
          setSendType("immediate");
        }

        if (postcard.postcard_path) {
          const imagePath = `${API_BASE_URL}${postcard.postcard_path}`;
          setImagePreview(imagePath);
        }
      } catch (error) {
        console.error("엽서 로드 실패:", error);
        await showModal({
          title: "오류",
          message: "엽서를 불러올 수 없습니다.",
          type: "alert",
        });
        router.push(ROUTES.LIST);
      } finally {
        setInitialLoading(false);
      }
    };

    loadPostcard();
  }, [postcardId, router]);

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

  // 이미지 삭제
  const handleImageRemove = () => {
    setImage(null);
    setImagePreview("");
    // input 파일도 초기화
    const fileInput = document.getElementById("imageInput") as HTMLInputElement;
    if (fileInput) {
      fileInput.value = "";
    }
  };

  // 저장 (update만 호출)
  const handleSave = async () => {
    if (!postcardId) {
      await showModal({
        title: "오류",
        message: "엽서 ID가 없습니다.",
        type: "alert",
      });
      return;
    }

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

    setSaving(true);

    try {
      // 이메일 주소 조합
      const recipientEmail =
        emailLocalPart && emailDomain
          ? `${emailLocalPart}@${emailDomain}`
          : undefined;

      const updatedPostcard = await postcardsApi.update(postcardId, {
        text,
        recipient_email: recipientEmail,
        recipient_name: recipientName,
        sender_name: senderName,
        scheduled_at:
          sendType === "scheduled" && scheduledAt
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
      setSaving(false);
    }
  };

  // 다시 접수하기 (update + send 호출)
  const handleSend = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!postcardId) {
      await showModal({
        title: "오류",
        message: "엽서 ID가 없습니다.",
        type: "alert",
      });
      return;
    }

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

    // 예약 발송 시 날짜 validation
    if (sendType === "scheduled" && !scheduledAt) {
      showToast({ message: "발송 일시를 선택해주세요.", type: "error" });
      return;
    }

    setLoading(true);

    try {
      // 이메일 주소 조합
      const recipientEmail = `${emailLocalPart}@${emailDomain}`;

      // 1. 엽서 내용 업데이트
      await postcardsApi.update(postcardId, {
        text,
        recipient_email: recipientEmail,
        recipient_name: recipientName,
        sender_name: senderName,
        scheduled_at:
          sendType === "scheduled" && scheduledAt
            ? new Date(scheduledAt).toISOString()
            : undefined,
        image: image || undefined,
      });

      // 2. 엽서 발송
      await postcardsApi.send(postcardId);

      setHasUnsavedChanges(false);
      router.push(ROUTES.LIST);
    } catch (error) {
      console.error("엽서 전송 실패:", error);
      if (error instanceof Error) {
        showToast({ message: `전송 실패: ${error.message}`, type: "error" });
      } else {
        showToast({ message: "전송 중 오류가 발생했습니다.", type: "error" });
      }
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <>
        <div className="hdrWrap">
          <Header title="엽서 수정하기" />
        </div>
        <div className="container">
          <div style={{ textAlign: "center", padding: "50px" }}>로딩 중...</div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="hdrWrap">
        <Header title="엽서 수정하기" />
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
              {!imagePreview ? (
                <div className={styles.fileInputWrapper}>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className={styles.fileInput}
                    id="imageInput"
                  />
                  <label htmlFor="imageInput" className={styles.fileLabel}>
                    <span className={styles.uploadText}>
                      사진을 선택해주세요
                    </span>
                    <span className={styles.uploadHint}>
                      클릭하여 사진 업로드
                    </span>
                  </label>
                </div>
              ) : (
                <div className={styles.imagePreviewContainer}>
                  <div className={styles.previewBox}>
                    <img
                      src={imagePreview}
                      alt="preview"
                      className={styles.previewImg}
                    />
                    <button
                      type="button"
                      onClick={handleImageRemove}
                      className={styles.removeImageBtn}
                      aria-label="사진 삭제"
                    >
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 20 20"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="M15 5L5 15M5 5L15 15"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                        />
                      </svg>
                    </button>
                  </div>
                  {image && <p className={styles.imageName}>{image.name}</p>}
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

            {/* 발송 방식 섹션 */}
            <div className={styles.section}>
              <h3 className={styles.sectionTitle}>전달 시간</h3>

              <div className={styles.sendTypeOptions}>
                <label
                  className={`${styles.sendTypeOption} ${
                    sendType === "immediate" ? styles.active : ""
                  }`}
                >
                  <input
                    type="radio"
                    name="sendType"
                    value="immediate"
                    checked={sendType === "immediate"}
                    onChange={(e) => setSendType(e.target.value as "immediate")}
                    className={styles.radioInput}
                  />
                  <div className={styles.optionContent}>
                    <div className={styles.optionText}>
                      <div className={styles.optionTitle}>바로 전달하기</div>
                      <div className={styles.optionDescription}>
                        접수 즉시 전달
                      </div>
                    </div>
                  </div>
                </label>

                <label
                  className={`${styles.sendTypeOption} ${
                    sendType === "scheduled" ? styles.active : ""
                  }`}
                >
                  <input
                    type="radio"
                    name="sendType"
                    value="scheduled"
                    checked={sendType === "scheduled"}
                    onChange={(e) => setSendType(e.target.value as "scheduled")}
                    className={styles.radioInput}
                  />
                  <div className={styles.optionContent}>
                    <div className={styles.optionText}>
                      <div className={styles.optionTitle}>예약 전달하기</div>
                      <div className={styles.optionDescription}>
                        날짜와 시간 선택
                      </div>
                    </div>
                  </div>
                </label>
              </div>

              {sendType === "scheduled" && (
                <div className={styles.scheduledDateWrapper}>
                  <label className={styles.dateInputLabel}>
                    <span className={styles.dateLabel}>발송 일시</span>
                    <input
                      id="scheduled_at"
                      type="datetime-local"
                      value={scheduledAt}
                      onChange={(e) => setScheduledAt(e.target.value)}
                      className={styles.dateInput}
                      required
                    />
                  </label>
                </div>
              )}
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
              disabled={loading || saving}
            >
              <span>나가기</span>
            </button>
            <button
              className={styles.saveBtn}
              type="button"
              onClick={handleSave}
              disabled={loading || saving}
            >
              {saving ? (
                <>
                  <span className={styles.smallSpinner}></span>
                  <span>저장 중</span>
                </>
              ) : (
                <span>임시저장</span>
              )}
            </button>
            <button
              className={styles.sendBtn}
              type="submit"
              form="postcardForm"
              disabled={loading || saving}
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

export default function Modify() {
  return (
    <Suspense
      fallback={
        <>
          <div className="hdrWrap">
            <Header title="엽서 수정하기" />
          </div>
          <div className="container">
            <div style={{ textAlign: "center", padding: "50px" }}>
              로딩 중...
            </div>
          </div>
        </>
      }
    >
      <ModifyContent />
    </Suspense>
  );
}

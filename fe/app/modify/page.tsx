"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import styles from "../write/write.module.scss";
import Header from "../Components/Header";
import { postcardsApi } from "../api/postcards";
import { useAuth } from "../hooks/useAuth";

export default function Modify() {
  useAuth(); // 인증 체크
  const router = useRouter();
  const searchParams = useSearchParams();
  const postcardId = searchParams.get("id");

  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [text, setText] = useState("");
  const [translatedText, setTranslatedText] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [recipientEmail, setRecipientEmail] = useState("");
  const [senderName, setSenderName] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");

  // 기존 엽서 데이터 로드
  useEffect(() => {
    if (!postcardId) {
      alert("엽서 ID가 없습니다.");
      router.push("/list");
      return;
    }

    const loadPostcard = async () => {
      try {
        setInitialLoading(true);
        const postcard = await postcardsApi.getById(postcardId);

        // 상태가 writing이나 pending일 때만 수정 가능
        if (postcard.status !== "writing" && postcard.status !== "pending") {
          alert("이미 발송되었거나 발송 중인 엽서는 수정할 수 없습니다.");
          router.push("/list");
          return;
        }

        setText(postcard.original_text || "");
        setTranslatedText(postcard.text || "");
        setRecipientName(postcard.recipient_name || "");
        setRecipientEmail(postcard.recipient_email || "");
        setSenderName(postcard.sender_name || "");

        if (postcard.scheduled_at) {
          // ISO 8601을 datetime-local 형식으로 변환
          const date = new Date(postcard.scheduled_at);
          const localDateTime = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
            .toISOString()
            .slice(0, 16);
          setScheduledAt(localDateTime);
        }

        if (postcard.postcard_path) {
          setImagePreview(postcard.postcard_path);
        }
      } catch (error) {
        console.error("엽서 로드 실패:", error);
        alert("엽서를 불러올 수 없습니다.");
        router.push("/list");
      } finally {
        setInitialLoading(false);
      }
    };

    loadPostcard();
  }, [postcardId, router]);

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
    }, 500);

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
      alert("엽서 ID가 없습니다.");
      return;
    }

    setLoading(true);

    try {
      // 엽서 내용 업데이트
      await postcardsApi.update(postcardId, {
        text,
        recipient_email: recipientEmail,
        recipient_name: recipientName,
        sender_name: senderName,
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : undefined,
        image: image || undefined,
      });

      alert("엽서가 수정되었습니다!");
      router.push("/list");
    } catch (error) {
      console.error("엽서 수정 실패:", error);
      if (error instanceof Error) {
        alert(`수정 실패: ${error.message}`);
      } else {
        alert("수정 중 오류가 발생했습니다.");
      }
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <>
        <div className="hdrWrap">
          <Header title="엽서 수정하기" path="/list" />
        </div>
        <div className="container">
          <div style={{ textAlign: "center", padding: "50px" }}>
            로딩 중...
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="hdrWrap">
        <Header title="엽서 수정하기" path="/list" />
      </div>

      <div className="container">
        <main className={styles.writeMain}>
          <form onSubmit={handleSubmit} id="postcardForm">
            <input
              type="text"
              value={recipientName}
              onChange={(e) => setRecipientName(e.target.value)}
              placeholder="받는 사람 이름 (…에게)"
              required
            />

            <div className={styles.textBox}>
              <div className={styles.transrait}>
                {translatedText || "제주방언이 여기에 표기됩니다."}
              </div>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="엽서 내용을 입력 해 주세요.(120자)"
                maxLength={120}
                required
              />
            </div>

            <input
              type="text"
              value={senderName}
              onChange={(e) => setSenderName(e.target.value)}
              placeholder="보내는 사람 이름"
            />

            <input
              type="email"
              value={recipientEmail}
              onChange={(e) => setRecipientEmail(e.target.value)}
              placeholder="받는 분 이메일"
              required
            />

            <label htmlFor="scheduled_at" className={styles.future}>
              미래시간을 정해주세요.
            </label>
            <input
              id="scheduled_at"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              required
            />

            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
            />
          </form>

          {imagePreview && (
            <div className={styles.previewBox}>
              <p>이미지 미리보기</p>
              <img
                src={imagePreview}
                alt="preview"
                className={styles.previewImg}
                height="140px"
              />
            </div>
          )}
        </main>
      </div>

      <div className="navWrap">
        <button
          className={styles.sendBtn}
          type="submit"
          form="postcardForm"
          disabled={loading}
        >
          {loading ? "수정 중..." : "수정 완료"}
        </button>
      </div>
    </>
  );
}

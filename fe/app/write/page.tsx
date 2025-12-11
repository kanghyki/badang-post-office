"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import styles from "./write.module.scss";
import Header from "../Components/Header";
import { postcardsApi } from "../api/postcards";
import { useAuth } from "../hooks/useAuth";

export default function Write() {
  useAuth(); // 인증 체크
  const router = useRouter();
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
        alert("엽서 생성에 실패했습니다.");
        router.push("/list");
      }
    };

    createPostcard();
  }, [router]);

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
      alert("엽서 ID가 없습니다. 페이지를 새로고침해주세요.");
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
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : undefined,
        image: image || undefined,
      });

      // 2. 엽서 발송
      await postcardsApi.send(postcardId);

      alert("엽서가 성공적으로 예약되었습니다!");
      router.push("/list");
    } catch (error) {
      console.error("엽서 전송 실패:", error);
      if (error instanceof Error) {
        alert(`전송 실패: ${error.message}`);
      } else {
        alert("요청 중 오류가 발생했습니다.");
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
          disabled={loading || !postcardId}
        >
          {loading ? "보내는 중..." : "엽서 보내기"}
        </button>
      </div>
    </>
  );
}
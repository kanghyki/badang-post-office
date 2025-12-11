"use client";

import { useState } from "react";
import styles from "./write.module.scss";
import Header from "../Components/Header";

export default function Write() {
  const [loading, setLoading] = useState(false);
  const [imageBase64, setImageBase64] = useState<string>("");

  // 이미지 파일 → base64 인코딩
  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onloadend = () => {
      const base64String = reader.result as string;
      setImageBase64(base64String);
      console.log("이미지 Base64 변환 완료");
    };

    reader.readAsDataURL(file); // base64로 변환
  };

  // 폼 제출
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData(e.currentTarget);

    const data = {
      template_id: formData.get("template_id") as string,
      text: formData.get("text") as string,
      recipient_email: formData.get("recipient_email") as string,
      recipient_name: formData.get("recipient_name") as string,
      sender_name: formData.get("sender_name") as string,
      scheduled_at: new Date(formData.get("scheduled_at") as string).toISOString(),
      postcard_path: imageBase64 // ★ base64 포함
    };

    try {
      const res = await fetch("https://jeju-be.hyki.me/api/v1/postcards/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      const result = await res.json();
      console.log("결과:", result);

      if (!res.ok) {
        alert("전송 실패: " + result.message);
      } else {
        alert("엽서가 성공적으로 예약되었습니다!");
      }
    } catch (err) {
      console.error(err);
      alert("요청 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="hdrWrap">
        <Header title="엽서 작성하기" path="/user" />
      </div>

      <div className="container">
        <main className={styles.writeMain}>
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              name="recipient_name"
              placeholder="받는 사람 이름 (…에게)"
              required
            />
            <div className={styles.textBox}>
              <div className={styles.transrait}>제주방언이 여기에 표기됩니다.</div>
              <textarea
                name="text"
                placeholder="엽서 내용을 입력 해 주세요.(120자)"
                maxLength={120}
                required
              />
            </div>

            <input
              type="email"
              name="recipient_email"
              placeholder="받는 분 이메일"
              required
            />
            <label htmlFor="scheduled_at" className={styles.future}>미래시간을 정해주세요.</label>
            <input
              id="scheduled_at"
              type="datetime-local"
              name="scheduled_at"
              required
            />

            <input type="hidden" name="template_id" value="default-template" />

            {/* 파일 선택 시 base64로 인코딩 */}
            <input
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              required
            />
          </form>

          {/* 업로드 이미지 미리보기 */}
          {imageBase64 && (
            <div className={styles.previewBox}>
              <p>이미지 미리보기</p>
              <img src={imageBase64} alt="preview" className={styles.previewImg} height="140px" />
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
          {loading ? "보내는 중..." : "엽서 보내기"}
        </button>
      </div>
    </>
  );
}
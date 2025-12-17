"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import styles from "./onboarding.module.scss";
import { authUtils } from "@/lib/utils/auth";
import { ROUTES } from "@/lib/constants/urls";

// ============================================
// 온보딩 슬라이드 데이터 - 이미지 경로만 수정하세요
// ============================================
const ONBOARDING_SLIDES = [
  {
    id: 1,
    image: "/images/onboarding/slide1.svg",
    title: "제주의 감성을 담은 엽서",
    description: "특별한 추억을 제주 감성 가득한 엽서로 전해보세요",
  },
  {
    id: 2,
    image: "/images/onboarding/slide2.svg",
    title: "AI가 만드는 제주어 번역",
    description: "당신의 메시지를 따뜻한 제주어로 번역해드려요",
  },
  {
    id: 3,
    image: "/images/onboarding/slide3.svg",
    title: "사진을 제주 스타일로",
    description: "소중한 사진이 제주의 감성으로 새롭게 태어나요",
  },
];

export default function Onboarding() {
  const router = useRouter();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);

  // 이미 로그인되어 있으면 메인으로 리다이렉트
  useEffect(() => {
    if (authUtils.getToken()) {
      router.replace(ROUTES.MAIN);
      return;
    }

    // 이미 온보딩을 본 사용자는 로그인 페이지로
    const hasSeenOnboarding = localStorage.getItem("hasSeenOnboarding");
    if (hasSeenOnboarding) {
      router.replace(ROUTES.LOGIN);
    }
  }, [router]);

  const handleNext = () => {
    if (currentSlide < ONBOARDING_SLIDES.length - 1) {
      setCurrentSlide(currentSlide + 1);
    } else {
      completeOnboarding();
    }
  };

  const handleSkip = () => {
    completeOnboarding();
  };

  const completeOnboarding = () => {
    localStorage.setItem("hasSeenOnboarding", "true");
    router.push(ROUTES.SIGNUP);
  };

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
  };

  // 터치 스와이프 핸들러
  const minSwipeDistance = 50;

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;

    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe && currentSlide < ONBOARDING_SLIDES.length - 1) {
      setCurrentSlide(currentSlide + 1);
    }
    if (isRightSwipe && currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    }
  };

  const isLastSlide = currentSlide === ONBOARDING_SLIDES.length - 1;
  const currentData = ONBOARDING_SLIDES[currentSlide];

  return (
    <div className={styles.onboardingContainer}>
      {/* 건너뛰기 버튼 */}
      {!isLastSlide && (
        <button className={styles.skipButton} onClick={handleSkip}>
          건너뛰기
        </button>
      )}

      {/* 슬라이드 영역 */}
      <div
        className={styles.slideArea}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        {/* 이미지 영역 */}
        <div className={styles.imageWrapper}>
          <div className={styles.imagePlaceholder}>
            {/* 실제 이미지로 교체하세요 */}
            <Image
              src={currentData.image}
              alt={currentData.title}
              fill
              style={{ objectFit: "contain" }}
              priority
              onError={(e) => {
                // 이미지 로드 실패 시 플레이스홀더 표시
                const target = e.target as HTMLImageElement;
                target.style.display = "none";
              }}
            />
            {/* 이미지가 없을 때 보이는 플레이스홀더 */}
            <div className={styles.placeholderContent}>
              <span className={styles.placeholderIcon}>🍊</span>
              <span className={styles.placeholderText}>
                이미지 {currentSlide + 1}
              </span>
            </div>
          </div>
        </div>

        {/* 텍스트 영역 */}
        <div className={styles.textWrapper}>
          <h1 className={styles.title}>{currentData.title}</h1>
          <p className={styles.description}>{currentData.description}</p>
        </div>
      </div>

      {/* 하단 컨트롤 영역 */}
      <div className={styles.controlArea}>
        {/* 인디케이터 */}
        <div className={styles.indicators}>
          {ONBOARDING_SLIDES.map((_, index) => (
            <button
              key={index}
              className={`${styles.indicator} ${
                index === currentSlide ? styles.active : ""
              }`}
              onClick={() => goToSlide(index)}
              aria-label={`슬라이드 ${index + 1}로 이동`}
            />
          ))}
        </div>

        {/* 다음/시작 버튼 */}
        <button className={styles.nextButton} onClick={handleNext}>
          {isLastSlide ? "시작하기" : "다음"}
        </button>
      </div>
    </div>
  );
}

'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import styles from './onboarding.module.scss';
import { authUtils } from '@/lib/utils/auth';
import { ROUTES } from '@/lib/constants/urls';

// ============================================
// 온보딩 슬라이드 데이터 - 이미지 경로만 수정하세요
// ============================================
const ONBOARDING_SLIDES = [
  {
    id: 1,
    image: '/images/onboarding/slide1.png',
    title: '제주의 감성을 담은 엽서',
    description: '바당우체국 입장해서 엽서 작성!',
  },
  {
    id: 2,
    image: '/images/onboarding/slide2.png',
    title: 'AI가 만드는 제주어 번역',
    description: '바당우체부가 제주어로 번역해줘요',
  },
  {
    id: 3,
    image: '/images/onboarding/slide3.png',
    title: '사진을 제주 스타일로',
    description: '제주빛으로 엽서 꾸미고 바당우체부가 배달!',
  },
];

export default function Onboarding() {
  const router = useRouter();
  const [currentSlide, setCurrentSlide] = useState(0);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // 이미 로그인되어 있으면 메인으로 리다이렉트
  useEffect(() => {
    if (authUtils.getToken()) {
      router.replace(ROUTES.MAIN);
      return;
    }

    // 이미 온보딩을 본 사용자는 로그인 페이지로
    const hasSeenOnboarding = localStorage.getItem('hasSeenOnboarding');
    if (hasSeenOnboarding) {
      router.replace(ROUTES.LOGIN);
    }
  }, [router]);

  // 스크롤 이벤트 핸들러 - 현재 슬라이드 인덱스 업데이트
  const handleScroll = () => {
    if (!scrollContainerRef.current) return;

    const container = scrollContainerRef.current;
    const scrollLeft = container.scrollLeft;
    const slideWidth = container.offsetWidth;
    const newSlide = Math.round(scrollLeft / slideWidth);

    if (newSlide !== currentSlide) {
      setCurrentSlide(newSlide);
    }
  };

  const handleNext = () => {
    if (currentSlide < ONBOARDING_SLIDES.length - 1) {
      scrollToSlide(currentSlide + 1);
    } else {
      completeOnboarding();
    }
  };

  const handleSkip = () => {
    completeOnboarding();
  };

  const completeOnboarding = () => {
    localStorage.setItem('hasSeenOnboarding', 'true');
    router.push(ROUTES.SIGNUP);
  };

  const scrollToSlide = (index: number) => {
    if (!scrollContainerRef.current) return;

    const container = scrollContainerRef.current;
    const slideWidth = container.offsetWidth;
    container.scrollTo({
      left: slideWidth * index,
      behavior: 'smooth',
    });
  };

  const isLastSlide = currentSlide === ONBOARDING_SLIDES.length - 1;

  return (
    <div className={styles.onboardingContainer}>
      {/* 건너뛰기 버튼 */}
      {!isLastSlide && (
        <button className={styles.skipButton} onClick={handleSkip}>
          건너뛰기
        </button>
      )}

      {/* 가로 스크롤 컨테이너 */}
      <div ref={scrollContainerRef} className={styles.scrollContainer} onScroll={handleScroll}>
        {ONBOARDING_SLIDES.map(slide => (
          <div key={slide.id} className={styles.slideArea}>
            {/* 이미지 영역 */}
            <div className={styles.imageWrapper}>
              <div className={styles.imagePlaceholder}>
                <Image
                  src={slide.image}
                  alt={slide.title}
                  fill
                  style={{ objectFit: 'contain' }}
                  priority
                  onError={e => {
                    // 이미지 로드 실패 시 플레이스홀더 표시
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                  }}
                />
              </div>
            </div>

            {/* 텍스트 영역 */}
            <div className={styles.textWrapper}>
              <h1 className={styles.title}>{slide.title}</h1>
              <p className={styles.description}>{slide.description}</p>
            </div>
          </div>
        ))}
      </div>

      {/* 하단 컨트롤 영역 */}
      <div className={styles.controlArea}>
        {/* 인디케이터 */}
        <div className={styles.indicators}>
          {ONBOARDING_SLIDES.map((_, index) => (
            <button
              key={index}
              className={`${styles.indicator} ${index === currentSlide ? styles.active : ''}`}
              onClick={() => scrollToSlide(index)}
              aria-label={`슬라이드 ${index + 1}로 이동`}
            />
          ))}
        </div>

        {/* 다음/시작 버튼 */}
        <button className={styles.nextButton} onClick={handleNext}>
          {isLastSlide ? '시작하기' : '다음'}
        </button>
      </div>
    </div>
  );
}

# 제주바당우체국 - Frontend

제주바당우체국의 프론트엔드 서비스입니다.

Next.js 16 (App Router)를 사용하여 구축되었습니다.

## 🛠 기술 스택

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **State Management**: MobX
- **Styling**: SCSS, Tailwind CSS
- **UI Components**: React Icons

## 🚀 시작하기 (Getting Started)

### 사전 요구사항 (Prerequisites)

- Node.js 18 이상

### 설정 및 실행

1. **디렉토리 이동**

   ```bash
   cd fe
   ```

2. **패키지 설치**

   ```bash
   npm install
   ```

3. **환경 변수 설정**
   필요한 경우 `.env.local` 파일을 생성하여 환경 변수를 설정합니다. (백엔드 API 주소 등)

4. **개발 서버 실행**
   ```bash
   npm run dev
   ```
   브라우저에서 `http://localhost:3000`을 열어 확인할 수 있습니다.

## 스크립트

- `npm run dev`: 개발 서버 실행
- `npm run build`: 프로덕션 빌드
- `npm start`: 빌드된 애플리케이션 실행
- `npm run lint`: 린트 검사

## 📂 프로젝트 구조

```
fe/
├── app/                # Next.js App Router (페이지 및 레이아웃)
│   ├── components/     # 공통 컴포넌트
│   ├── context/        # React Context
│   └── ...             # 기능별 페이지 (login, write, profile 등)
├── hooks/              # 커스텀 훅
├── lib/                # API 클라이언트 및 유틸리티
├── public/             # 정적 자산 (이미지, 아이콘)
├── store/              # MobX Store
├── styles/             # 전역 및 공통 스타일 (SCSS)
├── next.config.ts      # Next.js 설정
└── tsconfig.json       # TypeScript 설정
```

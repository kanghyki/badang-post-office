# 제주바당우체국 - Backend

제주바당우체국의 백엔드 서비스입니다.

FastAPI를 기반으로 구축되었으며, AI 번역, 이미지 처리, RAG 기반 제주어 번역 기능을 제공합니다.

## 🛠 기술 스택

-   **Framework**: FastAPI
-   **Database**: SQLite (Dev) / PostgreSQL (Prod), ChromaDB (Vector DB)
-   **AI & RAG**: OpenAI API, LangChain
-   **Task Queue**: Celery, Redis
-   **Scheduling**: APScheduler
-   **Auth**: JWT, Passlib

## 🚀 시작하기 (Getting Started)

### 사전 요구사항 (Prerequisites)

-   Docker & Docker Compose (Redis 실행용)
-   Python 3.11 이상

### 설정 및 실행

1. **디렉토리 이동**

    ```bash
    cd be
    ```

2. **가상환경 생성 및 패키지 설치**
   `setup.sh` 스크립트를 사용하여 간단하게 설정할 수 있습니다.

    ```bash
    ./setup.sh
    ```

3. **환경 변수 설정**
   `.env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요한 값을 입력합니다.

    ```bash
    cp .env.example .env
    # .env 파일을 열어 OpenAI API Key, DB URL 등을 설정해주세요.
    ```

4. **Redis 실행 (Docker)**
   Celery 및 캐싱을 위해 Redis가 필요합니다.

    ```bash
    docker-compose -f docker-compose.dev.yml up -d
    ```

5. **서버 실행**

    ```bash
    source .venv/bin/activate
    ./run_server.sh
    ```

    서버는 `http://localhost:8000`에서 실행됩니다.
    API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

6. **Worker 실행**

    이메일 전송 등 비동기 작업을 처리하려면 Worker를 실행해야 합니다.

    ```bash
    source .venv/bin/activate
    ./run_worker.sh
    ```

## 📂 프로젝트 구조

```
be/
├── app/
│   ├── database/       # DB 설정 및 모델
│   ├── dependencies/   # API 의존성 (Auth 등)
│   ├── models/         # Pydantic 스키마
│   ├── routes/         # API 엔드포인트
│   ├── services/       # 비즈니스 로직
│   ├── utils/          # 공통 유틸리티
│   ├── main.py         # 애플리케이션 진입점
│   ├── celery_app.py   # Celery 설정
│   └── worker.py       # Celery Worker
├── data/               # RAG 데이터 및 DB 파일
├── tests/              # 테스트 코드
├── Dockerfile          # 컨테이너 설정
└── requirements.txt    # 의존성 목록
```

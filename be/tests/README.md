# 테스트 가이드

## 개요

이 프로젝트는 FastAPI 백엔드의 모든 엔드포인트에 대한 테스트를 포함합니다.

## 테스트 구조

```
tests/
├── __init__.py
├── conftest.py              # 공통 fixtures 및 설정
├── test_auth.py             # 인증 엔드포인트 테스트
├── test_postcards.py        # 엽서 엔드포인트 테스트
├── test_templates.py        # 템플릿 엔드포인트 테스트
├── test_fonts.py            # 폰트 엔드포인트 테스트
├── test_translation.py      # 번역 엔드포인트 테스트
└── test_files.py            # 파일 접근 엔드포인트 테스트
```

## 설치

테스트 실행을 위한 의존성 설치:

```bash
pip install -r requirements.txt
```

## 테스트 실행

### 전체 테스트 실행

```bash
pytest
```

### 특정 파일의 테스트만 실행

```bash
pytest tests/test_auth.py
```

### 특정 테스트 클래스만 실행

```bash
pytest tests/test_auth.py::TestSignup
```

### 특정 테스트 함수만 실행

```bash
pytest tests/test_auth.py::TestSignup::test_signup_success
```

### 상세 출력과 함께 실행

```bash
pytest -v
```

### 테스트 커버리지 확인

```bash
pytest --cov=app --cov-report=html
```

## 테스트 커버리지

각 route 파일별 테스트 항목:

### 1. Auth (test_auth.py)

- ✅ POST /v1/auth/signup - 회원가입
  - 성공 케이스
  - 이메일 중복
  - 잘못된 이메일 형식
  - 필수 필드 누락
  - 짧은 비밀번호
- ✅ POST /v1/auth/login - 로그인
  - 성공 케이스
  - 잘못된 비밀번호
  - 존재하지 않는 이메일
  - 필수 필드 누락
  - 잘못된 이메일 형식

### 2. Postcards (test_postcards.py)

- ✅ POST /v1/postcards/create - 엽서 생성
  - 성공 케이스
  - 인증 없이 시도
- ✅ GET /v1/postcards - 엽서 목록 조회
  - 성공 케이스
  - 상태 필터링
  - 인증 없이 시도
  - 본인 엽서만 조회
- ✅ GET /v1/postcards/{id} - 엽서 상세 조회
  - 성공 케이스
  - 존재하지 않는 엽서
  - 인증 없이 시도
  - 다른 사용자의 엽서 조회 시도
- ✅ PATCH /v1/postcards/{id} - 엽서 수정
  - 텍스트 수정
  - 수신자 정보 수정
  - 인증 없이 시도
  - 존재하지 않는 엽서
- ✅ DELETE /v1/postcards/{id} - 엽서 취소/삭제
  - 성공 케이스
  - 인증 없이 시도
  - 존재하지 않는 엽서
- ✅ POST /v1/postcards/{id}/send - 엽서 발송
  - 성공 케이스
  - 인증 없이 시도
  - 존재하지 않는 엽서

### 3. Templates (test_templates.py)

- ✅ GET /v1/templates - 템플릿 목록 조회
  - 성공 케이스
  - 빈 목록
  - 인증 없이 시도
- ✅ GET /v1/templates/{id} - 템플릿 상세 조회
  - 성공 케이스
  - 존재하지 않는 템플릿
  - 인증 없이 시도
  - 필드가 있는 템플릿 조회

### 4. Fonts (test_fonts.py)

- ✅ GET /v1/fonts - 폰트 목록 조회
  - 성공 케이스
  - 빈 목록
  - 인증 헤더 있음
- ✅ GET /v1/fonts/{id} - 폰트 상세 조회
  - 성공 케이스
  - 존재하지 않는 폰트
  - 인증 헤더 있음
  - 시스템 폰트 조회

### 5. Translation (test_translation.py)

- ✅ POST /v1/translation/jeju - 제주 방언 번역
  - 성공 케이스
  - 긴 텍스트 번역
  - 빈 텍스트 (유효성 검사 실패)
  - 인증 없이 시도
  - API 에러 발생
  - 필수 필드 누락
  - 특수문자 포함
  - 숫자 포함
  - 줄바꿈 포함

### 6. Files (test_files.py)

- ✅ GET /v1/files/static/{file_path} - 보안 파일 접근
  - 템플릿 파일 접근 (모든 사용자)
  - 본인 업로드 파일 접근
  - 본인 생성 파일 접근
  - 다른 사용자 파일 접근 시도 (권한 없음)
  - 존재하지 않는 파일
  - 인증 없이 시도
  - 경로 탐색 공격 시도
  - 디렉토리 접근 시도
- ✅ GET /v1/files/templates/{file_path} - 템플릿 파일 공개 접근
  - 인증 없이 접근 성공
  - 인증 헤더가 있어도 접근 가능
  - 존재하지 않는 파일
  - 경로 탐색 공격 시도
  - 디렉토리 접근 시도
  - 중첩 디렉토리 파일 접근

## Fixtures

`conftest.py`에서 제공하는 주요 fixtures:

- `db_engine`: 테스트용 인메모리 SQLite 데이터베이스 엔진
- `db_session`: 테스트용 데이터베이스 세션
- `client`: 테스트용 HTTP 클라이언트
- `test_user`: 테스트용 사용자 1
- `test_user2`: 테스트용 사용자 2
- `auth_headers`: test_user의 인증 헤더
- `auth_headers_user2`: test_user2의 인증 헤더
- `setup_test_directories`: 테스트용 디렉토리 자동 생성

## 모킹 (Mocking)

외부 의존성(OpenAI API, 이메일 발송 등)은 `unittest.mock.patch`를 사용하여 모킹합니다:

```python
@patch("app.services.translation_service.translate_to_jeju")
async def test_translate_success(
    mock_translate: MagicMock,
    client: AsyncClient,
    auth_headers: dict
):
    mock_translate.return_value = "번역된 텍스트"
    # 테스트 코드...
```

## 주의사항

1. **인메모리 데이터베이스**: 각 테스트는 독립적인 인메모리 SQLite 데이터베이스를 사용합니다.
2. **파일 시스템**: 일부 테스트는 실제 파일 시스템을 사용하며, fixture에서 정리(cleanup)를 수행합니다.
3. **외부 API**: OpenAI API 등 외부 서비스는 모킹되어 실제 호출이 발생하지 않습니다.

## 문제 해결

### 테스트 실행 시 모듈을 찾을 수 없다는 에러

프로젝트 루트 디렉토리에서 실행하고 있는지 확인:

```bash
cd /path/to/jeju-gtp/be
pytest
```

### 비동기 테스트 에러

`pytest-asyncio`가 설치되어 있는지 확인:

```bash
pip install pytest-asyncio
```

### 데이터베이스 관련 에러

`aiosqlite`가 설치되어 있는지 확인:

```bash
pip install aiosqlite
```

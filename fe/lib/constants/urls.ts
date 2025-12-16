/**
 * URL 상수 정의
 * 프론트엔드와 백엔드의 모든 URL을 중앙에서 관리
 */

// ==================== 환경 변수 ====================
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// ==================== API 엔드포인트 ====================

/**
 * 인증 관련 API 엔드포인트
 */
export const AUTH_ENDPOINTS = {
  SIGNUP: "/v1/auth/signup",
  LOGIN: "/v1/auth/login",
  LOGOUT: "/v1/auth/logout",
  REFRESH: "/v1/auth/refresh",
  DELETE_ACCOUNT: "/v1/auth/withdrawal",
  ME: "/v1/auth/me",
  RESEND_VERIFICATION: "/v1/auth/resend-verification",
} as const;

/**
 * 엽서 관련 API 엔드포인트
 */
export const POSTCARD_ENDPOINTS = {
  LIST: "/v1/postcards",
  CREATE: "/v1/postcards/create",
  DETAIL: (id: string) => `/v1/postcards/${id}`,
  UPDATE: (id: string) => `/v1/postcards/${id}`,
  DELETE: (id: string) => `/v1/postcards/${id}`,
  SEND: (id: string) => `/v1/postcards/${id}/send`,
  CANCEL: (id: string) => `/v1/postcards/${id}/cancel`,
} as const;

/**
 * 번역 관련 API 엔드포인트
 */
export const TRANSLATION_ENDPOINTS = {
  TRANSLATE_TO_JEJU: "/v1/translation/jeju",
} as const;

/**
 * 템플릿 관련 API 엔드포인트
 */
export const TEMPLATE_ENDPOINTS = {
  LIST: "/v1/templates",
  DETAIL: (id: string) => `/v1/templates/${id}`,
} as const;

// ==================== 프론트엔드 라우트 ====================

/**
 * 페이지 라우트
 */
export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  SIGNUP: "/signup",
  LIST: "/list",
  WRITE: "/write",
  MODIFY: (id?: string) => (id ? `/modify?id=${id}` : "/modify"),
  MAIN: "/home",
  PROFILE: "/profile",
  LICENSE: "/license",
} as const;

/**
 * 인증이 필요한 라우트 목록
 */
export const PROTECTED_ROUTES = [
  ROUTES.LIST,
  ROUTES.WRITE,
  ROUTES.MAIN,
  ROUTES.PROFILE,
] as const;

/**
 * 인증된 사용자가 접근할 수 없는 라우트 (로그인/회원가입 페이지)
 */
export const AUTH_ONLY_ROUTES = [ROUTES.LOGIN, ROUTES.SIGNUP] as const;

// ==================== 쿼리 파라미터 ====================

/**
 * URL 쿼리 파라미터 키
 */
export const QUERY_PARAMS = {
  STATUS: "status",
  ID: "id",
  REDIRECT: "redirect",
} as const;

/**
 * 엽서 상태 값
 */
export const POSTCARD_STATUS = {
  WRITING: "writing",
  PENDING: "pending",
  SENT: "sent",
  FAILED: "failed",
  CANCELLED: "cancelled",
} as const;

// ==================== 헬퍼 함수 ====================

/**
 * API URL 생성 헬퍼
 */
export const buildApiUrl = (
  endpoint: string,
  params?: Record<string, string>
): string => {
  const url = new URL(endpoint, API_BASE_URL);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
  }
  return url.toString();
};

/**
 * 라우트 URL 생성 헬퍼
 */
export const buildRoute = (
  path: string,
  params?: Record<string, string>
): string => {
  const url = new URL(path, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
  }
  return url.pathname + url.search;
};

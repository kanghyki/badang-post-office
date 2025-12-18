import { API_BASE_URL } from '../constants/urls';

const API_URL = API_BASE_URL;

interface RequestConfig extends Omit<RequestInit, 'headers'> {
  requiresAuth?: boolean;
  headers?: Record<string, string>;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('accessToken');
  }

  async request<T>(endpoint: string, config: RequestConfig = {}): Promise<T> {
    const { requiresAuth = false, headers = {}, ...rest } = config;

    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (requiresAuth) {
      const token = this.getAuthToken();
      if (token) {
        requestHeaders['Authorization'] = `Bearer ${token}`;
      }
    }

    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...rest,
        headers: requestHeaders,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: '요청 처리 중 오류가 발생했습니다.',
        }));

        // detail이 객체인 경우 message 필드 추출
        let errorMessage: string;
        if (typeof errorData.detail === 'object' && errorData.detail !== null) {
          errorMessage = errorData.detail.message || JSON.stringify(errorData.detail);
        } else {
          errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}`;
        }

        throw new Error(errorMessage);
      }

      // 응답이 비어있으면 (204 No Content 등) null 반환
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        return null as T;
      }

      const text = await response.text();
      if (!text) {
        return null as T;
      }

      return JSON.parse(text);
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('네트워크 오류가 발생했습니다.');
    }
  }

  async get<T>(endpoint: string, requiresAuth = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET', requiresAuth });
  }

  async post<T>(endpoint: string, data?: unknown, requiresAuth = false): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      requiresAuth,
    });
  }

  async patch<T>(endpoint: string, data?: unknown, requiresAuth = false): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
      requiresAuth,
    });
  }

  async delete<T>(endpoint: string, requiresAuth = false): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE', requiresAuth });
  }
}

export const apiClient = new ApiClient(API_URL);

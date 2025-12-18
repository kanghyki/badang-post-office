import { apiClient } from './client';
import { AUTH_ENDPOINTS } from '../constants/urls';

export interface SignupRequest {
  email: string;
  name: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupResponse {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
    created_at: string;
  };
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  is_email_verified: boolean;
  created_at: string;
}

export interface UpdateProfileRequest {
  name?: string;
  password?: string;
}

export const authApi = {
  signup: async (data: SignupRequest): Promise<SignupResponse> => {
    return apiClient.post<SignupResponse>(AUTH_ENDPOINTS.SIGNUP, data);
  },

  login: async (data: LoginRequest): Promise<LoginResponse> => {
    return apiClient.post<LoginResponse>(AUTH_ENDPOINTS.LOGIN, data);
  },

  deleteAccount: async (): Promise<void> => {
    return apiClient.delete<void>(AUTH_ENDPOINTS.DELETE_ACCOUNT, true);
  },

  getUserProfile: async (): Promise<UserProfile> => {
    return apiClient.get<UserProfile>(AUTH_ENDPOINTS.ME, true);
  },

  updateUserProfile: async (data: UpdateProfileRequest): Promise<UserProfile> => {
    return apiClient.patch<UserProfile>(AUTH_ENDPOINTS.ME, data, true);
  },

  resendVerificationEmail: async (): Promise<{ message: string }> => {
    return apiClient.post<{ message: string }>(AUTH_ENDPOINTS.RESEND_VERIFICATION, undefined, true);
  },
};

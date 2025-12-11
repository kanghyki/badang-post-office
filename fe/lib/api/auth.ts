import { apiClient } from "./client";
import { AUTH_ENDPOINTS } from "../constants/urls";

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
};

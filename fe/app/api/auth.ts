import { apiClient } from "./client";

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
        return apiClient.post<SignupResponse>("/v1/auth/signup", data);
    },

    login: async (data: LoginRequest): Promise<LoginResponse> => {
        return apiClient.post<LoginResponse>("/v1/auth/login", data);
    },
};

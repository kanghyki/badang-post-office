import { apiClient } from "./client";

export type PostcardStatus = "writing" | "pending" | "sent" | "failed" | "cancelled";

export interface PostcardResponse {
    id: string;
    template_id: string;
    text: string | null;
    original_text: string | null;
    recipient_email: string | null;
    recipient_name: string | null;
    sender_name: string | null;
    status: PostcardStatus;
    scheduled_at: string | null;
    sent_at: string | null;
    postcard_path: string | null;
    error_message: string | null;
    created_at: string;
    updated_at: string;
}

export interface UpdatePostcardData {
    text?: string;
    recipient_email?: string;
    recipient_name?: string;
    sender_name?: string;
    scheduled_at?: string;
    image?: File;
}

export interface TranslationResponse {
    original_text: string;
    translated_text: string;
    model_used: string;
}

export const postcardsApi = {
    getList: async (status?: PostcardStatus): Promise<PostcardResponse[]> => {
        const params = status ? `?status=${status}` : "";
        return apiClient.get<PostcardResponse[]>(`/v1/postcards${params}`, true);
    },

    getById: async (id: string): Promise<PostcardResponse> => {
        return apiClient.get<PostcardResponse>(`/v1/postcards/${id}`, true);
    },

    create: async (): Promise<PostcardResponse> => {
        return apiClient.post<PostcardResponse>("/v1/postcards/create", undefined, true);
    },

    update: async (id: string, data: UpdatePostcardData): Promise<PostcardResponse> => {
        const formData = new FormData();

        if (data.text) formData.append("text", data.text);
        if (data.recipient_email) formData.append("recipient_email", data.recipient_email);
        if (data.recipient_name) formData.append("recipient_name", data.recipient_name);
        if (data.sender_name) formData.append("sender_name", data.sender_name);
        if (data.scheduled_at) formData.append("scheduled_at", data.scheduled_at);
        if (data.image) formData.append("image", data.image);

        const token = localStorage.getItem("accessToken");
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "https://jeju-be.hyki.me"}/v1/postcards/${id}`, {
            method: "PATCH",
            headers: {
                ...(token && { Authorization: `Bearer ${token}` }),
            },
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({
                message: "요청 처리 중 오류가 발생했습니다.",
            }));
            throw new Error(errorData.message || `HTTP ${response.status}`);
        }

        return await response.json();
    },

    send: async (id: string): Promise<PostcardResponse> => {
        return apiClient.post<PostcardResponse>(`/v1/postcards/${id}/send`, undefined, true);
    },

    delete: async (id: string): Promise<void> => {
        return apiClient.delete<void>(`/v1/postcards/${id}`, true);
    },

    translate: async (text: string): Promise<TranslationResponse> => {
        return apiClient.post<TranslationResponse>("/v1/translation/jeju", { text }, true);
    },
};

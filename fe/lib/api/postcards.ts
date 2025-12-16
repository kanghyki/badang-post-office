import { apiClient } from "./client";
import {
  POSTCARD_ENDPOINTS,
  TRANSLATION_ENDPOINTS,
  API_BASE_URL,
} from "../constants/urls";

export type PostcardStatus = "writing" | "pending" | "sent" | "failed";

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
  user_photo_url: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface UpdatePostcardData {
  template_id?: string;
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
    return apiClient.get<PostcardResponse[]>(
      `${POSTCARD_ENDPOINTS.LIST}${params}`,
      true
    );
  },

  getById: async (id: string): Promise<PostcardResponse> => {
    return apiClient.get<PostcardResponse>(POSTCARD_ENDPOINTS.DETAIL(id), true);
  },

  create: async (templateId?: string): Promise<PostcardResponse> => {
    const params = templateId ? `?template_id=${templateId}` : "";
    return apiClient.post<PostcardResponse>(
      `${POSTCARD_ENDPOINTS.CREATE}${params}`,
      undefined,
      true
    );
  },

  update: async (
    id: string,
    data: UpdatePostcardData
  ): Promise<PostcardResponse> => {
    const formData = new FormData();

    if (data.template_id) formData.append("template_id", data.template_id);
    if (data.text) formData.append("text", data.text);
    if (data.recipient_email)
      formData.append("recipient_email", data.recipient_email);
    if (data.recipient_name)
      formData.append("recipient_name", data.recipient_name);
    if (data.sender_name) formData.append("sender_name", data.sender_name);
    if (data.scheduled_at) formData.append("scheduled_at", data.scheduled_at);
    if (data.image) formData.append("image", data.image);

    const token = localStorage.getItem("accessToken");
    const response = await fetch(
      `${API_BASE_URL}${POSTCARD_ENDPOINTS.UPDATE(id)}`,
      {
        method: "PATCH",
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: formData,
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: "요청 처리 중 오류가 발생했습니다.",
      }));

      // detail이 객체인 경우 message 필드 추출
      let errorMessage: string;
      if (typeof errorData.detail === "object" && errorData.detail !== null) {
        errorMessage = errorData.detail.message || JSON.stringify(errorData.detail);
      } else {
        errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}`;
      }

      throw new Error(errorMessage);
    }

    return await response.json();
  },

  send: async (id: string): Promise<PostcardResponse> => {
    return apiClient.post<PostcardResponse>(
      POSTCARD_ENDPOINTS.SEND(id),
      undefined,
      true
    );
  },

  delete: async (id: string): Promise<void> => {
    return apiClient.delete<void>(POSTCARD_ENDPOINTS.DELETE(id), true);
  },

  cancel: async (id: string): Promise<void> => {
    return apiClient.post<void>(POSTCARD_ENDPOINTS.CANCEL(id), undefined, true);
  },

  translate: async (text: string): Promise<TranslationResponse> => {
    return apiClient.post<TranslationResponse>(
      TRANSLATION_ENDPOINTS.TRANSLATE_TO_JEJU,
      { text },
      true
    );
  },
};

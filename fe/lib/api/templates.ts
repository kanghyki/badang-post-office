import { apiClient } from "./client";
import { TEMPLATE_ENDPOINTS } from "../constants/urls";

export interface TemplateResponse {
  id: string;
  name: string;
  description: string | null;
  template_image_path: string;
  width: number;
  height: number;
  supports_photo: boolean;
}

export interface TemplateListResponse {
  templates: TemplateResponse[];
}

export interface TextConfig {
  id: string;
  template_id: string;
  config_name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  font_size: number;
  font_color: string;
  text_align: string;
  vertical_align: string;
  line_spacing: number;
  max_lines: number;
  letter_spacing: number;
}

export interface PhotoConfig {
  id: string;
  template_id: string;
  config_name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  border_radius: number;
  border_width: number;
  border_color: string;
  fit_mode: string;
}

export interface TemplateDetailResponse {
  id: string;
  name: string;
  description: string | null;
  template_image_path: string;
  width: number;
  height: number;
  supports_photo: boolean;
  text_configs: TextConfig[];
  photo_configs: PhotoConfig[];
  default_font_id: string | null;
  display_order: number;
}

export const templatesApi = {
  getList: async (): Promise<TemplateListResponse> => {
    return apiClient.get<TemplateListResponse>(
      TEMPLATE_ENDPOINTS.LIST,
      true
    );
  },

  getById: async (id: string): Promise<TemplateDetailResponse> => {
    return apiClient.get<TemplateDetailResponse>(
      TEMPLATE_ENDPOINTS.DETAIL(id),
      true
    );
  },
};

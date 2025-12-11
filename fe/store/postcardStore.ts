import { makeAutoObservable, runInAction } from "mobx";
import {
  postcardsApi,
  PostcardResponse,
  PostcardStatus,
} from "@/lib/api/postcards";

class PostcardStore {
  postcards: PostcardResponse[] = [];
  isLoading: boolean = false;
  error: string | null = null;

  constructor() {
    makeAutoObservable(this);
  }

  async fetchPostcards(status?: PostcardStatus) {
    this.isLoading = true;
    this.error = null;

    try {
      const data = await postcardsApi.getList(status);
      runInAction(() => {
        this.postcards = data;
        this.isLoading = false;
      });
    } catch (error) {
      runInAction(() => {
        this.error =
          error instanceof Error
            ? error.message
            : "엽서 목록을 불러오는데 실패했습니다.";
        this.isLoading = false;
      });
    }
  }

  async createPostcard() {
    this.isLoading = true;
    this.error = null;

    try {
      const newPostcard = await postcardsApi.create();
      runInAction(() => {
        this.postcards.push(newPostcard);
        this.isLoading = false;
      });
      return newPostcard;
    } catch (error) {
      runInAction(() => {
        this.error =
          error instanceof Error ? error.message : "엽서 생성에 실패했습니다.";
        this.isLoading = false;
      });
      throw error;
    }
  }

  async deletePostcard(id: string) {
    this.isLoading = true;
    this.error = null;

    try {
      await postcardsApi.delete(id);
      runInAction(() => {
        this.postcards = this.postcards.filter((p) => p.id !== id);
        this.isLoading = false;
      });
    } catch (error) {
      runInAction(() => {
        this.error =
          error instanceof Error ? error.message : "엽서 삭제에 실패했습니다.";
        this.isLoading = false;
      });
      throw error;
    }
  }

  get postcardsCount() {
    return this.postcards.length;
  }

  clearError() {
    this.error = null;
  }
}

export const postcardStore = new PostcardStore();

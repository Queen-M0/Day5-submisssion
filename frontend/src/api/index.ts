import { api } from "./client";
import type { Appeal, ContentItem, DemoUser, ReviewTask, ReviewTaskDetail, Scene } from "../types";

export const getDemoUsers = async () => (await api.get<{ items: DemoUser[] }>("/auth/demo-users")).data.items;
export const getScenes = async () => (await api.get<{ items: Scene[] }>("/scenes")).data.items;
export const getContents = async (sceneId: string) =>
  (await api.get<{ items: ContentItem[] }>(`/scenes/${sceneId}/contents`)).data.items;

export const createContent = async (payload: {
  sceneId: string;
  contentType: string;
  parentId: string | null;
  text: string;
}) => (await api.post("/contents", payload)).data;

export const submitAppeal = async (
  contentId: string,
  payload: { appealType: string; reason: string },
) => (await api.post(`/contents/${contentId}/appeals`, payload)).data;

export const getMyAppeals = async () => (await api.get<{ items: Appeal[] }>("/me/appeals")).data.items;
export const getReviewTasks = async () =>
  (await api.get<{ items: ReviewTask[] }>("/reviewer/tasks?status=pending")).data.items;
export const getReviewTask = async (taskId: string) =>
  (await api.get<ReviewTaskDetail>(`/reviewer/tasks/${taskId}`)).data;
export const submitReview = async (
  taskId: string,
  payload: {
    finalDecision: string;
    finalRiskLevel: number;
    reviewReason: string;
    correctionType: string;
  },
) => (await api.post(`/reviewer/tasks/${taskId}/decision`, payload)).data;

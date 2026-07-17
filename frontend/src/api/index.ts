import { api } from "./client";
import type {
  ApiAppeal,
  ApiContent,
  ApiReviewTask,
  ApiReviewTaskDetail,
  ApiTimelineEvent,
  ApiTopic,
  CommunitySummary,
  ContentCreationResult,
  DemoUser,
  ModerationRuleConfig,
  ModerationStatistics,
} from "../types";

export const getDemoUsers = async () =>
  (await api.get<{ items: DemoUser[] }>("/auth/demo-users")).data.items;

export const login = async (payload: { username: string; password: string }) =>
  (await api.post<{ accessToken: string; tokenType: string; expiresIn: number; user: DemoUser }>("/auth/login", payload)).data;

export const getCurrentUser = async () =>
  (await api.get<DemoUser>("/auth/me")).data;

export const getCommunity = async () =>
  (await api.get<CommunitySummary>("/community")).data;

export const getTopics = async (params?: { category?: string; q?: string }) =>
  (await api.get<{ items: ApiTopic[] }>("/topics", { params })).data.items;

export const getTopic = async (topicId: string) =>
  (await api.get<ApiTopic>(`/topics/${topicId}`)).data;

export const createTopic = async (payload: { title: string; category: string; body: string }) =>
  (await api.post<ContentCreationResult & { topicId: string }>("/topics", payload)).data;

export const getTopicContents = async (topicId: string) =>
  (await api.get<{ items: ApiContent[] }>(`/topics/${topicId}/contents`)).data.items;

export const createTopicContent = async (
  topicId: string,
  payload: { text: string; replyToContentId: string | null },
) => (await api.post<ContentCreationResult>(`/topics/${topicId}/contents`, payload)).data;

export const getMyContents = async (status?: string) =>
  (await api.get<{ items: ApiContent[] }>("/me/contents", { params: status ? { status } : undefined })).data.items;

export const getModeration = async (contentId: string) =>
  (await api.get<ApiModerationResponse>(`/contents/${contentId}/moderation`)).data;

interface ApiModerationResponse {
  contentId: string;
  status: string;
  appealable: boolean;
}

export const getContentTimeline = async (contentId: string) =>
  (await api.get<{ items: ApiTimelineEvent[] }>(`/contents/${contentId}/timeline`)).data.items;

export const submitAppeal = async (
  contentId: string,
  payload: { appealType: string; reason: string; extraContext: string },
) => (await api.post(`/contents/${contentId}/appeals`, payload)).data;

export const supplementAppeal = async (appealId: string, extraContext: string) =>
  (await api.post(`/appeals/${appealId}/supplement`, { extraContext })).data;

export const getMyAppeals = async () =>
  (await api.get<{ items: ApiAppeal[] }>("/me/appeals")).data.items;

export const getReviewTasks = async (params: {
  status: "pending" | "resolved";
  source?: "ai_escalation" | "user_appeal";
}) => (await api.get<{ items: ApiReviewTask[] }>("/reviewer/tasks", { params })).data.items;

export const getReviewTask = async (taskId: string) =>
  (await api.get<ApiReviewTaskDetail>(`/reviewer/tasks/${taskId}`)).data;

export const submitReviewDecision = async (
  taskId: string,
  payload: {
    finalDecision: "allow" | "maintain_limit" | "need_more_context";
    reviewReason: string;
  },
) => (await api.post(`/reviewer/tasks/${taskId}/decision`, payload)).data;

export const getModerationStatistics = async () =>
  (await api.get<ModerationStatistics>("/reviewer/statistics")).data;

export const getModerationRules = async () =>
  (await api.get<ModerationRuleConfig>("/reviewer/rules")).data;

export const getModerationRuleHistory = async () =>
  (await api.get<{ items: ModerationRuleConfig[] }>("/reviewer/rules/history")).data.items;

export const updateModerationRules = async (payload: {
  name: string;
  enabledRiskTypes: string[];
  autoLimitMinRiskLevel: number;
  manualReviewMinRiskLevel: number;
  minConfidence: number;
  requireGroundedEvidence: boolean;
  routeDivergenceToManual: boolean;
  changeReason: string;
}) => (await api.put<ModerationRuleConfig>("/reviewer/rules", payload)).data;

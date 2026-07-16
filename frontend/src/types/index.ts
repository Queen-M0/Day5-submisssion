export type Role = "user" | "reviewer" | "admin";

export interface DemoUser {
  id: string;
  username: string;
  displayName: string;
  role: Role;
}

export interface Scene {
  id: string;
  type: string;
  title: string;
  description: string;
  createdAt: string;
}

export interface Evidence {
  text: string;
  reason: string;
  riskType: string;
}

export interface ModerationSummary {
  riskLevel: number;
  riskScore: number;
  riskTypes: string[];
  decision: string;
  confidence: number;
  userVisibleReason: string;
  evidence?: Evidence[];
  contextReasoning?: string;
  reviewerReason?: string;
  rawResult?: Record<string, unknown>;
}

export interface ContentItem {
  id: string;
  sceneId: string;
  contentType: string;
  author: DemoUser;
  parentId: string | null;
  parentAuthorName: string | null;
  text: string;
  status: string;
  visibleToPublic: boolean;
  createdAt: string;
  moderation: ModerationSummary | null;
}

export interface Appeal {
  id: string;
  contentId: string;
  contentText: string;
  appealType: string;
  reason: string;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface ReviewTask {
  taskId: string;
  contentId: string;
  appealId: string | null;
  contentText: string;
  authorName: string;
  riskLevel: number;
  riskTypes: string[];
  decision: string;
  hasAppeal: boolean;
  createdAt: string;
  summary: string;
}

export interface ReviewTaskDetail {
  taskId: string;
  content: ContentItem;
  context: ContentItem[];
  moderation: ModerationSummary;
  appeal: null | {
    id: string;
    appealType: string;
    reason: string;
    status: string;
    createdAt: string;
  };
}


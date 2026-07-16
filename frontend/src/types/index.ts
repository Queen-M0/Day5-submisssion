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

export type DemoContentStatus =
  | "published"
  | "limited"
  | "pending_manual_review"
  | "appeal_submitted"
  | "appeal_reviewing"
  | "appeal_approved"
  | "appeal_rejected"
  | "need_more_context";

export interface DemoEvidence {
  contentId: string;
  quote: string;
  reason: string;
  verified: boolean;
}

export interface DemoModeration {
  riskLevel: 0 | 1 | 2 | 3;
  riskScore: number;
  riskTypes: string[];
  contextTags: string[];
  intent: string;
  targetUserIds: string[];
  evidence: DemoEvidence[];
  contextUsed: string[];
  uncertainties: string[];
  confidence: number;
  suggestedAction: "allow" | "limit" | "manual_review";
  systemDecision: "publish" | "limit" | "manual_review";
  userVisibleReason: string;
  reviewerReason: string;
}

export interface AuditEvent {
  id: string;
  time: string;
  actor: string;
  title: string;
  description: string;
  tone: "success" | "warning" | "danger" | "info";
}

export interface DemoFloor {
  id: string;
  topicId: string;
  floorNumber: number | null;
  authorId: string;
  text: string;
  replyToId: string | null;
  createdAt: string;
  status: DemoContentStatus;
  visibleToPublic: boolean;
  moderation: DemoModeration;
  auditTrail: AuditEvent[];
}

export interface DemoTopic {
  id: string;
  title: string;
  summary: string;
  category: string;
  authorId: string;
  createdAt: string;
  lastActiveAt: string;
  viewCount: number;
  floors: DemoFloor[];
}

export interface CounterAnalysis {
  supportsOriginalDecision: string[];
  supportsChange: string[];
  newEvidenceImpact: string;
  remainingUncertainties: string[];
  reviewSuggestion: string;
}

export interface DemoAppeal {
  id: string;
  contentId: string;
  authorId: string;
  appealType: string;
  reason: string;
  extraContext: string;
  status: "submitted" | "reviewing" | "approved" | "rejected" | "need_more_context";
  createdAt: string;
  counterAnalysis: CounterAnalysis | null;
  finalReason?: string;
}

export interface DemoReviewTask {
  id: string;
  contentId: string;
  appealId: string | null;
  source: "ai_escalation" | "user_appeal";
  priority: "normal" | "high";
  status: "pending" | "resolved";
  createdAt: string;
  resolvedAt?: string;
  finalDecision?: "allow" | "maintain_limit" | "need_more_context";
  reviewReason?: string;
}

export interface DemoState {
  topics: DemoTopic[];
  appeals: DemoAppeal[];
  reviewTasks: DemoReviewTask[];
}

export interface CommunitySummary {
  id: string;
  title: string;
  description: string;
  topicCount: number;
  publicFloorCount: number;
  memberCount: number;
  pendingReviewCount: number;
}

export interface ApiTopic {
  id: string;
  sceneId: string;
  title: string;
  summary: string;
  category: string;
  author: DemoUser;
  status: string;
  visibleToPublic: boolean;
  publicFloorCount: number;
  viewCount: number;
  lastReplyAuthorName: string | null;
  createdAt: string;
  lastActiveAt: string;
}

export interface ApiModeration {
  riskLevel: number;
  riskScore: number;
  riskTypes: string[];
  decision: string;
  suggestedAction: "allow" | "limit" | "manual_review";
  systemDecision: "publish" | "limit" | "manual_review";
  confidence: number;
  contextTags: string[];
  intent: string;
  targetUserIds: string[];
  contextUsed: string[];
  uncertainties: string[];
  evidence: DemoEvidence[];
  evidenceValid: boolean;
  userVisibleReason: string;
  reviewerReason?: string;
  failureReason?: string | null;
}

export interface ApiContent {
  id: string;
  sceneId: string;
  topicId: string;
  floorNumber: number | null;
  contentType: string;
  author: DemoUser;
  parentId: string | null;
  text: string;
  status: DemoContentStatus;
  visibleToPublic: boolean;
  createdAt: string;
  moderation: ApiModeration | null;
  topic?: Pick<ApiTopic, "id" | "title" | "category">;
  appealable?: boolean;
}

export interface ApiTimelineEvent {
  id: string;
  actor: string;
  action: string;
  title?: string;
  description: string;
  createdAt: string;
}

export interface ApiAppeal {
  id: string;
  contentId: string;
  contentText: string;
  topic: Pick<ApiTopic, "id" | "title" | "category">;
  appealType: string;
  reason: string;
  extraContext: string;
  status: "submitted" | "reviewing" | "approved" | "rejected" | "need_more_context";
  counterAnalysis: CounterAnalysis | null;
  finalReason: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface ApiReviewTask {
  taskId: string;
  contentId: string;
  appealId: string | null;
  source: "ai_escalation" | "user_appeal";
  priority: "normal" | "high";
  status: "pending" | "resolved";
  topicTitle: string;
  contentText: string;
  authorName: string;
  riskLevel: number;
  riskScore: number;
  riskTypes: string[];
  contextTags: string[];
  evidenceCount: number;
  createdAt: string;
  resolvedAt?: string;
  finalDecision?: "allow" | "maintain_limit" | "need_more_context";
  reviewReason?: string;
}

export interface ApiReviewTaskDetail {
  taskId: string;
  topic: ApiTopic;
  content: ApiContent;
  replyTo: ApiContent | null;
  context: ApiContent[];
  moderation: ApiModeration;
  evidenceValidation: { valid: boolean; items: DemoEvidence[] };
  appeal: null | {
    id: string;
    appealType: string;
    reason: string;
    extraContext: string;
    status: string;
    createdAt: string;
  };
  counterAnalysis: CounterAnalysis | null;
  timeline: ApiTimelineEvent[];
}

export interface ContentCreationResult {
  contentId: string;
  status: DemoContentStatus;
  floorNumber: number | null;
  visibleToPublic: boolean;
  moderation: ApiModeration;
}

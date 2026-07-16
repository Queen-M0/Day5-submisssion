import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  createTopic as createTopicRequest,
  createTopicContent,
  getCommunity,
  getContentTimeline,
  getMyAppeals,
  getMyContents,
  getReviewTask,
  getReviewTasks,
  getTopic,
  getTopicContents,
  getTopics,
  submitAppeal as submitAppealRequest,
  submitReviewDecision,
} from "../api";
import { apiErrorMessage } from "../api/client";
import { useAuth } from "./AuthContext";
import type {
  ApiAppeal,
  ApiContent,
  ApiModeration,
  ApiReviewTask,
  ApiReviewTaskDetail,
  ApiTimelineEvent,
  ApiTopic,
  AuditEvent,
  CommunitySummary,
  DemoAppeal,
  DemoFloor,
  DemoModeration,
  DemoReviewTask,
  DemoState,
  DemoTopic,
} from "../types";

interface NewTopicInput { title: string; body: string; category: string; authorId: string }
interface NewFloorInput { topicId: string; text: string; replyToId: string | null; authorId: string }
interface AppealInput { contentId: string; authorId: string; appealType: string; reason: string; extraContext: string }

interface DemoContextValue extends DemoState {
  community: CommunitySummary | null;
  loading: boolean;
  error: string | null;
  createTopic: (input: NewTopicInput) => Promise<string>;
  submitFloor: (input: NewFloorInput) => Promise<DemoFloor>;
  submitAppeal: (input: AppealInput) => Promise<void>;
  resolveTask: (taskId: string, decision: "allow" | "maintain_limit" | "need_more_context", reason: string) => Promise<void>;
  findTopic: (topicId: string) => DemoTopic | undefined;
  findFloor: (contentId: string) => { topic: DemoTopic; floor: DemoFloor } | undefined;
  findAppeal: (contentId: string) => DemoAppeal | undefined;
  loadTimeline: (contentId: string) => Promise<AuditEvent[]>;
  refresh: () => Promise<void>;
  resetDemo: () => void;
}

const emptyState: DemoState = { topics: [], appeals: [], reviewTasks: [] };
const DemoContext = createContext<DemoContextValue | null>(null);

const actionTitle: Record<string, string> = {
  "content.submitted": "提交内容",
  "moderation.context_built": "构建审核上下文",
  "moderation.completed": "上下文审核完成",
  "moderation.failed": "自动审核异常",
  "evidence.validated": "证据真实性校验",
  "content.published": "内容已公开",
  "content.limited": "内容暂时限制",
  "content.manual_review_requested": "转人工复核",
  "appeal.submitted": "提交申诉",
  "manual_review.decided": "人工复核完成",
  "content.restored": "内容恢复公开",
  "context.requested": "要求补充上下文",
};

function mapTimeline(events: ApiTimelineEvent[]): AuditEvent[] {
  return events.map((event) => ({
    id: event.id,
    time: event.createdAt,
    actor: event.actor,
    title: event.title || actionTitle[event.action] || event.action,
    description: event.description || "处理状态已更新。",
    tone: event.action.includes("published") || event.action.includes("restored") ? "success"
      : event.action.includes("limited") ? "danger"
      : event.action.includes("review") || event.action.includes("appeal") ? "warning"
      : "info",
  }));
}

function mapModeration(value: ApiModeration | null): DemoModeration {
  return {
    riskLevel: Math.min(3, Math.max(0, value?.riskLevel ?? 0)) as 0 | 1 | 2 | 3,
    riskScore: value?.riskScore ?? 0,
    riskTypes: value?.riskTypes ?? [],
    contextTags: value?.contextTags ?? [],
    intent: value?.intent ?? "等待审核结果",
    targetUserIds: value?.targetUserIds ?? [],
    evidence: value?.evidence ?? [],
    contextUsed: value?.contextUsed ?? [],
    uncertainties: value?.uncertainties ?? [],
    confidence: value?.confidence ?? 0,
    suggestedAction: value?.suggestedAction ?? "manual_review",
    systemDecision: value?.systemDecision ?? "manual_review",
    userVisibleReason: value?.userVisibleReason ?? "内容正在处理。",
    reviewerReason: value?.reviewerReason ?? "",
  };
}

function mapContent(content: ApiContent, auditTrail: AuditEvent[] = []): DemoFloor {
  return {
    id: content.id,
    topicId: content.topicId,
    floorNumber: content.floorNumber,
    authorId: content.author.id,
    text: content.text,
    replyToId: content.parentId,
    createdAt: content.createdAt,
    status: content.status,
    visibleToPublic: content.visibleToPublic,
    moderation: mapModeration(content.moderation),
    auditTrail,
  };
}

function mapTopic(topic: ApiTopic, contents: ApiContent[]): DemoTopic {
  return {
    id: topic.id,
    title: topic.title,
    summary: topic.summary,
    category: topic.category,
    authorId: topic.author.id,
    createdAt: topic.createdAt,
    lastActiveAt: topic.lastActiveAt,
    viewCount: topic.viewCount,
    floors: contents.map((item) => mapContent(item)),
  };
}

function mapAppeal(appeal: ApiAppeal, authorId: string): DemoAppeal {
  return {
    id: appeal.id,
    contentId: appeal.contentId,
    authorId,
    appealType: appeal.appealType,
    reason: appeal.reason,
    extraContext: appeal.extraContext,
    status: appeal.status,
    createdAt: appeal.createdAt,
    counterAnalysis: appeal.counterAnalysis,
    finalReason: appeal.finalReason ?? undefined,
  };
}

function mapTask(task: ApiReviewTask): DemoReviewTask {
  return {
    id: task.taskId,
    contentId: task.contentId,
    appealId: task.appealId,
    source: task.source,
    priority: task.priority,
    status: task.status,
    createdAt: task.createdAt,
    resolvedAt: task.resolvedAt,
    finalDecision: task.finalDecision,
    reviewReason: task.reviewReason,
  };
}

export function DemoProvider({ children }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth();
  const [state, setState] = useState<DemoState>(emptyState);
  const [community, setCommunity] = useState<CommunitySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  const refresh = useCallback(async () => {
    if (authLoading) return;
    const currentRequest = ++requestId.current;
    setLoading(true);
    setError(null);
    setState(emptyState);
    setCommunity(null);
    try {
      const reviewer = user.role === "reviewer" || user.role === "admin";
      const [communityData, publicTopics] = await Promise.all([getCommunity(), getTopics()]);
      let topicRecords = [...publicTopics];
      let appealRecords: ApiAppeal[] = [];
      let tasks: ApiReviewTask[] = [];
      let taskDetails: ApiReviewTaskDetail[] = [];
      let myContents: ApiContent[] = [];

      if (reviewer) {
        const [pending, resolved] = await Promise.all([
          getReviewTasks({ status: "pending" }),
          getReviewTasks({ status: "resolved" }),
        ]);
        tasks = [...pending, ...resolved];
        taskDetails = await Promise.all(tasks.map((task) => getReviewTask(task.taskId)));
        const knownTopicIds = new Set(topicRecords.map((topic) => topic.id));
        for (const detail of taskDetails) {
          if (!knownTopicIds.has(detail.topic.id)) {
            topicRecords.push(detail.topic);
            knownTopicIds.add(detail.topic.id);
          }
        }
      } else {
        [myContents, appealRecords] = await Promise.all([getMyContents(), getMyAppeals()]);
        const missingTopicIds = [...new Set(
          myContents.map((item) => item.topicId).filter((id) => !topicRecords.some((topic) => topic.id === id)),
        )];
        const privateTopics = await Promise.all(missingTopicIds.map((id) => getTopic(id)));
        topicRecords = [...topicRecords, ...privateTopics];
      }

      const contentEntries = await Promise.all(
        topicRecords.map(async (topic) => [topic.id, await getTopicContents(topic.id)] as const),
      );
      const contentsByTopic = new Map(contentEntries);
      const timelines = new Map<string, AuditEvent[]>();

      if (!reviewer && myContents.length > 0) {
        const timelineEntries = await Promise.all(
          myContents.map(async (content) => [content.id, await getContentTimeline(content.id)] as const),
        );
        for (const [contentId, events] of timelineEntries) {
          timelines.set(contentId, mapTimeline(events));
        }
      }

      const topics = topicRecords.map((topic) => {
        const contents = contentsByTopic.get(topic.id) ?? [];
        const mapped = mapTopic(topic, contents);
        mapped.floors = contents.map((content) => mapContent(content, timelines.get(content.id)));
        return mapped;
      });

      const reviewerAppeals: DemoAppeal[] = taskDetails.flatMap((detail) => {
        if (!detail.appeal) return [];
        return [{
          id: detail.appeal.id,
          contentId: detail.content.id,
          authorId: detail.content.author.id,
          appealType: detail.appeal.appealType,
          reason: detail.appeal.reason,
          extraContext: detail.appeal.extraContext,
          status: detail.appeal.status as DemoAppeal["status"],
          createdAt: detail.appeal.createdAt,
          counterAnalysis: detail.counterAnalysis,
        }];
      });

      const nextState: DemoState = {
        topics,
        appeals: reviewer ? reviewerAppeals : appealRecords.map((appeal) => mapAppeal(appeal, user.id)),
        reviewTasks: tasks.map(mapTask),
      };
      if (currentRequest === requestId.current) {
        setCommunity(communityData);
        setState(nextState);
      }
    } catch (caught) {
      if (currentRequest === requestId.current) setError(apiErrorMessage(caught));
    } finally {
      if (currentRequest === requestId.current) setLoading(false);
    }
  }, [authLoading, user.id, user.role]);

  useEffect(() => { void refresh(); }, [refresh]);

  const value = useMemo<DemoContextValue>(() => ({
    ...state,
    community,
    loading,
    error,
    createTopic: async ({ title, body, category }) => {
      const created = await createTopicRequest({ title, body, category });
      await refresh();
      return created.topicId;
    },
    submitFloor: async ({ topicId, text, replyToId, authorId }) => {
      const created = await createTopicContent(topicId, { text, replyToContentId: replyToId });
      await refresh();
      return {
        id: created.contentId,
        topicId,
        floorNumber: created.floorNumber,
        authorId,
        text,
        replyToId,
        createdAt: new Date().toISOString(),
        status: created.status,
        visibleToPublic: created.visibleToPublic,
        moderation: mapModeration(created.moderation),
        auditTrail: [],
      };
    },
    submitAppeal: async ({ contentId, appealType, reason, extraContext }) => {
      await submitAppealRequest(contentId, { appealType, reason, extraContext });
      await refresh();
    },
    resolveTask: async (taskId, decision, reason) => {
      await submitReviewDecision(taskId, { finalDecision: decision, reviewReason: reason });
      await refresh();
    },
    findTopic: (topicId) => state.topics.find((item) => item.id === topicId),
    findFloor: (contentId) => {
      for (const topic of state.topics) {
        const floor = topic.floors.find((item) => item.id === contentId);
        if (floor) return { topic, floor };
      }
      return undefined;
    },
    findAppeal: (contentId) => state.appeals.find((item) => item.contentId === contentId),
    loadTimeline: async (contentId) => {
      const events = mapTimeline(await getContentTimeline(contentId));
      setState((current) => ({
        ...current,
        topics: current.topics.map((topic) => ({
          ...topic,
          floors: topic.floors.map((floor) => floor.id === contentId ? { ...floor, auditTrail: events } : floor),
        })),
      }));
      return events;
    },
    refresh,
    resetDemo: () => { void refresh(); },
  }), [community, error, loading, refresh, state]);

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}

export function useDemo() {
  const value = useContext(DemoContext);
  if (!value) throw new Error("useDemo must be used inside DemoProvider");
  return value;
}

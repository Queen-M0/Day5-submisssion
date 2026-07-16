import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { analyzeDemoText, initialDemoState } from "../demo/data";
import type { DemoAppeal, DemoFloor, DemoReviewTask, DemoState, DemoTopic } from "../types";

const STORAGE_KEY = "contextguard.interactive-demo.v3";

interface NewTopicInput { title: string; body: string; category: string; authorId: string }
interface NewFloorInput { topicId: string; text: string; replyToId: string | null; authorId: string }
interface AppealInput { contentId: string; authorId: string; appealType: string; reason: string; extraContext: string }

interface DemoContextValue extends DemoState {
  createTopic: (input: NewTopicInput) => string;
  submitFloor: (input: NewFloorInput) => DemoFloor;
  submitAppeal: (input: AppealInput) => void;
  resolveTask: (taskId: string, decision: "allow" | "maintain_limit" | "need_more_context", reason: string) => void;
  findTopic: (topicId: string) => DemoTopic | undefined;
  findFloor: (contentId: string) => { topic: DemoTopic; floor: DemoFloor } | undefined;
  findAppeal: (contentId: string) => DemoAppeal | undefined;
  resetDemo: () => void;
}

const DemoContext = createContext<DemoContextValue | null>(null);
const cloneInitial = () => JSON.parse(JSON.stringify(initialDemoState)) as DemoState;
const stamp = () => new Date().toISOString();
const uid = (prefix: string) => `${prefix}-${Date.now().toString(36)}`;

export function DemoProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DemoState>(() => {
    try {
      const cached = localStorage.getItem(STORAGE_KEY);
      return cached ? (JSON.parse(cached) as DemoState) : cloneInitial();
    } catch { return cloneInitial(); }
  });

  useEffect(() => { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }, [state]);

  const value = useMemo<DemoContextValue>(() => ({
    ...state,
    createTopic: ({ title, body, category, authorId }) => {
      const topicId = uid("topic");
      const contentId = uid("floor");
      const time = stamp();
      const moderation = analyzeDemoText(contentId, body);
      const allowed = moderation.systemDecision === "publish";
      const firstFloor: DemoFloor = {
        id: contentId, topicId, floorNumber: allowed ? 1 : null, authorId, text: body, replyToId: null,
        createdAt: time, status: allowed ? "published" : moderation.systemDecision === "limit" ? "limited" : "pending_manual_review",
        visibleToPublic: allowed, moderation,
        auditTrail: [
          { id: uid("event"), time, actor: "内容作者", title: "发起新话题", description: "话题与 1 楼进入发布前审核。", tone: "info" },
          { id: uid("event"), time, actor: "AI 初审", title: "上下文分析完成", description: moderation.userVisibleReason, tone: allowed ? "success" : "warning" },
        ],
      };
      const topic: DemoTopic = { id: topicId, title, summary: body.slice(0, 54), category, authorId, createdAt: time, lastActiveAt: time, viewCount: 1, floors: [firstFloor] };
      setState((prev) => ({ ...prev, topics: [topic, ...prev.topics] }));
      return topicId;
    },
    submitFloor: ({ topicId, text, replyToId, authorId }) => {
      const contentId = uid("floor");
      const time = stamp();
      const moderation = analyzeDemoText(contentId, text);
      const allowed = moderation.systemDecision === "publish";
      const topic = state.topics.find((item) => item.id === topicId);
      const nextFloor = Math.max(0, ...(topic?.floors.filter((item) => item.floorNumber).map((item) => item.floorNumber ?? 0) ?? [])) + 1;
      const status = allowed ? "published" : moderation.systemDecision === "limit" ? "limited" : "pending_manual_review";
      const created: DemoFloor = {
        id: contentId, topicId, floorNumber: allowed ? nextFloor : null, authorId, text, replyToId, createdAt: time,
        status, visibleToPublic: allowed, moderation,
        auditTrail: [
          { id: uid("event"), time, actor: "内容作者", title: "提交新楼层", description: replyToId ? "回复指定楼层，等待审核。" : "内容进入发布前审核。", tone: "info" },
          { id: uid("event"), time, actor: "AI 初审", title: "完成说话者、对象与意图分析", description: moderation.userVisibleReason, tone: allowed ? "success" : "warning" },
          { id: uid("event"), time, actor: "证据校验", title: "证据真实性校验通过", description: moderation.evidence.length ? "所有引用片段均可定位到输入。" : "未发现需要绑定的风险证据。", tone: "success" },
        ],
      };
      setState((prev) => {
        const topics = prev.topics.map((item) => item.id === topicId ? { ...item, lastActiveAt: time, floors: [...item.floors, created] } : item);
        const reviewTasks = status === "pending_manual_review"
          ? [...prev.reviewTasks, { id: uid("review"), contentId, appealId: null, source: "ai_escalation", priority: "normal", status: "pending", createdAt: time } as DemoReviewTask]
          : prev.reviewTasks;
        return { ...prev, topics, reviewTasks };
      });
      return created;
    },
    submitAppeal: ({ contentId, authorId, appealType, reason, extraContext }) => {
      const time = stamp();
      const appealId = uid("appeal");
      const appeal: DemoAppeal = {
        id: appealId, contentId, authorId, appealType, reason, extraContext, status: "submitted", createdAt: time,
        counterAnalysis: {
          supportsOriginalDecision: ["原内容包含可能触发限制的表达", "第一次审核依据在原始记录中可以定位"],
          supportsChange: ["用户补充了新的语境说明", appealType === "quote_or_report" ? "引用或反驳关系可能被第一次审核忽略" : "新信息可能改变对真实意图的理解"],
          newEvidenceImpact: "补充信息对原判构成有效挑战，需要审核员结合上下文裁决。",
          remainingUncertainties: ["补充说明的真实性需要人工结合对话记录判断"],
          reviewSuggestion: "建议审核员同时查看支持维持与支持改判的依据。",
        },
      };
      setState((prev) => ({
        topics: prev.topics.map((topic) => ({ ...topic, floors: topic.floors.map((item) => item.id === contentId ? {
          ...item, status: "appeal_submitted", auditTrail: [...item.auditTrail, { id: uid("event"), time, actor: "内容作者", title: "提交申诉与补充上下文", description: reason, tone: "warning" }],
        } : item) })),
        appeals: [...prev.appeals, appeal],
        reviewTasks: [...prev.reviewTasks.filter((item) => item.contentId !== contentId || item.status !== "pending"), { id: uid("review"), contentId, appealId, source: "user_appeal", priority: "high", status: "pending", createdAt: time }],
      }));
    },
    resolveTask: (taskId, decision, reason) => {
      const task = state.reviewTasks.find((item) => item.id === taskId);
      if (!task) return;
      const time = stamp();
      setState((prev) => ({
        topics: prev.topics.map((topic) => {
          const target = topic.floors.find((item) => item.id === task.contentId);
          if (!target) return topic;
          const nextFloor = Math.max(0, ...topic.floors.filter((item) => item.floorNumber).map((item) => item.floorNumber ?? 0)) + 1;
          return { ...topic, lastActiveAt: decision === "allow" ? time : topic.lastActiveAt, floors: topic.floors.map((item) => item.id === task.contentId ? {
            ...item,
            status: decision === "allow" ? (task.appealId ? "appeal_approved" : "published") : decision === "maintain_limit" ? (task.appealId ? "appeal_rejected" : "limited") : "need_more_context",
            visibleToPublic: decision === "allow",
            floorNumber: decision === "allow" ? (item.floorNumber ?? nextFloor) : null,
            auditTrail: [...item.auditTrail, { id: uid("event"), time, actor: "审核员", title: decision === "allow" ? "人工改判：允许公开" : decision === "maintain_limit" ? "人工复核：维持限制" : "要求补充上下文", description: reason, tone: decision === "allow" ? "success" : "danger" }],
          } : item) };
        }),
        appeals: prev.appeals.map((item) => item.id === task.appealId ? { ...item, status: decision === "allow" ? "approved" : decision === "maintain_limit" ? "rejected" : "need_more_context", finalReason: reason } : item),
        reviewTasks: prev.reviewTasks.map((item) => item.id === taskId ? { ...item, status: "resolved", resolvedAt: time, finalDecision: decision, reviewReason: reason } : item),
      }));
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
    resetDemo: () => setState(cloneInitial()),
  }), [state]);

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}

export function useDemo() {
  const value = useContext(DemoContext);
  if (!value) throw new Error("useDemo must be used inside DemoProvider");
  return value;
}

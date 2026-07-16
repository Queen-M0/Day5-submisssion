import type { DemoFloor, DemoModeration, DemoState } from "../types";

const now = "2026-07-16T07:30:00.000Z";

const safe = (contentId: string, quote = ""): DemoModeration => ({
  riskLevel: 0,
  riskScore: quote ? 12 : 4,
  riskTypes: [],
  contextTags: quote ? ["quote", "counter_speech"] : ["safe"],
  intent: quote ? "引用并反对攻击性表达" : "正常讨论与信息交流",
  targetUserIds: [],
  evidence: quote ? [{ contentId, quote, reason: "攻击性片段处于引用语境，作者随后明确表达反对。", verified: true }] : [],
  contextUsed: ["当前内容", "所属话题", "最近 5 楼"],
  uncertainties: [],
  confidence: quote ? 0.91 : 0.97,
  suggestedAction: "allow",
  systemDecision: "publish",
  userVisibleReason: quote ? "已识别为引用并批评不友善表达，内容可以公开。" : "未发现需要限制的风险，内容已公开。",
  reviewerReason: quote ? "引用边界与反对意图明确，证据已定位到当前内容。" : "普通协作讨论，无定向攻击信号。",
});

const harassment: DemoModeration = {
  riskLevel: 2,
  riskScore: 76,
  riskTypes: ["harassment", "implicit_attack"],
  contextTags: ["repeated_targeting", "group_pressure"],
  intent: "持续针对特定用户进行贬损并引导群体围观",
  targetUserIds: ["student_a"],
  evidence: [
    { contentId: "floor-harassment", quote: "大家都看看他平时是什么样", reason: "引导其他成员围观并对特定对象施压。", verified: true },
    { contentId: "floor-103", quote: "请不要继续说我", reason: "目标用户已明确表达停止意愿。", verified: true },
  ],
  contextUsed: ["当前内容", "被回复楼层", "最近 5 楼", "同一作者近期发言"],
  uncertainties: ["无法确认双方线下关系"],
  confidence: 0.84,
  suggestedAction: "manual_review",
  systemDecision: "manual_review",
  userVisibleReason: "内容可能涉及持续针对他人的不友善表达，已进入人工复核。",
  reviewerReason: "请重点核对连续针对、停止请求和群体施压三个上下文信号。",
};

const quoteMisread: DemoModeration = {
  riskLevel: 3,
  riskScore: 88,
  riskTypes: ["insult"],
  contextTags: ["context_missing"],
  intent: "初审认为内容包含针对他人的直接攻击",
  targetUserIds: ["student_b"],
  evidence: [{ contentId: "floor-quote", quote: "你这种人不配待在这里", reason: "包含明显排斥与人身攻击表达。", verified: true }],
  contextUsed: ["当前内容", "最近 2 楼"],
  uncertainties: ["引用来源未被初审正确关联"],
  confidence: 0.78,
  suggestedAction: "limit",
  systemDecision: "limit",
  userVisibleReason: "内容包含可能针对他人的攻击性表达，当前暂不公开。",
  reviewerReason: "用户主张存在引用关系，请结合补充上下文复核说话者与真实意图。",
};

const floor = (value: Partial<DemoFloor> & Pick<DemoFloor, "id" | "topicId" | "authorId" | "text" | "floorNumber">): DemoFloor => ({
  replyToId: null,
  createdAt: now,
  status: "published",
  visibleToPublic: true,
  moderation: safe(value.id),
  auditTrail: [
    { id: `${value.id}-submit`, time: now, actor: "内容作者", title: "提交内容", description: "内容进入发布前审核。", tone: "info" },
    { id: `${value.id}-ai`, time: now, actor: "AI 初审", title: "上下文分析完成", description: "证据校验通过，建议允许公开。", tone: "success" },
    { id: `${value.id}-publish`, time: now, actor: "系统策略", title: "内容已公开", description: `分配为 ${value.floorNumber} 楼。`, tone: "success" },
  ],
  ...value,
});

export const initialDemoState: DemoState = {
  topics: [
    {
      id: "topic-ai-camp",
      title: "团队赛展示怎么分工更高效？",
      summary: "讨论 AI Native 训练营团队赛的产品、开发与答辩分工。",
      category: "训练营协作",
      authorId: "student_a",
      createdAt: "2026-07-16T01:20:00.000Z",
      lastActiveAt: "2026-07-16T07:28:00.000Z",
      viewCount: 128,
      floors: [
        floor({ id: "floor-101", topicId: "topic-ai-camp", floorNumber: 1, authorId: "student_a", text: "我们先把核心闭环跑通，我负责用户端和内容初审。", createdAt: "2026-07-16T01:20:00.000Z" }),
        floor({ id: "floor-102", topicId: "topic-ai-camp", floorNumber: 2, authorId: "student_b", text: "我负责申诉反证和审核员工作台，晚上一起联调。", createdAt: "2026-07-16T01:28:00.000Z", replyToId: "floor-101" }),
        floor({ id: "floor-103", topicId: "topic-ai-camp", floorNumber: 3, authorId: "student_a", text: "关于迟到我已经解释过原因了，请不要继续说我。", createdAt: "2026-07-16T06:55:00.000Z" }),
        floor({
          id: "floor-quote", topicId: "topic-ai-camp", floorNumber: null, authorId: "student_a",
          text: "他说“你这种人不配待在这里”，这种攻击别人的表达很不合适。",
          createdAt: "2026-07-16T07:12:00.000Z", status: "appeal_submitted", visibleToPublic: false, moderation: quoteMisread,
          auditTrail: [
            { id: "quote-submit", time: "2026-07-16T07:12:00.000Z", actor: "张三", title: "提交内容", description: "内容进入发布前 AI 审核。", tone: "info" },
            { id: "quote-limit", time: "2026-07-16T07:12:03.000Z", actor: "系统策略", title: "暂时限制", description: "初审识别到攻击性表达，内容未公开。", tone: "danger" },
            { id: "quote-appeal", time: "2026-07-16T07:18:00.000Z", actor: "张三", title: "提交申诉", description: "补充引用来源，等待审核员复核。", tone: "warning" },
          ],
        }),
        floor({
          id: "floor-harassment", topicId: "topic-ai-camp", floorNumber: null, authorId: "student_b",
          text: "大家都看看他平时是什么样。", replyToId: "floor-103", createdAt: "2026-07-16T07:28:00.000Z",
          status: "pending_manual_review", visibleToPublic: false, moderation: harassment,
          auditTrail: [
            { id: "harass-submit", time: "2026-07-16T07:28:00.000Z", actor: "李四", title: "提交内容", description: "回复 3 楼，进入上下文审核。", tone: "info" },
            { id: "harass-ai", time: "2026-07-16T07:28:04.000Z", actor: "AI 初审", title: "识别连续骚扰信号", description: "发现持续针对和群体施压，证据校验通过。", tone: "warning" },
            { id: "harass-review", time: "2026-07-16T07:28:05.000Z", actor: "系统策略", title: "转人工复核", description: "内容暂不公开，等待审核员判断。", tone: "warning" },
          ],
        }),
      ],
    },
    {
      id: "topic-campus-event",
      title: "明天路演活动需要提前多久到？",
      summary: "确认集合时间、物料检查和演示设备安排。",
      category: "校园活动",
      authorId: "student_c",
      createdAt: "2026-07-15T09:15:00.000Z",
      lastActiveAt: "2026-07-16T03:42:00.000Z",
      viewCount: 86,
      floors: [
        floor({ id: "floor-201", topicId: "topic-campus-event", floorNumber: 1, authorId: "student_c", text: "明天九点正式开始，大家觉得几点集合合适？", createdAt: "2026-07-15T09:15:00.000Z" }),
        floor({ id: "floor-202", topicId: "topic-campus-event", floorNumber: 2, authorId: "student_a", text: "建议八点二十到，预留设备调试和走台时间。", createdAt: "2026-07-16T03:42:00.000Z", replyToId: "floor-201" }),
      ],
    },
    {
      id: "topic-lost-found",
      title: "教学楼三层捡到一张校园卡",
      summary: "校园卡已交到一楼服务台，请失主携带证件领取。",
      category: "失物招领",
      authorId: "student_b",
      createdAt: "2026-07-14T11:05:00.000Z",
      lastActiveAt: "2026-07-15T02:10:00.000Z",
      viewCount: 43,
      floors: [
        floor({ id: "floor-301", topicId: "topic-lost-found", floorNumber: 1, authorId: "student_b", text: "卡片姓王，已经交给教学楼一楼服务台。", createdAt: "2026-07-14T11:05:00.000Z" }),
        floor({ id: "floor-302", topicId: "topic-lost-found", floorNumber: 2, authorId: "student_c", text: "谢谢，我转发到班级群里问一下。", createdAt: "2026-07-15T02:10:00.000Z" }),
      ],
    },
  ],
  appeals: [
    {
      id: "appeal-quote", contentId: "floor-quote", authorId: "student_a", appealType: "quote_or_report",
      reason: "前半句是引用 2 楼的原话，我是在批评这种表达，并不是攻击李四。",
      extraContext: "被引用内容来自讨论现场的原话；我的后半句明确写了“这种攻击别人的表达很不合适”。",
      status: "submitted", createdAt: "2026-07-16T07:18:00.000Z",
      counterAnalysis: {
        supportsOriginalDecision: ["当前内容确实包含明显排斥性表达", "初审上下文中未成功定位引用来源"],
        supportsChange: ["攻击性片段使用引号明确标记", "作者后半句明确反对攻击行为", "申诉补充了引用来源与说话者关系"],
        newEvidenceImpact: "新增信息足以改变对说话者和真实意图的判断。",
        remainingUncertainties: ["引用原话是否完整仍需审核员确认"],
        reviewSuggestion: "建议结合引用关系改判为允许发布。",
      },
    },
  ],
  reviewTasks: [
    { id: "review-quote", contentId: "floor-quote", appealId: "appeal-quote", source: "user_appeal", priority: "high", status: "pending", createdAt: "2026-07-16T07:18:02.000Z" },
    { id: "review-harassment", contentId: "floor-harassment", appealId: null, source: "ai_escalation", priority: "normal", status: "pending", createdAt: "2026-07-16T07:28:05.000Z" },
  ],
};

export function analyzeDemoText(id: string, text: string): DemoModeration {
  if (text.includes("大家都看看") || text.includes("大聪明")) return { ...harassment, evidence: [{ contentId: id, quote: text, reason: "结合前文存在定向贬损或群体施压。", verified: true }] };
  if (text.includes("放学等着") || text.includes("让你后悔")) return {
    ...harassment, riskLevel: 3, riskScore: 94, riskTypes: ["threat"], contextTags: ["direct_threat"],
    intent: "对特定对象发出明确威胁", suggestedAction: "limit", systemDecision: "limit", confidence: 0.96,
    evidence: [{ contentId: id, quote: text, reason: "包含明确的报复或伤害暗示。", verified: true }],
    userVisibleReason: "内容包含明确威胁信号，当前暂不公开。",
  };
  if ((text.includes("他说") || text.includes("楼上说")) && (text.includes("不合适") || text.includes("不应该"))) return safe(id, text.match(/“([^”]+)”/)?.[1] ?? text);
  return safe(id);
}

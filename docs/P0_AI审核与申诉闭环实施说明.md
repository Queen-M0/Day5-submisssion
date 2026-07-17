# P0 AI 审核与申诉闭环实施说明

最后更新：2026-07-16

## 1. 实施目标

本轮工作以 PRD F1～F17 和 SPEC S-AC-01～S-AC-12 为验收基线，不只接一个模型调用，而是完成以下闭环：

```text
用户提交内容
→ 上下文聚合
→ 初审 Agent
→ Schema 与证据真实性校验
→ 允许 / 限制 / 人工复核
→ 用户申诉并补充上下文
→ 申诉反证 Agent
→ 人工维持 / 改判 / 要求补充
→ 改判后恢复为最新公开楼层
→ 全过程审计留痕
```

最终边界保持为：AI 提供语义分析和建议，确定性代码负责校验、分流和状态机，人工审核员负责争议内容与申诉的最终裁决。

## 2. 开发前审计结论

开发前已经存在：React 页面骨架、FastAPI 路由、社区和话题、线性楼层、Mock 初审、基础申诉表、人工复核接口、时间线和两次 Alembic 迁移。

主要缺口：

1. `dependencies.py` 固定使用 Mock Provider，没有真实 MiMo 适配层；
2. 初审 Prompt 没有独立版本文件；
3. 证据只在当前内容中查找，无法验证回复楼层和历史上下文证据；
4. 申诉提交后不运行反证 Agent，`counter_analysis` 始终为空；
5. 反证调用没有独立运行记录，无法保存 provider、model、prompt 和失败原因；
6. 审核员要求补充后，用户没有继续补充并重新分析的接口；
7. Seed 中的预置申诉也是空反证数据；
8. 缺少 MiMo 协议、编造证据和二次反证回归测试。

## 3. 两个 Agent 的职责

### 3.1 初审 Agent（Moderation Analyzer）

输入：当前内容、作者、话题、被回复楼层、最近 5 楼、作者近期公开内容、目标用户近期相关内容。

输出：风险等级与分数、风险类型、表达意图、目标用户、引用/举报语境、隐晦攻击、连续骚扰、逐字证据、上下文推理、用户可见理由、审核员理由、不确定点和建议动作。

只允许三个业务建议：

- `publish`：安全或明确安全引用；
- `limit`：高风险且证据充分；
- `manual_review`：中风险、上下文不足或关系不清。

### 3.2 申诉反证 Agent（Appeal Critic）

输入：第一次 AI 分析、第一次系统决定、原始上下文、申诉类型、申诉理由和补充上下文。

输出：支持原判的依据、支持改判的依据、新信息影响、剩余不确定点、给审核员的建议和可定位证据。

反证 Agent 不直接修改内容状态为公开或驳回。它只能给 `allow`、`maintain_limit` 或 `need_more_context` 建议，人工审核员提交理由后才产生最终决定。

## 4. MiMo Provider

`backend/app/providers/mimo_provider.py` 通过 OpenAI-compatible `POST /chat/completions` 接入 MiMo。以下配置均可通过环境变量覆盖：

| 配置 | 用途 |
| --- | --- |
| `AI_PROVIDER` | `auto`、`mimo` 或 `mock` |
| `MIMO_API_KEY` | MiMo 密钥，不进入 Git |
| `MIMO_BASE_URL` | 接口根地址 |
| `MIMO_MODEL` | 控制台提供的模型 ID |
| `MIMO_TIMEOUT_SECONDS` | 请求超时 |
| `MIMO_MAX_TOKENS` | 最大输出 Token |
| `MIMO_TEMPERATURE` | 默认 0.1，降低随机性 |
| `MIMO_JSON_MODE` | 是否发送 JSON Object 响应格式 |

Provider 对 Markdown 代码围栏做兼容清理，但最终内容必须能解析为单个 JSON 对象，并通过严格 Pydantic Schema。额外字段、缺失字段、非法枚举、越界风险分数都会触发异常，由工作流安全转人工。

Prompt 分别保存在：

- `backend/app/prompts/moderation-v1.md`
- `backend/app/prompts/appeal-critic-v1.md`

Prompt 版本和模型版本随每次结果入库，便于答辩复现与后续回归。

## 5. 证据真实性校验

模型证据必须同时满足：

1. `contentId` 在本次输入源中存在；
2. `text` 是该输入源中的连续逐字片段；
3. 高风险 `limit` 至少有一条真实证据；
4. 支持申诉改判的反证至少有一条真实证据；
5. 申诉理由使用虚拟来源 ID `appeal-reason`；
6. 用户补充上下文使用虚拟来源 ID `appeal-extra-context`。

可验证输入源包括当前内容、被回复楼层、最近楼层、作者历史和目标用户历史。任何编造片段或错误 ID 都会设置 `evidence_valid=false` 并覆盖模型建议，进入人工复核。

## 6. 数据库设计

本项目当前有 9 张业务表，加 1 张 Alembic 版本表：

| 表 | 核心职责 | 本轮关键字段/关系 |
| --- | --- | --- |
| `users` | 预置普通用户与审核员 | `role` 区分权限 |
| `scenes` | 固定社区 | 一个社区关联多个话题 |
| `topics` | 话题元数据 | 状态、公开性、分类、最后活跃时间 |
| `contents` | 话题 1 楼和后续楼层 | `topic_id`、`floor_number`、`parent_id`、`target_user_id`、状态、公开性 |
| `moderation_records` | 每次初审完整记录 | provider、prompt/model/rule 版本、AI 建议、系统决定、证据、证据有效性、原始结果、失败原因 |
| `appeals` | 用户申诉主体 | 理由、补充上下文、最新反证结果、分析时间、当前状态 |
| `appeal_analysis_records` | 每一次反证 Agent 运行 | provider、prompt/model 版本、结构化结果、证据有效性、失败原因、时间 |
| `manual_reviews` | 人工终审 | 原决定、最终决定、最终风险、审核理由、纠正类型 |
| `audit_logs` | 全流程时间线 | actor、action、entity、detail、时间 |

新增迁移：`b62d91f47e30_add_appeal_analysis_records.py`。

之所以新增 `appeal_analysis_records`，而不是只覆盖 `appeals.counter_analysis`，是为了保存“首次反证 → 要求补充 → 二次反证”的每次运行证据。`appeals.counter_analysis` 保留最新快照用于页面快速读取。

## 7. 状态机与事务

### 7.1 初审

```text
pending_ai_review
├─ publish → published（事务内分配最新楼层号）
├─ limit → limited（不公开、不占楼层号）
└─ manual_review / AI 异常 → pending_manual_review
```

### 7.2 申诉

```text
limited / pending_manual_review
→ appeal_submitted
→ appeal_reviewing
├─ 人工 allow → appeal_approved + 恢复为最新公开楼层
├─ 人工 maintain_limit → appeal_rejected
└─ 人工 need_more_context → need_more_context
   → 用户 supplement
   → appeal_submitted
   → 第二次 appeal_reviewing
```

公开楼层号只在 `publish_content` 中分配。函数先对话题行 `SELECT ... FOR UPDATE`，再查询最大楼层号并加一，数据库唯一约束 `uq_contents_topic_floor` 防止同话题重复楼层。

## 8. API 补齐

| API | 用途 |
| --- | --- |
| `POST /api/topics/{topicId}/contents` | 发布并执行初审 |
| `GET /api/contents/{contentId}/moderation` | 查看初审、证据和失败信息 |
| `POST /api/contents/{contentId}/appeals` | 创建申诉并立即执行反证 Agent |
| `POST /api/appeals/{appealId}/supplement` | 追加上下文并再次执行反证 Agent |
| `GET /api/me/appeals` | 查看最新反证、运行元数据和人工结果 |
| `GET /api/reviewer/tasks` | AI 转人工与用户申诉队列 |
| `GET /api/reviewer/tasks/{taskId}` | 原文、上下文、初审、证据、反证和时间线 |
| `POST /api/reviewer/tasks/{taskId}/decision` | 人工最终裁决，理由必填 |
| `GET /api/contents/{contentId}/timeline` | 全流程审计事件 |
| `GET /api/health` | 当前 Provider 和模型，不返回密钥 |

## 9. 失败降级

| 失败 | 系统行为 |
| --- | --- |
| MiMo 未配置密钥且强制 `mimo` | 调用失败并转人工 |
| 请求超时或 HTTP 错误 | 保存失败原因并转人工 |
| 空响应或缺少 choices | 保存失败原因并转人工 |
| 非法 JSON / Markdown 外文本 | 解析失败并转人工 |
| Schema 字段缺失、额外或越界 | 校验失败并转人工 |
| 初审证据编造 | `evidence_valid=false`，覆盖为人工复核 |
| 反证证据编造 | 建议改为 `need_more_context`，人工直接核对 |
| 申诉反证 Agent 失败 | 仍创建人工任务，不阻断申诉权 |

## 10. 前端闭环

前端已使用真实 API，不再依赖 `demo/data.ts` 写业务状态：

- 发布结果展示 AI 建议、系统分流、置信度、上下文与已验证证据；
- “我的发布”展示受限原因并允许申诉；
- “我的申诉”展示反证摘要、Provider、模型、Prompt、证据状态和人工结果；
- `need_more_context` 时出现补充表单，提交后触发二次反证；
- 审核工作台并排展示原始上下文、初审证据、申诉正反依据和人工裁决；
- 反证 Agent 失败时明确显示已降级，不伪造分析；
- 人工理由少于约定长度无法提交。

## 11. 验证记录

本轮已执行：

```text
后端 compileall：通过
后端 pytest：14 passed
前端 TypeScript + Vite production build：通过
SQLite 从空库 upgrade head：通过
SQLite alembic check：No new upgrade operations detected
MySQL upgrade head：通过，当前 b62d91f47e30
MySQL alembic check：No new upgrade operations detected
MySQL Seed：Demo seed is ready
MySQL API 冒烟：health、我的申诉、审核详情、反证记录读取通过
git diff --check：通过
```

测试覆盖：正常发布、安全引用、隐晦攻击、明确威胁、话题可见性、权限、模型超时、编造证据、MiMo JSON 协议、申诉反证、人工改判、要求补充、二次反证和时间线。

当前开发机未提供真实 `MIMO_API_KEY`，因此没有消耗真实 MiMo 额度做在线调用；真实 Provider 的请求与解析通过 `httpx.MockTransport` 验证。配置密钥后，`AI_PROVIDER=auto` 会自动启用 MiMo，可通过 `/api/health` 确认。

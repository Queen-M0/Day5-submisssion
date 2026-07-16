# AI 文字内容审核与申诉复核系统开发指南

> 题目：AI 文字内容审核与申诉复核系统  
> 适用场景：社区广场、论坛话题、群组式文字交流等只处理文本内容的发布、审核、限制、申诉和人工复核闭环。

## 1. 任务理解

本题的核心不是做一个简单的“敏感词过滤器”，而是做一个结合上下文、说话人、对象、意图和历史行为的 AI Native 内容审核系统。

传统敏感词表只能发现显性的违规词，但这个题目特别强调两个难点：

1. 不能误判引用、转述、反讽、讨论规则、玩笑等非攻击性内容。
2. 不能漏判没有敏感词但通过隐喻、缩写、外号、连续回复、上下文暗示形成攻击、辱骂、骚扰、歧视、诈骗或威胁的内容。

因此，系统需要围绕“内容提交 -> 上下文分析 -> 风险判断 -> 发布或限制 -> 用户申诉 -> 审核人员复核 -> 结果保存”建立完整闭环。

## 2. 题目关键信息提炼

### 2.1 场景

社区广场中的话题讨论、楼层回复或群组式文字交流，希望使用 AI 识别以下风险：

- 辱骂
- 骚扰
- 歧视
- 诈骗
- 威胁
- 持续性攻击
- 隐晦称呼或缩写攻击
- 借引用、转述、反讽、玩笑等形式造成的语义误判

### 2.2 任务流程

题目图片中的闭环可以拆成 6 个关键步骤：

1. 用户提交内容。
2. AI 结合上下文分析风险。
3. 系统给出正常发布、限制发布或人工复核建议。
4. 用户查看处理结果并发起申诉。
5. 审核人员查看 AI 理由、上下文和申诉理由后复核。
6. 系统保存最终记录，用于审计、复盘和后续优化。

### 2.3 两个前端角色

系统建议分为两个前端：

- 普通用户端：发布内容、查看审核结果、查看限制理由、提交申诉。
- 审核人员端：查看待复核内容、查看上下文、查看 AI 分析理由、改判或维持原判、保存复核记录。

### 2.4 服务端职责

服务端负责：

- 内容接收
- 上下文聚合
- AI 风险分析
- 风险分级
- 内容状态流转
- 申诉管理
- 人工复核
- 审计记录
- 测试样例和演示数据管理

## 3. 推荐产品形态

虽然题目允许自由定义数据形态，但本项目固定选择“社区广场 + 话题楼层”的形态，这样既能保留公开讨论的真实语境，也更容易展示上下文判断能力。

推荐设定：

- 系统名称：ContextGuard AI 内容审核与申诉复核系统
- 使用场景：社区广场，包含公开话题、线性楼层和指定楼层回复。
- 内容类型：纯文字消息。
- 主要对象：社区普通用户、社区审核人员。
- 审核目标：在尽量少误杀正常表达的前提下，识别明显和隐晦的攻击、骚扰、歧视、诈骗、威胁内容。

### 3.1 为什么推荐这个形态

社区广场和话题楼层非常适合体现题目要求：

- 广场话题天然有公开讨论和连续上下文。
- 楼层回复天然有引用、回复和被回复对象。
- 社区场景容易出现外号、阴阳怪气、连续围攻等上下文攻击。
- 审核人员可以基于上下文判断 AI 是否误判。
- 演示时可以清晰展示“同一句话在不同上下文下有不同审核结果”。

## 4. 系统目标

### 4.1 必做目标

- 用户可以发布文本内容。
- 系统在发布前调用审核逻辑。
- AI 可以结合上下文判断风险。
- 审核结果至少包含：通过、限制、人工复核。
- 被限制或进入复核的内容需要给出可解释理由。
- 用户可以对被限制结果发起申诉。
- 审核人员可以查看申诉、上下文和 AI 理由。
- 审核人员可以维持或改判结果。
- 所有审核和复核结果需要保存。

### 4.2 加分目标

- 支持风险类型多标签识别。
- 支持风险分数和置信度。
- 支持敏感片段定位。
- 支持上下文证据提取。
- 支持误判类型标注。
- 支持规则引擎 + AI 模型混合审核。
- 支持审核策略配置。
- 支持样例库和回归测试。
- 支持数据看板，例如误判率、申诉成功率、高风险类别分布。

## 5. 核心设计原则

### 5.1 审核依据不是“词”，而是“语境中的行为”

系统不应该只问：“有没有敏感词？”

更应该问：

- 这句话是在骂人，还是在引用别人说过的话？
- 说话人是不是在攻击某个具体对象？
- 这句话是否和前文构成连续骚扰？
- 这句话是否用了外号、缩写、谐音、表情或隐喻规避检测？
- 这句话是否可能造成诈骗、诱导转账或威胁？
- 内容是否有教育、反驳、求助、举报、讨论规则等正当语境？

### 5.2 审核结果必须可解释

AI 不能只输出“违规”。它必须输出结构化理由：

- 风险类型
- 风险等级
- 命中的证据
- 上下文依据
- 是否存在引用或转述
- 推荐处理动作
- 给用户展示的温和提示
- 给审核人员看的详细分析

### 5.3 申诉不能只是“再调用同一个 AI”

题目特别强调：申诉不能只让同一个 AI 再重复一次错误。

因此申诉流程必须包含：

- 用户补充理由。
- 系统展示原始上下文。
- 审核人员进行人工复核。
- 审核人员可以选择维持、改判、部分放行、要求用户修改后重发。
- 系统记录复核理由。

## 6. 用户故事

### 6.1 普通用户

作为普通用户，我希望：

- 能正常发布社区广场话题或楼层评论。
- 如果内容被限制，我能知道大致原因。
- 如果我只是引用、解释、反驳或举报违规内容，我可以申诉。
- 我可以查看申诉进度和结果。
- 如果审核人员改判，我的内容可以恢复发布。

### 6.2 审核人员

作为审核人员，我希望：

- 能看到所有待复核和待申诉内容。
- 能看到用户发的原文、前后文、回复关系和历史互动。
- 能看到 AI 给出的风险类型、证据和推荐处理。
- 能快速做出维持、改判或要求修改的决定。
- 能保存复核理由，便于后续追责和模型优化。

### 6.3 后置管理能力

以下能力不进入本次双人开发主线，可以作为后续扩展：

- 能配置审核策略。
- 能维护敏感词、风险类别和处置规则。
- 能查看审核统计。
- 能导出审核记录。
- 能用样例集测试规则和 AI 表现。

## 7. 角色与权限

| 角色 | 权限 |
| --- | --- |
| 普通用户 | 发布内容、查看自己的审核结果、提交申诉、查看申诉结果 |
| 审核人员 | 查看待复核内容、查看申诉、执行复核、保存复核理由 |
| 系统服务 | 调用 AI、执行规则、更新状态、记录审计日志 |

## 8. 内容数据形态设计

建议支持两类内容：

### 8.1 IM 群聊消息

适合展示连续上下文和群体骚扰。

示例：

```json
{
  "contentType": "chat_message",
  "sceneId": "class_group_001",
  "senderId": "user_001",
  "text": "别装了，全班都知道你是什么水平",
  "replyToMessageId": "msg_1001",
  "createdAt": "2026-07-16T10:00:00+08:00"
}
```

### 8.2 论坛帖子或评论

适合展示楼层、引用、转述和回复关系。

示例：

```json
{
  "contentType": "forum_reply",
  "threadId": "thread_001",
  "parentId": "reply_010",
  "senderId": "user_002",
  "text": "我不是在骂他，我是在引用楼上那句“你就是废物”来说明这种话不合适。",
  "createdAt": "2026-07-16T10:05:00+08:00"
}
```

## 9. 风险分类体系

建议至少支持以下风险类型：

| 风险类型 | 说明 | 示例 |
| --- | --- | --- |
| insult | 辱骂、人身攻击 | 直接骂人、贬低人格 |
| harassment | 骚扰、持续性攻击 | 多次点名嘲讽、围攻 |
| discrimination | 歧视 | 针对性别、地域、身体、成绩等群体攻击 |
| threat | 威胁 | 威胁线下报复、恐吓 |
| fraud | 诈骗 | 诱导转账、虚假链接、冒充身份 |
| privacy | 隐私泄露 | 曝光手机号、住址、身份证等 |
| self_harm | 自伤风险 | 表达自残或轻生意图 |
| sexual | 性骚扰或低俗内容 | 对他人进行性化羞辱 |
| spam | 广告或刷屏 | 重复发送无意义内容或广告 |
| safe_context | 安全语境 | 引用、反驳、科普、举报、规则讨论 |

注意：`safe_context` 不是风险，而是帮助模型避免误判的重要标签。

## 10. 风险等级设计

建议使用 4 级：

| 等级 | 名称 | 说明 | 默认动作 |
| --- | --- | --- | --- |
| 0 | safe | 安全 | 直接发布 |
| 1 | low | 低风险 | 发布但记录，或提示用户修改 |
| 2 | medium | 中风险 | 暂不公开，进入人工复核 |
| 3 | high | 高风险 | 拦截，允许申诉 |

也可以用分数表达：

- 0 到 30：通过
- 31 到 60：提示或人工复核
- 61 到 80：限制发布
- 81 到 100：强限制并标记高优先级

推荐同时保存等级和分数，便于展示和统计。

## 11. 审核状态机

内容从提交到最终处理建议使用以下状态：

| 状态 | 含义 |
| --- | --- |
| pending_ai_review | 等待 AI 审核 |
| published | 已发布 |
| limited | 已限制，不公开或仅自己可见 |
| pending_manual_review | 等待人工复核 |
| appealable | 可申诉 |
| appeal_submitted | 用户已申诉 |
| appeal_reviewing | 申诉复核中 |
| appeal_approved | 申诉通过，内容恢复或允许重发 |
| appeal_rejected | 申诉驳回，维持限制 |
| withdrawn | 用户撤回 |

推荐状态流转：

```text
用户提交
  -> pending_ai_review
  -> AI 判断
      -> published
      -> limited / appealable
      -> pending_manual_review

limited / appealable
  -> 用户申诉
  -> appeal_submitted
  -> appeal_reviewing
  -> appeal_approved / appeal_rejected
```

## 12. 总体架构

推荐采用前后端分离架构：

```text
普通用户端
  - 发消息
  - 看审核结果
  - 提交申诉

审核人员端
  - 申诉列表
  - 待复核列表
  - 上下文查看
  - 复核处理

服务端 API
  - 内容管理
  - 上下文聚合
  - 审核任务
  - 申诉复核
  - 审计日志

审核引擎
  - 规则预检
  - 上下文构建
  - AI 审核
  - 风险合并
  - 结果解释

数据库
  - 用户
  - 场景
  - 内容
  - 审核记录
  - 申诉记录
  - 人工复核记录
  - 策略配置
```

## 13. 推荐技术栈

可以按团队熟悉程度选择，下面给出一个比赛/课程项目友好的组合。本项目建议固定采用 React + FastAPI + MySQL，降低协作沟通成本。

### 13.1 前端

- React
- TypeScript
- Vite
- Ant Design
- React Router
- Axios / Fetch

### 13.2 后端

- Python + FastAPI
- Pydantic，用于请求参数和 AI 结构化输出校验
- SQLAlchemy，用于数据库访问
- PyMySQL，用于连接 MySQL
- Alembic 可选，用于数据库迁移
- Redis 暂不作为 MVP 必需项

### 13.3 AI 调用

- Mock AI Provider，优先保证演示稳定
- 可替换的大语言模型 Provider
- 规则引擎作为兜底
- 审核提示词模板版本化保存
- 受控 ReAct-like 工作流：AI 负责分析，后端固定编排证据校验、规则分流和时间线记录

### 13.4 推荐最小可行技术栈

如果时间紧，建议：

- 前端：React + TypeScript + Vite + Ant Design
- 后端：FastAPI + Pydantic + SQLAlchemy
- 数据库：MySQL 8.x
- AI：一个可替换的 `ModerationProvider` 接口
- 演示数据：JSON seed 文件

MySQL 建库建议：

```sql
CREATE DATABASE ai_moderation
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

示例连接串：

```text
mysql+pymysql://user:password@localhost:3306/ai_moderation?charset=utf8mb4
```

## 14. 后端模块划分

### 14.1 Auth 模块

职责：

- 用户登录
- 角色识别
- 权限校验

最小实现可以使用模拟登录：

- `user_a`
- `user_b`
- `reviewer_1`

### 14.2 Content 模块

职责：

- 创建消息或评论
- 查询内容列表
- 查询内容详情
- 更新内容状态
- 恢复内容

### 14.3 Context 模块

职责：

- 获取目标内容的上下文
- 获取被回复内容
- 获取同一讨论串前后若干条内容
- 获取同一对话中同一对象的连续攻击记录
- 标记引用、转述和回复关系

### 14.4 Moderation 模块

职责：

- 创建审核任务
- 调用规则引擎
- 构建 AI 输入
- 调用 AI 模型
- 解析 AI 输出
- 合并风险结果
- 保存审核记录
- 决定内容状态

### 14.5 Appeal 模块

职责：

- 用户提交申诉
- 查询申诉详情
- 查询申诉进度
- 审核人员处理申诉
- 保存复核结果

### 14.6 AuditLog 模块

职责：

- 记录每一次 AI 审核
- 记录每一次人工复核
- 记录状态变更
- 记录申诉过程
- 支持后续审计和导出

### 14.7 Policy 模块

职责：

- 风险类别配置
- 敏感词或短语配置
- 风险等级阈值配置
- 自动通过/拦截/人工复核策略配置
- 提示词版本管理

## 15. 核心数据库表设计

以下字段可根据实际技术栈调整。

### 15.1 users

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 用户 ID |
| username | string | 用户名 |
| display_name | string | 展示名 |
| role | string | user / reviewer |
| created_at | datetime | 创建时间 |

### 15.2 scenes

表示社区广场、话题、群组式文字交流空间。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 场景 ID |
| type | string | chat_group / forum_thread |
| title | string | 场景标题 |
| description | string | 描述 |
| created_at | datetime | 创建时间 |

### 15.3 contents

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 内容 ID |
| scene_id | string | 所属场景 |
| content_type | string | chat_message / forum_reply |
| author_id | string | 作者 |
| parent_id | string | 回复对象，可为空 |
| text | text | 原文 |
| normalized_text | text | 归一化文本 |
| status | string | 当前状态 |
| visible_to_public | boolean | 是否公开可见 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 15.4 moderation_records

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 审核记录 ID |
| content_id | string | 内容 ID |
| provider | string | AI 提供方或规则引擎 |
| prompt_version | string | 提示词版本 |
| risk_level | int | 0-3 |
| risk_score | int | 0-100 |
| risk_types | json | 风险类型数组 |
| decision | string | publish / limit / manual_review |
| confidence | float | 置信度 |
| evidence | json | 证据片段 |
| context_summary | text | 上下文摘要 |
| user_visible_reason | text | 给用户看的理由 |
| reviewer_reason | text | 给审核人员看的详细理由 |
| raw_ai_response | json | AI 原始响应 |
| created_at | datetime | 创建时间 |

### 15.5 appeals

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 申诉 ID |
| content_id | string | 内容 ID |
| user_id | string | 申诉人 |
| reason | text | 用户申诉理由 |
| status | string | submitted / reviewing / approved / rejected |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 15.6 manual_reviews

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 复核 ID |
| appeal_id | string | 申诉 ID，可为空 |
| content_id | string | 内容 ID |
| reviewer_id | string | 审核人员 |
| original_decision | string | 原 AI 决策 |
| final_decision | string | 最终决策 |
| final_risk_level | int | 最终风险等级 |
| review_reason | text | 人工复核理由 |
| correction_type | string | correct / false_positive / false_negative / policy_unclear |
| created_at | datetime | 创建时间 |

### 15.7 policy_rules

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 规则 ID |
| name | string | 规则名 |
| type | string | keyword / regex / semantic / threshold |
| config | json | 规则配置 |
| action | string | warn / manual_review / limit |
| enabled | boolean | 是否启用 |
| created_at | datetime | 创建时间 |

## 16. 内容审核流程详解

### 16.1 用户提交内容

用户在群聊或帖子下输入文本，点击发送。

前端调用：

```http
POST /api/contents
```

请求示例：

```json
{
  "sceneId": "class_group_001",
  "contentType": "chat_message",
  "parentId": "msg_1001",
  "text": "你别再装了，大家都知道你是什么货色"
}
```

后端处理：

1. 保存内容，状态为 `pending_ai_review`。
2. 归一化文本。
3. 聚合上下文。
4. 创建审核任务。
5. 调用审核引擎。
6. 根据结果更新内容状态。
7. 返回处理结果。

### 16.2 文本归一化

归一化用于提高规则和 AI 的稳定性。

建议处理：

- 全角转半角
- 大小写统一
- 去除异常空白
- 合并重复标点
- 识别谐音、缩写、拼音、数字替代
- 保留原文，不要覆盖原始内容

示例：

```text
原文：n  b  a，别  装  了！！！
归一化：n b a，别装了！
```

注意：归一化结果只能作为辅助，最终解释仍要基于原文和上下文。

### 16.3 上下文构建

这是本题最重要的部分之一。

上下文至少应包含：

- 当前内容原文。
- 当前内容作者。
- 被回复内容。
- 同一线程或群聊最近 N 条消息。
- 当前作者最近 N 条消息。
- 被提及对象最近相关消息。
- 是否包含引用符号、引号、冒号、转述词。
- 是否存在连续攻击同一对象的模式。

推荐上下文窗口：

- 群聊：当前消息前 10 条，后续复核时可看前后 20 条。
- 论坛：当前楼层的父回复、同级前后 5 条、主帖摘要。
- 历史行为：同一作者 24 小时内对同一对象的相关回复。

### 16.4 引用和转述识别

为了避免误判，需要识别内容是否在引用他人。

常见引用信号：

- 使用引号：他说“你真差劲”。
- 明确转述：楼上说的那句“……”不合适。
- 举报语境：有人骂我“……”，请审核员处理。
- 反驳语境：不要说“……”，这是人身攻击。
- 规则讨论：像“……”这种话应该被禁。

但注意：引用不是绝对安全。以下引用仍可能违规：

- 借引用再次传播严重侮辱。
- 表面引用，实际继续攻击。
- 引用后附加赞同或煽动。
- 大量重复他人辱骂内容。

所以模型需要输出 `is_quote_or_report` 和 `quote_context_safe` 两个判断。

## 17. 审核引擎设计

推荐采用“规则预检 + AI 语义判断 + 策略合并”的混合方案。

```text
输入内容
  -> 文本归一化
  -> 规则预检
  -> 上下文聚合
  -> AI 语义审核
  -> 风险合并
  -> 策略决策
  -> 保存记录
```

### 17.1 规则预检

规则预检适合识别：

- 明确敏感词
- 电话、身份证、银行卡等隐私格式
- URL 或二维码文本
- 大量重复刷屏
- 极端辱骂词

规则预检不能直接代替最终审核，尤其不能因为命中词就直接判违规。

规则输出示例：

```json
{
  "matched": true,
  "matches": [
    {
      "type": "keyword",
      "value": "废物",
      "position": [12, 14],
      "riskHint": "insult"
    }
  ],
  "suggestedRiskLevel": 2
}
```

### 17.2 AI 语义审核

AI 负责判断：

- 是否有攻击对象。
- 是否存在明确恶意。
- 是否是引用、反驳、举报或规则讨论。
- 是否有隐晦攻击。
- 是否和上下文构成持续骚扰。
- 是否需要人工复核。

### 17.3 策略合并

最终决策不应该完全依赖模型一句话。

建议合并以下信息：

- 规则命中结果。
- AI 风险分数。
- AI 置信度。
- 内容作者历史违规情况。
- 是否出现明确受害对象。
- 是否涉及隐私、威胁、诈骗等高风险类别。
- 是否存在安全语境。

示例策略：

```text
如果 risk_level = 0：
  发布

如果 risk_level = 1：
  发布，但记录；可前端提示“请注意表达方式”

如果 risk_level = 2：
  暂不公开，进入人工复核

如果 risk_level = 3：
  限制发布，允许用户申诉

如果 AI 置信度低于 0.65：
  不直接限制，进入人工复核

如果存在隐私泄露、诈骗、威胁：
  优先限制或人工复核
```

## 18. AI 审核提示词设计

建议使用结构化输出，方便后端解析。

### 18.1 System Prompt

```text
你是一个中文社区内容审核助手。你的任务是结合当前文本、回复关系、上下文和历史互动，判断文本是否存在辱骂、骚扰、歧视、威胁、诈骗、隐私泄露或其他社区风险。

不要只根据敏感词判断。你必须区分以下情况：
1. 直接攻击、隐晦攻击、缩写攻击、外号攻击、连续骚扰。
2. 引用、转述、反驳、举报、规则讨论、教学说明等安全语境。
3. 玩笑和反讽需要结合双方关系、上下文和表达强度判断。

你必须输出严格 JSON，不要输出 Markdown。
```

### 18.2 User Prompt 模板

```text
请审核下面这条用户内容。

【当前内容】
content_id: {{content_id}}
作者: {{author_display_name}} / {{author_id}}
文本: {{text}}

【回复关系】
parent_content_id: {{parent_id}}
被回复内容: {{parent_text}}
被回复作者: {{parent_author}}

【最近上下文】
{{context_messages}}

【作者近期相关行为】
{{author_recent_messages}}

【规则预检结果】
{{rule_check_result}}

请判断：
1. 当前文本是否违规。
2. 如果违规，风险类型和风险等级是什么。
3. 是否存在引用、转述、反驳、举报或规则讨论等安全语境。
4. 是否存在隐晦攻击、缩写攻击、外号攻击或连续骚扰。
5. 推荐系统如何处理：publish、warn、manual_review、limit。
6. 给普通用户展示的简短理由。
7. 给审核人员查看的详细依据。

请返回严格 JSON，字段如下：

{
  "is_violation": boolean,
  "risk_level": 0 | 1 | 2 | 3,
  "risk_score": number,
  "risk_types": string[],
  "confidence": number,
  "decision": "publish" | "warn" | "manual_review" | "limit",
  "target_users": string[],
  "is_quote_or_report": boolean,
  "quote_context_safe": boolean,
  "has_implicit_attack": boolean,
  "has_continuous_harassment": boolean,
  "evidence": [
    {
      "text": string,
      "reason": string,
      "risk_type": string
    }
  ],
  "context_reasoning": string,
  "user_visible_reason": string,
  "reviewer_reason": string,
  "suggested_revision": string
}
```

### 18.3 输出示例：安全引用

输入：

```text
我不是在骂他，我是在引用楼上那句“你就是废物”来说明这种话不合适。
```

期望输出：

```json
{
  "is_violation": false,
  "risk_level": 0,
  "risk_score": 12,
  "risk_types": ["safe_context"],
  "confidence": 0.86,
  "decision": "publish",
  "target_users": [],
  "is_quote_or_report": true,
  "quote_context_safe": true,
  "has_implicit_attack": false,
  "has_continuous_harassment": false,
  "evidence": [
    {
      "text": "我是在引用楼上那句",
      "reason": "作者明确说明是在引用并批评该表达",
      "risk_type": "safe_context"
    }
  ],
  "context_reasoning": "文本包含侮辱性词汇，但语境是反对该表达，不是在攻击他人。",
  "user_visible_reason": "内容已发布。",
  "reviewer_reason": "命中辱骂词，但属于引用和规则讨论语境，建议放行。",
  "suggested_revision": ""
}
```

### 18.4 输出示例：隐晦攻击

输入上下文：

```text
A: 这次小组作业我想重新分一下工。
B: 某些人又开始装领导了。
B: 懂的都懂，别让那个“天才”碰代码。
B: 不点名了，反正大家知道说谁。
```

期望输出：

```json
{
  "is_violation": true,
  "risk_level": 2,
  "risk_score": 72,
  "risk_types": ["harassment", "implicit_attack"],
  "confidence": 0.79,
  "decision": "manual_review",
  "target_users": ["A"],
  "is_quote_or_report": false,
  "quote_context_safe": false,
  "has_implicit_attack": true,
  "has_continuous_harassment": true,
  "evidence": [
    {
      "text": "某些人又开始装领导了",
      "reason": "结合上下文指向发起分工的用户 A，带有贬低意味",
      "risk_type": "implicit_attack"
    },
    {
      "text": "别让那个“天才”碰代码",
      "reason": "反讽称呼与排挤行为结合，构成针对性攻击",
      "risk_type": "harassment"
    }
  ],
  "context_reasoning": "单句未出现明显敏感词，但连续回复均指向同一对象，形成隐晦骚扰。",
  "user_visible_reason": "内容可能涉及针对他人的不友善表达，已进入人工复核。",
  "reviewer_reason": "建议重点查看 B 对 A 的连续回复，存在反讽称呼和排挤语义。",
  "suggested_revision": "请聚焦具体任务分工，避免对同学进行暗示性评价。"
}
```

## 19. API 设计

### 19.1 创建内容

```http
POST /api/contents
```

请求：

```json
{
  "sceneId": "class_group_001",
  "contentType": "chat_message",
  "parentId": null,
  "text": "这次作业我们重新分一下任务吧"
}
```

响应：

```json
{
  "contentId": "msg_001",
  "status": "published",
  "decision": "publish",
  "riskLevel": 0,
  "userVisibleReason": "内容已发布"
}
```

### 19.2 查询场景内容

```http
GET /api/scenes/{sceneId}/contents
```

响应：

```json
{
  "items": [
    {
      "id": "msg_001",
      "author": {
        "id": "user_001",
        "displayName": "李同学"
      },
      "text": "这次作业我们重新分一下任务吧",
      "status": "published",
      "createdAt": "2026-07-16T10:00:00+08:00"
    }
  ]
}
```

### 19.3 查询审核结果

```http
GET /api/contents/{contentId}/moderation
```

响应：

```json
{
  "contentId": "msg_002",
  "status": "limited",
  "riskLevel": 3,
  "riskTypes": ["insult"],
  "decision": "limit",
  "userVisibleReason": "内容包含可能攻击他人的表达，暂未发布。",
  "appealable": true
}
```

### 19.4 提交申诉

```http
POST /api/contents/{contentId}/appeals
```

请求：

```json
{
  "reason": "我是引用别人说过的话，并不是在攻击同学。"
}
```

响应：

```json
{
  "appealId": "appeal_001",
  "status": "submitted",
  "message": "申诉已提交，等待审核人员复核。"
}
```

### 19.5 审核人员查看待处理列表

```http
GET /api/reviewer/tasks?status=pending
```

响应：

```json
{
  "items": [
    {
      "taskId": "review_task_001",
      "contentId": "msg_002",
      "appealId": "appeal_001",
      "riskLevel": 2,
      "riskTypes": ["harassment", "implicit_attack"],
      "createdAt": "2026-07-16T10:30:00+08:00",
      "summary": "疑似对同一对象连续使用反讽称呼"
    }
  ]
}
```

### 19.6 审核人员查看上下文详情

```http
GET /api/reviewer/tasks/{taskId}
```

响应应包含：

- 当前内容
- 前后文
- 回复关系
- AI 审核结果
- 用户申诉理由
- 历史审核记录

### 19.7 审核人员提交复核结果

```http
POST /api/reviewer/tasks/{taskId}/decision
```

请求：

```json
{
  "finalDecision": "appeal_approved",
  "finalRiskLevel": 0,
  "reviewReason": "用户确实是在引用并批评攻击性内容，不构成违规。",
  "correctionType": "false_positive"
}
```

响应：

```json
{
  "success": true,
  "contentStatus": "published",
  "appealStatus": "approved"
}
```

## 20. 前端页面设计

### 20.1 普通用户端页面

#### 20.1.1 群聊 / 讨论区页面

核心功能：

- 展示消息列表。
- 输入文本并发送。
- 显示消息状态。
- 被限制内容对本人显示“仅自己可见 / 待复核 / 已限制”。
- 对被限制内容展示“查看原因”和“申诉”按钮。

推荐状态展示：

| 状态 | 用户看到的提示 |
| --- | --- |
| pending_ai_review | 正在审核 |
| published | 正常显示 |
| limited | 内容暂未公开 |
| pending_manual_review | 内容正在人工复核 |
| appeal_submitted | 申诉已提交 |
| appeal_approved | 申诉通过，内容已恢复 |
| appeal_rejected | 申诉未通过 |

#### 20.1.2 审核结果弹窗

展示：

- 内容原文
- 处理结果
- 用户可见理由
- 风险类型的简化描述
- 申诉入口

注意：不要把完整敏感词策略暴露给普通用户，避免被绕过。

#### 20.1.3 申诉页面

字段：

- 内容原文
- 系统处理原因
- 申诉理由输入框
- 可选申诉类型：
  - 我是在引用或转述
  - 我是在反驳或举报
  - 这是玩笑或误会
  - 内容被断章取义
  - 其他

提交后展示：

- 申诉编号
- 当前进度
- 预计处理提示

### 20.2 审核人员端页面

#### 20.2.1 审核工作台

列表字段：

- 内容摘要
- 风险等级
- 风险类型
- AI 推荐动作
- 是否有申诉
- 等待时间
- 优先级

筛选条件：

- 待人工复核
- 待申诉复核
- 高风险
- 疑似误判
- 风险类型
- 时间范围

#### 20.2.2 复核详情页

页面建议分为三栏：

左栏：上下文

- 当前消息高亮。
- 前后消息按时间排列。
- 回复对象标记。
- 被提及用户标记。

中栏：AI 分析

- 风险等级
- 风险分数
- 风险类型
- 证据片段
- 上下文理由
- 推荐处理
- 置信度

右栏：人工操作

- 维持限制
- 改为通过
- 要求修改后重发
- 升级高风险
- 复核理由输入框
- 误判类型选择

#### 20.2.3 审核记录页

展示：

- 内容 ID
- AI 初判
- 人工终判
- 是否申诉成功
- 复核人员
- 复核时间
- 理由

#### 20.2.4 数据看板

可展示：

- 总提交量
- AI 自动通过率
- AI 自动限制率
- 人工复核数量
- 申诉数量
- 申诉成功率
- 常见风险类型
- 常见误判原因

## 21. 演示样例设计

为了体现题目重点，建议内置至少 8 组演示样例。

### 21.1 明确辱骂

```text
你就是废物，别来拖累我们。
```

期望：

- 风险类型：insult
- 风险等级：3
- 动作：limit

### 21.2 安全引用

```text
他说“你就是废物”这种话真的很不合适，建议审核员处理。
```

期望：

- 风险类型：safe_context
- 风险等级：0
- 动作：publish

### 21.3 引用但继续攻击

```text
我就引用一下：“你就是废物”，而且我觉得他说得也没错。
```

期望：

- 风险类型：insult
- 风险等级：3
- 动作：limit

### 21.4 隐晦外号攻击

```text
别让“广场混子”负责展示了，懂的都懂。
```

结合上下文目标明确时，期望：

- 风险类型：implicit_attack / harassment
- 风险等级：2
- 动作：manual_review

### 21.5 连续骚扰

```text
B: 某些人又开始装了。
B: 每次都是他拖后腿。
B: 不点名，大家都知道。
```

期望：

- 风险类型：harassment
- 风险等级：2 或 3
- 动作：manual_review 或 limit

### 21.6 反讽和玩笑

```text
A: 我这次终于没迟到。
B: 奇迹出现了哈哈哈。
```

如果双方关系和上下文友好，期望：

- 风险等级：0 或 1
- 动作：publish 或 warn

### 21.7 诈骗

```text
班费统一转到这个私人账户，今晚不转就取消资格。
```

期望：

- 风险类型：fraud
- 风险等级：3
- 动作：limit

### 21.8 威胁

```text
你放学等着，我会让你后悔。
```

期望：

- 风险类型：threat
- 风险等级：3
- 动作：limit

## 22. 申诉复核设计

### 22.1 申诉触发条件

以下情况允许申诉：

- 内容被限制。
- 内容进入人工复核但长时间未处理。
- 用户认为 AI 断章取义。
- 用户认为内容属于引用、举报、反驳或讨论规则。

### 22.2 申诉理由结构化

用户申诉时建议收集：

- 申诉类型
- 详细说明
- 是否需要补充上下文

示例：

```json
{
  "appealType": "quote_or_report",
  "reason": "我是引用对方骂我的话，希望审核员处理，不是在骂别人。"
}
```

### 22.3 审核人员复核标准

复核时重点判断：

- AI 是否忽略了引用关系。
- AI 是否忽略了回复对象。
- AI 是否把反驳误判为攻击。
- AI 是否漏掉了隐晦攻击。
- AI 是否漏掉了连续骚扰。
- AI 是否误把玩笑当作恶意。
- 是否需要调整风险等级。

### 22.4 复核结果

复核结果建议支持：

| 结果 | 含义 |
| --- | --- |
| maintain_limit | 维持限制 |
| publish | 改为发布 |
| require_edit | 要求修改后重发 |
| escalate | 升级为高风险 |
| no_action | 不处理 |

### 22.5 误判类型

建议审核人员选择误判类型，用于后续统计：

- false_positive_quote：引用误判
- false_positive_context：上下文误判
- false_positive_joke：玩笑误判
- false_negative_implicit：隐晦攻击漏判
- false_negative_harassment：连续骚扰漏判
- policy_unclear：规则不明确

## 23. 审计与可追溯性

每次自动审核和人工复核都应记录：

- 谁提交了内容
- 提交了什么
- 当时上下文是什么
- AI 输入摘要
- AI 输出结果
- 使用的提示词版本
- 使用的策略版本
- 谁进行了人工复核
- 复核理由是什么
- 最终结果是什么

注意：如果涉及隐私数据，需要限制日志查看权限，并避免在普通用户页面展示他人敏感信息。

## 24. 策略配置建议

### 24.1 风险阈值配置

```json
{
  "publishMaxScore": 30,
  "warnMaxScore": 50,
  "manualReviewMaxScore": 75,
  "limitMinScore": 76,
  "lowConfidenceThreshold": 0.65
}
```

### 24.2 高风险类型配置

```json
{
  "alwaysManualReview": ["privacy", "self_harm"],
  "alwaysLimitWhenHighConfidence": ["fraud", "threat"],
  "allowAppeal": true
}
```

### 24.3 敏感词配置

敏感词只作为线索，不作为唯一依据。

```json
{
  "term": "废物",
  "riskType": "insult",
  "defaultRiskLevel": 2,
  "requiresContextCheck": true
}
```

## 25. AI 输出解析与容错

因为模型输出可能不稳定，后端必须做容错。

建议：

- 强制 JSON Schema 校验。
- 如果 JSON 解析失败，重试一次。
- 如果仍失败，进入人工复核。
- 如果 risk_score 越界，进行裁剪。
- 如果 decision 和 risk_level 冲突，以策略层重新计算最终动作。
- 保存原始响应，方便排查。

示例校验规则：

```text
risk_level 必须是 0、1、2、3
risk_score 必须是 0 到 100
confidence 必须是 0 到 1
decision 必须是 publish、warn、manual_review、limit 之一
risk_types 必须是数组
```

## 26. 安全与隐私

### 26.1 用户隐私

- 普通用户不能查看完整审核策略。
- 普通用户不能查看他人的隐私信息。
- 审核人员查看上下文需要记录访问日志。
- 审计日志需要权限控制。

### 26.2 防绕过

需要考虑：

- 谐音
- 拼音
- 缩写
- 空格拆字
- 数字替代
- 表情夹杂
- 反复发送边缘内容

### 26.3 防滥用申诉

可以限制：

- 同一内容只能申诉一次或有限次数。
- 高频无效申诉需要冷却。
- 恶意申诉记录可进入审核人员视野。

## 27. 测试方案

### 27.1 单元测试

重点测试：

- 文本归一化
- 规则命中
- 风险等级合并
- 状态流转
- JSON 输出解析
- API 权限校验

### 27.2 集成测试

重点测试：

- 提交内容后自动审核。
- AI 返回通过时内容发布。
- AI 返回限制时内容不公开。
- AI 返回人工复核时进入审核队列。
- 用户申诉后审核人员能处理。
- 审核人员改判后内容状态更新。

### 27.3 回归样例测试

建议维护 `moderation_cases.json`：

```json
[
  {
    "name": "安全引用不应拦截",
    "text": "他说“你就是废物”这种话不合适。",
    "context": [],
    "expectedDecision": "publish"
  },
  {
    "name": "引用后赞同攻击应拦截",
    "text": "他说你是废物，我觉得没说错。",
    "context": [],
    "expectedDecision": "limit"
  }
]
```

每次修改提示词或策略后跑一遍样例，确保不会破坏核心场景。

## 28. 最小可行版本开发计划

### 28.1 第 1 阶段：基础闭环

目标：完成从发布到审核结果返回。

任务：

- 用户和角色模拟登录。
- 群聊或论坛页面。
- 内容提交接口。
- 基础数据库表。
- 规则预检。
- AI 审核接口封装。
- 内容状态更新。

验收：

- 用户能发消息。
- 安全内容能发布。
- 高风险内容能被限制。
- 审核记录能保存。

### 28.2 第 2 阶段：上下文审核

目标：体现题目核心能力。

任务：

- 支持回复关系。
- 支持最近上下文聚合。
- 支持引用识别。
- 支持连续攻击识别。
- AI 输出证据和理由。

验收：

- “引用辱骂内容”不会被误杀。
- “无敏感词但连续攻击”能被识别。
- 审核详情能展示上下文依据。

### 28.3 第 3 阶段：申诉和人工复核

目标：完成闭环。

任务：

- 用户申诉页面。
- 审核人员工作台。
- 复核详情页。
- 人工改判接口。
- 复核记录保存。

验收：

- 用户能申诉。
- 审核人员能查看上下文和 AI 理由。
- 审核人员能改判或维持。
- 最终结果能保存。

### 28.4 第 4 阶段：优化和展示

目标：提高完成度和演示效果。

任务：

- 样例库。
- 数据看板。
- 策略配置。
- 错误处理。
- UI 打磨。
- 演示脚本。

验收：

- 可以用内置样例完整演示系统价值。
- 可以展示误判如何通过申诉纠正。
- 可以展示隐晦攻击如何被上下文识别。

## 29. 推荐目录结构

如果从零开发，可以使用以下结构：

```text
project-root/
  backend/
    app/
      main.py
      api/
        contents.py
        moderation.py
        appeals.py
        reviewer.py
      services/
        moderation_service.py
        context_service.py
        appeal_service.py
        policy_service.py
      providers/
        ai_provider.py
        mock_ai_provider.py
      models/
        user.py
        content.py
        moderation_record.py
        appeal.py
      schemas/
        content_schema.py
        moderation_schema.py
      seed/
        demo_cases.json
    tests/
  frontend/
    src/
      pages/
        UserChatPage.tsx
        AppealPage.tsx
        ReviewerDashboard.tsx
        ReviewDetailPage.tsx
      components/
        MessageList.tsx
        ModerationBadge.tsx
        ContextTimeline.tsx
        RiskPanel.tsx
      api/
        client.ts
        contents.ts
        appeals.ts
        reviewer.ts
  docs/
    AI_TEXT_MODERATION_DEVELOPMENT_GUIDE.md
```

## 30. 后端伪代码

### 30.1 内容提交

```python
async def create_content(user_id: str, payload: CreateContentRequest):
    content = await content_repo.create(
        author_id=user_id,
        scene_id=payload.scene_id,
        parent_id=payload.parent_id,
        text=payload.text,
        status="pending_ai_review",
        visible_to_public=False,
    )

    context = await context_service.build_context(content.id)
    moderation = await moderation_service.review(content, context)

    final_status = policy_service.map_decision_to_status(moderation.decision)

    await content_repo.update_status(
        content_id=content.id,
        status=final_status,
        visible_to_public=final_status == "published",
    )

    await moderation_repo.save(content.id, moderation)

    return {
        "contentId": content.id,
        "status": final_status,
        "decision": moderation.decision,
        "riskLevel": moderation.risk_level,
        "userVisibleReason": moderation.user_visible_reason,
    }
```

### 30.2 审核服务

```python
async def review(content: Content, context: ModerationContext):
    normalized = normalize_text(content.text)
    rule_result = rule_engine.check(normalized)

    ai_input = prompt_builder.build(
        content=content,
        context=context,
        rule_result=rule_result,
    )

    ai_result = await ai_provider.moderate(ai_input)
    parsed = parse_and_validate(ai_result)

    decision = policy_service.merge(
        rule_result=rule_result,
        ai_result=parsed,
        author_history=context.author_history,
    )

    return ModerationResult(
        **parsed,
        decision=decision,
    )
```

### 30.3 申诉处理

```python
async def submit_appeal(user_id: str, content_id: str, reason: str):
    content = await content_repo.get(content_id)

    if content.author_id != user_id:
        raise ForbiddenError()

    if content.status not in ["limited", "pending_manual_review"]:
        raise InvalidStateError("当前内容不支持申诉")

    appeal = await appeal_repo.create(
        content_id=content_id,
        user_id=user_id,
        reason=reason,
        status="submitted",
    )

    await review_task_repo.create(
        content_id=content_id,
        appeal_id=appeal.id,
        type="appeal_review",
        status="pending",
    )

    return appeal
```

## 31. 前端交互细节

### 31.1 发送消息后的反馈

推荐交互：

1. 用户点击发送。
2. 消息先以“审核中”状态显示在自己的消息列表中。
3. 后端返回结果后更新状态。
4. 如果发布成功，正常显示。
5. 如果被限制，显示“内容暂未公开，查看原因 / 申诉”。

### 31.2 审核人员复核体验

复核页面要降低审核人员判断成本：

- 当前内容高亮。
- AI 证据片段高亮。
- 被回复内容用连线或缩进展示。
- 风险等级用颜色区分。
- 复核按钮固定在右侧。
- 复核理由必填。

### 31.3 用户侧理由表达

用户侧理由要温和，不要刺激用户：

推荐：

```text
这条内容可能涉及针对他人的不友善表达，暂未公开。你可以修改后重新发送，或提交申诉说明具体语境。
```

不推荐：

```text
你发布了违规辱骂内容。
```

## 32. 演示脚本

演示时可以按以下顺序：

### 32.1 正常发布

用户发送：

```text
这次小组作业我们今晚八点开会讨论吧。
```

系统直接发布。

### 32.2 明确违规

用户发送：

```text
你就是废物，别拖累大家。
```

系统限制发布，并展示原因。

### 32.3 误判避免

用户发送：

```text
楼上说“你就是废物”这种话不合适，请审核员处理。
```

系统识别为引用和举报语境，允许发布。

### 32.4 隐晦攻击

构造上下文：

```text
A: 我来负责这次 PPT 吧。
B: 某些人又开始表现了。
B: 别让那个“大聪明”碰展示，懂的都懂。
```

系统识别为隐晦攻击和连续骚扰，进入人工复核。

### 32.5 用户申诉

用户对被限制内容提交：

```text
我是引用对方的话来举报，并不是在攻击别人。
```

审核人员查看上下文后改判，通过申诉并恢复内容。

## 33. 评分点对齐

| 题目要求 | 对应实现 |
| --- | --- |
| 用户发布文字内容 | 普通用户端发布页面 + `/api/contents` |
| AI 结合上下文分析风险 | Context Service + AI Prompt |
| 系统给出正常、限制或人工复核建议 | Moderation Decision |
| 用户申诉 | Appeal 模块 |
| 审核人员复核并保存结果 | Reviewer 工作台 + Manual Review |
| 不能只靠敏感词 | 规则 + AI 语义 + 上下文 |
| 避免引用误判 | 引用识别 + safe_context |
| 识别隐晦攻击 | implicit_attack + continuous_harassment |
| 只处理文字 | 所有数据模型围绕 text |

## 34. 常见风险和解决方案

### 34.1 AI 输出不稳定

解决：

- 使用 JSON Schema。
- 解析失败重试。
- 低置信度进入人工复核。
- 保存原始输出。

### 34.2 审核过严导致误伤

解决：

- 区分用户可见理由和审核人员详细理由。
- 强化引用、反驳、举报识别。
- 中风险进入人工复核，不直接封禁。
- 统计申诉成功率。

### 34.3 审核过松导致漏判

解决：

- 聚合连续上下文。
- 识别同一作者对同一对象的多次回复。
- 维护隐晦称呼样例。
- 对高风险类型设置更严格策略。

### 34.4 申诉流程形同虚设

解决：

- 必须由审核人员复核。
- 展示完整上下文。
- 保存复核理由。
- 统计 AI 误判类型。

### 34.5 演示效果不明显

解决：

- 准备对比样例：同一个敏感词在不同上下文下不同结果。
- 准备隐晦攻击样例：无敏感词但结合上下文违规。
- 准备申诉改判样例：展示闭环。

## 35. 推荐交付物

最终建议提交：

- 项目源码。
- 开发说明文档。
- 数据库初始化脚本。
- 演示数据。
- AI 提示词模板。
- 接口文档。
- 测试样例。
- 演示视频或截图。

## 36. 版本规划

### V0.1

- 基础发帖 / 发消息。
- Mock AI 审核。
- 内容状态展示。

### V0.2

- 接入真实 AI。
- 支持上下文分析。
- 支持风险解释。

### V0.3

- 支持用户申诉。
- 支持审核人员复核。
- 支持记录保存。

### V1.0

- 完整闭环。
- 数据看板。
- 策略配置。
- 样例回归测试。

## 37. 最终实现建议

如果时间有限，优先保证以下 5 件事：

1. 普通用户能发内容，并看到审核结果。
2. AI 审核输入里真的包含上下文。
3. 系统能区分“引用攻击性内容”和“真正攻击别人”。
4. 系统能识别“没有敏感词但连续针对某人的隐晦攻击”。
5. 用户申诉后，审核人员能查看上下文、改判并保存结果。

这 5 件事直接对应题目最核心的考点。只要它们跑通，即使 UI 和策略配置不复杂，也能体现这是一个真正围绕 AI 语义审核和申诉复核构建的系统，而不是普通敏感词过滤器。

<div align="center">

# 言鉴 AI（ContextGuard）

### 能理解上下文、核验证据、接受申诉，并把最终责任交给人的 AI 文字内容审核系统

[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](frontend/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](frontend/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](backend/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4-4479A1?logo=mysql&logoColor=white)](backend/migrations/)
[![MiMo](https://img.shields.io/badge/AI-Xiaomi_MiMo-FF6900)](backend/app/providers/)
[![Tests](https://img.shields.io/badge/tests-26_passed-2EA44F)](backend/tests/)
[![Workflow](https://img.shields.io/badge/workflow-Human_in_the_Loop-6F42C1)](SDD/design/system-design.md)

**上下文初审 Agent · 申诉反证 Agent · 双模型分歧 · 证据真实性校验 · 人工终审 · 规则运营**

</div>

---

言鉴 AI 不是“输入一句话，模型返回违规/不违规”的 API 包装。项目实现了完整的社区内容流转：用户登录后发布话题或回复，系统构建上下文并调用小米 MiMo 初审；代码验证模型证据，双模型发现不确定性，版本化规则完成系统分流；用户可对受限内容申诉，独立 Appeal Critic 主动挑战第一次判断，最终由审核员填写理由并作出裁决。模型、Prompt、规则、证据和状态变化全部留痕。

## 一句话价值

```text
AI 负责理解语境和提出证据
代码负责验证真实性和执行确定性规则
人工负责边界案例与最终裁决
```

这套分工解决了普通敏感词或单模型审核的四个关键问题：

1. **引用误判**：区分“作者在攻击”与“作者引用并反对攻击”；
2. **隐性风险**：结合回复对象和连续发言识别反讽、外号、群体施压；
3. **模型幻觉**：证据必须绑定真实消息 ID，并逐字存在于输入；
4. **错误纠正**：用户可补充上下文，反证 Agent 挑战原判，人工完成终审。

项目方案来自 2026-07-16 团队研讨会，并经过 SDD、实现和测试逐步收敛。会议提出的 React、FastAPI、MySQL、先 Mock 后真实模型、双 Agent 和按业务模块全栈闭环均已落地；Element Plus/Tailwind、LangGraph 等早期候选没有被机械照搬，最终分别选择 Ant Design 和更适合短周期交付的受控服务工作流。会议原始纪要保存在本地 `meeting/`，关键人工决策已整理到 [`ai-log.md`](ai-log.md)。

---

## 完成范围

### P0：完整审核与申诉闭环

- 固定单社区、多话题、线性楼层；
- 发起话题、发布新楼层、回复指定楼层；
- 发布前 AI 上下文初审；
- 消息 ID 级 Evidence 校验；
- 允许、限制、转人工三种系统分流；
- “我的发布”和用户可见审核原因；
- 用户申诉与补充上下文；
- 独立申诉反证 Agent；
- 审核员队列、人工决定和必填理由；
- 完整审计时间线与失败降级。

### P1：高分增强与基础运营

- 账号密码登录、令牌恢复、退出和角色隔离；
- 主/辅双模型独立复核和分歧检测；
- AI 建议、系统分流、人工终审三段式对比；
- 模型、Prompt、规则版本留痕；
- 连续行为分析和跨楼层证据；
- 一键边界测试案例；
- 状态筛选、模型分歧筛选和话题搜索；
- 数据统计看板；
- 审核规则配置与版本历史。

### 明确不做

- 多社区、成员管理、点赞收藏；
- 嵌套评论树；
- 批量审核、导出和消息通知；
- 多模态审核；
- 自主多 Agent 委员会；
- 替代生产审核员或承诺开放世界准确率。

---

## 评分亮点与证据

| 评分亮点 | 项目实现 | 可核验证据 |
| --- | --- | --- |
| AI Native | 上下文初审 Agent + 申诉反证 Agent + 双模型分歧 | `backend/app/providers/`、`backend/app/prompts/` |
| 不只是模型壳 | Context Builder、Schema、Evidence Validator、Rule Router、人工终审 | `backend/app/services/` |
| 复杂语境 | 引用/举报、回复对象、最近楼层、作者/目标用户历史 | `context_service.py`、Prompt |
| 可信与安全 | 严格 JSON、逐字证据、异常转人工、权限隔离 | `schemas/common.py`、`evidence_service.py` |
| 可纠错 | 申诉、补充上下文、独立 Appeal Critic、人工改判 | `appeal_service.py`、审核员页面 |
| 可追溯 | 模型/Prompt/规则版本、原始结果、审计时间线 | 数据库迁移、`audit_logs` |
| 可运营 | 统计看板、规则配置、版本历史、分歧率和改判率 | `statistics.py`、`rules.py` |
| 工程质量 | Alembic、Provider 工厂、Mock 回归、26 项测试、前端构建 | `backend/tests/`、`migrations/` |
| AI 协作过程 | 记录 AI 建议、人工采纳/拒绝、验证和证据 | [`ai-log.md`](ai-log.md) |

---

## 系统架构

```text
┌──────────────── React + TypeScript + Ant Design ────────────────┐
│ 登录 │ 社区/话题 │ 我的发布/申诉 │ 审核台 │ 统计 │ 规则配置       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Bearer Token / REST JSON
┌──────────────────────────▼ FastAPI ─────────────────────────────┐
│ Auth/RBAC │ Topic/Content │ Appeal │ Reviewer │ Statistics/Rules│
└───────────────┬───────────────────────────────┬─────────────────┘
                │                               │
        ┌───────▼────────┐              ┌───────▼─────────┐
        │ Controlled AI  │              │ SQLAlchemy      │
        │ Context Builder│              │ + Alembic       │
        │ Moderation     │              │ + MySQL 8.4     │
        │ Dual Review    │              └─────────────────┘
        │ Evidence Check │
        │ Rule Router    │
        │ Appeal Critic  │
        └───────┬────────┘
                │ OpenAI-compatible API
        ┌───────▼────────────────┐
        │ 小米 MiMo / Mock      │
        │ mimo-v2.5             │
        │ mimo-v2.5-pro         │
        └────────────────────────┘
```

### 为什么是受控工作流

模型只输出分析，不直接修改公开状态。一次审核依次经过：

```text
提交内容（默认不公开）
→ 构建上下文
→ 主模型严格结构化分析
→ 证据真实性校验
→ 辅助模型独立复核
→ 分歧检测
→ 读取当前规则版本
→ 系统分流
→ 发布 / 限制 / 人工复核
```

失败策略统一保守：超时、HTTP 错误、空内容、非法 JSON、字段缺失、枚举错误、证据不存在、上下文异常或双模型不确定，全部转人工，不默认放行，也不默认永久处罚。

---

## 界面与交互设计

系统前端不是管理后台模板的简单拼接，而是围绕两种责任角色设计两套信息结构：

| 用户端 | 审核员端 |
| --- | --- |
| 登录、社区首页、话题与楼层 | 待复核队列、模型分歧筛选 |
| 发布前审核结果、双模型摘要 | 原始上下文、主辅模型与证据 |
| 我的发布、受限原因、处理时间线 | Appeal Critic 正反论据 |
| 发起申诉、补充上下文 | 人工终审、历史对比、统计与规则 |

核心页面采用统一的风险颜色、状态标签、证据卡片和时间线。普通用户只看到可解释的处理原因，不暴露内部规则和 Prompt；审核员则能看到模型版本、证据有效性、分歧原因、不确定点和原始审计信息。

> 真实系统截图必须从运行中的页面采集后放入 `docs/images/`，不使用设计稿或其他项目截图冒充。推荐至少保留登录页、社区发布结果、审核员工作台、统计看板和规则配置五张截图。

---

## 两个 Agent 与双模型的区别

### 1. 上下文初审 Agent

输入包括：

- 当前内容、作者、所属话题；
- 被回复楼层和目标用户；
- 最近 5 楼；
- 当前作者近期内容；
- 目标用户近期内容。

输出包括风险等级、风险类型、建议动作、说话意图、目标用户、Evidence、使用的上下文和不确定点。Prompt 明确要求区分作者自己的攻击与引用、转述、举报、批评或反对攻击。

### 2. 申诉反证 Agent（Appeal Critic）

它不是把原内容再审核一次，而是读取：

- 原审核结论与原证据；
- 用户申诉理由；
- 新增上下文；
- 完整对话关系。

它必须同时输出支持原判和支持改判的依据、新证据影响、剩余不确定点及人工建议。它不能直接改判。

### 3. 双模型分歧检测

主模型和辅助模型独立运行。系统比较：

- 建议动作是否一致；
- 风险等级是否相差 2 级以上；
- 两路高风险类型是否没有交集；
- 辅助证据是否能在输入中定位；
- 辅助模型是否失败。

双模型不是投票。分歧只说明不确定性上升，默认进入人工队列。

---

## Evidence 为什么可信

模型返回的 Evidence 不能直接作为事实。代码会执行二次校验：

```text
Evidence.contentId 是否属于本次输入？
→ Evidence.text 是否逐字存在于对应消息？
→ 限制性结论是否至少有一条真实证据？
```

校验失败时：

- `evidence_valid=false`；
- 内容转人工复核；
- 保存模型原始结果和失败原因；
- 审核员页面明确显示证据无效。

这让系统可以区分“模型分析能力”和“证据真实性责任”。

---

## 规则引擎与版本化

审核规则配置不是装饰页面，它真正参与每次 `systemDecision`：

1. 证据无效且规则要求真实证据：转人工；
2. 风险类型未允许自动处置：转人工；
3. 置信度低于阈值：转人工；
4. 双模型分歧且规则开启安全路由：转人工；
5. 证据充分且达到自动限制等级：限制；
6. 达到人工阈值但模型建议公开：转人工；
7. 其他情况采用模型建议。

每次保存生成新的 `community-vN`：旧版本停用但保留，审核记录保存当时使用的 `rule_version`，因此历史结果能够解释和复盘。

---

## 状态闭环

### 内容主链

```text
pending_ai_review
├─ publish → published（分配公开楼层号）
├─ limit → limited（作者与审核员可见）
└─ manual_review → pending_manual_review
```

### 申诉链

```text
limited / pending_manual_review
→ submitted
→ Appeal Critic
→ reviewing
├─ allow → appeal_approved / 恢复公开
├─ maintain_limit → appeal_rejected
└─ need_more_context → 用户补充 → 再次反证分析
```

公开楼层号只在内容公开时分配，因此受限或待审内容不会导致社区出现空楼层。

---

## 数据库设计

| 表 | 作用 |
| --- | --- |
| `users` | 账号、角色和 PBKDF2 密码哈希 |
| `scenes` | 社区场景 |
| `topics` | 话题、分类、状态和公开性 |
| `contents` | 楼层、回复关系、正文和公开状态 |
| `moderation_records` | 主模型结果、证据、版本、系统决定和失败原因 |
| `moderation_comparisons` | 辅助模型结果、分歧原因和系统处理 |
| `moderation_rule_configs` | 不可覆盖的规则版本历史 |
| `appeals` | 申诉理由、补充上下文和状态 |
| `appeal_analysis_records` | 每次 Appeal Critic 运行记录 |
| `manual_reviews` | 原决定、人工终审、风险等级和理由 |
| `audit_logs` | 提交、审核、证据、申诉、规则与人工操作时间线 |

所有结构变化通过 Alembic 管理。主要新增迁移：

- `b62d91f47e30`：申诉分析运行记录；
- `e7c18a45d2f1`：双模型比较；
- `f39a6c20be74`：规则配置版本；
- `a82f94d17b63`：用户密码哈希。

---

## 数据统计口径

审核员统计看板展示：

- 内容总量、公开、待人工、受限；
- 申诉总数、待处理、申诉通过率；
- 人工复核数、人工改判数、改判率；
- 双模型比较数、分歧数、分歧率；
- L0–L3 风险分布；
- 系统决定分布；
- 最近 7 天提交与人工复核趋势；
- 当前模型、辅助模型、双模型开关和规则版本。

公式：

```text
申诉通过率 = approved / (approved + rejected)
人工改判率 = 人工最终决定与原 systemDecision 不同的数量 / 人工复核数
双模型分歧率 = divergent comparison / comparison 总数
```

分母为 0 时返回 0，风险和决定分布只统计每条内容的最新审核记录。

---

## 登录与权限

演示账号：

| 身份 | 用户名 | 密码 | 可访问功能 |
| --- | --- | --- | --- |
| 普通用户 | `zhangsan` | `user123` | 社区、发布、我的发布、申诉 |
| 审核员 | `reviewer` | `review123` | 待复核、历史、统计、规则配置 |

安全措施：

- 密码使用 PBKDF2-SHA256、随机盐和 210,000 次迭代保存；
- 登录签发带过期时间的 HMAC 令牌；
- 浏览器使用 `Authorization: Bearer`；
- 前端路由守卫 + 后端 401/403 双重控制；
- `X-User-Id` 只用于自动化测试，不用于浏览器登录。

这是演示级轻量登录。生产上线仍需刷新令牌、撤销列表、登录限流、HTTPS-only Cookie、验证码和统一身份平台。

---

## 技术栈

### 前端

- React 18 + TypeScript；
- Vite；
- Ant Design；
- React Router；
- Axios；
- Day.js。

### 后端

- Python 3.11；
- FastAPI + Pydantic v2；
- SQLAlchemy 2；
- Alembic；
- HTTPX；
- PyMySQL；
- PBKDF2/HMAC 标准库认证。

### AI 与数据

- 小米 MiMo OpenAI-compatible API；
- 主模型 `mimo-v2.5`；
- 辅助模型 `mimo-v2.5-pro`；
- MySQL 8.4；
- Mock Provider 用于确定性回归。

---

## 项目结构

```text
day5-submission/
├─ ai-log.md                       # 根目录 AI 协作证据
├─ README.md                       # 项目总览和运行说明
├─ frontend/                       # React 用户端与审核员端
│  └─ src/
│     ├─ pages/                    # 登录、社区、申诉、审核、统计、规则
│     ├─ components/               # 状态、风险、双模型组件
│     ├─ context/                  # 登录和业务数据状态
│     └─ api/                      # REST 客户端
├─ backend/
│  ├─ app/
│  │  ├─ api/                      # FastAPI 路由
│  │  ├─ providers/                # MiMo/Mock/Appeal Critic Provider
│  │  ├─ prompts/                  # 版本化 Prompt
│  │  ├─ services/                 # 上下文、审核、证据、申诉、规则
│  │  ├─ models/                   # SQLAlchemy ORM
│  │  └─ schemas/                  # Pydantic 契约
│  ├─ migrations/                  # Alembic 历史
│  └─ tests/                       # 26 项回归测试
├─ SDD/                            # 诊断、PRD、方案、架构、测试和风险
├─ docs/                           # 开发契约与完整实施说明
└─ scripts/                        # 数据库初始化脚本
```

---

## 环境配置

复制模板：

```powershell
Copy-Item backend\.env.example backend\.env
```

最小配置：

```dotenv
APP_ENV=development
AUTH_SECRET=请替换为长随机字符串
DATABASE_URL=mysql+pymysql://用户名:密码@数据库地址:3306/ai_moderation?charset=utf8mb4

AI_PROVIDER=auto
MIMO_API_KEY=你的密钥
MIMO_MODEL=mimo-v2.5
MIMO_SECONDARY_MODEL=mimo-v2.5-pro
AI_DUAL_REVIEW_ENABLED=true
```

团队共享 MySQL 的无密码模板见 `backend/.env.example`。数据库密码和 MiMo Key 只能写入本地 `.env`，该文件已被 Git 忽略。

Provider 模式：

- `AI_PROVIDER=auto`：存在 Key 时使用 MiMo，否则 Mock；
- `AI_PROVIDER=mimo` 或 `real`：使用真实 Provider；
- `AI_PROVIDER=mock`：确定性离线开发和测试。

---

## 本地运行

### Windows PowerShell

后端：

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m app.seed.seed_demo
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

### macOS / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m app.seed.seed_demo
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

另一个终端：

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1
```

访问地址：

- 前端：<http://127.0.0.1:5173>
- 后端健康检查：<http://127.0.0.1:8000/api/health>
- OpenAPI：<http://127.0.0.1:8000/docs>

---

## 测试与质量门禁

后端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall -q app tests migrations
.\.venv\Scripts\python.exe -m alembic check
.\.venv\Scripts\python.exe -m pytest -q
```

当前回归结果：

```text
26 passed
```

覆盖内容：

- 正常发布、安全引用、明确威胁、隐性攻击；
- 私有内容隔离和角色权限；
- 跨楼层 Evidence 与伪造证据；
- Provider 超时、HTTP 错误和非法 JSON；
- 申诉反证、补充上下文、二次分析、人工改判；
- 登录令牌、401/403；
- 规则版本、低置信度转人工；
- 双模型分歧落库；
- 统计聚合字段和趋势。

前端：

```powershell
cd frontend
npm run build
```

TypeScript 和 Vite 生产构建通过。当前只有大包体积优化提示，不影响功能验收；后续可使用路由级动态加载优化首屏体积。

---

## 关键 API

| 模块 | 接口 |
| --- | --- |
| 登录 | `POST /api/auth/login`、`GET /api/auth/me` |
| 社区 | `GET /api/community`、`GET /api/topics` |
| 发布 | `POST /api/topics`、`POST /api/topics/{id}/contents` |
| 我的内容 | `GET /api/me/contents`、`GET /api/me/appeals` |
| 申诉 | `POST /api/contents/{id}/appeals`、`POST /api/appeals/{id}/supplement` |
| 审核员 | `GET /api/reviewer/tasks`、`POST /api/reviewer/tasks/{id}/decision` |
| 统计 | `GET /api/reviewer/statistics` |
| 规则 | `GET/PUT /api/reviewer/rules`、`GET /api/reviewer/rules/history` |
| 系统 | `GET /api/health` |

完整请求与响应结构可在启动后的 `/docs` 查看。

---

## 推荐演示流程（约 6 分钟）

1. **普通用户登录**：说明未登录不能进入系统，用户端看不到审核员功能；
2. **正常发布**：加载“正常交流”，展示 AI 建议、规则分流和公开楼层号；
3. **安全引用**：提交带攻击性原句但明确反对的内容，展示语境理解和真实 Evidence；
4. **边界案例**：提交群体施压或低置信度表达，展示双模型分歧/转人工；
5. **用户申诉**：在“我的发布”补充“引用/台词”等上下文；
6. **审核员登录**：查看原上下文、主辅模型、证据和 Appeal Critic；
7. **人工终审**：填写具体理由，展示 AI → 系统 → 人工三段对比和时间线；
8. **运营能力**：打开统计看板，修改规则并生成新的 `community-vN`。

---

## SDD 与实施文档

建议按以下顺序阅读：

1. [问题定义](SDD/diagnosis/problem-framing.md)
2. [澄清问题](SDD/diagnosis/clarifying-questions.md)
3. [产品 PRD](SDD/product-prd/product-prd.md)
4. [方案对比](SDD/design-options/design-options.md)
5. [规格说明](SDD/spec/spec.md)
6. [决策备忘录](SDD/decision/decision-memo.md)
7. [系统设计](SDD/design/system-design.md)
8. [开发流程](SDD/dev-workflow/dev-workflow.md)
9. [测试策略](SDD/validation/test-strategy.md)
10. [质量门禁](SDD/validation/qa-gates.md)
11. [风险审查](SDD/validation/risk-review.md)
12. [P0 实施说明](docs/P0_AI审核与申诉闭环实施说明.md)
13. [P1 完整实施与汇报说明](docs/P1_完整功能实施过程与汇报说明.md)
14. [AI 协作日志](ai-log.md)

---

## 当前结论

项目已经完成从 SDD、实现、数据库迁移、真实模型接入、失败降级、前后端联调到自动化测试的闭环。它的核心价值不是“多调用几个模型”，而是把 AI 放在可验证、可追溯、可纠错的工程边界内：模型可以犯错，但错误不会被静默放大为不可解释的系统处罚。

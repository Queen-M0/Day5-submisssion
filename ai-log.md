# Day 5 AI 协作与开发日志

## 索引

本文件汇总 2026-07-16 至 2026-07-17 的真实 AI 协作、人工决策、工程实现和验证记录。内容依据本轮对话、SDD、Git 提交、测试结果和实际联调整理。

- 开发前问题定义：`SDD/diagnosis/`
- 产品与技术方案：`SDD/design-options/`
- 架构与决策：`SDD/design/`、`SDD/decision/`
- 开发流程：`SDD/dev-workflow/`
- 测试与风险：`SDD/validation/`
- 详细实现说明：`docs/P1_完整功能实施过程与汇报说明.md`

记录原则：

1. 区分“AI 建议”“人工决定”和“最终实现”；
2. 不把计划描述成已完成；
3. 不在日志中记录 API Key、数据库密码或完整令牌；
4. 每项关键实现必须给出代码、测试、迁移或运行结果作为证据。

## 会议纪要与最终实现对照

参考材料：`meeting/智能纪要：AI课程项目开发框架与分工研讨 2026年7月16日上午 - 飞书云文档.pdf`。会议纪要由 AI 自动生成，团队将其作为讨论线索而非无条件事实，最终以 SDD、Git 和测试为准。

| 会议决策/候选 | 最终处理 | 实际结果 |
| --- | --- | --- |
| 极简文字社区、内容线性堆叠 | 采纳 | 固定社区、多话题、线性楼层、回复某楼但不做评论树 |
| 审核链路优先，剔除图片、富文本、复杂权限 | 采纳 | 完成 P0/P1，P2 只提升统计和规则配置 |
| React + TypeScript | 采纳 | React 18 + TypeScript + Vite |
| Element Plus + Tailwind | 修改 | Element Plus 属于 Vue 生态；最终采用 Ant Design + 项目 CSS |
| Python + FastAPI + MySQL | 采纳 | FastAPI、SQLAlchemy、Alembic、MySQL 8.4 |
| 前期 Mock，主链跑通后接真实模型 | 采纳 | Mock Provider 稳定回归，MiMo Provider 真实联调 |
| 双 Agent 初审/复审 | 修改后采纳 | 初审 Agent + 申诉反证 Agent；系统规则与人工终审不包装成 Agent |
| LangGraph 状态流 | 未直接采用 | 固定审核链路用显式服务编排，更易测试和追踪；保留未来扩展可能 |
| 轻量上下文压缩 | 按项目规模调整 | 当前固定最近 5 楼 + 作者/目标用户历史，避免无边界上下文增长 |
| 按业务模块全栈分工 | 采纳 | 模块负责人覆盖页面、API、数据库和测试，减少前后端交接成本 |
| AI 生成文档初稿，人工共同确认 | 采纳并加强 | 增加采纳/拒绝记录、测试证据和诚实边界，避免把 AI 初稿当事实 |

---

## 第 1 条：从题目收敛为可验证的社区审核产品

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-16 |
| **目的** | 根据题目和 SDD 明确产品形态，避免把项目做成单句审核表单或过度复杂的完整社区 |
| **输入** | 题目要求、`problem-framing.md`、`clarifying-questions.md`、团队两天交付约束 |
| **AI 建议** | 使用固定单社区、多话题、线性楼层；内容发布前先审核，审核结果真实决定是否进入公开区 |
| **人工判断** | **采纳极简社区，拒绝多社区、成员管理、点赞收藏、无限嵌套评论。** 理由是这些功能与上下文审核的评分核心关系弱，会稀释两天交付范围 |
| **最终实现** | 固定社区、话题列表、话题搜索、线性楼层、回复指定楼层、未审核内容不占公开楼层号 |
| **验证** | 社区、话题、公开楼层和权限隔离接口测试通过 |
| **证据** | `SDD/design-options/product-prd/product-prd.md`、`frontend/src/pages/CommunityPage.tsx`、`backend/tests/test_moderation_flow.py` |

## 第 2 条：选择受控 AI 工作流而不是模型直接终审

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-16 |
| **目的** | 解决引用误判、隐性攻击、模型幻觉和申诉纠错问题 |
| **输入** | 纯规则、单模型直接裁决、受控工作流三种候选方案 |
| **AI 建议** | 将职责拆成上下文构建、AI 分析、Schema 校验、证据校验、规则分流和人工终审 |
| **人工判断** | **采纳受控工作流，拒绝“模型风险分数高就直接处罚”。** 风险分数不是经过校准的真实概率，最终行为必须受证据、确定性规则和人工责任约束 |
| **最终实现** | 同时保存 `decision`、`suggested_action`、`system_decision`，页面展示“AI 建议 → 系统分流 → 人工决定” |
| **验证** | 编造证据、非法输出和 Provider 失败均转人工；原模型记录不被人工结果覆盖 |
| **证据** | `SDD/decision/decision-memo.md`、`backend/app/services/moderation_service.py`、`frontend/src/pages/ReviewHistoryPage.tsx` |

## 第 3 条：实现上下文初审 Agent

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-16 |
| **目的** | 完成 P0 内容发布前审核，避免只看当前一句话 |
| **输入** | 当前内容、作者、话题、回复对象、最近 5 楼、作者历史、目标用户历史 |
| **AI 建议** | Prompt 要求识别说话者、对象、意图、引用/举报语境、连续针对、反讽、群体施压，并输出严格 JSON |
| **人工判断** | 采纳结构化 Agent；限制决定必须提供可定位原文。不确定时转人工，不让模型强行二分类 |
| **最终实现** | `ContextService` 构建审核包；MiMo/Mock Provider 输出 `ModerationResult`；Pydantic 严格校验字段、枚举和范围 |
| **验证** | 正常发布、安全引用、威胁限制、隐性攻击转人工、跨楼层证据等测试通过 |
| **证据** | `backend/app/services/context_service.py`、`backend/app/prompts/moderation-v2.md`、`backend/app/schemas/common.py` |

## 第 4 条：增加消息 ID 级证据真实性校验

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-16 |
| **目的** | 防止模型编造证据、改写原文或引用不存在的消息 |
| **输入** | Agent 返回的 Evidence 与实际输入消息集合 |
| **AI 建议** | 每条证据必须绑定真实 `contentId`，证据文本必须逐字存在于对应输入；校验结果由代码完成，不能让模型自证 |
| **人工判断** | 全部采纳。模型负责语义分析，代码负责真实性验证 |
| **最终实现** | `EvidenceValidator` 校验当前内容和跨楼层证据，写入 `evidence_valid`；无效证据转人工并保留失败记录 |
| **验证** | 真实跨楼层引用通过；模型虚构原文失败并进入人工队列 |
| **证据** | `backend/app/services/evidence_service.py`、`test_evidence_quote_from_other_floor_is_verified`、`test_fabricated_quote_fails_evidence_and_goes_manual` |

## 第 5 条：实现申诉反证 Agent，而不是重复第一次审核

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-16 |
| **目的** | 让申诉能够发现第一次判断的盲点，而不是让同一模型简单重复原结论 |
| **输入** | 原内容、原审核结果、原证据、申诉理由、用户补充上下文、完整对话上下文 |
| **AI 建议** | 独立 Appeal Critic 同时输出支持维持原判和支持改判的理由、新证据影响、剩余不确定点及给审核员的建议 |
| **人工判断** | **采纳独立反证角色，拒绝 AI 自动改判。** Appeal Critic 只帮助审核员寻找反例，人工仍是最终责任主体 |
| **最终实现** | 独立 Provider 边界、独立 Prompt/Schema、每次运行新增 `appeal_analysis_records`，补充上下文后可重新分析且不覆盖旧记录 |
| **验证** | 反证结果写入、消费原审核、跨楼层证据、失败降级和二次分析测试通过 |
| **证据** | `backend/app/providers/real_appeal_critic_provider.py`、`backend/app/services/appeal_service.py`、`backend/tests/test_appeal_critic_flow.py` |

## 第 6 条：接入真实小米 MiMo 并保留 Mock 回归能力

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-16 |
| **目的** | 从确定性 Demo Provider 切换为真实大模型，同时保证离线测试稳定 |
| **输入** | 用户提供的本地 `.env` Key、MiMo OpenAI-compatible API、当前 Prompt 和 Schema |
| **AI 建议** | 使用 Provider 工厂隔离真实/Mock；Key 只读本地 `.env`；健康接口只展示 Provider 和模型名，不展示密钥 |
| **人工判断** | 采纳 `auto / mimo / mock` 三种模式；真实调用异常必须显式记录并转人工，不能静默回退成“审核通过” |
| **最终实现** | 主模型 `mimo-v2.5`、辅助模型 `mimo-v2.5-pro`、独立 Appeal Critic Provider；Mock 用于 26 项自动回归 |
| **验证** | 真实 MiMo 请求成功进入工作流；HTTP 错误、超时、非法 JSON 和 Schema 不匹配可观察且安全降级 |
| **证据** | `backend/app/providers/factory.py`、`mimo_provider.py`、`openai_compat.py`、`test_mimo_provider.py` |

## 第 7 条：真实联调发现 riskScore 量表歧义并升级 Prompt

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-16 |
| **目的** | 修复辅助模型返回 `riskScore=0.1` 与系统 0–100 整数契约不一致的问题 |
| **输入** | 真实 `mimo-v2.5-pro` 输出和 Pydantic ValidationError |
| **AI 建议** | 可以放宽 Schema，也可以明确 Prompt 后继续严格校验 |
| **人工判断** | **拒绝偷偷放宽 Schema，采纳 Prompt 升级。** `riskScore` 继续保持 0–100 整数，`confidence` 才使用 0–1 小数 |
| **最终实现** | 新增 `moderation-v2`，明确数值量表、布尔类型和数组完整性；异常输出仍转人工 |
| **验证** | 原异常被真实捕获并形成 comparison 失败记录；Prompt 版本在审核记录中可追溯 |
| **证据** | `backend/app/prompts/moderation-v2.md`、`ModerationRecord.prompt_version`、真实联调记录 |

## 第 8 条：实现双模型分歧检测而不是模型投票

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-16 |
| **目的** | 提升边界案例识别能力，同时避免“多数投票等于正确”的伪可靠性 |
| **输入** | 主模型和辅助模型的动作、等级、风险类型、证据有效性和失败状态 |
| **AI 建议** | 两模型独立分析；比较动作不一致、等级差 ≥2、高风险类型无交集、辅助证据无效和辅助调用失败 |
| **人工判断** | 采纳“分歧发现器”，拒绝自主多 Agent 委员会和多数投票。分歧只表示不确定性，需要转人工 |
| **最终实现** | `moderation_comparisons` 保存辅助结果、分歧原因和系统处理；审核队列可筛选模型分歧 |
| **验证** | 双模型动作分歧正确落库并转人工；统计看板计算分歧率 |
| **证据** | `backend/app/models/entities.py`、`moderation_service.py`、`frontend/src/components/DualReviewPanel.tsx` |

## 第 9 条：将审核规则配置真正接入决策链

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-16 至 2026-07-17 |
| **目的** | 完成 P1 审核规则配置，避免页面只保存表单却不影响业务 |
| **输入** | 风险类型、人工阈值、自动限制阈值、最低置信度、证据开关、分歧策略 |
| **AI 建议** | 规则使用不可覆盖的版本历史；安全兜底优先于自动处置；每条审核保存实际使用的规则版本 |
| **人工判断** | 采纳 `community-vN` 版本化；修改理由必填；旧版本停用但保留。拒绝直接更新唯一一行导致历史不可解释 |
| **最终实现** | 规则 GET/PUT/history API、审核员配置页、`moderation_rule_configs`、审计日志和审核服务集成 |
| **验证** | 新版本递增、只有一个 active、低置信度转人工、权限 403 等测试通过 |
| **证据** | `backend/app/services/rule_service.py`、`backend/app/api/rules.py`、`ModerationRulesPage.tsx` |

## 第 10 条：补齐统计看板和审核前后对比

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-17 |
| **目的** | 将原 P2 的两个运营能力提升到本轮 P1，证明系统不仅能审核，还能观察和调参 |
| **输入** | 用户指定新增“数据统计看板、审核规则配置”，P2 其他功能不做 |
| **AI 建议** | 统计内容流转、申诉、人工改判、双模型分歧、风险/决定分布和 7 日趋势；明确每个指标口径 |
| **人工判断** | 采纳两个运营功能，继续拒绝导出、多社区、批量审核、消息通知等 P2 扩张 |
| **最终实现** | 审核员统计 API 和页面；人工记录展示 AI 建议、系统分流、人工终审三段式结果 |
| **验证** | 统计字段、4 级风险分布、7 日趋势和权限测试通过 |
| **证据** | `backend/app/api/statistics.py`、`frontend/src/pages/StatisticsDashboard.tsx`、`test_statistics_endpoint_returns_all_p1_metrics` |

## 第 11 条：补充登录、权限和密码迁移

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-17 |
| **目的** | 实现用户明确要求的登录功能，替换前端直接切换身份 |
| **输入** | 原 `X-User-Id` 演示身份、普通用户与审核员权限需求 |
| **AI 建议** | PBKDF2-SHA256 密码哈希、12 小时 HMAC 签名令牌、前端路由守卫、Bearer 请求和角色校验 |
| **人工判断** | 采纳轻量演示登录；保留 `X-User-Id` 仅供自动化测试。明确它不是完整生产 IAM |
| **最终实现** | 登录页、令牌恢复、退出登录、401/403、密码哈希字段和已有用户数据迁移 |
| **验证** | 未登录 401、错误密码 401、令牌恢复成功、普通用户访问审核员接口 403 |
| **证据** | `backend/app/services/auth_service.py`、迁移 `a82f94d17b63`、`frontend/src/pages/LoginPage.tsx` |

## 第 12 条：数据库迁移、远程联调与完整回归

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-17 |
| **目的** | 合并远程 main 后使用团队共享 MySQL，确认不同成员环境可复现 |
| **输入** | `origin/main`、共享 MySQL 地址、本地被忽略的数据库密码、Alembic 历史 |
| **AI 建议** | 先停止旧服务、快进/合并 main、保留本地秘密、验证连接、执行迁移、检查数据后再启动 |
| **人工判断** | 采纳；冲突策略由用户指定为远程 main 优先；密码只写 `.env` 不进 Git |
| **最终实现** | 本地 `wzm` 合并最新 main；远程 MySQL 8.4.10 连接成功；迁移到 `a82f94d17b63 (head)`；已有演示数据直接复用 |
| **验证** | 后端 26 项测试通过；远程库审核员登录成功；前端和后端 HTTP 200；健康检查展示真实双模型 |
| **证据** | Git 提交 `406bf05`、`56a82e2` 后续合并记录、Alembic current、pytest 输出 |

## 第 13 条：Git 分支、秘密保护和交付文档整理

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-17 |
| **目的** | 确保代码进入正确分支，敏感信息和非提交材料不进入远程仓库 |
| **输入** | 独立 `day5-submission` Git 仓库、`wzm`/`main`、本地 `.env`、运行日志、答辩参考目录 |
| **AI 建议** | 先识别内外层仓库；只操作内层；忽略 `.env`、虚拟环境、依赖、构建目录、日志和答辩参考 |
| **人工判断** | 采纳。答辩参考保留本地但从 Git 索引移除；数据库密码和模型 Key 不写入文档或提交 |
| **最终实现** | `.gitignore` 完善；P0/P1 实施文档、README 和根目录 AI 日志齐全 |
| **验证** | 提交前执行 staged sensitive path 检查、`git diff --check`、pytest 和前端 build |
| **证据** | `.gitignore`、`docs/P0_AI审核与申诉闭环实施说明.md`、`docs/P1_完整功能实施过程与汇报说明.md` |

## 第 14 条：搭建团队共享远端 MySQL 联调库

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-17 |
| **目的** | 让不同成员不再只连各自本地 `127.0.0.1` 数据库，而是可以使用同一套团队 dev 数据进行联调 |
| **输入** | 云服务器 `122.51.176.83`、MySQL root 终端、数据库名 `ai_moderation`、应用账号 `contextguard` |
| **AI 建议** | 先建库和应用账号，再只授予目标库权限；密码只通过本地 `.env` 使用，不写入 Git |
| **人工判断** | 采纳共享 dev 库方案；拒绝把数据库密码或完整连接串直接提交到仓库 |
| **最终实现** | 在云端创建 `ai_moderation`，授权 `contextguard@%` 访问目标库，并确认数据库和授权记录存在 |
| **验证** | `SHOW DATABASES LIKE 'ai_moderation'` 返回目标库；`SHOW GRANTS FOR 'contextguard'@'%'` 显示目标库授权 |
| **证据** | 云端 MySQL 执行记录、`backend/.env.example`、`docs/本地开发与数据库协作说明.md` |

## 第 15 条：将远端 MySQL 纳入 Alembic 迁移和 Seed 验证

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-17 |
| **目的** | 确认云端数据库不是空配置，而是真的能承载后端当前表结构和演示数据 |
| **输入** | 本地 `backend/.env` 中的远端 `DATABASE_URL`、Alembic 迁移历史、幂等 Seed 脚本 |
| **AI 建议** | 使用 conda `py310` 环境执行迁移和 Seed；先验证连接，再跑 `upgrade head`，避免只靠本地 SQLite 通过 |
| **人工判断** | 采纳真实 MySQL 验证；不把远端密码写入测试命令、日志或提交内容 |
| **最终实现** | 对远端 MySQL 执行 `alembic upgrade head`，随后运行 `python -m app.seed.seed_demo` 写入/复用演示数据 |
| **验证** | Alembic 升级完成；Seed 输出演示数据 ready；后端测试在 `py310` 环境通过 |
| **证据** | `backend/migrations/versions/`、`backend/app/seed/seed_demo.py`、`backend/tests/` |

## 第 16 条：真实 MiMo API 联调与超时参数收敛

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-17 |
| **目的** | 确认项目不是只依赖 Mock Provider，真实小米 MiMo API 可以在当前工作流中运行 |
| **输入** | 本地私有 MiMo Key、`mimo-v2.5`、`mimo-v2.5-pro`、后端 `/api/health` 和 Provider 调用链 |
| **AI 建议** | 先测 OpenAI-compatible 基础请求，再测项目 Provider；真实 Key 只放本地环境变量 |
| **人工判断** | 采纳真实 API 校验；发现默认输出 token 太大导致超时后，调整模板默认值而不是把失败隐藏为 Mock 成功 |
| **最终实现** | 保持 `AI_PROVIDER=auto/mimo/mock` 模式；将 `MIMO_MAX_TOKENS` 示例默认值收敛为 `400`，减少真实联调超时 |
| **验证** | `/api/health` 返回真实 Provider 和模型名；MiMo `/models` 与最小 chat completions 请求成功；项目 Provider 在较小 token 设置下完成 |
| **证据** | `backend/app/providers/factory.py`、`backend/app/providers/mimo_provider.py`、`backend/.env.example` |

## 第 17 条：合并后前后端真实运行验收

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-17 |
| **目的** | 在合并到 `main` 前确认代码、数据库、真实 AI 配置和前端页面能一起工作 |
| **输入** | 合并后的 `main`、远端 MySQL、conda `py310`、前端 Vite 项目 |
| **AI 建议** | 先跑后端测试和前端构建，再启动 FastAPI 与 Vite，最后用健康检查和页面访问确认 |
| **人工判断** | 采纳完整本地验收；验收完成后按用户要求关闭 8000 和 5173 服务，避免后台进程遗留 |
| **最终实现** | 后端在 `py310` 环境运行，前端 Vite 可访问；验收完成后停止前后端进程 |
| **验证** | `pytest backend/tests` 通过；`npm run build` 通过；后端健康检查 HTTP 200；前端页面可打开 |
| **证据** | `backend/tests/`、`frontend/package.json`、`frontend/vite.config.ts` |

## 第 18 条：补齐远端数据库配置说明并推送 main

| 字段 | 内容 |
| --- | --- |
| **日期** | 2026-07-17 |
| **目的** | 解决合作方拉取远端 `main` 后仍看到 `127.0.0.1` 数据库模板、无法判断远端主机的问题 |
| **输入** | 合作方反馈、远端 MySQL 主机、账号、库名、现有 `.env.example` 和协作文档 |
| **AI 建议** | 在仓库中提交可共享的主机、端口、库名和账号；密码继续使用占位符并由成员本地填写 |
| **人工判断** | 采纳“可复现但不泄密”的模板；不提交真实数据库密码和真实 AI Key |
| **最终实现** | `backend/.env.example` 增加注释版远端连接模板；README 和数据库协作文档补充远端库说明 |
| **验证** | `git diff --check` 通过；敏感信息检查未发现真实密码；提交 `d731a32` 已推送到远端 `main` |
| **证据** | `README.md`、`backend/.env.example`、`docs/本地开发与数据库协作说明.md`、Git 提交 `d731a32` |

---

## 人工采纳、修改与拒绝汇总

| 类型 | 决策 | 理由 |
| --- | --- | --- |
| 采纳 | 固定社区、多话题、线性楼层 | 能展示真实公开效果且范围可控 |
| 采纳 | 受控 AI 工作流 | AI、代码、规则、人工职责清晰 |
| 采纳 | 初审 Agent + 申诉反证 Agent | 分别解决首次判断和纠错问题 |
| 采纳 | Evidence Validator | 用确定性代码限制模型幻觉 |
| 采纳 | 双模型分歧检测 | 把模型不一致转化为人工复核信号 |
| 采纳 | 规则版本化与统计看板 | 形成基础运营和审计能力 |
| 修改 | 模型输出格式不稳定 | 升级 Prompt，不放宽关键 Schema |
| 拒绝 | 单一分数直接封禁 | 分数不等同于真实概率 |
| 拒绝 | 申诉时同一模型直接重判 | 容易重复第一次错误且责任不清 |
| 拒绝 | 多 Agent 自主讨论/投票 | 增加成本和不确定性，无法证明正确 |
| 拒绝 | 多社区、批量审核、通知、导出 | 超出 P0/P1，不能证明核心审核价值 |

## 最终验证结论

- 后端自动化测试：`26 passed`；
- Alembic：远程 MySQL 已到最新 `head`；
- 前端：TypeScript 与 Vite 生产构建通过；
- 真实模型：主模型和辅助模型调用链已接入，异常可观察并安全降级；
- 数据闭环：提交、审核、申诉、反证、人工终审、统计和审计均可运行；
- 安全：API Key、数据库密码、令牌和本地环境文件未提交。

## 诚实边界

本项目证明的是“受控、可追溯、可纠错的 AI 审核工作流”，不宣称开放世界生产级准确率。真实上线仍需要完整 IAM、令牌撤销、限流、监控告警、Prompt/模型评测集、数据脱敏、密钥轮换和更严格的运营审批。

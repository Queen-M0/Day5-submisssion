# 言鉴 AI（ContextGuard）

AI 文字内容审核与申诉复核社区。

本仓库包含 React 前端，以及按 `docs/前后端对接与后端开发契约.md` 实现的 FastAPI 后端和数据库迁移。

后端当前覆盖账号登录、固定社区、多话题、线性楼层、MiMo/Mock 发布前 AI 初审、跨上下文证据校验、双模型分歧检测、规则版本化、内容可见性、我的发布、申诉反证 Agent、补充上下文、人工复核、审核历史、统计看板和处理时间线。

## 提交结构

```text
frontend/         React 前端
backend/          FastAPI 后端
SDD/              系统设计文档
docs/             开发文档
答辩参考/         答辩材料
scripts/          Shell 脚本
```

## 本地启动

### 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cd ..
./scripts/bootstrap_db.sh
cd backend
uvicorn app.main:app --reload
```

接入 MiMo 时复制 `backend/.env.example` 为 `backend/.env`，至少配置：

```dotenv
AI_PROVIDER=auto
MIMO_API_KEY=你的密钥
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5
MIMO_SECONDARY_MODEL=mimo-v2.5-pro
AI_DUAL_REVIEW_ENABLED=true
```

`AI_PROVIDER=auto` 会在存在密钥时使用 MiMo，否则使用确定性的 Mock Provider。也可以设置为 `mimo` 强制走真实模型，或设为 `mock` 进行离线回归。模型超时、HTTP 错误、非法 JSON、Schema 不匹配和证据无法定位都会安全转入人工复核，不会自动放行。`GET /api/health` 会返回当前生效的 Provider 和模型名，但不会返回密钥。

团队共享远端 MySQL 的连接模板见 `backend/.env.example` 和 `docs/本地开发与数据库协作说明.md`。当前联调库为 `122.51.176.83:3306/ai_moderation`，账号 `contextguard`；密码只写入个人本地 `backend/.env`，不得提交 Git。

`scripts/bootstrap_db.sh` 会启动并等待 MySQL 8.4、执行全部 Alembic 迁移、写入幂等演示 Seed，并检查模型与迁移是否一致。

后端地址为 `http://127.0.0.1:8000`，OpenAPI 文档为 `http://127.0.0.1:8000/docs`。

### 前端

```bash
cd frontend
npm install
npm run dev
```

Vite 会将浏览器中的 `/api` 请求代理到 `http://127.0.0.1:8000`。浏览器登录后使用 Bearer 令牌访问接口，未登录不能进入业务路由。

演示账号：

- 普通用户：`zhangsan / user123`
- 审核员：`reviewer / review123`

密码仅以 PBKDF2-SHA256 哈希保存。`X-User-Id` 只保留给本地自动化测试，不用于浏览器登录。

## 后端测试

```bash
cd backend
pytest -q
alembic check
```

测试覆盖登录令牌、角色权限、正常发布、安全引用、隐晦攻击、明确威胁、规则版本化、低置信度转人工、双模型分歧落库、统计口径、模型失败、编造证据、申诉反证、要求补充、二次反证和人工改判公开。MiMo Provider 使用模拟 HTTP 响应验证 OpenAI-compatible 请求、严格 JSON 解析和异常传播，回归测试不消耗真实额度。

## SDD 文档导航

### 开发前基线

1. `SDD/diagnosis/spec.md`
2. `SDD/diagnosis/problem-framing.md`
3. `SDD/diagnosis/clarifying-questions.md`
4. `SDD/design-options/product-prd/product-prd.md`
5. `SDD/design-options/design-options.md`
6. `SDD/design-options/spec/spec.md`
7. `SDD/decision/decision-memo.md`
8. `SDD/design/system-design.md`
9. `SDD/dev-workflow/dev-workflow.md`
10. `SDD/validation/test-strategy.md`
11. `SDD/validation/qa-gates.md`

### 过程证据

- `SDD/ai-log/ai-collaboration-log.md`
- `SDD/ai-log/adopted-rejected.md`
- `SDD/validation/risk-review.md`
- `答辩参考/reflection/*`

### 原型与答辩

- `答辩参考/PROTOTYPE/prototype-guide.md`
- `答辩参考/PROTOTYPE/demo-script.md`

## MVP

- 单社区、多话题、线性楼层
- 发布前 AI 审核与证据校验
- 允许、限制、人工复核
- 我的发布
- 用户申诉与 Appeal Critic
- 人工维持或改判
- 审计时间线
- 双模型分歧检测
- 数据统计看板
- 版本化审核规则配置
- 账号登录与角色权限

完整实现过程、数据库表、Agent、状态机和 P1 运营功能见 [`docs/P1_完整功能实施过程与汇报说明.md`](docs/P1_完整功能实施过程与汇报说明.md)。

## 非目标

- 完整社区社交功能
- 多社区、嵌套评论
- 多模态
- 自主多 Agent
- 生产级准确率

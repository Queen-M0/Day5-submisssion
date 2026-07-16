# 言鉴 AI（ContextGuard）

AI 文字内容审核与申诉复核社区。

本仓库包含 React 前端，以及按 `docs/前后端对接与后端开发契约.md` 实现的 FastAPI 后端和数据库迁移。

后端当前覆盖固定社区、多话题、线性楼层、发布前 AI 审核、内容可见性、我的发布、申诉、人工复核、审核历史和处理时间线。

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

`scripts/bootstrap_db.sh` 会启动并等待 MySQL 8.4、执行全部 Alembic 迁移、写入幂等演示 Seed，并检查模型与迁移是否一致。

后端地址为 `http://127.0.0.1:8000`，OpenAPI 文档为 `http://127.0.0.1:8000/docs`。

### 前端

```bash
cd frontend
npm install
npm run dev
```

Vite 会将浏览器中的 `/api` 请求代理到 `http://127.0.0.1:8000`。页面右上角切换演示身份时，前端通过 `X-User-Id` 请求头访问对应用户或审核员数据。

## 后端测试

```bash
cd backend
pytest -q
alembic check
```

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

## 非目标

- 完整社区社交功能
- 多社区、嵌套评论
- 完整登录
- 多模态
- 自主多 Agent
- 生产级准确率

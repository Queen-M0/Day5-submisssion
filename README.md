# 言鉴 AI（ContextGuard）

AI 文字内容审核与申诉复核社区。

## 一句话介绍

一个以 AI 上下文审核为核心的极简文字社区：内容公开前经过 AI 分析和证据校验，争议内容支持用户申诉，并由审核员最终裁决。

## 提交结构

```text
SRC/
PROTOTYPE/
DOCS/
README.md
```

## 文档导航

### 开发前基线

1. `DOCS/spec.md`
2. `DOCS/diagnosis/problem-framing.md`
3. `DOCS/diagnosis/clarifying-questions.md`
4. `DOCS/diagnosis/product-prd.md`
5. `DOCS/options/design-options.md`
6. `DOCS/decision/decision-memo.md`
7. `DOCS/design/system-design.md`
8. `DOCS/collaboration/dev-workflow.md`
9. `DOCS/validation/test-strategy.md`
10. `DOCS/validation/qa-gates.md`

### 过程证据

- `DOCS/ai/ai-collaboration-log.md`
- `DOCS/ai/adopted-rejected.md`
- `DOCS/validation/risk-review.md`
- `DOCS/collaboration/contribution-map.md`
- `DOCS/collaboration/meeting-notes-template.md`
- `DOCS/reflection/*`

### 原型与答辩

- `PROTOTYPE/prototype-guide.md`
- `PROTOTYPE/demo-script.md`

## 文档时序说明

- SPEC、PRD、Options、Decision、Design、Workflow、Test Strategy 和 QA Gates 按“开发前”口径书写；
- 实际完成情况只进入 Git、Issue、dev-log、测试记录和 AI 协作日志；
- 未执行的测试不得写 PASS；
- 未发生的会议、Review 和个人贡献不得补造。

## MVP

- 单社区、多话题、线性楼层；
- 发布前 AI 审核；
- 证据校验；
- 允许、限制、人工复核；
- 我的发布；
- 用户申诉；
- Appeal Critic；
- 人工维持或改判；
- 审计时间线。

## 非目标

- 完整社区社交功能；
- 多社区；
- 嵌套评论；
- 完整登录；
- 多模态；
- 自主多 Agent；
- 生产级准确率。

## 运行说明

请在项目真实代码完成后填写：

```text
前端安装与启动：
后端安装与启动：
MySQL 建库：
Alembic 迁移：
Seed：
环境变量：
测试命令：
```

禁止保留虚假命令或未验证步骤。

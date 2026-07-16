# 开发工作流（Dev Workflow）

> 本文是开发前工作计划，不是完成情况记录。实际进展、变更和失败必须在 Issue、Git commit、会议记录和测试记录中按发生时间填写。

## 1. 工作流目标

两天内同时保证：

1. P0 主链可运行；
2. 关键判断可验证；
3. AI 使用有人工判断；
4. 两名成员均有独立贡献证据；
5. 过程文件与实际代码一致；
6. Day 7 能稳定演示并回答约束变化问题。

## 2. 阶段顺序

```text
问题诊断
→ 关键澄清
→ 三方案比较与反证
→ MVP/非目标冻结
→ SPEC/PRD
→ DESIGN
→ 测试策略与验收样例
→ 任务拆分
→ 功能实现
→ 集成验证
→ AI Review
→ 证据整理
→ 冻结与答辩
```

## 3. 开发前冻结项

研发前，两人共同确认：

- 内容形态：单社区、多话题、线性楼层；
- 状态枚举；
- 风险分类；
- AI 初审 Schema；
- 申诉反证 Schema；
- API 请求响应字段；
- 数据表和外键；
- 楼层号规则；
- 可见性规则；
- 12–18 个固定测试样例；
- A/B 责任边界。

未冻结时，不允许两人分别创造不同枚举或接口字段。

## 4. 两人纵向分工

### 成员 A：初审与证据验证链

负责：

```text
内容提交
→ 上下文构建
→ 初审 AI
→ Schema/证据校验
→ 第一次系统分流
→ 用户审核详情
```

证据要求：

- Prompt 快照；
- 接口和核心代码 commit；
- 正常、引用、骚扰、AI 失败测试；
- 一条被人工修改的 AI 建议；
- 自己模块的运行截图或日志。

### 成员 B：申诉反证与人工复核链

负责：

```text
用户申诉
→ 原审核与新增上下文对比
→ 申诉反证 AI
→ 待复核队列
→ 人工维持或改判
→ 恢复公开与时间线
```

证据要求：

- 反证 Prompt；
- 接口和核心代码 commit；
- 改判、维持、理由为空、重复申诉测试；
- 一条被人工修改的 AI 建议；
- 自己模块的运行截图或日志。

### 共同责任

- 基础数据模型；
- API/Schema 冻结；
- Alembic 迁移；
- Seed 数据；
- E2E 联调；
- README；
- AI Review；
- 演示脚本和答辩。

## 5. Git 工作方式

推荐分支：

```text
main
integration
feature/initial-moderation
feature/appeal-review
docs/evidence
```

提交原则：

- 一次提交只解决一个可说明的问题；
- Commit 信息说明“做了什么”，不写模糊的 `update`；
- 数据库字段变化必须带迁移；
- Prompt 变化必须带版本和对应回归；
- 文档不得声明未发生的测试通过；
- 合并前由另一名成员 Review。

示例：

```text
feat(moderation): add evidence grounding validation
feat(appeal): add appeal critic structured output
test(moderation): cover fabricated evidence fallback
docs(decision): record rejection of score-only auto block
```

## 6. 数据库协作

每人本地运行独立 MySQL。

同步内容：

- SQLAlchemy Model；
- Alembic Migration；
- Seed 脚本；
- 枚举常量；
- 测试数据。

禁止：

- 提交 `.env`；
- 共享 root 密码；
- 只在 Navicat 手工改表；
- 未拉取最新迁移就生成新迁移；
- 两人长期共用某一人的本地 MySQL。

标准步骤：

```text
拉取最新代码
→ alembic upgrade head
→ 修改 Model
→ 生成迁移
→ 本地验证升级与回滚
→ 提交迁移
→ 另一成员拉取并升级
```

## 7. Day 5 计划：收敛到 MVP

### 节点 1：诊断与澄清

产出：

- `spec.md`
- `problem-framing.md`
- `clarifying-questions.md`

准出：

- ≥10 个澄清；
- ≥3 个 P0；
- P0 说明答案变化如何改变方案。

### 节点 2：方案比较与决定

产出：

- `design-options.md`
- `decision-memo.md`
- `adopted-rejected.md`

准出：

- 3 个本质不同方案；
- 选择和不选理由；
- 风险与代价；
- 至少 2 条被拒绝或显著修改的 AI 建议。

### 节点 3：设计与测试先行

产出：

- `system-design.md`
- `test-strategy.md`
- `qa-gates.md`

准出：

- 状态、Schema、API 和数据结构冻结；
- 正常、边界、失败、误判、回归均有计划；
- 至少一条 E2E；
- 至少三条自补边界/失败样例。

### 节点 4：主路径实现

优先顺序：

1. 正常内容公开；
2. 风险内容不公开；
3. 用户可查看结果；
4. 用户可申诉；
5. 审核员可改判；
6. 时间线可追溯。

Day 5 日终应保存真实进度，不要求虚构“全部完成”。

## 8. Day 6 计划：验证到答辩

1. 站会根据真实进度重排 P0；
2. 跑通完整申诉改判链；
3. 执行正常、边界、失败、误判和回归；
4. AI Review 方案、代码和证据链；
5. 两人交叉 Review；
6. 补齐真实 AI 日志和测试记录；
7. 保存截图与录屏兜底；
8. 完善 README；
9. 彩排并冻结；
10. 停止新增无证据的大功能。

## 9. AI 协作工作流

每次关键 AI 使用记录：

```text
目标
输入摘要
AI 输出摘要
采纳内容
拒绝内容
人工修改
实际影响
关联文件/commit/test
```

必须覆盖至少五类：

- 澄清；
- 对比；
- 反证；
- 实现；
- 验证；
- Review。

反证或风险 Review 必须有真实记录。

## 10. 任务状态

统一状态：

- TODO
- IN_PROGRESS
- BLOCKED
- REVIEW
- DONE

`DONE` 必须满足：

- 代码或文档已保存；
- 对应测试已执行；
- 结果已记录；
- 另一成员能找到证据；
- 不存在“口头完成”。

## 11. 日终记录模板

```markdown
# Day N 日终记录

## 今日目标
## 实际完成
## 未完成及原因
## 发生的方案变更
## AI 使用与人工判断
## 测试结果
## 新发现的风险
## 明日 P0
## 证据链接
```

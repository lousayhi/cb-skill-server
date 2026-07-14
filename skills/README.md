# Skills 单一主 agent 结构说明

## 结构原则
- 所有需求统一从 `master-agent` 进入。
- `master-agent` 负责自动识别任务类型、自动路由到内部能力、统一汇总。
- 用户不需要指定插件、技能或子 agent。
- 其他技能保留为内部能力，不作为用户必须选择的入口。

## 推荐使用路径
- 任意需求：优先从 `master-agent` 进入。
- 由 `master-agent` 根据内容自动决定内部执行路径。

## 当前角色划分
### 唯一主 agent
- `master-agent`

### 内部能力
- `testing-orchestrator`
- `test-plan-auto-generate`
- `python-test-toolkit`
- `jmeter-locust-stress-gen`
- `security-basic-test`
- `test-report-auto`
- `requirement-risk-scan`
- `bug-rca-analyze`
- 以及其他具体技能

## 目录约定
- 主入口只保留一个统一入口。
- 其他能力按主题和领域继续组织，但不要求用户显式指定。

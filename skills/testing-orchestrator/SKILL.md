---
name: testing-orchestrator
description: 测试域内部能力，供主 agent 自动调用；统一编排测试方案、自动化、性能、安全、报告等测试相关产出。
ref:
  standard: 测试主子能力编排规范V1.0
  role: internal_test_orchestrator
  scene: 测试需求接入、方案拆解、脚本生成、风险评估、报告整合
  output: 测试编排结果与统一交付内容
---
# 测试域职责
1. 接收来自主 agent 的测试相关任务；
2. 自动识别测试需求类型并路由到对应测试能力；
3. 汇总测试方案、脚本、报告与结论；
4. 管控输出格式与质量标准；
5. 兼容功能、接口、性能、安全、数据、报告等测试链路。

# 可调度测试能力
- `test-plan-auto-generate`
- `python-test-toolkit`
- `jmeter-locust-stress-gen`
- `security-basic-test`
- `test-report-auto`
- `requirement-risk-scan`
- `bug-rca-analyze`

# 编排规则
## 1. 需求先分型
- 需求评审/测试方案 → 测试方案能力
- 接口自动化/造数/环境清理 → 自动化能力
- 压测/性能瓶颈 → 性能能力
- 基础安全/风险扫描 → 安全能力
- 测试总结/复盘/报告 → 报告能力

## 2. 结果统一汇总
- 去重
- 补齐缺项
- 统一术语
- 统一交付顺序

# 输出固定顺序
1. 需求识别
2. 能力路由
3. 执行结果
4. 汇总结论
5. 最终交付

# 禁止行为
1. 禁止将本文件作为用户必须选择的入口；
2. 禁止不同测试能力各自独立输出而不汇总；
3. 禁止遗漏路由说明与交付标准；
4. 禁止输出无关内容。

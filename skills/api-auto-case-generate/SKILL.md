---
name: api-auto-case-generate
description: 接口自动化脚本生成专用技能，支持传入接口URL/请求头/入参/响应样例或完整Swagger文档，一键输出三类产物：Postman导出JSON脚本、JMeter参数化完整脚本、Python Requests+pytest自动化用例代码，完全自包含无外部依赖模板。
ref:
  standard: 接口自动化脚本输出规范V1.0
  input: 手动接口信息 / Swagger OpenAPI 两种输入兼容规则
  output: Postman Collection、JMeter jmx脚本、Python pytest三套标准化模板
  scene: 正常请求、参数异常、分页边界、鉴权失效、重复提交场景自动覆盖
---
# 全局最高强制约束，不可违背
1. 输入两种模式兼容：
   模式A：手动输入URL、Method、Headers、Query/Body参数、成功响应示例；
   模式B：完整Swagger/OpenAPI JSON/YAML文档文本；
2. 固定输出三类完整产物，缺一不可：
   ① Postman Collection 标准JSON（可直接导入Postman）
   ② JMeter完整JMX脚本文本（包含线程组、HTTP请求、参数化、响应断言、查看结果树）
   ③ Python Requests + pytest 可运行自动化代码（含参数化、响应校验、异常捕获）
3. 自动覆盖接口测试场景：正常正向、参数缺失、参数类型错误、边界值、Token过期/空Token、分页极值、重复并发请求；
4. 代码/脚本自带注释，变量统一规范，可直接复制运行，无需二次改造；
5. 禁止多余闲聊、需求分析、表格、YAML、思维导图，仅输出三段产物，分段清晰标注标题；
6. 鉴权统一处理：Header携带token场景自动添加token变量参数化；
7. 分页接口自动嵌入page/size边界参数测试数据；
8. POST/PUT JSON请求统一做Body参数化，GET统一处理Query参数；
9. 响应断言自动生成：状态码校验、返回码校验、关键字段存在性校验。

# 完整执行流程
## Step1 解析接口输入信息
1. 区分输入类型：手动接口信息 / Swagger文档
2. 提取核心要素：请求地址、请求方法GET/POST/PUT/DELETE/PATCH、请求头、鉴权方式、请求参数（路径/查询/请求体）、响应结构、业务返回码、数据字段
3. 识别特殊类型：分页接口、文件上传接口、带Token鉴权接口、枚举参数接口、数字边界参数接口

## Step2 自动扩充测试参数集
基于接口参数自动生成多组测试数据：
1. 合法正常参数（正向场景）
2. 参数缺失（不传必填字段）
3. 参数类型错误（数字传字符串、数组传对象）
4. 数值边界极值、字符串超长/空值
5. Token为空、Token过期、伪造非法Token
6. 分页page=-1、page=0、size=0、size超限

## Step3 生成Postman Collection JSON
规范要求：
1. 顶层collection结构，包含folder分组；
2. 全局变量：baseUrl、access_token，统一复用；
3. 每个接口下新建多个请求：正常场景、参数异常、鉴权异常；
4. Tests脚本内置响应校验：状态码200、code=0、关键字段存在；
5. 可直接复制保存为xxx.postman_collection.json导入Postman。

## Step4 生成JMeter JMX脚本文本
规范要求：
1. 线程组：10并发、循环2次；
2. 用户定义变量：base_url、token；
3. HTTP请求取样器区分多场景；
4. CSV数据文件配置（参数化数据源模板）；
5. 响应断言：响应代码、业务code、响应包含关键字；
6. 查看结果树、汇总报告监听器；
7. 纯JMX XML文本，直接保存后缀.jmx打开JMeter。

## Step5 生成Python pytest自动化代码
规范要求：
1. 依赖requests+pytest，头部附requirements；
2. 封装基础请求类，统一携带token；
3. @pytest.mark.parametrize参数化多组测试数据；
4. 分层用例：正向正常、参数异常、鉴权失效、边界分页；
5. 断言封装：状态码、业务码、字段长度、数据匹配；
6. 增加异常捕获try-except，打印请求日志；
7. 完整可运行，无需补充配置。

# 细分接口处理规则
## 1. 分页接口（带page/size）
三组参数自动生成：正常(page=1,size=10)、边界(page=0,size=0)、超限(page=9999,size=1000)
## 2. 鉴权接口（Header: Authorization/Bearer Token）
三套token：有效token、空""、过期伪造token
## 3. JSON Body POST接口
自动生成：完整参数、缺失必填参数、参数类型错误、超长字符串
## 4. 文件上传接口
JMeter添加文件上传配置、Python增加files传参、Postman form-data模式
## 5. Swagger批量输入
自动遍历所有paths接口，批量生成全套脚本，按接口路径分组

# 输出固定排版格式（严格遵守，不调整顺序）
## 1. Postman Collection JSON
```json
// 完整可导入JSON
```
## 2. JMeter JMX 完整脚本
```
<?xml version="1.0" encoding="UTF-8"?>
// 完整jmx xml
```
## 3. Python pytest 自动化代码
```
# 完整可运行代码
```

## 禁止行为清单
禁止输出多余说明文字、流程讲解、表格、YAML；
禁止省略三类产物任意一种；
禁止简化断言、不做参数化；
禁止脚本缺少注释、变量硬编码；
禁止丢失边界 / 异常测试场景；
禁止打乱三段输出顺序。


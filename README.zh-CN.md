# Deposit Defender Desk

[English](README.md) | 中文

## Hero Section

Deposit Defender Desk 是一个本地优先的租房押金争议证据工作台，帮助租客整理 security deposit dispute packet。

- 把房东扣款项和 move-in / move-out 证据逐项匹配。
- 根据可编辑的州/地区规则估算押金返还截止日期。
- 生成证据缺口、行动优先级和文档请求草稿。

上线前补充截图或 GIF。

快速体验：

```bash
python server.py
```

打开 `http://127.0.0.1:8790`，点击 **Load sample**，再点击 **Run analysis**。

## 问题

押金争议最后通常拼的是证据。租客可能有照片、视频、清洁收据、walkthrough 表、短信和房东扣款清单，但这些材料分散在相册、邮箱、PDF 和记忆里。截止日期临近时，真正困难的是把每一项扣款对应到正确证据，并看清还缺哪些材料。

## 为什么现有方式不够

普通文件夹只能存照片，不能把照片和扣款项对应起来。表格需要租客手动算截止日期和证据强度。法律文章能解释规则，但不会帮用户整理本地证据包。单纯问 AI 又容易过度承诺，或者忽略用户实际掌握的证明。

Deposit Defender Desk 关注中间这层实际工作：组织证据、匹配扣款、发现缺口、生成简洁的文档请求草稿。

## 这个项目做什么

`证据 CSV / 证据笔记 / 扣款 CSV -> 证据匹配 -> 截止日期和缺口分析 -> 争议材料草稿 -> Markdown/JSON 报告`

## 核心功能

- 灵活导入证据 CSV，支持 dated move-in/move-out 照片、视频、walkthrough 表和收据。
- 导入房东扣款 CSV，包含金额、区域、描述和房东提供的证明。
- 粘贴证据笔记解析，适合快速补充人工记录。
- 可编辑州/地区规则 JSON，用于押金返还期限和收据阈值。
- 按房间/区域和扣款类别匹配证据。
- 标记缺少 move-in 证据、move-out 证据、房东收据和高金额扣款证明。
- 生成文档请求 / 争议材料草稿。
- Markdown 和 JSON 导出。

## 为什么有用

它把混乱的押金争议材料变成结构化证据包：哪些扣款有对应证据，哪些缺少证明，按照配置规则 notice 是否可能逾期，以及回复前应该补哪些材料。

## 演示

上线前补充截图或 GIF。

内置样例包含 move-in 证据、move-out 证据、签字 walkthrough、清洁收据、厨房/墙面/清洁/公共区域扣款、房东缺少证明，以及逾期 notice 场景。

## 快速开始

```bash
cd products/product-022/repo
python server.py
```

然后打开：

```text
http://127.0.0.1:8790
```

不需要账号、API key、房东系统、邮箱连接或联网。

## 输入 / 输出示例

证据 CSV：

```csv
evidence_id,date,area,description,stage,file_path
E001,2025-04-01,kitchen,"Move-in photo shows existing chip near sink edge",move-in,photos/kitchen.jpg
E002,2026-03-31,kitchen,"Move-out photo shows sink edge unchanged",move-out,photos/kitchen_out.jpg
```

扣款 CSV：

```csv
deduction_id,area,description,amount,landlord_evidence
D001,kitchen,"Countertop chip repair near sink",450,""
```

输出文件：

```text
outputs/deposit-defender-report.md
outputs/deposit-defender-report.json
```

## 使用场景

- 回复房东的 itemized deduction 清单。
- 检查每项扣款是否有 move-in/move-out 证据支持。
- 找出缺少的收据、照片或 walkthrough 表。
- 在升级争议前生成简洁的文档请求。
- 不把租房证据上传到云服务，也能保留本地记录。

## 工作原理

分析器会按房间/区域标准化证据和扣款，分类扣款文本，把每一项扣款与同区域 move-in/move-out 证据匹配，标记证据缺口，应用可配置的州/地区截止日期规则，并生成 triage score。这个分数只是工作流优先级，不是法律结果预测。

## 项目结构

```text
deposit_defender_desk/analyzer.py  证据解析、扣款匹配、截止日期分析和导出
server.py                          本地 HTTP 服务
web/                               浏览器界面
samples/                           证据和扣款样例
examples/                          粘贴证据笔记
tests/                             单元测试
scripts/smoke_test.py              用户视角 smoke test
```

## 路线图

- 照片 metadata 导入辅助功能。
- PDF 扣款清单解析。
- 独立可编辑的州/地区规则包。
- Exhibit 编号和可打印证据包导出。
- 押金截止日期日历提醒导出。

## 限制

Deposit Defender Desk 不是法律建议，也不预测法院结果。州和地方规则会变化，用户需要自行核验。应用不会上传照片、读取图片内容、联系房东、提交索赔，或连接邮箱/云盘。证据匹配基于文本、区域、日期和本地规则配置。

## 许可证

MIT

## Language

English version: [README.md](README.md)


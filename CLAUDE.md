# AI Knowledge Garden

## 项目概述

自动从 GitHub Trending 和 Hacker News 采集 AI/LLM/Agent 领域的技术动态，通过 AI 分析后结构化存储为 JSON 知识条目，并支持多渠道分发（飞书、企业微信）。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 运行时 | Python 3.12 |
| AI 模型 | Claude (Anthropic) + 国产大模型（DeepSeek / Qwen） |
| 工作流编排 | LangGraph |
| 网页抓取 | OpenClaw |
| 数据格式 | JSON（知识条目）、Markdown（文章） |
| 分发渠道 | 飞书 Webhook、企业微信 Webhook |

---

## 编码规范

- **风格**: 严格遵循 PEP 8，行宽 ≤ 100 字符
- **命名**: 变量、函数、模块一律 `snake_case`；类名 `PascalCase`；常量 `UPPER_SNAKE_CASE`
- **Docstring**: Google 风格，所有公开函数/类必须写
- **日志**: 禁止裸 `print()`，统一使用 `logging` 模块（`logger = logging.getLogger(__name__)`）
- **类型注解**: 所有函数签名必须有类型注解（Python 3.12 原生 `type` 语法优先）
- **异常处理**: 禁止裸 `except:`，必须捕获具体异常类型
- **导入顺序**: 标准库 → 第三方库 → 本地模块，各组之间空一行

```python
# ✅ GOOD
import logging
from typing import Optional

import httpx
from langgraph.graph import StateGraph

from garden.models import KnowledgeItem

logger = logging.getLogger(__name__)

def fetch_trending(limit: int = 20) -> list[KnowledgeItem]:
    """从 GitHub Trending 采集 AI 相关项目。

    Args:
        limit: 最多采集条目数，默认 20。

    Returns:
        结构化知识条目列表。

    Raises:
        httpx.HTTPError: 网络请求失败时抛出。
    """
    ...
```

---

## 项目结构

```
ai-knowledge-garden/
├── CLAUDE.md                   # 本文件
├── pyproject.toml
├── .env.example
│
├── .claude/
│   ├── agents/                 # Sub-agent 定义（YAML + Prompt）
│   │   ├── collector.md        # 采集 Agent
│   │   ├── analyzer.md         # 分析 Agent
│   │   └── organizer.md        # 整理 Agent
│   └── skills/                 # 可复用技能片段
│       ├── fetch_github.py
│       ├── fetch_hackernews.py
│       └── publish_feishu.py
│
├── garden/                     # 核心业务代码
│   ├── __init__.py
│   ├── models.py               # Pydantic 数据模型
│   ├── graph.py                # LangGraph 工作流定义
│   ├── nodes/                  # LangGraph 节点
│   │   ├── collect.py
│   │   ├── analyze.py
│   │   └── distribute.py
│   └── publishers/             # 分发渠道适配器
│       ├── feishu.py
│       └── wecom.py
│
├── data/
│   ├── raw/                    # 原始抓取内容（临时，不提交）
│   └── articles/               # 结构化知识条目 JSON
│
└── tests/
    └── ...
```

> `data/raw/` 和 `data/articles/` 已加入 `.gitignore`，不提交到版本库。

---

## 知识条目 JSON 格式

每个知识条目存储为独立 JSON 文件，文件名为 `{id}.json`。

```json
{
  "id": "gh-2025-05-10-001",
  "title": "microsoft/graphrag: A modular graph-based RAG system",
  "source": "github_trending",
  "source_url": "https://github.com/microsoft/graphrag",
  "collected_at": "2025-05-10T08:00:00Z",
  "published_at": null,
  "summary": "微软开源的基于知识图谱的 RAG 框架，支持全局和局部查询模式，适合需要跨文档推理的场景。",
  "key_points": [
    "支持 Global Search（全局摘要）和 Local Search（局部上下文）两种查询模式",
    "基于社区检测算法构建层次化知识图谱",
    "本周新增 Star 数：3.2k"
  ],
  "tags": ["rag", "knowledge-graph", "llm", "microsoft"],
  "language": "zh-CN",
  "status": "draft",
  "relevance_score": 0.92,
  "distributed_to": []
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `str` | 唯一标识，格式 `{source_prefix}-{date}-{seq}` |
| `title` | `str` | 原始标题 |
| `source` | `str` | 来源：`github_trending` / `hacker_news` |
| `source_url` | `str` | 原始链接 |
| `collected_at` | `str` | ISO 8601 采集时间（UTC） |
| `published_at` | `str \| null` | 分发时间，未分发为 `null` |
| `summary` | `str` | AI 生成的中文摘要（100-200 字） |
| `key_points` | `list[str]` | 3-5 条核心要点 |
| `tags` | `list[str]` | 小写英文标签 |
| `language` | `str` | 摘要语言，默认 `zh-CN` |
| `status` | `str` | `draft` / `ready` / `published` / `skipped` |
| `relevance_score` | `float` | AI 评估的相关度，0.0-1.0 |
| `distributed_to` | `list[str]` | 已分发渠道列表，如 `["feishu", "wecom"]` |

---

## Agent 角色概览

| Agent | 文件 | 职责 | 输入 | 输出 |
|-------|------|------|------|------|
| **Collector** | `.claude/agents/collector.md` | 从 GitHub Trending / HN 抓取原始内容，过滤 AI 相关条目 | 日期、关键词配置 | `data/raw/*.json` |
| **Analyzer** | `.claude/agents/analyzer.md` | 调用 AI 模型生成摘要、要点、标签，评估相关度 | `data/raw/*.json` | `data/articles/*.json`（status=ready） |
| **Organizer** | `.claude/agents/organizer.md` | 去重、归档、触发多渠道分发，更新 status 和 distributed_to | `data/articles/*.json` | 分发结果、归档记录 |

工作流由 LangGraph 编排，节点间通过共享 State 传递数据。

---

## 红线（绝对禁止）

1. **禁止硬编码密钥** — API Key、Webhook URL 必须通过环境变量或 `.env` 文件注入，禁止出现在代码或提交历史中
2. **禁止裸 `print()`** — 所有输出必须走 `logging`，便于日志级别控制和生产环境过滤
3. **禁止修改已发布条目** — `status=published` 的条目只读，需修正时创建新条目并标注 `supersedes` 字段
4. **禁止无限重试** — 所有外部 HTTP 请求必须设置超时（`timeout=30`）和最大重试次数（≤ 3）
5. **禁止提交 `data/` 目录** — 原始数据和知识条目不进版本库，通过对象存储或本地持久化管理
6. **禁止跳过相关度过滤** — `relevance_score < 0.6` 的条目自动标记为 `skipped`，不进入分发流程
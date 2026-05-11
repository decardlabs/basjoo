# Ccbot 智能体平台 — 监控与告警设计

> 补充阶段一遗漏：关键监控指标、告警阈值、告警渠道
> 生成时间：2026-05-10

---

## 一、监控目标

1. **实时感知系统健康度**：Qdrant、Redis、后端API、前端可用性
2. **预测容量瓶颈**：Token消耗趋势、文档存储增长
3. **快速定位故障**：trace_id串联请求链路
4. **业务指标可视化**：回答准确率、来源覆盖率趋势

---

## 二、监控指标体系

### 2.1 API 层指标

```python
# Prometheus metrics 定义
from prometheus_client import Counter, Histogram, Gauge

# 请求计数
API_REQUEST_TOTAL = Counter(
    "ccbot_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"]
)

# 请求延迟
API_REQUEST_DURATION = Histogram(
    "ccbot_api_request_duration_seconds",
    "API request duration",
    ["method", "endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# 当前活跃会话
ACTIVE_SESSION_GAUGE = Gauge(
    "ccbot_active_sessions",
    "Current active chat sessions"
)
```

| 指标 | PromQL 表达式 | 告警阈值 | 告警等级 |
|------|-----------------|----------|----------|
| API P95延迟 | `histogram_quantile(0.95, rate(ccbot_api_request_duration_seconds_bucket[5m]))` | > 2s | 🔴 Critical |
| API P99延迟 | `histogram_quantile(0.99, rate(ccbot_api_request_duration_seconds_bucket[5m]))` | > 5s | 🟡 Warning |
| 错误率（5xx） | `sum(rate(ccbot_api_requests_total{status=~"5.."}[5m])) / sum(rate(ccbot_api_requests_total[5m]))` | > 5% | 🔴 Critical |
| 4xx错误率 | `sum(rate(ccbot_api_requests_total{status=~"4.."}[5m])) / sum(rate(ccbot_api_requests_total[5m]))` | > 20% | 🟡 Warning |

### 2.2 RAG 核心指标

```python
# RAG 专用指标
RAG_RETRIEVAL_DURATION = Histogram(
    "ccbot_rag_retrieval_duration_seconds",
    "RAG retrieval duration",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

RAG_EMBEDDING_DURATION = Histogram(
    "ccbot_rag_embedding_duration_seconds",
    "Embedding generation duration"
)

RAG_RECALL_RATE = Gauge(
    "ccbot_rag_recall_rate",
    "Retrieval recall rate"
)

LLM_TOKENS_TOTAL = Counter(
    "ccbot_llm_tokens_total",
    "Total LLM tokens consumed",
    ["model", "agent_id"]
)
```

| 指标 | 说明 | 告警阈值 | 告警等级 |
|------|------|----------|----------|
| Qdrant 查询P95延迟 | 向量检索耗时 | > 500ms | 🟡 Warning |
| Qdrant 查询P99延迟 |  | > 2s | 🔴 Critical |
| Embedding 生成P95延迟 | bge模型推理耗时 | > 1s | 🟡 Warning |
| LLM 响应P95延迟 | MiniMax/DeepSeek响应 | > 10s | 🟡 Warning |
| 召回率（日均值） | Top-5召回准确率 | < 90% | 🟡 Warning |
| 拒答率（日均值） | 正确拒绝比例 | < 80% | 🟡 Warning |
| Token消耗日环比 | 日Token消耗增长率 | > 50% | 🟡 Warning |

### 2.3 下游依赖指标

| 指标 | 数据源 | 告警阈值 | 告警等级 |
|------|--------|----------|----------|
| 硅基流动API错误率 | 外部API调用 | > 10% | 🔴 Critical |
| UniAPI 错误率 | 外部LLM调用 | > 5% | 🔴 Critical |
| Redis 连接数 | Redis INFO | > 80% maxconn | 🟡 Warning |
| Qdrant 存储使用率 | Qdrant Cluster info | > 80% | 🟡 Warning |
| SQLite 磁盘使用 | 文件系统监控 | > 90% | 🔴 Critical |

### 2.4 业务指标

| 指标 | 说明 | 告警阈值 | 告警等级 |
|------|------|----------|----------|
| 回答准确率（日） | 基于LLM-as-Judge | < 85% | 🔴 Critical |
| 来源覆盖率（日） | 有来源标注的回答占比 | < 95% | 🟡 Warning |
| 用户满意度（周） | 👍 占比 | < 75% | 🟡 Warning |
| 首轮解决率（周） | 用户无需追问 | < 70% | 🟡 Warning |

---

## 三、日志规范

### 3.1 统一日志格式（JSON）

```python
import json
import time
from datetime import datetime

def log_event(level, event, **kwargs):
    """统一日志格式"""
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": level,          # INFO / WARNING / ERROR / CRITICAL
        "event": event,          # 事件类型
        "trace_id": kwargs.get("trace_id"),       # 请求链路ID
        "agent_id": kwargs.get("agent_id"),
        "session_id": kwargs.get("session_id"),
        "duration_ms": kwargs.get("duration_ms"),
        "metadata": kwargs.get("metadata", {}),
    }
    # 输出到 stdout（Docker 采集）
    print(json.dumps(record, ensure_ascii=False))
```

### 3.2 关键日志事件

| 事件代码 | 级别 | 触发场景 | 日志内容示例 |
|----------|------|----------|----------------|
| `rag_query` | INFO | 用户发起RAG查询 | `{"query": "...", "agent_id": "agt_xxx", "trace_id": "..."}` |
| `rag_retrieval` | INFO | 检索完成 | `{"retrieved_count": 5, "duration_ms": 120, "scores": [0.95, 0.88, ...]}` |
| `rag_llm_response` | INFO | LLM回答完成 | `{"model": "MiniMax", "tokens": 256, "duration_ms": 850}` |
| `rag_low_score` | WARNING | retrieval_score < 0.3 | `{"query": "...", "top_score": 0.25, "sources": [...]}` |
| `embedding_error` | ERROR | Embedding API失败 | `{"api": "siliconflow", "error": "timeout", "duration_ms": 30000}` |
| `qdrant_error` | ERROR | Qdrant操作失败 | `{"operation": "upsert", "error": "connection refused"}` |
| `document_delete` | INFO | 文档删除 | `{"doc_id": "...", "chunks_deleted": 45, "duration_ms": 320}` |
| `evaluation_run` | INFO | 评估任务执行 | `{"run_id": "...", "accuracy": 0.87, "duration_seconds": 120}` |

### 3.3 trace_id 串联

```python
# 中间件：为每个请求生成 trace_id
@app.middleware("http")
async def trace_middleware(request, call_next):
    trace_id = request.headers.get("X-Trace-Id", generate_trace_id())
    request.state.trace_id = trace_id

    # 设置到 contextvar（供子函数使用）
    set_trace_id(trace_id)

    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response
```

---

## 四、告警规则配置

### 4.1 Alertmanager 配置示例

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ["alertname", "severity"]
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: "default"

  routes:
    - match:
        severity: critical
      receiver: "critical-alerts"
    - match:
        severity: warning
      receiver: "warning-alerts"

receivers:
  - name: "default"
    webhook_configs:
      - url: "http://ccbot-backend:8000/api/v1/alerts/webhook"

  - name: "critical-alerts"
    webhook_configs:
      - url: "https://oapi.dingtalk.com/robot/send?access_token=xxx"  # 钉钉
    email_configs:
      - to: "ops@decard.cc"

  - name: "warning-alerts"
    webhook_configs:
      - url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"  # 企业微信
```

### 4.2 PrometheusRule 示例

```yaml
# prometheus-rules.yml
groups:
  - name: ccbot.rules
    rules:
      # API 延迟告警
      - alert: HighAPILatency
        expr: histogram_quantile(0.95, rate(ccbot_api_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API P95延迟超过2秒（当前 {{ $value }}s）"
          description: "服务 {{ $labels.instance }} 的API延迟持续过高"

      # 错误率告警
      - alert: HighErrorRate
        expr: sum(rate(ccbot_api_requests_total{status=~"5.."}[5m])) / sum(rate(ccbot_api_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API错误率超过5%（当前 {{ $value | humanizePercentage }}）"

      # Qdrant 查询慢
      - alert: SlowQdrantQuery
        expr: histogram_quantile(0.95, rate(ccbot_rag_retrieval_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Qdrant查询P95延迟超过500ms"

      # Token消耗异常
      - alert: AbnormalTokenConsumption
        expr: rate(ccbot_llm_tokens_total[1h]) > 100000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Token消耗速率异常（{{ $value | humanize }} tokens/hour）"

      # 召回率低
      - alert: LowRecallRate
        expr: ccbot_rag_recall_rate < 0.9
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "召回率低于90%（当前 {{ $value | humanizePercentage }}）"

      # 存储空间不足
      - alert: LowDiskSpace
        expr: (1 - node_filesystem_free_bytes{mountpoint="/opt/ccbot"} / node_filesystem_size_bytes{mountpoint="/opt/ccbot"}) > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "存储空间使用超过80%"
```

---

## 五、告警渠道设计

### 5.1 告警分级与通知渠道

| 等级 | 定义 | 通知渠道 | 响应时间要求 |
|------|------|----------|----------------|
| 🔴 Critical | 影响核心功能（API不可用、数据丢失风险） | 电话 + 短信 + 钉钉/企微 | 15分钟内响应 |
| 🟡 Warning | 性能下降、预测性告警 | 钉钉/企微 + 邮件 | 2小时内处理 |
| 🟢 Info |  informational，无需立即处理 | 邮件汇总（日报） | 24小时内查看 |

### 5.2 告警抑制规则

```yaml
# 告警抑制：Critical 告警触发时，抑制同服务的 Warning 告警
inhibit_rules:
  - source_match:
      severity: critical
    target_match:
      severity: warning
    equal: ["alertname", "instance"]
```

---

## 六、可视化仪表盘设计

### 6.1 Grafana Dashboard 布局

```
┌─────────────────────────────────────────────────────────┐
│  Ccbot 系统监控                                [时间范围] │
├─────────────────────────────────────────────────────────┤
│  [API请求量]  [错误率]  [P95延迟]  [活跃会话]         │
│     1200/min    0.8%     850ms       342             │
├─────────────────────────────────────────────────────────┤
│  RAG 性能                                                   │
│  [检索P95]  [Embedding P95]  [召回率]  [拒答率]      │
│     120ms        450ms          92%          85%        │
├─────────────────────────────────────────────────────────┤
│  LLM 用量                                                   │
│  [Token消耗/小时]  [按模型分布]  [成本/天]              │
│     45K              MiniMax 70%      ¥128             │
├─────────────────────────────────────────────────────────┤
│  [下游依赖健康度]  [Qdrant存储]  [Redis连接]          │
│     正常              45MB          120/1000            │
└─────────────────────────────────────────────────────────┘
```

### 6.2 关键图表 PromQL

```promql
# API 请求量（按_endpoint）
sum(rate(ccbot_api_requests_total[1m])) by (endpoint)

# 错误率堆叠
sum(rate(ccbot_api_requests_total{status=~"5.."}[5m])) by (endpoint)

# Token消耗趋势
sum(rate(ccbot_llm_tokens_total[1h])) by (model)

# 召回率趋势
avg_over_time(ccbot_rag_recall_rate[1d])
```

---

## 七、验收测试

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_metrics_endpoint | 访问 `/metrics` | PromQL格式指标返回 | HTTP 200 |
| test_alert_firing | 人为触发高延迟 | Alertmanager收到告警 | 5分钟内 |
| test_log_format | 发起API请求 | 日志为合法JSON | 可被Logstash解析 |
| test_trace_id_propagate | 跨服务调用 | trace_id一致 | 全链路可追踪 |
| test_grafana_dashboard | 查看Grafana | 图表数据正确 | 无空数据 |

---

## 八、T1.X 任务归属

将监控告警作为阶段一补充任务：

| 任务ID | 描述 | 优先级 |
|--------|------|--------|
| T1.17 | Prometheus metrics 埋点 | P0 |
| T1.18 | 日志规范实现（JSON + trace_id） | P0 |
| T1.19 | Alertmanager 配置 + 告警规则 | P1 |
| T1.20 | Grafana Dashboard 配置 | P1 |
| T1.21 | 告警渠道对接（钉钉/企微） | P1 |

---

*本文档补充 PHASED_ROADMAP.md 遗漏的监控与告警设计。*

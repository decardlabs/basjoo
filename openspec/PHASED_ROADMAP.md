# Ccbot 智能体平台 — 分阶段任务拆解与功能描述

> **核心原则：好的系统是测试出来的，不是开发出来的。**
> 
> 每个功能模块的开发，必须从定义该功能的验收测试开始。
> 测试基础设施是一切开发的前提，在验证体系未建立前，不得开发其他功能。
> 
> 生成时间：2026-05-07
> 最后更新：2026-05-10（阶段一文件格式扩展）

---

## 目录

- [一、TDD 开发流程总览](#一tdd-开发流程总览)
- [二、阶段 0：测试基础设施（最高优先级）](#二阶段-0测试基础设施最高优先级)
- [三、阶段 1：功能开发](#三阶段-1功能开发)
- [四、阶段 2：多模态输入](#四阶段-2多模态输入)
- [五、阶段 3：多媒体检索与返回](#五阶段-3多媒体检索与返回)
- [六、跨阶段公共能力](#六跨阶段公共能力)
- [七、测试数据集概览](#七测试数据集概览)
- [八、任务优先级总览](#八任务优先级总览)

---

## 一、TDD 开发流程总览

### 1.1 TDD 开发原则

```
传统开发流程（❌ 错误）：
  需求 → 设计 → 开发 → 测试 → 上线
                               ↑
                        发现问题已晚

TDD 开发流程（✅ 正确）：
  需求 → 设计测试 → 开发 → 验证测试 → 上线
       ↑
    测试先行
```

### 1.2 任务开发顺序

```
┌─────────────────────────────────────────────────────────────────┐
│  阶段 0：测试基础设施（必须最先完成）                             │
│  ├── T0.1  TestSet 数据模型                                      │
│  ├── T0.2  评估执行 API                                         │
│  ├── T0.3  评估指标计算                                          │
│  ├── T0.9  LLM-as-Judge                                         │
│  ├── T0.13 160条测试用例导入                                     │
│  └── T0.14 测试集管理 API                                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  阶段 1：功能开发（每个功能前先定义测试）                         │
│  ├── T1.1  PDF上传 → 先定义解析验收测试                          │
│  ├── T1.2  数据清洗 → 先定义清洗质量测试                          │
│  ├── T1.3  语义切块 → 先定义切块边界测试                          │
│  └── ...                                                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  阶段 2：持续集成                                                │
│  ├── T0.7  quality_gate（质量门禁）                               │
│  ├── T0.15 CI/CD 集成                                            │
│  └── T0.11 定时报告                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 质量门禁规则

| 阶段 | 质量门禁条件 | 未达标处理 |
|------|-------------|-----------|
| 阶段 0 完成 | 测试基础设施可用 | 阻塞功能开发 |
| 功能上线前 | 该功能验收测试全部通过 | 阻塞功能上线 |
| 每日/每周 | 回归测试集通过率 ≥ 95% | 告警 + 阻止新功能上线 |
| 定期评估 | 核心指标（准确率 ≥ 85%） | 触发优化流程 |

---

## 二、阶段 0：测试基础设施（最高优先级）

> **⚠️ 这是所有开发的前提。在 T0 任务完成前，不得开发任何功能。**

### 2.1 为什么先建测试基础设施？

```
没有测试基础设施 = 盲目开发

问题：
  - 怎么知道 PDF 解析功能是否正确？
  - 怎么知道混合检索比纯向量检索好？
  - 怎么知道这次更新没有破坏已有功能？
  - 怎么量化准确率是 85% 还是 60%？

答案：
  - 测试基础设施提供量化标准
  - 测试基础设施提供回归保护
  - 测试基础设施提供持续反馈
```

### 2.2 测试数据集

#### 已就绪

| 测试集 | 文件 | 条数 | 状态 |
|--------|------|------|------|
| 文字问答 | `openspec/EVAL_TEST_SET.md` | 160 | ✅ 已生成 |

#### 待生成

| 测试集 | 条数 | 负责阶段 | 状态 |
|--------|------|----------|------|
| 语音输入 | 30 | 阶段二 | ❌ 待生成 |
| 图片输入 | 20 | 阶段二 | ❌ 待生成 |
| 视频输入 | 10 | 阶段二 | ❌ 待生成 |
| 图片检索 | 20 | 阶段三 | ❌ 待生成 |
| 视频检索 | 15 | 阶段三 | ❌ 待生成 |
| **回归测试集** | 50+ | **阶段0** | ❌ 待定义 |

**回归测试集说明**：从历史错误案例中提炼，包括：
- 之前答错的问题
- 之前检索召回失败的问题
- 之前幻觉生成的回答
- 之前引用错误的案例

### 2.3 评估指标体系

| 指标 | 定义 | 目标值 | 验收方式 | 备注 |
|------|------|--------|----------|------|
| **回答准确率** | 评估回答是否正确解决用户问题 | ≥ 85% | LLM-as-Judge + 人工抽检 | |
| **来源覆盖率** | 有来源标注的回答占比 | ≥ 95% | 自动统计 | |
| **检索召回率** | 正确答案在 Top-5 检索结果中的比例 | ≥ 90% | 自动计算 | 阶段二引入 NDCG@k / MRR@k |
| **无答案率** | 知识库无相关内容时的正确拒绝率 | ≥ 80% | 自动化测试 | **阶段一新增拒答测试用例（10-20条）** |
| **首轮解决率** | 用户无需追问即可得到满意回答的比例 | ≥ 70% | 用户反馈统计 | |
| **用户满意度** | 消息末尾 👍 占比 | ≥ 75% | 用户反馈统计 | |

**拒答测试说明**（阶段一新增）：
- 测试集须包含 10-20 条与文档库无关的问题
- 验证 RAG 是否能正确拒绝回答（而非幻觉作答）
- 验收标准：拒答准确率 ≥ 80%

**阶段二评估增强**（待引入）：
- **NDCG@k**：评估相关性排序质量（是否将最相关文档排在第一位）
- **MRR@k**：评估第一个相关结果的排名
- **语义相似度**（BLEU/ROUGE）：评估生成答案与预期答案的语义匹配度

### 2.4 任务拆解

#### T0.1 TestSet 数据模型

**功能描述**：定义测试用例的存储结构。

**数据模型**：
```python
class TestSet(Base):
    id: str                    # 唯一标识，格式 test_XXX
    category: str              # 分类：平台功能/技术问题/边界场景等
    question: str              # 用户问题原文
    expected_answer_keywords: List[str]  # 期望关键词（自动评分）
    expected_sources: List[str]         # 期望来源（检索验证）
    rejection_expected: bool            # 是否期望正确拒绝
    difficulty: str             # easy/medium/hard
    note: str                   # 人工备注

class EvaluationRun(Base):
    id: str
    test_set_id: str
    run_at: datetime
    total_cases: int
    passed: int
    failed: int
    metrics: dict               # 各指标详细分数
    details: List[CaseResult]   # 每条用例的详细结果
```

**验收测试**：
- [ ] test_testsets_crud：增删改查正常
- [ ] test_testset_validation：必填字段校验
- [ ] test_testsets_query：分类查询、分页

**质量门禁**：无（基础设施本身）

---

#### T0.2 评估执行 API

**功能描述**：批量运行测试集，返回评估结果。

**API 设计**：
```
POST /api/v1/evaluation/run
Request: {
    "test_set_id": "test_set_001",
    "agent_id": "agt_xxx",
    "mode": "full" | "quick"  # quick 仅关键词匹配
}
Response: {
    "run_id": "run_xxx",
    "status": "running" | "completed",
    "total": 160,
    "passed": 136,
    "failed": 24,
    "accuracy": 0.85,
    "duration_seconds": 120
}
```

**验收测试**：
- [ ] test_evaluation_run_basic：正常执行
- [ ] test_evaluation_run_concurrent：并发执行仅一实例
- [ ] test_evaluation_run_invalid：无效 test_set_id 返回 404

**质量门禁**：单元测试通过

---

#### T0.3 评估指标计算

**功能描述**：计算各项评估指标。

**指标计算逻辑**：

```python
def calculate_accuracy(response, test_case):
    """回答准确率：关键词匹配 + LLM-as-Judge"""
    keywords_match = all(kw in response for kw in test_case.expected_answer_keywords)
    return keywords_match or llm_judge(response, test_case)

def calculate_recall(retrieved_docs, test_case):
    """检索召回率：正确答案在 Top-N 中"""
    relevant_sources = set(test_case.expected_sources)
    retrieved_sources = set(d.source_id for d in retrieved_docs[:5])
    return len(relevant_sources & retrieved_sources) / max(len(relevant_sources), 1)

def calculate_rejection_rate(responses, test_cases):
    """无答案率：正确拒绝的比例"""
    correct_rejections = sum(
        1 for r, tc in zip(responses, test_cases)
        if tc.rejection_expected and is_rejection(r)
    )
    expected_rejections = sum(1 for tc in test_cases if tc.rejection_expected)
    return correct_rejections / max(expected_rejections, 1)
```

**验收测试**：
- [ ] test_accuracy_calculation：关键词全匹配/部分匹配
- [ ] test_recall_calculation：Top-5/Top-10 召回
- [ ] test_rejection_calculation：正确拒绝/错误拒绝

**质量门禁**：单元测试覆盖率 ≥ 90%

---

#### T0.4 Playground 单条测试

**功能描述**：在 Playground 页面输入 query，显示检索来源 + LLM 回答。

**前端组件**：
```
┌─────────────────────────────────────────────┐
│  Playground - 单条测试                       │
├─────────────────────────────────────────────┤
│  输入：ccbot 支持哪些渠道接入？              │
│  [执行测试]                                  │
├─────────────────────────────────────────────┤
│  检索结果：                                  │
│  ┌─────────────────────────────────────┐    │
│  │ 1. [来源1] 渠道说明... (0.95)      │    │
│  │ 2. [来源2] 多渠道支持... (0.88)    │    │
│  │ 3. [来源3] 飞书配置... (0.72)      │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  LLM 回答：                                  │
│  ccbot 支持以下渠道接入：                   │
│  - 网页 Widget ✅                            │
│  - 微信公众号 ✅                             │
│  - 企业微信 ✅                               │
│  - 飞书 Bot ✅                               │
│                                             │
│  来源：[doc_001] [doc_002]                  │
├─────────────────────────────────────────────┤
│  评分：准确率 100% | 来源覆盖率 100%         │
└─────────────────────────────────────────────┘
```

**验收测试**：
- [ ] test_playground_display_sources：检索来源正确显示
- [ ] test_playground_highlight_keywords：命中关键词高亮
- [ ] test_playground_llm_response：LLM 回答正常

**质量门禁**：功能测试通过

---

#### T0.5 管理后台评估页面

**功能描述**：管理后台增加「准确率评估」Tab。

**页面功能**：
- 测试集列表（创建/编辑/导入/导出）
- 评估历史记录
- 评估报告详情（指标/趋势/低分问题）
- 知识库健康度仪表盘

**验收测试**：
- [ ] test_admin_evaluation_list：测试集列表正常
- [ ] test_admin_evaluation_report：报告详情正确
- [ ] test_admin_evaluation_export：JSON 导出正常

**质量门禁**：功能测试通过

---

#### T0.6 定时评估任务

**功能描述**：支持每日/每周自动运行测试集，发送报告到邮件/飞书。

**配置项**：
```python
class EvaluationSchedule(Base):
    test_set_id: str
    schedule_type: str  # daily / weekly
    schedule_time: str   # "09:00"
    notification_channels: List[str]  # email / feishu
    quality_gate: dict   # { "min_accuracy": 0.85 }
```

**验收测试**：
- [ ] test_schedule_daily：每日定时触发
- [ ] test_schedule_weekly：每周定时触发
- [ ] test_notification_channels：邮件/飞书通知正常

**质量门禁**：集成测试通过

---

#### T0.7 质量门禁（Quality Gate）

**功能描述**：在 IndexJob 完成前检查准确率，未达标阻止上线。

**工作流程**：
```
知识库更新 → 触发增量索引 → 索引完成 → quality_gate 检查
                                                    ↓
                              准确率 ≥ 阈值？──→ 否 → 阻止上线 + 告警
                                                    ↓ 是
                                              允许上线
```

**API 设计**：
```
POST /api/v1/evaluation/quality_gate
Request: {
    "agent_id": "agt_xxx",
    "pending_changes": ["url_added", "qa_updated"]
}
Response: {
    "passed": true/false,
    "accuracy": 0.87,
    "threshold": 0.85,
    "blocked": false,
    "recommendations": ["建议补充 xxx 相关 Q&A"]
}
```

**验收测试**：
- [ ] test_quality_gate_pass：准确率达标时通过
- [ ] test_quality_gate_block：准确率不达标时阻止
- [ ] test_quality_gate_notification：阻止时发送告警

**质量门禁**：集成测试 + 人工确认

---

#### T0.8 低分回答告警

**功能描述**：retrieval_score < 0.3 时自动记录到审计日志。

**日志格式**：
```json
{
    "timestamp": "2026-05-07T21:00:00Z",
    "event": "low_retrieval_score",
    "agent_id": "agt_xxx",
    "session_id": "sess_xxx",
    "message": "用户问题...",
    "retrieval_score": 0.25,
    "retrieved_docs": [...],
    "llm_response": "..."
}
```

**验收测试**：
- [ ] test_low_score_logging：低分时写入日志
- [ ] test_low_score_threshold：阈值校验

**质量门禁**：功能测试通过

---

#### T0.9 LLM-as-Judge

**功能描述**：用另一个 LLM 评估回答是否有依据。

**Prompt 模板**：
```
你是一个专业的客服质量评估员。请评估以下回答的质量：

问题：{question}
回答：{answer}
参考来源：{sources}

评估维度：
1. 准确性：回答是否正确解决了用户问题？
2. 完整性：回答是否包含所有必要信息？
3. 忠诚度：回答是否仅基于参考来源，没有幻觉？
4. 表达质量：回答是否清晰、易懂？

输出格式（JSON）：
{
    "accuracy": 0.0-1.0,
    "completeness": 0.0-1.0,
    "faithfulness": 0.0-1.0,
    "expression": 0.0-1.0,
    "overall": 0.0-1.0,
    "reasoning": "评估理由...",
    "suggestions": ["改进建议..."]
}
```

**验收测试**：
- [ ] test_llm_judge_consistency：同一回答多次评估结果一致
- [ ] test_llm_judge_correlation：与人工评估结果相关性 ≥ 0.8
- [ ] test_llm_judge_cost：评估成本控制在合理范围

**质量门禁**：人工抽检通过率 ≥ 90%

---

#### T0.10 用户反馈收集

**功能描述**：消息末尾增加「没帮上忙？补充问题」入口。

**前端交互**：
```
┌─────────────────────────────────────────────┐
│  [AI 回答内容...]                            │
│                                             │
│  👍 有帮助    👎 没帮助    💬 补充问题       │
├─────────────────────────────────────────────┤
│  💬 补充问题（展开）                          │
│  ┌─────────────────────────────────────┐    │
│  │ 请描述您的补充问题：                 │    │
│  │ [输入框........................]    │    │
│  │ [提交]                              │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

**验收测试**：
- [ ] test_feedback_buttons_display：正确显示反馈按钮
- [ ] test_feedback_submission：反馈提交成功
- [ ] test_followup_question：补充问题进入下一轮对话

**质量门禁**：功能测试通过

---

#### T0.11 准确率趋势报告

**功能描述**：每周生成准确率趋势报告，发送给运营人员。

**报告内容**：
- 本周准确率趋势图
- 各分类通过率对比
- 低分问题 Top 10
- 知识库缺口建议
- 与上周/上月对比

**验收测试**：
- [ ] test_weekly_report_generation：报告生成正常
- [ ] test_weekly_report_delivery：邮件/飞书发送正常

**质量门禁**：集成测试通过

---

#### T0.12 知识库健康度仪表盘

**功能描述**：管理后台展示检索召回率分布图、低分问题热力图。

**页面组件**：
- 准确率趋势折线图
- 各分类通过率柱状图
- 低分问题列表（可点击查看详情）
- 知识库覆盖率饼图

**验收测试**：
- [ ] test_dashboard_metrics_display：指标正确显示
- [ ] test_dashboard_trend_chart：趋势图渲染正常

**质量门禁**：功能测试通过

---

#### T0.13 导入 160 条测试用例

**功能描述**：将 `openspec/EVAL_TEST_SET.md` 中的 160 条测试用例导入数据库。

**导入脚本**：
```python
async def import_test_set():
    with open("openspec/EVAL_TEST_SET.md") as f:
        content = f.read()
    
    # 解析 JSON 格式的测试用例
    test_cases = parse_test_set(content)
    
    # 批量导入
    for case in test_cases:
        await TestSet.create(**case)
```

**验收测试**：
- [ ] test_import_160_cases：160 条全部导入
- [ ] test_import_deduplication：重复导入不重复
- [ ] test_import_validation：无效数据校验

**质量门禁**：数据库验证通过

---

#### T0.14 测试集管理 API

**功能描述**：支持测试集的导入/导出/版本管理。

**API 设计**：
```
GET    /api/v1/testsets              # 列表
POST   /api/v1/testsets              # 创建
GET    /api/v1/testsets/{id}         # 详情
PUT    /api/v1/testsets/{id}         # 更新
DELETE /api/v1/testsets/{id}         # 删除

POST   /api/v1/testsets/import       # 导入 JSON
GET    /api/v1/testsets/export/{id}  # 导出 JSON
POST   /api/v1/testsets/{id}/clone   # 克隆测试集
```

**验收测试**：
- [ ] test_testsets_crud_full：完整 CRUD
- [ ] test_testsets_import：JSON 导入
- [ ] test_testsets_export：JSON 导出
- [ ] test_testsets_clone：克隆功能

**质量门禁**：API 测试通过

---

#### T0.15 CI/CD 集成

**功能描述**：GitHub Actions 触发评估，未达标阻止合并。

**工作流程**：
```yaml
# .github/workflows/evaluation.yml
name: Accuracy Evaluation

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Evaluation
        run: |
          curl -X POST $API_URL/api/v1/evaluation/run \
            -d '{"test_set_id": "regression_set", "mode": "full"}'
      
      - name: Check Results
        run: |
          if [ $ACCURACY -lt 0.85 ]; then
            echo "Accuracy $ACCURACY < 0.85, blocking merge"
            exit 1
          fi
```

**验收测试**：
- [ ] test_github_actions_trigger：PR 时触发评估
- [ ] test_quality_gate_block_pr：准确率不达标时阻止合并
- [ ] test_regression_set：回归测试集定义

**质量门禁**：E2E 测试通过

---

### 2.5 阶段 0 验收标准

**阶段 0 完成条件**：

| 验收项 | 标准 | 检查方式 |
|--------|------|----------|
| 测试基础设施可用 | T0.1~T0.15 全部完成 | 功能演示 |
| 160 条测试用例入库 | 数据库可查询 | SQL 验证 |
| 评估 API 正常 | /evaluation/run 返回正确结果 | curl 测试 |
| LLM-as-Judge 可用 | 评估结果与人工评估相关性 ≥ 0.8 | 人工抽检 |
| 质量门禁生效 | 准确率不达标时阻止上线 | 集成测试 |
| CI/CD 集成 | PR 时自动触发评估 | GitHub Actions |
| 报告推送 | 邮件/飞书收到定时报告 | 实际接收 |

---

## 三、阶段 1：功能开发

> **⚠️ 阶段 0 完成前不得开始阶段 1。**
> 
> **每个功能模块前必须先定义验收测试。**

### 3.1 TDD 开发流程（阶段 1）

```
功能开发流程：
  1. 读取该功能的验收测试定义
  2. 运行验收测试（预期失败）
  3. 实现功能
  4. 运行验收测试（预期通过）
  5. 优化直到测试通过
  6. Code Review + 测试覆盖率检查
  7. 上线
```

### 3.2 功能模块任务拆解

---

### 3.1 阶段一：文件格式支持总览

> **核心约束：图片/视频是知识库的一等公民，非实时生成，从已有素材提取。**

#### 支持的文件格式

| 格式 | MIME 类型 | 优先级 | 说明 |
|------|-----------|--------|------|
| **TXT** | `text/plain` | 🔴 高 | 纯文本，最基础格式 |
| **HTML** | `text/html` | 🔴 高 | 网页文件，可直接提取正文 |
| **Markdown** | `text/markdown` | 🔴 高 | `.md` 文件，保持结构 |
| **PDF** | `application/pdf` | 🔴 高 | 含文字提取 + 内嵌图片索引 |
| **Word** | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | 🟡 中 | `.docx` 格式，含图片/表格 |
| **Excel** | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | 🟡 中 | `.xlsx` 格式，表格数据 |
| **图片** | `image/jpeg`, `image/png`, `image/gif` | 🟢 低 | 独立图片上传（PDF内嵌图片可复用） |

#### 统一上传 API

```
POST /api/v1/knowledge/upload
Content-Type: multipart/form-data

file: (binary)
agent_id: agt_xxx
file_type: auto  # 或指定：pdf/docx/xlsx/txt/md/image

Response: {
    "document_id": "doc_xxx",
    "status": "parsing" | "chunked" | "indexed",
    "file_type": "pdf",
    "file_name": "report.pdf",
    "chunks_created": 45,
    "images_extracted": 3  # 仅 PDF
}
```

#### 图片索引原则

1. **PDF 内嵌图片**：随 PDF 一起处理，提取后作为独立资源索引
2. **Word 内嵌图片**：随 Word 一起处理，提取后作为独立资源索引
3. **独立图片上传**：直接作为图片资源索引，支持图片问答
4. **图片检索**：从知识库已有图片提取返回，禁止实时生成

#### 任务依赖关系

```
T1.1 文档上传基座（统一上传端点 + 路由分发）
    ├── T1.2 TXT/Markdown 支持
    ├── T1.3 PDF 支持（含图片提取）
    ├── T1.4 Word 支持（含图片/表格）
    ├── T1.5 Excel 支持
    └── T1.6 图片上传支持
```

#### 技术栈配置（已确认，经 RAG 专家评审修正）

**Embedding 模型**：
- 当前：硅基流动（Silicon Flow）`bge-large-zh-v1.5`
- 后续：接入 UniAPI 后统一走 UniAPI
- 向量维度：1024
- 距离算法：Cosine（余弦）

**Qdrant Collection 设计（⚠️ 已修正：单 Collection + Payload 过滤）**：

> **设计变更说明**：原方案按 `agent_id` 分 Collection，经 RAG 专家评审指出存在资源浪费和运维灾难风险。已修正为单 Collection + Payload 过滤方案。

- **Collection 名称**：`ccbot_docs`（单一集合）
- **逻辑隔离**：通过 `payload.agent_id` 字段区分不同 agent 的数据
- **Payload 索引**：对 `agent_id` 建 keyword 索引，查询性能几乎无损
- **扩展优势**：调整向量维度或距离算法只需操作一个 Collection

```python
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType

# 创建单一 Collection
client.create_collection(
    collection_name="ccbot_docs",
    vectors_config=VectorParams(
        size=1024,
        distance=Distance.COSINE,
    ),
)

# 对 agent_id 建 Payload 索引（加速过滤查询）
client.create_payload_index(
    collection_name="ccbot_docs",
    field_name="agent_id",
    field_schema=PayloadSchemaType.KEYWORD,
)

# 写入时带 agent_id
client.upsert(
    collection_name="ccbot_docs",
    points=[{
        "id": chunk_id,
        "vector": embedding,
        "payload": {
            "agent_id": agent_id,
            "doc_id": doc_id,
            "chunk_index": 0,
            "content": "...",
            "content_type": "text",  # or "image", "table"
        }
    }]
)

# 查询时按 agent_id 过滤
from qdrant_client.models import Filter, FieldCondition, MatchValue

client.search(
    collection_name="ccbot_docs",
    query_vector=query_embedding,
    query_filter=Filter(must=[
        FieldCondition(key="agent_id", match=MatchValue(value=agent_id))
    ]),
    limit=5,
)
```

**图片/文件存储路径**：

| 阶段 | 存储方式 | 路径/位置 | 说明 |
|------|-----------|------------|------|
| 阶段一 | 本地文件系统 | `/opt/ccbot/storage/` | 单机部署，定期备份 |
| 阶段二 | MinIO（S3 兼容） | `s3://ccbot-docs/` | 分布式，支持扩容 |

```python
# 阶段一：本地存储
STORAGE_BACKEND = "local"
LOCAL_STORAGE_PATH = "/opt/ccbot/storage"

# 阶段二：迁移到 MinIO
# STORAGE_BACKEND = "minio"
# MINIO_ENDPOINT = "minio.decard.cc"
# MINIO_BUCKET = "ccbot-docs"
```

- Qdrant 只存向量 + 元数据（文件路径/URL），**不存原始二进制文件**
- 图片元数据存入 payload：`{"content_type": "image", "file_path": "/opt/ccbot/storage/images/xxx.jpg", "image_description": "..."}`

**AI 辅助任务模型分配**：

| 任务 | 模型 | 说明 |
|------|------|------|
| TXT AI 分段/提取标题 | DeepSeek-chat | 结构化 JSON 输出 |
| 表格转 Markdown（Excel/Word） | DeepSeek-chat | 需要推理能力 |
| PDF 内嵌图片描述 | — | 阶段一只存图片，描述留阶段二 |
| Text Embedding | bge-large-zh-v1.5（硅基流动） | 中文向量化 |
| RAG 回答生成 | MiniMax（主力）/ DeepSeek（兜底） | 已确认 |

**文本归一化规则**：
```python
NORMALIZATION_RULES = {
    "traditional_to_simplified": True,   # 用 opencc 转换
    "fullwidth_to_halfwidth": True,       # 英文/数字全角转半角
    "punctuation": "preserve",           # 保留原文标点
    "code_blocks": "preserve_as_type",   # 保留并标记 content_type: code
}
```

---

#### T1.1 统一文件上传基座

**功能描述**：构建统一的上传入口，根据文件 MIME 类型自动路由到对应解析器。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_upload_pdf | `sample.pdf` | 路由到 PDF 解析器 | status=parsing |
| test_upload_docx | `sample.docx` | 路由到 Word 解析器 | status=parsing |
| test_upload_xlsx | `data.xlsx` | 路由到 Excel 解析器 | status=parsing |
| test_upload_txt | `readme.txt` | 路由到文本解析器 | status=parsing |
| test_upload_md | `guide.md` | 路由到 Markdown 解析器 | status=parsing |
| test_upload_image | `photo.jpg` | 路由到图片解析器 | status=parsing |
| test_upload_unsupported | `sample.exe` | 返回 400 错误 | error="Unsupported file type" |
| test_upload_large | 50MB PDF | 异步处理 | status=queued |

**任务拆解**：
- [ ] T1.1.1 MIME 类型检测
- [ ] T1.1.2 文件大小限制（默认 50MB）
- [ ] T1.1.3 异步处理队列
- [ ] T1.1.4 统一错误处理

**质量门禁**：8 个验收测试全部通过

---

#### T1.2 TXT/HTML/Markdown 上传

**功能描述**：支持纯文本、HTML 和 Markdown 文件，保持原有结构。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_txt_utf8 | UTF-8 文本 | 正常解析 | content 完整 |
| test_txt_gbk | GBK 编码文本 | 自动转换 | content 正确 |
| test_txt_empty | 空文件 | 返回空 chunks | 不报错 |
| test_md_headers | 带 H1-H6 的 md | 标题层级保留 | metadata.heading_level |
| test_md_code | 带代码块 md | 代码块不丢失 | 格式保留 |
| test_md_link | 带链接 md | 链接保留 | href 不丢失 |
| test_html_parse | 完整 HTML | 提取正文 | 移除 script/style |
| test_html_preserve | 带结构的 HTML | 标题/段落保留 | 结构完整 |

**任务拆解**：
- [ ] T1.2.1 编码自动检测与转换（txt/html/md）
- [ ] T1.2.2 HTML 解析（BeautifulSoup）和正文提取
- [ ] T1.2.3 Markdown 标题层级提取
- [ ] T1.2.4 代码块和链接保留

**质量门禁**：6 个验收测试全部通过

---

#### T1.3 PDF 文档上传

**功能描述**：支持 PDF 文件上传，提取文字内容和内嵌图片。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_pdf_text_extraction | 10页 PDF | 文字提取准确率 ≥ 98% | 与 OCR 对比 |
| test_pdf_page_metadata | 5页 PDF | chunk.metadata.page 正确 | 每页对应 |
| test_pdf_title_extraction | 带书签 PDF | 标题层级正确 | chunk 结构 |
| test_pdf_encoding | 乱码 PDF | 自动修复或报错 | 错误信息友好 |
| test_pdf_corrupted | 损坏 PDF | 返回明确错误 | 不崩溃 |
| test_pdf_image_extract | 含 3 张图片 PDF | 提取 3 张图片 | images_extracted=3 |
| test_pdf_image_index | PDF 内嵌图片 | 图片独立索引 | 可检索 |

**API 设计**：
```
POST /api/v1/knowledge/upload
Content-Type: multipart/form-data

file: (binary)
agent_id: agt_xxx

Response: {
    "document_id": "doc_xxx",
    "status": "indexed",
    "file_type": "pdf",
    "page_count": 10,
    "chunks_created": 45,
    "images_extracted": 3
}
```

**任务拆解**：
- [ ] T1.3.1 集成 pypdf/PyMuPDF 解析
- [ ] T1.3.2 页码元数据保留
- [ ] T1.3.3 内嵌图片提取（pillow）
- [ ] T1.3.4 图片独立索引
- [ ] T1.3.5 加密/损坏 PDF 处理

**质量门禁**：7 个验收测试全部通过

---

#### T1.4 Word/DOCX 上传

**功能描述**：支持 Word 文档上传，保留段落/标题结构和内嵌图片/表格。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_docx_paragraph | sample.docx | 段落结构保留 | chunk 边界正确 |
| test_docx_headings | 多级标题文档 | H1-H4 层级正确 | metadata 完整 |
| test_docx_table | 含表格文档 | 表格行列保留 | 不丢失数据 |
| test_docx_image | 含内嵌图片 | 图片提取成功 | 可独立访问 |
| test_docx_complex | 复杂排版文档 | 内容完整 | 无遗漏 |

**任务拆解**：
- [ ] T1.4.1 集成 python-docx
- [ ] T1.4.2 标题层级保留
- [ ] T1.4.3 表格结构处理
- [ ] T1.4.4 内嵌图片提取
- [ ] T1.4.5 前端上传 UI

**质量门禁**：5 个验收测试全部通过

---

#### T1.5 Excel/XLSX 上传

**功能描述**：支持 Excel 表格上传，提取工作表、行列数据。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_xlsx_single_sheet | 单工作表 | 正确解析 | 数据完整 |
| test_xlsx_multi_sheet | 3 个工作表 | 全部解析 | sheet_names 正确 |
| test_xlsx_formula | 含公式格子 | 公式值而非公式 | 计算结果 |
| test_xlsx_empty | 空工作表 | 空 chunks | 不报错 |
| test_xlsx_mixed | 文本+数字混合 | 类型保留 | 类型正确 |

**任务拆解**：
- [ ] T1.5.1 集成 openpyxl
- [ ] T1.5.2 多工作表处理
- [ ] T1.5.3 表格转文本块

**质量门禁**：5 个验收测试全部通过

---

#### T1.6 图片上传

**功能描述**：支持独立图片上传，作为知识库一等公民独立索引。

> **注意**：此任务可晚于其他文档格式实现，因为 PDF/Word 内嵌图片已可处理。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_image_jpeg | 1MB JPEG | 成功索引 | document_id 返回 |
| test_image_png | PNG 透明图 | 保留透明通道 | alpha 通道不丢失 |
| test_image_gif | GIF 动图 | 首帧提取 | 静态索引 |
| test_image_large | 10MB 图片 | 缩放存储 | 存储 < 5MB |
| test_image_caption | 图片 + alt text | alt text 作为描述 | metadata.caption |

**任务拆解**：
- [ ] T1.6.1 图片格式验证
- [ ] T1.6.2 图片存储优化（压缩/缩放）
- [ ] T1.6.3 图片多模态 embedding
- [ ] T1.6.4 alt text / 文件名作为 caption

**质量门禁**：5 个验收测试全部通过

---

### 3.3 数据清洗

> **阶段一清洗决策（已确认）**：
> 1. PDF 扫描版 OCR：本阶段不支持，标记跳过
> 2. 重复文件检测：基于 content_hash 去重
> 3. 表格处理：转成 Markdown 文本入库
> 4. TXT 文件：尝试用 AI 自动分段和提取标题
> 5. 清洗失败处理：尝试部分提取，并报错

#### T1.7 数据清洗

**功能描述**：清洗上传的文档内容，移除噪音，保留正文；支持重复检测、表格转 Markdown、AI 辅助分段。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_clean_dedup_hash | 相同文件上传2次 | 第二次拒绝或覆盖 | content_hash 一致 |
| test_clean_table_to_md | Word/Excel 含表格 | 表格转 Markdown 入库 | 行列数据不丢失 |
| test_clean_txt_ai_segment | 无结构 TXT 文件 | AI 自动分段 + 提取标题 | 标题置信度 ≥ 70% |
| test_clean_partial_extract | 部分损坏的 PDF | 提取完整页 + 报错提示 | 部分内容入库 |
| test_clean_scan_ocr_skip | 扫描版 PDF | 标记 `needs_ocr=true`，跳过 | 不阻塞其他文件 |
| test_clean_encoding | GBK/UTF-8 混合 | 自动检测并转换 | 乱码率 < 1% |
| test_clean_html_noise | 含 nav/footer 的 HTML | 噪音移除 | 正文完整度 ≥ 95% |

**清洗规则**：
```python
CLEANING_RULES = {
    "dedup": {
        "method": "content_hash_md5",
        "action_on_duplicate": "reject_with_message",  # 或 "overwrite"
    },
    "table": {
        "convert_to": "markdown",
        "preserve_header": True,
        "merge_merged_cells": True,  # Excel 合并单元格展开
        "ai_model": "deepseek-chat",  # 表格理解用 DeepSeek
    },
    "txt_ai_segment": {
        "enabled": True,
        "model": "deepseek-chat",
        "prompt": "请对以下纯文本进行分段，并提取各级标题（如有可能）。输出 JSON：{title: str, sections: [{heading: str, content: str}]}",
    },
    "scan_pdf": {
        "detect_method": "text_layer_length < 50 chars/page",
        "action": "mark_needs_ocr_and_skip",
    },
    "partial_failure": {
        "strategy": "extract_best_effort",
        "report_failed_pages": True,
    },
    "normalization": {
        # 繁简与编码
        "traditional_to_simplified": True,   # 用 opencc 转换
        "fullwidth_to_halfwidth": True,       # 英文/数字全角转半角
        "html_entities": "decode",             # &nbsp;→空格，&lt;→<，&amp;→&
        # 格式与内容
        "whitespace": "collapse",             # 合并连续空白为 1 个空格
        "invisible_chars": "remove",           # 过滤零宽字符/BOM/控制字符
        "punctuation": "preserve",            # 保留原文标点
        "markdown_syntax": "preserve",         # 保留 **bold**、[text](url) 等原始格式
        "code_blocks": "preserve_as_type",    # 保留并标记 content_type: code
        # 日期与公式
        "date": {
            "format": "preserve_original_plus_iso",
            "example": "2024年5月10日 → 2024年5月10日 [DATE:2024-05-10]",
        },
        "formula": {
            "latex": "preserve_as_is",           # 保留 $E=mc^2$ 原文
            "omml": "convert_to_latex_or_preserve_unicode",  # Word 公式对象
            "unicode_math": "preserve",            # 保留 ∫∑√∞ 等数学符号
            "allow_long_chunk": True,              # 公式可略超 max_tokens
        },
    },
}
```

**任务拆解**：
- [ ] T1.7.1 基于 content_hash 的重复文件检测
- [ ] T1.7.2 表格转 Markdown（Word/Excel，AI 模型 deepseek-chat）
- [ ] T1.7.3 TXT 文件 AI 自动分段/提取标题（deepseek-chat）
- [ ] T1.7.4 扫描版 PDF 检测与标记（跳过，W101）
- [ ] T1.7.5 部分提取失败处理（报错 + 入库成功部分，W103）
- [ ] T1.7.6 HTML 噪音移除（nav/footer/aside/script/style）
- [ ] T1.7.7 编码自动检测（chardet）
- [ ] T1.7.8 繁简转换（opencc）
- [ ] T1.7.9 文本归一化（全角→半角、代码块标记）

**质量门禁**：7 个验收测试全部通过

---

#### T1.8 语义切块

> **Chunk 策略（已确认）**：混合策略（方案 D）—— 既按数量分块，又保证语义完整性。

**核心原则**：
- 有结构的文档（MD/Word/PDF 有标题）→ 优先按标题层级切分
- 无结构文档（TXT）→ AI 分段失败则 fallback 到固定 Token
- 表格（Excel/Word 表格）→ 一个表格一个 chunk
- chunk 最小长度 ≥ 50 tokens，不足则合并到上一个 chunk
- Overlap = 动态计算：`chunk_size × (10%~20%)`

** chunk 配置**：
```python
CHUNK_CONFIG = {
    "max_tokens": 512,
    "min_tokens": 50,           # 不足则合并到前一个 chunk
    "overlap_ratio": "dynamic",  # 10-20% of chunk_size
    "overlap_tokens": None,       # 动态计算，设此字段则覆盖
    "respect_heading": True,      # 优先在标题处切分
    "merge_short_chunks": True,
    "table_as_single_chunk": True,# Excel/Word 表格整体作为一个 chunk
    "txt_fallback": "smart_fixed_token", # ⚠️ 已优化：优先在标点/换行符处切分
    "overlap_semantic": True,    # ⚠️ 新增：Overlap 内容保证语义完整
}

# ⚠️ 智能固定 Token 切分（优化版，避免破坏语义）
def smart_fixed_chunk(text: str, max_tokens: int = 512, min_tokens: int = 50):
    """优化版固定Token切分：优先在标点/换行符处切分，保证语义完整"""
    import re
    from roughkness import tokenizer  # 或用 tiktoken
    
    def count_tokens(s):
        return len(tokenizer.encode(s))
    
    tokens = count_tokens(text)
    if tokens <= max_tokens:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # 按句子分割（。！？\n 作为优先切分点）
    # 避免硬切分破坏句子
    sentences = re.split(r'(?<=[。！？\n])', text)
    
    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        current_tokens = count_tokens(current_chunk)
        
        if current_tokens + sentence_tokens <= max_tokens:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk)
    
    # 合并短 chunk（< min_tokens）
    chunks = merge_short_chunks(chunks, min_tokens)
    return chunks

def merge_short_chunks(chunks, min_tokens):
    """将短 chunk 合并到前一个 chunk"""
    if not chunks:
        return chunks
    merged = [chunks[0]]
    for chunk in chunks[1:]:
        if count_tokens(chunk) < min_tokens:
            merged[-1] += chunk  # 合并到前一个
        else:
            merged.append(chunk)
    return merged

def calc_overlap(chunk_size: int, strategy: str = "semantic") -> int:
    """动态计算 overlap，并保证语义完整"""
    ratio = 0.15  # 默认 15%
    raw_overlap = max(50, int(chunk_size * ratio))
    
    if strategy == "semantic":
        # 尝试在句子边界切分 overlap，保证语义完整
        # 取前 raw_overlap 个 token 对应的文本，然后向前/后调整到句子边界
        return raw_overlap  # 实际实现时在 chunk 级别调整
    return raw_overlap
```

**按文档类型的切分策略**：

| 文档类型 | Chunk 策略 | 说明 |
|---------|------------|------|
| Markdown/Word（有标题） | 按 H1/H2 层级 + Token 上限 | H1/H2 为 chunk 边界，超长再分 |
| PDF（有文字层） | 按段落边界 + Token 上限 | pdfplumber 提取段落 |
| HTML | 按 DOM 主内容块（article/main）+ Token 上限 | BeautifulSoup 提取 |
| TXT（无结构） | 先 AI 分段 → 按标题切分；失败则固定 Token | 依赖 T1.7 txt_ai_segment |
| Excel（表格） | 每个 Sheet 一个 chunk（表头 + 所有行） | 表格整体索引，不分拆 |
| PDF/Word 内嵌表格 | 表格单独提取 → 一个表格一个 chunk | 与正文 chunk 分开 |

**动态 Overlap 计算**：
```python
def calc_overlap(chunk_size: int) -> int:
    """动态计算 overlap：chunk_size 的 10-20%"""
    ratio = 0.15  # 默认 15%
    return max(50, int(chunk_size * ratio))
```

**切块元数据**：
```json
{
    "chunk_id": "chunk_xxx",
    "content": "...",
    "token_count": 487,
    "metadata": {
        "source_type": "pdf",
        "file_name": "quality.pdf",
        "title": "产品质量标准",
        "page": 3,
        "chapter": "第三章",
        "heading_level": 2,
        "chunk_index": 1,
        "total_chunks": 12,
        "overlap_prev": 80,
        "overlap_next": 80,
        "warnings": ["W102", "W201"]
    }
}
```

---

**处理警告项代码体系**：

> 所有处理异常（非致命错误）均生成警告代码，存入 `chunk.metadata.warnings[]`，并在前端展示。

| 代码 | 级别 | 说明 | 触发场景 |
|------|------|------|----------|
| **W101** | ⚠️ 警告 | PDF 扫描版，跳过 OCR | `text_layer_length < 50 chars/page`，标记 `needs_ocr=true` |
| **W102** | ⚠️ 警告 | TXT AI 分段失败，已 fallback 到固定 Token 切分 | AI 分段 API 不可用或置信度 < 70% |
| **W103** | ⚠️ 警告 | 部分页面/区块提取失败，已跳过 | PDF/Word 中某些页损坏或无文字 |
| **W104** | ⚠️ 警告 | 编码自动检测置信度低，可能存在乱码 | chardet confidence < 0.7 |
| **W105** | ℹ️ 提示 | 短 chunk 已合并到上一个 chunk | chunk tokens < `min_tokens`（50） |
| **W106** | ℹ️ 提示 | 表格超过单 chunk 上限，已截断 | 表格 token 数 > `max_tokens`（ rare，表格整体为 1 chunk 时可能触发） |
| **W107** | ⚠️ 警告 | 重复文件检测：此文件内容与他人相同 | content_hash 已存在，执行覆盖更新 |
| **W108** | ℹ️ 提示 | 标题层级不完整，chunk 边界可能不准 | AI 分段未识别出 H1-H3 |
| **W109** | ⚠️ 警告 | 图片提取失败（PDF/Word 内嵌图片） | PIL/Pillow 解压失败 |
| **W110** | ℹ️ 提示 | Overlap 动态计算值已应用 | 每次 chunk 时记录实际 overlap 值 |

**警告返回格式**（API Response 中新增 `warnings` 字段）：
```json
{
    "document_id": "doc_xxx",
    "status": "partial_success",   // 全部成功=full_success，部分成功=partial_success，全部失败=failed
    "chunks_created": 45,
    "warnings": [
        {"code": "W102", "level": "warning", "message": "TXT AI分段失败，已使用智能固定Token切分", "detail": "AI API 响应超时，已自动在标点符号处切分"}
    ],
    "errors": [],
    "debug_info": {   // ⚠️ 新增：仅在 debug=true 参数时返回
        "retrieved_doc_ids": ["chunk_001", "chunk_002", "chunk_003"],
        "embedding_time_ms": 120,
        "model_response_time_ms": 850,
        "rerank_scores": [0.92, 0.87, 0.75],
        "chunk_strategy_used": "smart_fixed_token",
        "overlap_actual": 80
    }
}
```

**Debug 模式使用方式**：
```
POST /api/v1/knowledge/upload?debug=true
POST /api/v1/rag/query
{
    "query": "什么是Ccbot？",
    "agent_id": "agent_001",
    "debug": true   // 开启调试模式
}
```

---

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_chunk_heading_boundary | H1-H4 文档 | 标题边界完整率 ≥ 95% | 边界不错位 |
| test_chunk_overlap_dynamic | 512 tokens chunk | overlap = 80 tokens（~15%） | 动态计算正确 |
| test_chunk_merge_short | 含 <50 token 段落的文档 | 短 chunk 合并到前一个 | 无独立短 chunk |
| test_chunk_table_single | Excel/Word 表格 | 一个表格一个 chunk | 表格不拆分成多 chunk |
| test_chunk_txt_fallback | AI 分段失败的 TXT | fallback 固定 Token + W102 警告 | W102 在 warnings 中 |
| test_chunk_metadata_complete | 多来源文档 | metadata 字段完整 | title/page/heading_level 正确 |
| test_chunk_warning_codes | 含扫描页的 PDF | W101 警告代码返回 | warnings[] 含 W101 |
| test_chunk_min_length | min_tokens=50 | 所有 chunk ≥ 50 tokens 或被合并 | 无 <50 token 的独立 chunk |

**任务拆解**：
- [ ] T1.8.1 按标题层级切分（MD/Word/PDF 有结构文档）
- [ ] T1.8.2 固定 Token 切分（TXT fallback + RecursiveCharacterTextSplitter）
- [ ] T1.8.3 动态 Overlap 计算
- [ ] T1.8.4 短 chunk 合并逻辑（min_tokens=50）
- [ ] T1.8.5 表格整体作为一个 chunk（Excel/Word）
- [ ] T1.8.6 警告代码体系实现（W101-W110）
- [ ] T1.8.7 chunk 元数据自动注入

**质量门禁**：8 个验收测试全部通过

---

#### T1.9 混合检索（Hybrid Search）

**功能描述**：结合向量检索和 BM25 关键词检索，提高召回率。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_hybrid_keyword_match | 精确关键词查询 | BM25 命中 | 关键词精确匹配 |
| test_hybrid_semantic | 同义词查询 | 向量检索命中 | 语义相似 |
| test_hybrid_fusion | 混合查询 | RRF 融合结果 | 排序合理 |
| test_hybrid_diversity | 模糊查询 | 结果多样性 | 不全返回同类 |
| test_hybrid_recall | 标准测试集 | 召回率 ≥ 90% | T0.3 指标 |

**混合检索流程**：
```
用户查询
  ├── 向量检索（Dense）→ top-20 结果
  ├── BM25 关键词检索（Sparse）→ top-20 结果
  └── RRF 融合排序
        ↓
    Top-5 结果 → LLM 生成
```

**RRF 算法**：
```python
def reciprocal_rank_fusion(results_list, k=60):
    """RRF 融合排序"""
    scores = defaultdict(float)
    for results in results_list:
        for rank, doc in enumerate(results):
            scores[doc.id] += 1 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: -x[1])
```

**任务拆解**：
- [ ] T1.9.1 集成 rank-bm25
- [ ] T1.9.2 实现 RRF 融合
- [ ] T1.9.3 升级 retrieve() 方法
- [ ] T1.9.4 Playground 展示检索来源

**质量门禁**：5 个验收测试全部通过 + T0.3 召回率 ≥ 90%

---

#### T1.10 增量索引

**功能描述**：只更新变化的文档，不重建整个索引。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_incremental_changed | 3/100 URL 变化 | 仅更新 3 个 | 效率提升 90%+ |
| test_incremental_unchanged | 0 URL 变化 | 无更新操作 | 零开销 |
| test_incremental_etag | ETag 变化 | 检测到变化 | ETag 正确 |
| test_incremental_upsert | 变化文档 | 精确 upsert | 不影响其他 |
| test_incremental_rollback | 更新失败 | 自动回滚 | 数据一致 |

**任务拆解**：
- [ ] T1.10.1 变更检测（etag/last_modified）
- [ ] T1.10.2 增量 upsert 逻辑
- [ ] T1.10.3 统计信息记录
- [ ] T1.10.4 前端更新详情展示

**质量门禁**：5 个验收测试全部通过

---

#### T1.11 答案引用溯源

**功能描述**：增强引用来源展示，标注页码、章节。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_citation_format_web | 网页来源 | 标题 + URL 可点击 | 格式正确 |
| test_citation_format_pdf | PDF 来源 | 文件名 + 页码 | 格式正确 |
| test_citation_format_qa | Q&A 来源 | 显示问题 | 不显示链接 |
| test_citation_rejection | 无相关内容 | "未找到" | 明确拒绝 |
| test_citation_coverage | 标准测试集 | 来源覆盖率 ≥ 95% | T0.3 指标 |

**任务拆解**：
- [ ] T1.11.1 增强 extract_sources()
- [ ] T1.11.2 前端引用展示优化
- [ ] T1.11.3 LLM Prompt 优化
- [ ] T1.11.4 无来源场景处理

**质量门禁**：5 个验收测试全部通过 + T0.3 来源覆盖率 ≥ 95%

---

#### T1.12 计费与用量控制

**功能描述**：基础计费能力，月度用量统计和限制。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_quota_message_increment | 发送消息 | 用量 +1 | 计数准确 |
| test_quota_monthly_reset | 每月 1 日 | 用量重置 | 零点重置 |
| test_quota_limit_exceed | 超配额发送 | HTTP 429 | 友好提示 |
| test_quota_export | 导出请求 | CSV 文件 | 数据完整 |
| test_quota_dashboard | 管理后台 | 图表展示 | 趋势正确 |

**任务拆解**：
- [ ] T1.12.1 数据库迁移脚本
- [ ] T1.12.2 用量异步更新
- [ ] T1.8.3 月度重置任务
- [ ] T1.8.4 前端用量展示

**质量门禁**：5 个验收测试全部通过

---

#### T1.9 数据安全增强

**功能描述**：增强数据隔离和审计日志。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_tenant_isolation | 跨 tenant 请求 | 403 Forbidden | 完全隔离 |
| test_audit_log_delete | 删除操作 | 日志记录 | 可追溯 |
| test_audit_log_config | 配置变更 | 日志记录 | 可追溯 |
| test_confirm_dialog | 危险操作 | 确认弹窗 | 防误删 |

**任务拆解**：
- [ ] T1.9.1 Tenant 校验中间件
- [ ] T1.9.2 审计日志表
- [ ] T1.9.3 前端确认弹窗

**质量门禁**：4 个验收测试全部通过

---
---

#### T1.13 文档生命周期管理（新增）

**功能描述**：文档删除时向量清理、版本管理、垃圾回收。详见 `openspec/DOCUMENT_LIFECYCLE.md`。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_delete_vector_cleanup | 删除含45个chunk的文档 | Qdrant中向量已删除 | chunk_id不存在 |
| test_update_atomic | 更新文档 | 旧向量删除+新向量插入 | 无旧向量残留 |
| test_gc_orphaned | 手动插入孤立向量 | GC任务清理 | 孤立向量删除 |

**任务拆解**：
- [ ] T1.13.1 文档软删除 + 向量清理
- [ ] T1.13.2 文档版本管理 + 回滚
- [ ] T1.13.3 垃圾回收定时任务
- [ ] T1.13.4 删除/更新 API

**质量门禁**：3 个验收测试全部通过

---

#### T1.14 Prometheus 监控埋点（新增）

**功能描述**：API层、RAG核心、下游依赖指标埋点。详见 `openspec/MONITORING_ALERTING.md`。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_metrics_endpoint | 访问 `/metrics` | PromQL格式指标返回 | HTTP 200 |
| test_log_json | 发起API请求 | 日志为合法JSON | 可被Logstash解析 |

**任务拆解**：
- [ ] T1.14.1 API请求/延迟/错误率指标
- [ ] T1.14.2 RAG检索/Embedding/LLM指标  
- [ ] T1.14.3 日志规范实现（JSON + trace_id）
- [ ] T1.14.4 Alertmanager 配置 + 告警规则

**质量门禁**：2 个验收测试全部通过

---

#### T1.15 Grafana 仪表盘（新增）

**功能描述**：可视化仪表盘，展示API性能、RAG指标、LLM用量。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_grafana_dashboard | 查看Grafana | 图表数据正确 | 无空数据 |

**任务拆解**：
- [ ] T1.15.1 Grafana Dashboard 配置
- [ ] T1.15.2 告警渠道对接（钉钉/企微）

**质量门禁**：1 个验收测试全部通过

---

#### T1.16 文件上传安全（新增）

**功能描述**：文件上传三层验证、内容安全审核、向量注入防护。详见 `openspec/SECURITY_BOUNDARY.md`。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_upload_exe | 上传 `malware.exe` | HTTP 400 | 拒绝上传 |
| test_upload_mime_spoof | 修改MIME类型 | HTTP 400 | 检测真实类型 |
| test_vector_injection | 含危险指令的文档 | 内容被清理 | chunk中无危险指令 |

**任务拆解**：
- [ ] T1.16.1 文件上传三层验证（扩展名+MIME+签名）
- [ ] T1.16.2 内容安全审核（文本+图片）
- [ ] T1.16.3 向量注入攻击防护
- [ ] T1.16.4 API 限流与鉴权
- [ ] T1.16.5 安全审计日志

**质量门禁**：3 个验收测试全部通过

---

#### T1.17 Qdrant 运维（新增）

**功能描述**：Qdrant备份恢复、扩容方案、MinIO迁移。详见 `openspec/OPS_MANUAL.md`。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_qdrant_backup | 执行备份脚本 | 快照文件生成 | 文件大小>0 |
| test_qdrant_restore | 从快照恢复 | 数据完整恢复 | 向量数量一致 |
| test_health_check | 执行健康检查 | 所有服务OK | 自动修复触发 |

**任务拆解**：
- [ ] T1.17.1 Qdrant 备份脚本 + 定时任务
- [ ] T1.17.2 Qdrant 恢复流程文档 + 演练
- [ ] T1.17.3 MinIO 迁移方案 + 脚本
- [ ] T1.17.4 健康检查脚本 + 自动修复
- [ ] T1.17.5 运维任务自动化（Cron + 告警）

**质量门禁**：3 个验收测试全部通过

---


### 3.3 阶段 1 验收标准

**阶段 1 完成条件**：

| 功能模块 | 验收测试通过率 | 核心指标达标 |
|----------|---------------|-------------|
| 统一上传基座 | 8/8 | MIME 路由正确 |
| TXT/HTML/MD 上传 | 8/8 | 编码/结构保留 |
| PDF 上传 | 7/7 | 文字准确率 ≥ 98%，图片提取 |
| Word 上传 | 5/5 | 段落/表格/图片保留 |
| Excel 上传 | 5/5 | 多 Sheet 正确解析 |
| 图片上传 | 5/5 | 格式/缩放正确 |
| 数据清洗 | 7/7 | 去重/表格转MD/AI分段 |
| 语义切块 | 9/9 | 边界完整率 ≥ 95%，智能切分 |
| 混合检索 | 5/5 | 召回率 ≥ 90% |
| 增量索引 | 5/5 | 效率提升 ≥ 90% |
| 引用溯源 | 5/5 | 来源覆盖率 ≥ 95% |
| 计费控制 | 5/5 | 计数准确率 100% |
| 安全增强 | 4/4 | 隔离性 100% |

**综合准确率**：≥ 85%（由 T0.3 评估确认）
**拒答测试通过率**：≥ 80%（新增，测试集含 10-20 条无关问题）

---

## 四、阶段 2：多模态输入

> **前提：阶段 1 完成，文字问答准确率 ≥ 85%**
> 
> **⚠️ 每个功能前先定义验收测试。**

### 4.1 测试集扩展

#### 待生成的测试集

| 测试集 | 条数 | 格式 |
|--------|------|------|
| 语音输入 | 30 | 音频文件 + 文本标注 |
| 图片输入 | 20 | 图片文件 + 描述标注 |
| 视频输入 | 10 | 视频文件 + 关键信息标注 |

**语音测试集规范**：
```
{
    "id": "voice_001",
    "audio_url": "/test_data/voice/capital_cities.mp3",
    "transcript": "中国的首都是哪里？",
    "expected_keywords": ["北京", "首都"],
    "language": "mandarin",
    "has_noise": false,
    "duration_seconds": 5
}
```

**图片测试集规范**：
```
{
    "id": "image_001",
    "image_url": "/test_data/images/printer_error.jpg",
    "description": "打印机显示 E005 错误代码",
    "expected_keywords": ["E005", "卡纸", "清除"],
    "image_type": "screenshot"
}
```

### 4.2 新增评估指标

| 指标 | 目标值 | 验收方式 |
|------|--------|----------|
| ASR 准确率 | ≥ 90% | 语音转文字与原文对比 |
| 图片理解准确率 | ≥ 85% | 图片描述与预期对比 |
| 视频关键帧召回率 | ≥ 80% | 关键信息提取准确率 |

### 4.3 功能模块

#### T2.1 语音输入（ASR）

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_asr_mandarin | 普通话录音 | 转文字准确率 ≥ 90% | 字错误率 < 10% |
| test_asr_noise | 带噪音录音 | 噪音不影响理解 | 关键词准确 |
| test_asr_long | 60秒录音 | 完整转写 | 不截断 |
| test_asr_realtime | 实时录音 | 延迟 < 2秒 | 端到端延迟 |
| test_asr_format | 多格式音频 | 自动转换 | MP3/WAV/M4A |

#### T2.2 图片理解

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_image_product | 产品实物图 | 正确描述 | 关键特征准确 |
| test_image_screenshot | 软件截图 | 正确理解 UI | 按钮/菜单正确 |
| test_image_blur | 模糊照片 | 降级处理或明确告知 | 错误提示友好 |
| test_image_with_text | 含文字图片 | 文字正确识别 | OCR 准确率 ≥ 90% |
| test_image_multimodal | 图片 + 文字问题 | 联合理解 | 上下文关联 |

#### T2.3 视频理解

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_video_keyframe | 操作演示视频 | 关键帧提取 | 5分钟视频提取10-20帧 |
| test_video_transcript | 含音频视频 | ASR 转写 | 准确率 ≥ 85% |
| test_video_timestamp | 故障排查视频 | 时间戳映射 | 关键内容定位准确 |
| test_video_large | 100MB+ 视频 | 异步处理 | 不阻塞，有进度 |

#### T2.4 渠道适配

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_channel_wechat_voice | 公众号语音 | 转文字 → 回答 | 流畅无阻塞 |
| test_channel_feishu_image | 飞书图片 | 理解 → 回答 | 图片正确显示 |
| test_channel_adaptation | 统一消息格式 | 各渠道正确渲染 | 格式一致 |

---

## 五、阶段 3：多媒体检索与返回

> **前提：阶段 2 完成，多模态输入稳定**
> 
> **⚠️ 每个功能前先定义验收测试。**

### 5.1 测试集扩展

| 测试集 | 条数 | 格式 |
|--------|------|------|
| 图片检索 | 20 | 图片 URL + 预期召回来源 |
| 视频检索 | 15 | 视频 URL + 关键时间戳 |

### 5.2 新增评估指标

| 指标 | 目标值 | 验收方式 |
|------|--------|----------|
| 图片检索命中率 | ≥ 80% | 召回相关图片 |
| 视频检索命中率 | ≥ 75% | 召回相关视频 |
| 多媒体引用准确率 | ≥ 85% | 引用的多媒体确实相关 |
| 视频时间戳准确率 | ≥ 90% | 时间戳误差 < 5秒 |

### 5.3 功能模块

#### T3.1 消息结构升级

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_content_blocks_text | 纯文字回复 | content_blocks 正确 | 渲染正常 |
| test_content_blocks_image | 含图片回复 | 图片正确显示 | 缩略图 + 放大 |
| test_content_blocks_video | 含视频回复 | 视频正确播放 | 时间戳正确 |
| test_content_blocks_mixed | 混合回复 | 各类型正确渲染 | 顺序正确 |
| test_content_blocks_backward | 旧格式数据 | 兼容转换 | 正常显示 |

#### T3.2 资料库多媒体索引

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_multimodal_index_image | PDF 内嵌图片 | 独立索引 | 多模态 embedding |
| test_multimodal_index_video | 上传视频 | 关键帧 + 描述索引 | 时间戳映射 |
| test_multimodal_retrieval | 图片检索请求 | 召回相关图片 | 命中率 ≥ 80% |
| test_multimodal_citation | 回答引用图片 | 正确展示来源 | 来源可点击 |

#### T3.3 视频片段精确返回

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_video_timestamp_extraction | 视频索引 | 时间戳映射表 | 关键内容覆盖 |
| test_video_timestamp_retrieval | 检索命中 | 返回时间戳区间 | 误差 < 5秒 |
| test_video_player_integration | 时间戳引用 | 播放器跳转 | 从指定位置播放 |

---

## 六、跨阶段公共能力

### C.1 监控与可观测性

**任务拆解**：

| 任务 | 描述 | 验收标准 |
|------|------|----------|
| C.1.1 | Prometheus metrics 埋点 | 请求数/延迟/Token 消耗 |
| C.1.2 | 消息反馈字段 | 👍/👎 统计 |
| C.1.3 | 反馈 UI | 按钮正确显示 |
| C.1.4 | 低分告警 | retrieval_score < 0.3 |
| C.1.5 | 质量仪表盘 | 指标可视化 |

### C.2 成本优化

**任务拆解**：

| 任务 | 描述 | 验收标准 |
|------|------|----------|
| C.2.1 | Embedding Redis 缓存 | 相同 query 缓存命中 |
| C.2.2 | 低置信度降级 | 用便宜模型回答"未找到" |
| C.2.3 | 知识库大小限制 | 超限时阻止上传 |

### C.3 用户反馈优化闭环

```
用户反馈（👍/👎）
      ↓
低分回答聚类分析
      ↓
发现知识库缺口 → 补充 Q&A / 文档
      ↓
发现切块问题 → 优化切块策略
      ↓
重新评估验证
      ↓
指标提升 → 继续监控
```

---

## 七、测试数据集概览

| 测试集 | 分类 | 条数 | 所在文件 | 状态 |
|--------|------|------|----------|------|
| **阶段 0** 回归测试集 | 历史错误案例 | 50+ | 待定义 | ❌ 待定义 |
| **阶段 1** 文字问答 | 平台功能/技术问题等 | 160 | `EVAL_TEST_SET.md` | ✅ 已生成 |
| **阶段 2** 语音输入 | 普通话/方言/噪音 | 30 | 待生成 | ❌ 待生成 |
| **阶段 2** 图片输入 | 实物/截图/模糊 | 20 | 待生成 | ❌ 待生成 |
| **阶段 2** 视频输入 | 操作演示/故障 | 10 | 待生成 | ❌ 待生成 |
| **阶段 3** 图片检索 | 产品外观/尺寸 | 20 | 待生成 | ❌ 待生成 |
| **阶段 3** 视频检索 | 操作演示/维修 | 15 | 待生成 | ❌ 待生成 |
| **合计** | | **305+** | | 1/7 |

---

## 八、任务优先级总览

### 阶段 0（TDD 基础设施）— 最高优先级

```
P0: T0.1 → T0.2 → T0.3 → T0.13 → T0.14 → T0.9 → T0.7 → T0.15
P1: T0.4 → T0.5 → T0.6 → T0.10 → T0.11 → T0.12 → T0.8
```

### 阶段 1（功能开发）— 第二优先级

> ⚠️ 必须阶段 0 完成后开始
> ⚠️ 每个功能前先定义验收测试

```
P0: T1.3（清洗）→ T1.4（切块）→ T1.5（检索）
P1: T1.1（PDF）→ T1.2（Word）→ T1.6（增量）→ T1.7（引用）
P2: T1.8（计费）→ T1.9（安全）
```

### 阶段 2（多模态输入）

> ⚠️ 阶段 1 完成且准确率 ≥ 85%

```
P0: T2.0（测试集）→ T2.1（ASR）→ T2.2（图片）
P1: T2.4（渠道适配）
P2: T2.3（视频）
```

### 阶段 3（多媒体检索）

> ⚠️ 阶段 2 完成

```
P0: T3.0（测试集）→ T3.1（消息结构）→ T3.2（索引）
P2: T3.3（视频时间戳）
```

---

## 附录：TDD 检查清单

### 开发前检查

- [ ] 该功能的验收测试已定义
- [ ] 验收测试已加入测试套件
- [ ] 运行验收测试（预期失败）

### 开发后检查

- [ ] 验收测试全部通过
- [ ] 代码覆盖率 ≥ 80%
- [ ] Code Review 通过
- [ ] 文档已更新
- [ ] 回归测试集通过

### 上线前检查

- [ ] 质量门禁通过（准确率 ≥ 阈值）
- [ ] 集成测试通过
- [ ] 人工验收通过

---

*本文档基于 ccbot 项目现状（2026-05）评估生成，按 TDD 原则重构。*

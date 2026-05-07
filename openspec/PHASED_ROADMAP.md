# Ccbot 智能体平台 — 分阶段任务拆解与功能描述

> **核心原则：好的系统是测试出来的，不是开发出来的。**
> 
> 每个功能模块的开发，必须从定义该功能的验收测试开始。
> 测试基础设施是一切开发的前提，在验证体系未建立前，不得开发其他功能。
> 
> 生成时间：2026-05-07
> 最后更新：2026-05-07（TDD 原则重构）

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

| 指标 | 定义 | 目标值 | 验收方式 |
|------|------|--------|----------|
| **回答准确率** | 评估回答是否正确解决用户问题 | ≥ 85% | LLM-as-Judge + 人工抽检 |
| **来源覆盖率** | 有来源标注的回答占比 | ≥ 95% | 自动统计 |
| **检索召回率** | 正确答案在 Top-5 检索结果中的比例 | ≥ 90% | 自动计算 |
| **无答案率** | 知识库无相关内容时的正确拒绝率 | ≥ 80% | 自动化测试 |
| **首轮解决率** | 用户无需追问即可得到满意回答的比例 | ≥ 70% | 用户反馈统计 |
| **用户满意度** | 消息末尾 👍 占比 | ≥ 75% | 用户反馈统计 |

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

#### T1.1 PDF 文档上传

**功能描述**：支持 PDF 文件上传，自动解析文字内容进入知识库。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_pdf_text_extraction | sample.pdf（10页，含文字/图片） | 文字提取准确率 ≥ 98% | 与 OCR 结果对比 |
| test_pdf_page_metadata | sample.pdf（5页） | chunk.metadata.page 正确 | 检查数据库 |
| test_pdf_title_extraction | 带书签的 PDF | 标题层级正确 | 检查 chunk 结构 |
| test_pdf_encoding | 乱码 PDF | 自动修复或明确报错 | 错误信息友好 |
| test_pdf_corrupted | 损坏 PDF | 返回明确错误 | 不崩溃 |

**API 设计**：
```
POST /api/v1/knowledge/upload
Content-Type: multipart/form-data

file: (binary)
agent_id: agt_xxx

Response: {
    "document_id": "doc_xxx",
    "status": "parsing" | "chunked" | "indexed",
    "page_count": 10,
    "chunks_created": 45
}
```

**任务拆解**：
- [ ] T1.1.1 实现文件上传端点
- [ ] T1.1.2 集成 pypdf 解析
- [ ] T1.1.3 保留页码元数据
- [ ] T1.1.4 错误处理（损坏/加密）
- [ ] T1.1.5 前端上传 UI + 进度条

**质量门禁**：5 个验收测试全部通过

---

#### T1.2 Word/DOCX 上传

**功能描述**：支持 Word 文档上传，保留段落/标题结构。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_docx_paragraph | sample.docx | 段落结构保留 | 检查 chunk 边界 |
| test_docx_headings | 带多级标题文档 | H1-H4 层级正确 | 检查 metadata |
| test_docx_table | 含表格文档 | 表格结构保留 | 不丢失行列 |
| test_docx_image | 含内嵌图片 | 图片提取成功 | 图片可访问 |

**任务拆解**：
- [ ] T1.2.1 集成 python-docx
- [ ] T1.2.2 保留标题层级
- [ ] T1.2.3 表格结构处理
- [ ] T1.2.4 前端上传 UI

**质量门禁**：4 个验收测试全部通过

---

#### T1.3 数据清洗

**功能描述**：清洗爬取的网页内容，移除噪音，保留正文。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_clean_nav_removal | 含导航栏 HTML | 导航栏已移除 | 清洗后无 nav/menu |
| test_clean_footer_removal | 含页脚 HTML | 页脚已移除 | 清洗后无 footer |
| test_clean_dedup | 同一 URL 重复爬取 | 不重复索引 | content_hash 对比 |
| test_clean_encoding | 非 UTF-8 内容 | 自动修复或标记 | 乱码率 < 1% |
| test_clean_metadata | 结构化 HTML | title/content 分离 | metadata 完整 |

**清洗规则**：
```python
CLEANING_RULES = {
    "remove_tags": ["nav", "footer", "header", "aside", "script", "style", "iframe"],
    "remove_selectors": [".nav", ".menu", ".sidebar", ".ad", ".advertisement"],
    "preserve_tags": ["main", "article", "section", "p", "h1", "h2", "h3", "ul", "ol", "table"],
}
```

**任务拆解**：
- [ ] T1.3.1 基于 DOM 结构过滤
- [ ] T1.3.2 content_hash 去重
- [ ] T1.3.3 编码自动修复
- [ ] T1.3.4 预览清洗结果 API

**质量门禁**：5 个验收测试全部通过

---

#### T1.4 语义切块

**功能描述**：按标题层级和语义边界切分文档，提高检索准确率。

**验收测试（先定义）**：

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_chunk_heading_boundary | H1-H4 文档 | 标题边界完整率 ≥ 95% | 边界不错位 |
| test_chunk_overlap | 500 tokens 切块 | 上下文重叠 10-20% | 重叠合理 |
| test_chunk_metadata | 多来源文档 | title/url/page 完整 | metadata 正确 |
| test_chunk_semantic | 语义边界明确的文档 | 不跨语义主题 | 主题内聚 |
| test_chunk_size_config | 不同大小配置 | 切块大小符合配置 | 配置生效 |

**切块元数据**：
```json
{
    "chunk_id": "chunk_xxx",
    "content": "...",
    "metadata": {
        "source_type": "pdf",
        "title": "产品质量标准",
        "url_or_filename": "/docs/quality.pdf",
        "page": 3,
        "chapter": "第三章",
        "chunk_index": 1,
        "total_chunks": 12
    }
}
```

**任务拆解**：
- [ ] T1.4.1 基于标题层级切块
- [ ] T1.4.2 RecursiveCharacterTextSplitter
- [ ] T1.4.3 元数据自动注入
- [ ] T1.4.4 切块大小可配置

**质量门禁**：5 个验收测试全部通过

---

#### T1.5 混合检索（Hybrid Search）

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
- [ ] T1.5.1 集成 rank-bm25
- [ ] T1.5.2 实现 RRF 融合
- [ ] T1.5.3 升级 retrieve() 方法
- [ ] T1.5.4 Playground 展示检索来源

**质量门禁**：5 个验收测试全部通过 + T0.3 召回率 ≥ 90%

---

#### T1.6 增量索引

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
- [ ] T1.6.1 变更检测（etag/last_modified）
- [ ] T1.6.2 增量 upsert 逻辑
- [ ] T1.6.3 统计信息记录
- [ ] T1.6.4 前端更新详情展示

**质量门禁**：5 个验收测试全部通过

---

#### T1.7 答案引用溯源

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
- [ ] T1.7.1 增强 extract_sources()
- [ ] T1.7.2 前端引用展示优化
- [ ] T1.7.3 LLM Prompt 优化
- [ ] T1.7.4 无来源场景处理

**质量门禁**：5 个验收测试全部通过 + T0.3 来源覆盖率 ≥ 95%

---

#### T1.8 计费与用量控制

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
- [ ] T1.8.1 数据库迁移脚本
- [ ] T1.8.2 用量异步更新
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

### 3.3 阶段 1 验收标准

**阶段 1 完成条件**：

| 功能模块 | 验收测试通过率 | 核心指标达标 |
|----------|---------------|-------------|
| PDF 上传 | 5/5 | 准确率 ≥ 98% |
| Word 上传 | 4/4 | 段落结构保留 |
| 数据清洗 | 5/5 | 噪音移除率 ≥ 95% |
| 语义切块 | 5/5 | 边界完整率 ≥ 95% |
| 混合检索 | 5/5 | 召回率 ≥ 90% |
| 增量索引 | 5/5 | 效率提升 ≥ 90% |
| 引用溯源 | 5/5 | 来源覆盖率 ≥ 95% |
| 计费控制 | 5/5 | 计数准确率 100% |
| 安全增强 | 4/4 | 隔离性 100% |

**综合准确率**：≥ 85%（由 T0.3 评估确认）

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

# Ccbot 智能体平台 — 文档生命周期管理设计

> 补充阶段一遗漏：文档删除/更新时向量同步策略
> 生成时间：2026-05-10

---

## 一、核心问题

### 1.1 问题背景

当前方案定义了文档上传、解析、切块、入库流程，但**缺少文档删除和更新时的向量清理机制**。

```
当前流程（缺失部分）：
  上传文档 → 解析 → 切块 → Qdrant upsert → 完成
                   ↓
  删除文档 → ???（向量未清理）
  更新文档 → ???（旧向量未删除）
```

### 1.2 风险分析

| 风险场景 | 影响 |
|----------|------|
| 删除文档后向量残留 | 用户隐私泄露（旧数据仍可被检索到） |
| 更新文档旧向量未删 | 回答引用过期内容，误导用户 |
| 大量更新后向量膨胀 | Qdrant存储浪费，检索性能下降 |

---

## 二、文档生命周期状态机

### 2.1 状态定义

```python
class DocumentStatus(str, Enum):
    """文档生命周期状态"""
    UPLOADING = "uploading"        # 上传中
    PARSING = "parsing"            # 解析中
    CHUNKING = "chunking"          # 切块中
    INDEXING = "indexing"          # 索引中
    ACTIVE = "active"              # 活跃（可检索）
    UPDATING = "updating"          # 更新中
    DELETING = "deleting"          # 删除中
    DELETED = "deleted"           # 已删除（软删除）
    ARCHIVED = "archived"          # 归档
```

### 2.2 状态转换图

```
                    ┌─────────────────────────────────────────────┐
                    │                                             │
                    ▼                                             │
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│UPLOADING│───▶│ PARSING │───▶│CHUNKING │───▶│INDEXING │───▶│ ACTIVE  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                          │     │
                                                          │     │
                              ┌───────────┐               │     │  ┌─────────┐
                              │ DELETING  │◀──────────────┘     └──▶│UPDATING │
                              └───────────┘                      └─────────┘
                                   │                                   │
                                   ▼                                   │
                              ┌─────────┐                              │
                              │ DELETED │◀─────────────────────────────┘
                              └─────────┘     （用户恢复/系统清理）
                                   │
                                   ▼
                              ┌─────────┐
                              │ARCHIVED │（定时清理）
                              └─────────┘
```

---

## 三、删除机制设计

### 3.1 软删除 + 异步清理

```python
# 文档删除流程
async def delete_document(agent_id: str, doc_id: str):
    """
    文档删除：软删除 + 异步向量清理
    """
    # 1. 软删除文档记录
    await Document.update(
        doc_id,
        status=DocumentStatus.DELETING,
        deleted_at=datetime.utcnow()
    )

    # 2. 获取该文档关联的所有 chunk_id
    chunks = await Chunk.query(doc_id=doc_id).all()
    chunk_ids = [c.chunk_id for c in chunks]

    # 3. 异步删除 Qdrant 向量
    await asyncio.create_task(
        qdrant_delete_vectors(agent_id, chunk_ids)
    )

    # 4. 标记文档为已删除
    await Document.update(
        doc_id,
        status=DocumentStatus.DELETED
    )

    # 5. 清理文件存储（可选：保留N天供恢复）
    await schedule_file_cleanup(doc_id, retention_days=7)
```

### 3.2 Qdrant 向量删除

```python
async def qdrant_delete_vectors(agent_id: str, chunk_ids: List[str]):
    """
    删除 Qdrant 中的向量记录
    """
    from qdrant_client.models import Filter, FieldCondition, MatchAny

    # 方法1：按 ID 删除（推荐，精确）
    client.delete(
        collection_name="ccbot_docs",
        points_selector=PointIdsList(
            points=chunk_ids
        ),
        wait=True  # 等待删除完成
    )

    # 方法2：按 Payload 条件删除（备选）
    # 删除属于某文档的所有向量
    client.delete(
        collection_name="ccbot_docs",
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(key="agent_id", match=MatchValue(value=agent_id)),
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id))
                ]
            )
        ),
        wait=True
    )
```

### 3.3 删除确认 API

```
DELETE /api/v1/knowledge/documents/{doc_id}

Response:
{
    "doc_id": "doc_xxx",
    "status": "deleting",
    "chunks_to_delete": 45,
    "estimated_completion": "2026-05-10T22:05:00Z"
}

# 查询删除状态
GET /api/v1/knowledge/documents/{doc_id}/deletion-status

Response:
{
    "doc_id": "doc_xxx",
    "status": "deleted",
    "vectors_deleted": 45,
    "deleted_at": "2026-05-10T22:04:32Z"
}
```

---

## 四、更新机制设计

### 4.1 更新策略：原子性替换

```python
async def update_document(agent_id: str, doc_id: str, new_file: UploadFile):
    """
    文档更新：原子性替换（删除旧版 + 插入新版）
    """
    # 1. 标记文档为更新中
    await Document.update(doc_id, status=DocumentStatus.UPDATING)

    # 2. 删除旧版向量（保留旧版记录用于回滚）
    old_chunks = await Chunk.query(doc_id=doc_id).all()
    old_chunk_ids = [c.chunk_id for c in old_chunks]
    await qdrant_delete_vectors(agent_id, old_chunk_ids)

    # 3. 保存旧版元数据（用于回滚）
    old_version = await Document.get(doc_id)
    await DocumentVersion.create(
        doc_id=doc_id,
        version=old_version.version,
        metadata=old_version.to_dict(),
        chunks=old_chunks,
        created_at=datetime.utcnow()
    )

    # 4. 解析新版本
    new_chunks = await parse_and_chunk(new_file)

    # 5. 写入新版向量
    await qdrant_upsert_vectors(agent_id, doc_id, new_chunks)

    # 6. 更新文档记录
    await Document.update(
        doc_id,
        version=old_version.version + 1,
        status=DocumentStatus.ACTIVE,
        updated_at=datetime.utcnow()
    )

    # 7. 清理旧版本记录（保留最近N个版本）
    await cleanup_old_versions(doc_id, keep_versions=3)
```

### 4.2 回滚机制

```python
async def rollback_document(doc_id: str, target_version: int):
    """
    回滚到指定版本
    """
    version_record = await DocumentVersion.get(doc_id, version=target_version)

    # 删除当前版本向量
    current_chunks = await Chunk.query(doc_id=doc_id).all()
    await qdrant_delete_vectors(agent_id, [c.chunk_id for c in current_chunks])

    # 恢复旧版本向量
    await qdrant_upsert_vectors(
        agent_id,
        doc_id,
        version_record.chunks,
        version=target_version
    )

    # 更新文档记录
    await Document.update(
        doc_id,
        version=target_version,
        status=DocumentStatus.ACTIVE
    )
```

---

## 五、版本管理设计

### 5.1 数据库表结构

```sql
-- 文档表
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER,
    content_hash TEXT,  -- MD5，用于去重检测
    version INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,

    -- 软删除支持
    is_deleted BOOLEAN DEFAULT FALSE,

    -- 索引
    INDEX idx_agent_id (agent_id),
    INDEX idx_status (status),
    INDEX idx_content_hash (content_hash)
);

-- 文档版本历史表
CREATE TABLE document_versions (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    metadata JSON,           -- 文档元数据快照
    chunk_count INTEGER,
    file_snapshot_path TEXT, -- 旧版本文件快照路径
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(doc_id, version),
    INDEX idx_doc_id (doc_id)
);

-- chunk 表
CREATE TABLE document_chunks (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_doc_id (doc_id),
    INDEX idx_doc_chunk (doc_id, chunk_index)
);
```

### 5.2 版本查询 API

```
GET /api/v1/knowledge/documents/{doc_id}/versions

Response:
{
    "doc_id": "doc_xxx",
    "current_version": 3,
    "versions": [
        {"version": 1, "created_at": "2026-05-01T10:00:00Z", "chunks": 45},
        {"version": 2, "created_at": "2026-05-05T14:30:00Z", "chunks": 52},
        {"version": 3, "created_at": "2026-05-10T09:15:00Z", "chunks": 48}
    ]
}
```

---

## 六、垃圾回收设计

### 6.1 定时清理任务

```python
# 垃圾回收：清理孤立向量和过期版本
class GarbageCollector:
    """文档生命周期垃圾回收器"""

    def __init__(self, qdrant_client, db_session):
        self.qdrant = qdrant_client
        self.db = db_session

    async def cleanup_orphaned_vectors(self):
        """清理孤立的 Qdrant 向量（数据库中已删除但向量库中仍存在）"""

        # 1. 获取数据库中所有活跃 chunk_id
        db_chunk_ids = set(
            row.chunk_id
            for row in await self.db.query(Chunk).all()
        )

        # 2. 获取 Qdrant 中所有向量 ID
        qdrant_ids = set(
            point.id
            async for point in self.qdrant.scroll("ccbot_docs", limit=10000)
        )

        # 3. 计算孤立向量
        orphaned_ids = qdrant_ids - db_chunk_ids

        # 4. 删除孤立向量（分批，每批1000）
        for batch in chunked(orphaned_ids, 1000):
            await self.qdrant.delete(
                "ccbot_docs",
                points=batch
            )
            logger.info(f"Deleted {len(batch)} orphaned vectors")

    async def cleanup_old_versions(self, max_versions: int = 3):
        """清理旧版本记录"""

        # 保留每个文档最近 N 个版本
        result = await self.db.execute("""
            DELETE FROM document_versions
            WHERE id IN (
                SELECT id FROM document_versions dv
                WHERE (
                    SELECT COUNT(*) FROM document_versions dv2
                    WHERE dv2.doc_id = dv.doc_id
                    AND dv2.version >= dv.version
                ) > :max_versions
            )
        """, {"max_versions": max_versions})

        logger.info(f"Cleaned up {result.rowcount} old version records")

    async def cleanup_deleted_files(self, retention_days: int = 7):
        """清理已删除文档的文件存储"""

        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        deleted_docs = await self.db.query(Document).filter(
            Document.is_deleted == True,
            Document.deleted_at < cutoff_date
        ).all()

        for doc in deleted_docs:
            # 删除物理文件
            await delete_file(doc.file_path)
            # 删除版本快照
            await delete_directory(f"/storage/versions/{doc.id}")

            await self.db.delete(doc)

        logger.info(f"Cleaned up {len(deleted_docs)} deleted documents")
```

### 6.2 定时任务配置

```python
# 垃圾回收调度
SCHEDULE_CONFIG = {
    "cleanup_orphaned_vectors": {
        "interval": "daily",  # 每天执行
        "time": "03:00",      # 凌晨3点
    },
    "cleanup_old_versions": {
        "interval": "weekly", # 每周执行
        "day": "Sunday",
        "time": "04:00",
    },
    "cleanup_deleted_files": {
        "interval": "daily",
        "time": "05:00",
        "retention_days": 7,  # 删除7天前的文件
    }
}
```

---

## 七、验收测试

### 7.1 删除流程测试

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_delete_document_vector_cleanup | 删除含45个chunk的文档 | Qdrant中向量已删除 | chunk_id不存在 |
| test_delete_document_soft_delete | 删除文档 | documents表is_deleted=True | 可恢复 |
| test_delete_document_concurrent | 并发删除同一文档 | 仅执行一次删除 | 不报错 |
| test_delete_large_document | 删除含500个chunk的文档 | 批量删除完成 | 不超时 |

### 7.2 更新流程测试

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_update_document_atomic | 更新文档 | 旧向量删除+新向量插入 | 无旧向量残留 |
| test_update_document_rollback | 更新后回滚 | 恢复到指定版本 | 内容一致 |
| test_update_document_version_increment | 更新文档3次 | 版本为1→2→3 | 版本递增 |
| test_update_large_document | 更新大文档（500页PDF） | 异步处理完成 | 不阻塞 |

### 7.3 垃圾回收测试

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_gc_orphaned_vectors | 手动插入孤立向量 | GC任务清理 | 孤立向量删除 |
| test_gc_old_versions | 保留3个版本 | GC后只保留3个 | 多余版本删除 |
| test_gc_deleted_files | 删除7天前文档 | 文件物理删除 | 存储释放 |

---

## 八、T1.X 任务归属

将文档生命周期管理作为阶段一补充任务：

| 任务ID | 描述 | 优先级 |
|--------|------|--------|
| T1.13 | 文档软删除 + 向量清理 | P0 |
| T1.14 | 文档版本管理 + 回滚 | P1 |
| T1.15 | 垃圾回收定时任务 | P2 |
| T1.16 | 删除/更新 API | P0 |

---

*本文档补充 PHASED_ROADMAP.md 遗漏的文档生命周期管理设计。*

# Ccbot 智能体平台 — 安全边界设计

> 补充阶段一遗漏：文件上传限制、安全审核、向量注入防护
> 生成时间：2026-05-10

---

## 一、安全设计原则

1. **零信任原则**：所有上传文件必须验证，不信任客户端传来的 MIME 类型
2. **最小权限原则**：文件处理服务仅能访问指定目录
3. **纵深防御**：多层验证（扩展名 + MIME + 内容签名 + 病毒扫描）
4. **可审计性**：所有安全事件必须记录并可追溯

---

## 二、文件上传安全设计

### 2.1 文件类型白名单

```python
# 允许上传的文件类型（严格白名单）
ALLOWED_FILE_TYPES = {
    "text/plain": {
        "extensions": [".txt"],
        "max_size_mb": 10,
        "security_check": "text_only"
    },
    "text/html": {
        "extensions": [".html", ".htm"],
        "max_size_mb": 20,
        "security_check": "html_sanitize"
    },
    "text/markdown": {
        "extensions": [".md"],
        "max_size_mb": 20,
        "security_check": "text_only"
    },
    "application/pdf": {
        "extensions": [".pdf"],
        "max_size_mb": 50,
        "security_check": "pdf_validate"
    },
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
        "extensions": [".docx"],
        "max_size_mb": 50,
        "security_check": "offic_validate"
    },
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
        "extensions": [".xlsx"],
        "max_size_mb": 50,
        "security_check": "offic_validate"
    },
    "image/jpeg": {
        "extensions": [".jpg", ".jpeg"],
        "max_size_mb": 20,
        "security_check": "image_validate"
    },
    "image/png": {
        "extensions": [".png"],
        "max_size_mb": 20,
        "security_check": "image_validate"
    },
    "image/gif": {
        "extensions": [".gif"],
        "max_size_mb": 20,
        "security_check": "image_validate"
    }
}
```

### 2.2 文件大小限制

| 文件类型 | 限制 | 说明 |
|----------|------|------|
| TXT/MD | 10MB | 纯文本，较小 |
| HTML | 20MB | 网页文件 |
| PDF | 50MB | 平衡文档大小和用户体验 |
| DOCX/XLSX | 50MB | Office 文档 |
| 图片 | 20MB | 单张图片限制 |
| **总存储/agent** | 500MB | 阶段一限制，阶段二按订阅调整 |

### 2.3 三层验证机制

```python
async def validate_upload_file(file: UploadFile) -> ValidationResult:
    """
    文件上传三层验证
    1. 扩展名白名单
    2. MIME 类型检测（python-magic）
    3. 文件头签名验证
    """
    result = ValidationResult(is_valid=True)

    # 第一层：扩展名检查
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return ValidationResult(
            is_valid=False,
            error_code="ERR_FILE_TYPE_NOT_ALLOWED",
            message=f"文件类型 {ext} 不在允许列表中"
        )

    # 第二层：MIME 类型检测（不信任客户端）
    file_head = await file.read(8192)  # 读取前8KB
    await file.seek(0)  # 重置指针

    detected_mime = magic.from_buffer(file_head, mime=True)
    if detected_mime not in ALLOWED_MIME_TYPES:
        return ValidationResult(
            is_valid=False,
            error_code="ERR_MIME_MISMATCH",
            message=f"文件实际类型为 {detected_mime}，与扩展名不符"
        )

    # 第三层：文件头签名验证
    if not validate_file_signature(file_head, ext):
        return ValidationResult(
            is_valid=False,
            error_code="ERR_FILE_SIGNATURE_INVALID",
            message="文件签名验证失败，可能文件已损坏或被篡改"
        )

    return result
```

### 2.4 文件头签名验证

```python
FILE_SIGNATURES = {
    ".pdf": [b"%PDF"],
    ".docx": [b"PK\x03\x04"],  # ZIP 格式（Office Open XML）
    ".xlsx": [b"PK\x03\x04"],
    ".jpg": [b"\xFF\xD8\xFF"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".gif": [b"GIF87a", b"GIF89a"],
    ".txt": None,  # 文本文件无需签名
    ".md": None,
    ".html": None,
}

def validate_file_signature(file_head: bytes, ext: str) -> bool:
    """验证文件头签名"""
    expected_sigs = FILE_SIGNATURES.get(ext)
    if expected_sigs is None:
        # 文本类文件：尝试解码为 UTF-8/GBK
        try:
            file_head.decode("utf-8")
            return True
        except UnicodeDecodeError:
            try:
                file_head.decode("gbk")
                return True
            except UnicodeDecodeError:
                return False

    # 二进制文件：检查文件头
    return any(file_head.startswith(sig) for sig in expected_sigs)
```

---

## 三、内容安全审核

### 3.1 文本内容审核

```python
class ContentSecurityChecker:
    """文本内容安全审核"""

    # 敏感词库（可扩展）
    SENSITIVE_PATTERNS = [
        r"病毒",  # 恶意软件相关
        r"黑客工具",
        r"攻击",
        r"入侵",
        # ... 更多规则
    ]

    async def check_text_content(self, text: str) -> SecurityResult:
        """检查文本内容"""
        # 1. 敏感词检测
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, text):
                return SecurityResult(
                    is_safe=False,
                    reason=f"包含敏感词：{pattern}",
                    action="reject"
                )

        # 2. 调用 OpenAI Moderation API（可选）
        # if await openai_moderation_check(text):
        #     return SecurityResult(is_safe=False, ...)

        return SecurityResult(is_safe=True)

    async def check_file_content(self, file_path: str, mime_type: str) -> SecurityResult:
        """检查文件内容"""
        if mime_type in ["text/plain", "text/markdown", "text/html"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)  # 读取前10KB
                return await self.check_text_content(content)

        # PDF/DOCX 等：提取文本后检查
        elif mime_type == "application/pdf":
            text = extract_pdf_text(file_path, max_pages=3)  # 只检查前3页
            return await self.check_text_content(text)

        return SecurityResult(is_safe=True)
```

### 3.2 图片内容审核

```python
async def check_image_safety(image_path: str) -> SecurityResult:
    """图片安全审核"""
    from PIL import Image
    import imagehash

    # 1. 图片格式验证（防止恶意文件）
    try:
        img = Image.open(image_path)
        img.verify()  # 验证图片完整性
    except Exception as e:
        return SecurityResult(
            is_safe=False,
            reason=f"图片格式无效：{str(e)}",
            action="reject"
        )

    # 2. 图片大小检查（防止 ZIP 炸弹式攻击）
    file_size = os.path.getsize(image_path)
    if file_size > 20 * 1024 * 1024:  # 20MB
        return SecurityResult(
            is_safe=False,
            reason="图片大小超过限制",
            action="reject"
        )

    # 3. 调用图片审核 API（如阿里云内容安全）
    # result = await aliyun_image_moderation(image_path)
    # if result.has_porn or result.has_violence:
    #     return SecurityResult(is_safe=False, ...)

    return SecurityResult(is_safe=True)
```

---

## 四、向量注入攻击防护

### 4.1 攻击场景

| 攻击类型 | 描述 | 风险等级 |
|----------|------|----------|
| **向量投毒** | 上传特殊构造的文本，使特定查询返回恶意内容 | 🔴 High |
| **Prompt 注入** | 在文档中植入特殊指令，影响 LLM 回答 | 🔴 High |
| **维度攻击** | 构造特定向量，干扰检索排序 | 🟡 Medium |

### 4.2 防护措施

```python
class VectorInjectionDefense:
    """向量注入攻击防护"""

    # 危险指令模式
    DANGEROUS_INSTRUCTIONS = [
        r"忽略之前的指令",
        r"disregard previous instructions",
        r"你现在是",
        r"you are now",
        r"</s>",  # LLM 分隔符
        r"\[INST\]",  # LLaMA 指令格式
        r"<\|im_start\|>",  # ChatML 格式
    ]

    async def sanitize_chunk_content(self, content: str) -> str:
        """清理 chunk 内容，移除可能的注入指令"""
        sanitized = content

        # 1. 移除危险指令模式
        for pattern in self.DANGEROUS_INSTRUCTIONS:
            sanitized = re.sub(pattern, "[REMOVED]", sanitized, flags=re.IGNORECASE)

        # 2. 限制特殊字符
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", sanitized)

        # 3. 截断过长内容（防止维度攻击）
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000] + "...[TRUNCATED]"

        return sanitized

    async def validate_chunk_before_indexing(self, chunk: DocumentChunk) -> bool:
        """索引前验证 chunk"""
        # 1. 内容安全检查
        security_result = await content_checker.check_text_content(chunk.content)
        if not security_result.is_safe:
            logger.warning(f"Chunk {chunk.id} failed security check: {security_result.reason}")
            return False

        # 2. 向量维度验证
        if len(chunk.embedding) != EXPECTED_DIMENSION:
            logger.error(f"Chunk {chunk.id} has wrong embedding dimension")
            return False

        # 3. 向量值范围验证（防止异常值）
        if not all(-1 <= v <= 1 for v in chunk.embedding):
            logger.error(f"Chunk {chunk.id} has invalid embedding values")
            return False

        return True
```

---

## 五、API 安全设计

### 5.1 上传接口限流

```python
# 上传接口限流配置
UPLOAD_RATE_LIMIT = {
    "per_agent": "10 uploads/minute",
    "per_ip": "30 uploads/minute",
    "max_concurrent": 3  # 同时处理的上传任务数
}

@app.post("/api/v1/knowledge/upload")
@limiter.limit("10/minute", key_func=lambda: get_agent_id())
@limiter.limit("30/minute", key_func=lambda: request.client.host)
async def upload_document(request, agent_id: str = Depends(get_current_agent)):
    """上传文档接口（带限流）"""
    # 检查并发数
    concurrent_count = await get_concurrent_upload_count(agent_id)
    if concurrent_count >= UPLOAD_RATE_LIMIT["max_concurrent"]:
        raise HTTPException(
            status_code=429,
            detail="Too many concurrent uploads. Please wait."
        )

    # ... 正常上传流程
```

### 5.2 文件访问鉴权

```python
async def get_file_path(doc_id: str, agent_id: str) -> str:
    """
    获取文件路径（带鉴权）
    确保 agent 只能访问自己的文件
    """
    doc = await Document.get(doc_id)
    if not doc or doc.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = doc.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # 路径遍历检查
    real_path = os.path.realpath(file_path)
    base_path = os.path.realpath("/opt/ccbot/storage/")
    if not real_path.startswith(base_path):
        raise HTTPException(status_code=403, detail="Access denied")

    return real_path
```

---

## 六、安全审计日志

### 6.1 审计事件定义

```python
class SecurityAuditLogger:
    """安全审计日志"""

    AUDIT_EVENTS = {
        "file_upload_attempt": {
            "level": "INFO",
            "retention_days": 90
        },
        "file_upload_rejected": {
            "level": "WARNING",
            "retention_days": 180,
            "alert": True
        },
        "security_violation": {
            "level": "CRITICAL",
            "retention_days": 365,
            "alert": True,
            "notify_ops": True
        },
        "suspicious_content_detected": {
            "level": "WARNING",
            "retention_days": 180,
            "alert": True
        }
    }

    async def log_upload_attempt(self, agent_id: str, filename: str,
                               file_size: int, mime_type: str):
        """记录上传尝试"""
        await self._write_audit_log({
            "event": "file_upload_attempt",
            "agent_id": agent_id,
            "filename": filename,
            "file_size": file_size,
            "mime_type": mime_type,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def log_security_violation(self, agent_id: str, violation_type: str,
                                      details: dict):
        """记录安全违规"""
        await self._write_audit_log({
            "event": "security_violation",
            "agent_id": agent_id,
            "violation_type": violation_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })

        # 触发告警
        await self._send_security_alert(agent_id, violation_type, details)
```

### 6.2 审计日志 PromQL 监控

```promql
# 文件上传拒绝率
sum(rate(ccbot_security_events_total{event="file_upload_rejected"}[5m])) > 0.05

# 安全违规告警
ccbot_security_events_total{event="security_violation"} > 0
```

---

## 七、渗透测试检查清单

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 恶意文件上传 | 上传 `.exe`/`.php` 等可执行文件 | 拒绝（400错误） |
| MIME 欺骗 | 修改上传请求的 MIME 类型 | 二次检测后拒绝 |
| 路径遍历 | 文件名包含 `../` | 拒绝或过滤 |
| 超大文件 | 上传 100MB 文件 | 拒绝（413错误） |
| 并发上传 | 同时上传 20 个文件 | 限流生效（429错误） |
| 向量注入 | 上传含特殊指令的文档 | 内容被清理 |
| XSS 注入 | 在 HTML 文件中植入 `<script>` | HTML 净化后存储 |

---

## 八、验收测试

| 测试用例 | 输入 | 期望输出 | 验收标准 |
|----------|------|----------|----------|
| test_upload_exe_file | `malware.exe` | HTTP 400 | 拒绝上传 |
| test_upload_mime_spoofing | 修改 MIME 为 `text/plain` 的 PHP 文件 | HTTP 400 | 检测真实类型 |
| test_upload_path_traversal | `../../../etc/passwd` | HTTP 400 | 文件名被过滤 |
| test_upload_large_file | 100MB 文件 | HTTP 413 | 拒绝上传 |
| test_upload_rate_limit | 1分钟内上传20个文件 | HTTP 429 | 限流生效 |
| test_vector_injection | 含 `</s>` 的文档 | 内容被清理 | chunk 中无危险指令 |
| test_audit_log_write | 上传文件 | 审计日志写入 | 日志可被检索 |

---

## 九、T1.X 任务归属

将安全边界作为阶段一补充任务：

| 任务ID | 描述 | 优先级 |
|--------|------|--------|
| T1.22 | 文件上传三层验证 | P0 |
| T1.23 | 内容安全审核（文本+图片） | P0 |
| T1.24 | 向量注入攻击防护 | P1 |
| T1.25 | API 限流与鉴权 | P0 |
| T1.26 | 安全审计日志 | P1 |

---

*本文档补充 PHASED_ROADMAP.md 遗漏的安全边界设计。*

"""简历 PDF 解析与入库管线"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.rag.core.vector_store import vector_store
from app.rag.core.extractors import extract_text_from_pdf, extract_text_from_file

# 目录映射：尝试识别的章节标题 → 标准化 section 名
SECTION_KEYWORDS = {
    "personal_info": ["个人信息", "基本资料", "个人资料", "联系方式", "基本信息"],
    "skills": ["技能", "专业技能", "技术技能", "核心技术", "技术栈"],
    "work_experience": ["工作经历", "工作经验", "工作履历", "从业经历"],
    "projects": ["项目经验", "项目经历", "项目"],
    "education": ["教育背景", "教育经历", "学历", "教育"],
    "self_evaluation": ["自我评价", "个人评价", "关于我"],
}


def detect_section(title: str) -> str:
    """根据章节标题识别标准化 section 名"""
    title_stripped = title.strip()
    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in title_stripped:
                return section
    return "other"


def smart_chunk(text: str) -> list[tuple[str, str]]:
    """智能分块：先尝试按章节分割，再对长块做二次切分

    返回: [(section, content), ...]
    """
    lines = text.split("\n")
    chunks: list[tuple[str, str]] = []
    current_section = "other"
    current_content: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 判断是否是章节标题
        matched_section = None
        for section, keywords in SECTION_KEYWORDS.items():
            for kw in keywords:
                if stripped == kw or stripped.startswith(kw) and len(stripped) < 20:
                    matched_section = section
                    break
            if matched_section:
                break

        if matched_section:
            # 保存上一段
            if current_content:
                chunks.append((current_section, "\n".join(current_content)))
            current_section = matched_section
            current_content = []
        else:
            current_content.append(stripped)

    # 最后一段
    if current_content:
        chunks.append((current_section, "\n".join(current_content)))

    # 如果没有识别出任何章节，整段作为一个块
    if not chunks:
        chunks.append(("other", text))

    # 对长块做二次切分
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        length_function=len,
    )

    result: list[tuple[str, str]] = []
    for section, content in chunks:
        if len(content) <= 500:
            if content.strip():
                result.append((section, content))
        else:
            sub_chunks = text_splitter.split_text(content)
            for sc in sub_chunks:
                if sc.strip():
                    result.append((section, sc))

    return result


def process_resume_text(text: str, user_id: int, source: str = "resume.txt") -> dict:
    """完整管线：文本 → 分块 → 入库"""
    if not text.strip():
        return {"chunks_count": 0, "status": "error", "message": "内容为空"}

    # 1. 删除旧 chunks
    vector_store.delete_user_chunks(user_id)

    # 2. 分块
    chunks = smart_chunk(text)

    # 3. 构建 Document 对象（过滤空内容，避免 DashScope embedding 报错）
    documents = []
    for i, (section, content) in enumerate(chunks):
        if not content or not content.strip():
            continue
        doc = Document(
            page_content=content,
            metadata={
                "chunk_id": str(uuid.uuid4()),
                "user_id": user_id,
                "doc_type": "resume",
                "section": section,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source": source,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        documents.append(doc)

    # 4. 入库
    vector_store.add_documents(documents)

    return {
        "chunks_count": len(documents),
        "status": "success",
        "sections": list(set(s for s, _ in chunks)),
    }


def process_resume_pdf(file_path: str, user_id: int) -> dict:
    """PDF 文件版：解析 → 分块 → 入库"""
    text = extract_text_from_pdf(file_path)
    if not text:
        return {"chunks_count": 0, "status": "error", "message": "PDF 内容为空"}
    return process_resume_text(text, user_id, source=os.path.basename(file_path))


def process_resume_file(file_path: str, user_id: int) -> dict:
    """自动识别文件类型并提取文本 → 分块 → 入库"""
    try:
        text = extract_text_from_file(file_path)
    except ValueError as e:
        return {"chunks_count": 0, "status": "error", "message": str(e)}

    if not text:
        return {"chunks_count": 0, "status": "error", "message": "文件内容为空"}
    return process_resume_text(text, user_id, source=os.path.basename(file_path))
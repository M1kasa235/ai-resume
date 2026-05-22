"""管理后台 API — 知识库管理 + 题目管理"""

import csv
import io
import json
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from langchain_core.documents import Document
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_current_admin_user, get_db
from app.models.user import User
from app.models.question import Question
from app.models.knowledge_partition import KnowledgePartition
from app.rag.core.vector_store import (
    vector_store,
    knowledge_vector_store,
    COLLECTION_RESUME,
    COLLECTION_KNOWLEDGE,
)
from app.rag.ingestion.resume import process_resume_file, smart_chunk
from app.rag.core.chunker import KnowledgeChunker
from app.rag import get_knowledge_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["管理后台"])


# ==================== 知识库管理 ====================

@router.get("/knowledge/stats")
async def knowledge_stats(
    admin: User = Depends(get_current_admin_user),
):
    """知识库统计（含分区明细）"""
    from app.rag.ingestion.knowledge import KnowledgeIngestion

    resume_count = vector_store.count({"user_id": {"$ne": 0}})
    job_stats = KnowledgeIngestion().stats()

    return {
        "collections": [
            {
                "name": COLLECTION_RESUME,
                "document_count": resume_count,
                "type": "resume",
            },
            {
                "name": COLLECTION_KNOWLEDGE,
                "document_count": job_stats["total"],
                "type": "knowledge_base",
                "partitions": job_stats["types"],
            },
        ]
    }


def _get_store(collection: str):
    """根据 collection 名称返回对应的 VectorStore 实例"""
    if collection == COLLECTION_KNOWLEDGE:
        return knowledge_vector_store
    return vector_store


@router.get("/knowledge/chunks")
async def list_chunks(
    collection: str = Query(COLLECTION_RESUME),
    user_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin_user),
):
    """查看知识库文档块（支持切换 collection）"""
    store = _get_store(collection)
    where_filter = {}
    if user_id is not None:
        where_filter["user_id"] = user_id

    results = store.db.get(
        where=where_filter if where_filter else None,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    total = store.count(where_filter if where_filter else None)

    items = []
    for i in range(len(ids)):
        items.append({
            "id": ids[i],
            "content": documents[i][:300] if documents[i] else "",
            "metadata": metadatas[i] if i < len(metadatas) else {},
        })

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.delete("/knowledge/chunks")
async def delete_chunks(
    ids: list[str] = Query(...),
    collection: str = Query(COLLECTION_RESUME),
    admin: User = Depends(get_current_admin_user),
):
    """删除指定文档块（支持切换 collection）"""
    store = _get_store(collection)
    try:
        store.db.delete(ids=ids)
        return {"deleted": len(ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.delete("/knowledge/user/{user_id}")
async def delete_user_chunks(
    user_id: int,
    admin: User = Depends(get_current_admin_user),
):
    """删除指定用户的所有文档块"""
    vector_store.delete_user_chunks(user_id)
    return {"deleted": True}


@router.post("/knowledge/import")
async def import_jobs(
    file: UploadFile = File(...),
    doc_type: str = Query(None, description="手动指定分区: job / resume_guide / interview，留空则从文件名自动推断"),
    admin: User = Depends(get_current_admin_user),
):
    """上传 CSV/JSON/PDF/DOCX/TXT 导入知识库（自动识别格式和分区）"""
    import tempfile
    from app.rag.ingestion.knowledge import KnowledgeIngestion

    suffix = Path(file.filename).suffix
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = KnowledgeIngestion().import_file(tmp_path, doc_type=doc_type, clear_existing=False)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    finally:
        os.unlink(tmp_path)


# ==================== 知识库分区管理 ====================

@router.delete("/knowledge/partition/{doc_type}")
async def clear_knowledge_partition(
    doc_type: str,
    admin: User = Depends(get_current_admin_user),
):
    """清理指定分区（job / resume_guide / interview）"""
    from app.rag.ingestion.knowledge import KnowledgeIngestion

    result = KnowledgeIngestion().clear_type(doc_type)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/knowledge/partition/{doc_type}/reimport")
async def reimport_knowledge_partition(
    doc_type: str,
    admin: User = Depends(get_current_admin_user),
):
    """重新导入指定分区（从 test_data/knowledge/）"""
    from app.rag.ingestion.knowledge import KnowledgeIngestion

    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "test_data", "knowledge", f"{doc_type}.json",
    )
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"数据文件不存在: {file_path}")

    result = KnowledgeIngestion().import_from_json(file_path, clear_existing=True)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/knowledge/rebuild")
async def rebuild_all_knowledge(
    admin: User = Depends(get_current_admin_user),
):
    """重新生成并导入所有知识数据"""
    import subprocess
    import os

    knowledge_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "test_data", "knowledge",
    )

    results = []
    # 先跑所有生成脚本
    for g in sorted(os.listdir(knowledge_dir)):
        if g.startswith("gen_") and g.endswith(".py"):
            gpath = os.path.join(knowledge_dir, g)
            try:
                subprocess.run(["python", gpath], cwd=os.path.dirname(knowledge_dir), check=True, capture_output=True, text=True)
                results.append({"generator": g, "status": "ok"})
            except subprocess.CalledProcessError as e:
                results.append({"generator": g, "status": "error", "message": e.stderr})

    # 再导入所有 JSON
    from app.rag.ingestion.knowledge import KnowledgeIngestion

    ingestion = KnowledgeIngestion()
    for jf in sorted(os.listdir(knowledge_dir)):
        if jf.endswith(".json") and not jf.startswith("gen_"):
            jpath = os.path.join(knowledge_dir, jf)
            r = ingestion.import_file(jpath, clear_existing=True)
            results.append(r)

    return {"results": results}


# ==================== 知识库分区与文档管理 ====================

class KnowledgeDocumentRequest(BaseModel):
    """创建/更新知识文档的请求体"""
    parent_id: Optional[str] = Field(None, description="更新时传入，新建时留空")
    title: str = Field(..., min_length=1, max_length=500)
    category: str = Field("", max_length=200)
    content: str = Field(..., min_length=1)
    doc_type: str = Field(..., description="分区标识：job / resume_guide / interview 或自定义")


class CreatePartitionRequest(BaseModel):
    """创建自定义分区"""
    doc_key: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$", description="分区键，如 my_kb")
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=500)


class UpdatePartitionRequest(BaseModel):
    """更新分区信息"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)


@router.get("/knowledge/partitions")
async def list_partitions(
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """列出所有知识库分区（从数据库 + Chroma 统计合并）"""
    from app.rag.ingestion.knowledge import KnowledgeIngestion
    import logging
    _logger = logging.getLogger(__name__)

    # 数据库中的分区定义
    try:
        stmt = select(KnowledgePartition).order_by(KnowledgePartition.id)
        db_result = await db.execute(stmt)
        db_partitions = list(db_result.scalars().all())
    except Exception as e:
        _logger.warning(f"查询 knowledge_partitions 表失败（表可能未创建）: {e}")
        db_partitions = []

    # Chroma 中的实际数据统计
    try:
        chroma_stats = KnowledgeIngestion().stats()
        chroma_types = chroma_stats.get("types", {})
    except Exception as e:
        _logger.warning(f"查询 Chroma 统计失败: {e}")
        chroma_types = {}

    partitions = []
    seen_keys = set()

    # 数据库优先
    for p in db_partitions:
        info = chroma_types.get(p.doc_key, {})
        partitions.append({
            "id": p.id,
            "doc_type": p.doc_key,
            "name": p.name,
            "description": p.description,
            "parent_count": info.get("parent", 0),
            "child_count": info.get("child", 0),
            "total": info.get("total", 0),
            "titles": info.get("titles", []),
            "is_custom": p.doc_key not in ("job", "resume_guide", "interview"),
        })
        seen_keys.add(p.doc_key)

    # Chroma 中有数据但 DB 中无定义的分区（显示为"未注册"）
    for dt, info in chroma_types.items():
        if dt in seen_keys:
            continue
        partitions.append({
            "id": None,
            "doc_type": dt,
            "name": dt,
            "description": "",
            "parent_count": info.get("parent", 0),
            "child_count": info.get("child", 0),
            "total": info.get("total", 0),
            "titles": info.get("titles", []),
            "is_custom": True,
        })

    return {"total": len(partitions), "partitions": partitions}


@router.post("/knowledge/partitions", status_code=201)
async def create_partition(
    data: CreatePartitionRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新知识库分区"""
    existing = await db.execute(select(KnowledgePartition).where(KnowledgePartition.doc_key == data.doc_key))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"分区键 {data.doc_key} 已存在")

    part = KnowledgePartition(
        doc_key=data.doc_key,
        name=data.name,
        description=data.description,
        created_by=admin.id,
    )
    db.add(part)
    await db.commit()
    await db.refresh(part)
    return {"id": part.id, "doc_key": part.doc_key, "name": part.name}


@router.put("/knowledge/partitions/{partition_id}")
async def update_partition(
    partition_id: int,
    data: UpdatePartitionRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新分区名称或描述"""
    stmt = select(KnowledgePartition).where(KnowledgePartition.id == partition_id)
    result = await db.execute(stmt)
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="分区不存在")
    if data.name is not None:
        part.name = data.name
    if data.description is not None:
        part.description = data.description
    await db.commit()
    return {"id": part.id, "doc_key": part.doc_key, "name": part.name}


@router.delete("/knowledge/partitions/{partition_id}")
async def delete_partition(
    partition_id: int,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除分区定义及其全部 Chroma 数据"""
    stmt = select(KnowledgePartition).where(KnowledgePartition.id == partition_id)
    result = await db.execute(stmt)
    part = result.scalar_one_or_none()
    if not part:
        raise HTTPException(status_code=404, detail="分区不存在")

    # 清理 Chroma 中该分区的所有数据
    try:
        knowledge_vector_store.delete_by_filter({"doc_type": part.doc_key})
    except Exception:
        logger.warning("清理分区 Chroma 数据失败 (doc_key=%s)", part.doc_key, exc_info=True)

    # 使 BM25 缓存失效
    get_knowledge_service().invalidate_partition(part.doc_key)

    await db.delete(part)
    await db.commit()
    return {"deleted": True, "doc_key": part.doc_key}


@router.post("/knowledge/partitions/seed")
async def seed_default_partitions(
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """种子默认分区（job / resume_guide / interview）"""
    defaults = [
        ("job", "岗位知识", "岗位描述、技能要求等"),
        ("resume_guide", "简历指南", "简历撰写与优化技巧"),
        ("interview", "面试题库", "常见面试问题与答案"),
    ]
    created = 0
    for doc_key, name, desc in defaults:
        existing = await db.execute(select(KnowledgePartition).where(KnowledgePartition.doc_key == doc_key))
        if existing.scalar_one_or_none():
            continue
        db.add(KnowledgePartition(doc_key=doc_key, name=name, description=desc, created_by=admin.id))
        created += 1
    await db.commit()
    return {"status": "ok", "created": created}


@router.get("/knowledge/documents")
async def list_documents(
    doc_type: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin_user),
):
    """列出某分区下所有 parent 文档"""
    store = knowledge_vector_store

    # Chroma get where 只支持单 key，先按 doc_type 拉取，再 Python 过滤
    try:
        results = store.db.get(where={"doc_type": doc_type}, include=["metadatas", "documents"])
    except Exception:
        return {"total": 0, "page": page, "page_size": page_size, "items": []}

    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    # 只保留 parent chunks
    parents = []
    for i in range(len(ids)):
        meta = metadatas[i] if i < len(metadatas) else {}
        if meta.get("chunk_type") != "parent":
            continue
        parents.append({
            "id": ids[i],
            "parent_id": meta.get("parent_id", ids[i]),
            "title": meta.get("title", ""),
            "category": meta.get("category", ""),
            "content": (documents[i] or "")[:500],
            "content_full": documents[i] or "",
            "doc_type": meta.get("doc_type", ""),
            "source_file": meta.get("source_file", ""),
        })

    total = len(parents)
    start = (page - 1) * page_size
    end = start + page_size
    paged = parents[start:end]

    return {"total": total, "page": page, "page_size": page_size, "items": paged}


@router.get("/knowledge/documents/{parent_id}/chunks")
async def get_document_chunks(
    parent_id: str,
    admin: User = Depends(get_current_admin_user),
):
    """获取 parent 文档及其所有 child chunks"""
    store = knowledge_vector_store

    try:
        results = store.db.get(where={"parent_id": parent_id}, include=["metadatas", "documents"])
    except Exception:
        raise HTTPException(status_code=404, detail="文档不存在")

    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    parent = None
    children = []
    for i in range(len(ids)):
        meta = metadatas[i] if i < len(metadatas) else {}
        item = {
            "id": ids[i],
            "content": documents[i] or "",
            "metadata": meta,
        }
        if meta.get("chunk_type") == "parent":
            parent = item
        else:
            item["child_index"] = meta.get("child_index", i)
            children.append(item)

    if not parent:
        raise HTTPException(status_code=404, detail="文档不存在")

    children.sort(key=lambda c: c.get("child_index", 0))
    return {"parent": parent, "children": children, "child_count": len(children)}


@router.post("/knowledge/documents")
async def save_knowledge_document(
    data: KnowledgeDocumentRequest,
    admin: User = Depends(get_current_admin_user),
):
    """创建或更新知识文档（写入 parent + child chunks）"""
    chunker = KnowledgeChunker()
    store = knowledge_vector_store

    # 如果是更新，按 doc_group_id 全量清理旧 chunks（避免多 parent 残留）
    if data.parent_id:
        try:
            old = store.db.get(where={"parent_id": data.parent_id}, include=["metadatas"])
            if old.get("ids"):
                group_ids = set()
                for m in old.get("metadatas", []):
                    gid = m.get("doc_group_id")
                    if gid:
                        group_ids.add(gid)
                # 按 doc_group_id 删，退化为按 parent_id
                if group_ids:
                    for gid in group_ids:
                        to_delete = store.db.get(where={"doc_group_id": gid})
                        if to_delete.get("ids"):
                            store.db.delete(ids=to_delete["ids"])
                else:
                    store.db.delete(ids=old["ids"])
        except Exception:
            pass

    content = data.content
    if data.category:
        content = f"分类：{data.category}\n\n{content}"

    parent_metadata = {
        "doc_type": data.doc_type,
        "title": data.title,
        "category": data.category,
        "source_file": "admin_manual",
        "user_id": 0,
    }

    parent_docs, child_docs = chunker.chunk(content, parent_metadata)
    store.add_documents(parent_docs)
    if child_docs:
        store.add_documents(child_docs)

    # 使 BM25 缓存失效
    get_knowledge_service().invalidate_partition(data.doc_type)

    doc_group_id = parent_docs[0].metadata.get("doc_group_id", "") if parent_docs else ""

    return {
        "status": "success",
        "doc_group_id": doc_group_id,
        "title": data.title,
        "parent_chunks": len(parent_docs),
        "child_chunks": len(child_docs),
    }


@router.delete("/knowledge/documents/{parent_id}")
async def delete_knowledge_document(
    parent_id: str,
    admin: User = Depends(get_current_admin_user),
):
    """删除知识文档及其所有 child chunks（按 doc_group_id 全量清理）"""
    store = knowledge_vector_store

    try:
        old = store.db.get(where={"parent_id": parent_id}, include=["metadatas"])
        if not old.get("ids"):
            raise HTTPException(status_code=404, detail="文档不存在")

        # 按 doc_group_id 全量删除（多 parent 文档一并清理）
        group_ids = set()
        for m in old.get("metadatas", []):
            gid = m.get("doc_group_id")
            if gid:
                group_ids.add(gid)

        deleted = 0
        if group_ids:
            for gid in group_ids:
                to_delete = store.db.get(where={"doc_group_id": gid})
                if to_delete.get("ids"):
                    store.db.delete(ids=to_delete["ids"])
                    deleted += len(to_delete["ids"])
        else:
            store.db.delete(ids=old["ids"])
            deleted = len(old["ids"])

        # 使 BM25 缓存失效（从残留 metadata 取 doc_type）
        for m in old.get("metadatas", []):
            dt = m.get("doc_type")
            if dt:
                get_knowledge_service().invalidate_partition(dt)
                break
        else:
            # fallback: 从 Chroma metadata 获取不到，遍历所有已知分区逐个失效
            for dt in ("job", "resume_guide", "interview"):
                get_knowledge_service().invalidate_partition(dt)

        return {"deleted": True, "chunks_removed": deleted}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/knowledge/upload")
async def upload_knowledge_file(
    file: UploadFile = File(...),
    doc_type: str = Query(..., description="分区标识：job / resume_guide / interview"),
    admin: User = Depends(get_current_admin_user),
):
    """上传 JSON 文件导入知识库"""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="仅支持 JSON 格式")

    from app.rag.ingestion.knowledge import KnowledgeIngestion

    content = await file.read()
    try:
        records = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {str(e)}")

    if isinstance(records, dict):
        records = records.get("records", records.get("data", [records]))
    if not isinstance(records, list):
        raise HTTPException(status_code=400, detail="JSON 格式错误: 需要数组")
    if not records:
        raise HTTPException(status_code=400, detail="JSON 数组为空")

    # 写入临时文件
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(records, tmp, ensure_ascii=False)
        tmp_path = tmp.name

    try:
        result = KnowledgeIngestion().import_from_json(tmp_path, doc_type=doc_type, clear_existing=True)
        # 使 BM25 缓存失效
        get_knowledge_service().invalidate_partition(doc_type)
        return result
    finally:
        os.unlink(tmp_path)


# ==================== 题目管理 ====================

class QuestionCreateRequest(BaseModel):
    category_id: int
    type: str = Field(..., pattern=r"^(single_choice|multiple_choice|essay|coding|open)$")
    difficulty: str = Field("medium", pattern=r"^(easy|medium|hard)$")
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    options: Optional[list] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    code_template: Optional[str] = None
    test_cases: Optional[list] = None
    tags: Optional[list] = None
    company_tags: Optional[list] = None
    is_hot: bool = False


class QuestionUpdateRequest(BaseModel):
    category_id: Optional[int] = None
    type: Optional[str] = Field(None, pattern=r"^(single_choice|multiple_choice|essay|coding|open)$")
    difficulty: Optional[str] = Field(None, pattern=r"^(easy|medium|hard)$")
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    options: Optional[list] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    code_template: Optional[str] = None
    test_cases: Optional[list] = None
    tags: Optional[list] = None
    company_tags: Optional[list] = None
    is_hot: Optional[bool] = None


@router.post("/questions")
async def create_question(
    data: QuestionCreateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建题目"""
    question = Question(
        category_id=data.category_id,
        type=data.type,
        difficulty=data.difficulty,
        title=data.title,
        content=data.content,
        options=data.options,
        correct_answer=data.correct_answer,
        explanation=data.explanation,
        code_template=data.code_template,
        test_cases=data.test_cases,
        tags=data.tags,
        company_tags=data.company_tags,
        is_hot=data.is_hot,
        created_by=admin.id,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return {"id": question.id, "message": "创建成功"}


@router.put("/questions/{question_id}")
async def update_question(
    question_id: int,
    data: QuestionUpdateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新题目"""
    stmt = select(Question).where(Question.id == question_id)
    result = await db.execute(stmt)
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    await db.commit()
    return {"message": "更新成功"}


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: int,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除题目"""
    stmt = select(Question).where(Question.id == question_id)
    result = await db.execute(stmt)
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    await db.delete(question)
    await db.commit()
    return {"message": "删除成功"}


# ==================== 简历知识库管理 ====================

SECTION_LABELS = {
    "personal_info": "个人信息",
    "skills": "专业技能",
    "work_experience": "工作经历",
    "projects": "项目经验",
    "education": "教育背景",
    "self_evaluation": "自我评价",
    "other": "其他",
}


@router.get("/resume/users")
async def list_resume_users(
    admin: User = Depends(get_current_admin_user),
):
    """列出所有已上传简历的用户（按 user_id 分组）"""
    store = vector_store
    results = store.db.get(include=["metadatas"])
    metadatas = results.get("metadatas", [])
    ids = results.get("ids", [])

    # 按 user_id 分组
    users: dict[int, dict] = {}
    for i in range(len(ids)):
        meta = metadatas[i] if i < len(metadatas) else {}
        uid = meta.get("user_id", 0)
        if uid == 0:
            continue
        if uid not in users:
            users[uid] = {
                "user_id": uid,
                "chunk_count": 0,
                "section_count": 0,
                "sections": set(),
            }
        users[uid]["chunk_count"] += 1
        users[uid]["sections"].add(meta.get("section", "other"))

    result = []
    for uid, info in sorted(users.items()):
        result.append({
            "user_id": info["user_id"],
            "chunk_count": info["chunk_count"],
            "section_count": len(info["sections"]),
            "sections": [SECTION_LABELS.get(s, s) for s in sorted(info["sections"])],
        })

    return {"total": len(result), "items": result}


@router.get("/resume/users/{user_id}/sections")
async def list_resume_sections(
    user_id: int,
    admin: User = Depends(get_current_admin_user),
):
    """列出指定用户简历的分区（section 维度）"""
    store = vector_store
    results = store.db.get(where={"user_id": user_id}, include=["metadatas"])
    metadatas = results.get("metadatas", [])
    ids = results.get("ids", [])

    if not ids:
        raise HTTPException(status_code=404, detail="该用户没有简历数据")

    sections: dict[str, dict] = {}
    for i in range(len(ids)):
        meta = metadatas[i] if i < len(metadatas) else {}
        sec = meta.get("section", "other")
        if sec not in sections:
            sections[sec] = {
                "section": sec,
                "label": SECTION_LABELS.get(sec, sec),
                "chunk_count": 0,
            }
        sections[sec]["chunk_count"] += 1

    return {
        "user_id": user_id,
        "total_sections": len(sections),
        "total_chunks": len(ids),
        "items": sorted(sections.values(), key=lambda x: x["section"]),
    }


@router.get("/resume/users/{user_id}/sections/{section}")
async def list_resume_chunks(
    user_id: int,
    section: str,
    admin: User = Depends(get_current_admin_user),
):
    """列出指定用户指定 section 下的所有分块"""
    store = vector_store
    results = store.db.get(
        where={"$and": [{"user_id": user_id}, {"section": section}]},
        include=["metadatas", "documents"],
    )
    metadatas = results.get("metadatas", [])
    documents = results.get("documents", [])
    ids = results.get("ids", [])

    if not ids:
        raise HTTPException(status_code=404, detail="该分区没有数据")

    items = []
    for i in range(len(ids)):
        meta = metadatas[i] if i < len(metadatas) else {}
        items.append({
            "id": ids[i],
            "content": documents[i] or "",
            "metadata": {
                "chunk_index": meta.get("chunk_index", i),
                "total_chunks": meta.get("total_chunks", len(ids)),
                "source": meta.get("source", ""),
                "created_at": meta.get("created_at", ""),
                "section": meta.get("section", section),
            },
        })

    items.sort(key=lambda c: c["metadata"]["chunk_index"])

    return {
        "user_id": user_id,
        "section": section,
        "label": SECTION_LABELS.get(section, section),
        "total": len(items),
        "items": items,
    }


@router.delete("/resume/users/{user_id}")
async def delete_resume_user(
    user_id: int,
    admin: User = Depends(get_current_admin_user),
):
    """删除指定用户的所有简历文档块"""
    results = vector_store.db.get(where={"user_id": user_id})
    count = len(results.get("ids", []))
    if count == 0:
        raise HTTPException(status_code=404, detail="该用户没有简历数据")
    vector_store.db.delete(ids=results["ids"])
    return {"deleted": True, "chunks_removed": count}


@router.delete("/resume/chunks")
async def delete_resume_chunks(
    ids: list[str] = Query(...),
    admin: User = Depends(get_current_admin_user),
):
    """删除指定的简历文档块"""
    try:
        vector_store.db.delete(ids=ids)
        return {"deleted": len(ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

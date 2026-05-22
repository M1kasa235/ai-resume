"""知识库入库管线 — Parent/Child 分层导入

支持的格式: JSON CSV PDF DOCX TXT

用法:
    python -m app.rag.ingestion.knowledge test_data/knowledge/resume.json
    python -m app.rag.ingestion.knowledge test_data/knowledge/jobs.csv
    python -m app.rag.ingestion.knowledge test_data/knowledge/doc.pdf --doc-type handbook
    python -m app.rag.ingestion.knowledge test_data/knowledge/ --clear
"""

import csv
import io
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document

from app.rag.core.vector_store import knowledge_vector_store
from app.rag.core.chunker import KnowledgeChunker
from app.rag.core.parsers import parse_json, parse_csv
from app.rag.core.extractors import extract_text_from_file

logger = logging.getLogger(__name__)


class KnowledgeIngestion:
    """知识库入库管线，支持 JSON / CSV / PDF / DOCX / TXT"""

    def __init__(self, vector_store=knowledge_vector_store, chunker: KnowledgeChunker = None):
        self.vector_store = vector_store
        self.chunker = chunker or KnowledgeChunker()

    @staticmethod
    def _build_content(
        title: str,
        category: str,
        description: str,
        requirements: str,
        doc_type: str = "job",
    ) -> str:
        """按 doc_type 构造向量友好文本，需求/问题字段前置提高 embedding 匹配度"""
        if doc_type == "job":
            parts = []
            if requirements:
                parts.append(f"技能要求：{requirements}")
            if title:
                parts.append(f"岗位：{title}")
            if description:
                parts.append(f"职责：{description}")
            if category:
                parts.append(f"公司：{category}")
            return "\n".join(parts)
        elif doc_type == "resume_guide":
            parts = []
            if title:
                parts.append(f"简历技巧：{title}")
            if description:
                parts.append(description)
            if requirements:
                parts.append(f"关键要点：{requirements}")
            return "\n".join(parts)
        elif doc_type == "interview":
            parts = []
            if title:
                parts.append(f"面试题：{title}")
            if description:
                parts.append(f"参考答案：{description}")
            if requirements:
                parts.append(f"评分标准：{requirements}")
            return "\n".join(parts)
        # fallback
        parts = [f"标题：{title}", f"分类：{category}", f"描述：{description}", f"要求：{requirements}"]
        return "\n".join(p for p in parts if p)

    # ── 结构化入库（JSON / CSV）共用核心 ──

    @staticmethod
    def _derive_doc_type(stem: str) -> str:
        """从文件名推导 doc_type"""
        lower = stem.lower()
        if any(kw in lower for kw in ["resume", "简历", "cv", "履历", "求职"]):
            return "resume_guide"
        if any(kw in lower for kw in ["interview", "面试", "面经", "问答", "常见问题", "faq", "面試"]):
            return "interview"
        return "job"

    def _source_exists(self, source_file: str, title: Optional[str] = None) -> bool:
        """检查指定 source_file（+ 可选 title）是否已有 chunk，用于导入去重"""
        where = {"source_file": source_file}
        if title:
            where["title"] = title
        return self.vector_store.count(where) > 0

    def _ingest_records(
        self,
        records: list[dict],
        doc_type: str,
        source_file: str,
        clear_existing: bool = False,
    ) -> dict:
        """逐条分块入库，JSON/CSV 共用"""
        if clear_existing:
            try:
                self.vector_store.delete_by_filter({"doc_type": doc_type})
            except Exception:
                logger.warning("清理旧分区失败 (doc_type=%s)，继续导入", doc_type, exc_info=True)

        parent_count = 0
        child_count = 0
        skipped = 0
        for record in records:
            title = record.get("title", "")
            category = record.get("category", "")
            description = record.get("description", "")
            requirements = record.get("requirements", "")

            if not clear_existing and self._source_exists(source_file, title):
                skipped += 1
                continue

            content = self._build_content(title, category, description, requirements, doc_type)
            if not content.strip():
                continue

            parent_metadata = {
                "doc_type": doc_type,
                "source_file": source_file,
                "title": title,
                "category": category,
                "imported_at": datetime.now(timezone.utc).isoformat(),
                "user_id": 0,
            }

            parent_docs, child_docs = self.chunker.chunk(content, parent_metadata)
            try:
                self.vector_store.add_documents(parent_docs)
                parent_count += len(parent_docs)
            except Exception:
                logger.error("写入 parent chunk 失败 (title=%s, doc_type=%s)", title, doc_type, exc_info=True)
                continue

            if child_docs:
                try:
                    self.vector_store.add_documents(child_docs)
                    child_count += len(child_docs)
                except Exception:
                    logger.error("写入 child chunks 失败 (title=%s, doc_type=%s, count=%d)", title, doc_type, len(child_docs), exc_info=True)

        result = {
            "status": "success",
            "doc_type": doc_type,
            "source_file": source_file,
            "records": len(records),
            "parent_chunks": parent_count,
            "child_chunks": child_count,
        }
        if skipped:
            result["skipped"] = skipped
        return result

    # ── 结构化格式 ──

    def import_from_json(
        self,
        file_path: str,
        doc_type: Optional[str] = None,
        clear_existing: bool = False,
    ) -> dict:
        """从 JSON 文件导入（字段名自动归一化）"""
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "message": f"文件不存在: {file_path}"}

        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        try:
            records = parse_json(raw_text)
        except (json.JSONDecodeError, ValueError) as e:
            return {"status": "error", "message": f"JSON 解析失败: {e}"}

        if not records:
            return {"status": "error", "message": "未解析到有效记录"}

        if doc_type is None:
            doc_type = self._derive_doc_type(path.stem)

        return self._ingest_records(records, doc_type, path.name, clear_existing)

    def import_from_csv(
        self,
        file_path: str,
        doc_type: Optional[str] = None,
        clear_existing: bool = False,
    ) -> dict:
        """从 CSV 文件导入（字段名自动归一化）"""
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "message": f"文件不存在: {file_path}"}

        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            raw_text = f.read()
        try:
            records = parse_csv(raw_text)
        except (csv.Error, ValueError) as e:
            return {"status": "error", "message": f"CSV 解析失败: {e}"}

        if not records:
            return {"status": "error", "message": "未解析到有效记录"}

        if doc_type is None:
            doc_type = self._derive_doc_type(path.stem)

        return self._ingest_records(records, doc_type, path.name, clear_existing)

    # ── 非结构化文档 ──

    def import_from_text_file(
        self,
        file_path: str,
        doc_type: Optional[str] = None,
        clear_existing: bool = False,
    ) -> dict:
        """从 PDF / DOCX / TXT 等文档导入（全文作为单条知识）

        自动提取文本 → parent+child 分块入库
        """
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "message": f"文件不存在: {file_path}"}

        if doc_type is None:
            doc_type = self._derive_doc_type(path.stem)

        if not clear_existing and self._source_exists(path.name):
            return {"status": "skipped", "source_file": path.name, "reason": "已存在，跳过导入"}

        try:
            text = extract_text_from_file(file_path)
        except ValueError as e:
            return {"status": "error", "message": str(e)}

        if not text or not text.strip():
            return {"status": "error", "message": "文件内容为空"}

        if clear_existing:
            try:
                self.vector_store.delete_by_filter({"doc_type": doc_type})
            except Exception:
                logger.warning("清理旧分区失败 (doc_type=%s)，继续导入", doc_type, exc_info=True)

        title = path.stem
        metadata = {
            "doc_type": doc_type,
            "source_file": path.name,
            "title": title,
            "category": "",
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "user_id": 0,
        }

        try:
            parent_docs, child_docs = self.chunker.chunk(text, metadata)
            self.vector_store.add_documents(parent_docs)
            parent_count = len(parent_docs)
            child_count = 0
            if child_docs:
                self.vector_store.add_documents(child_docs)
                child_count = len(child_docs)
        except Exception as e:
            return {"status": "error", "message": f"入库失败: {e}"}

        return {
            "status": "success",
            "doc_type": doc_type,
            "source_file": path.name,
            "title": title,
            "parent_chunks": parent_count,
            "child_chunks": child_count,
        }

    # ── 统一分发 ──

    def import_file(self, file_path: str, **kwargs) -> dict:
        """自动检测文件类型并导入

        支持: .json .csv .txt .pdf .doc .docx
        """
        ext = Path(file_path).suffix.lower()
        if ext == ".json":
            return self.import_from_json(file_path, **kwargs)
        elif ext == ".csv":
            return self.import_from_csv(file_path, **kwargs)
        elif ext in (".txt", ".pdf", ".doc", ".docx"):
            return self.import_from_text_file(file_path, **kwargs)
        return {"status": "error", "message": f"不支持的文件格式: {ext}"}

    def clear_type(self, doc_type: str) -> dict:
        """清理指定类型的所有知识数据"""
        try:
            self.vector_store.delete_by_filter({"doc_type": doc_type})
            return {"status": "success", "doc_type": doc_type}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stats(self) -> dict:
        """查看知识库分区统计"""
        results = self.vector_store.db.get(limit=10000, include=["metadatas"])
        if not results["ids"]:
            return {"total": 0, "types": {}}

        types = {}
        for m in results["metadatas"]:
            dt = m.get("doc_type", "unknown")
            ct = m.get("chunk_type", "unknown")
            types.setdefault(dt, {"parent": 0, "child": 0, "titles": []})
            types[dt][ct] = types[dt].get(ct, 0) + 1
            if ct == "parent":
                title = m.get("title", "")
                if title and title not in types[dt]["titles"]:
                    types[dt]["titles"].append(title)

        return {
            "total": len(results["ids"]),
            "types": {
                dt: {
                    "parent": v["parent"],
                    "child": v["child"],
                    "total": v["parent"] + v["child"],
                    "titles": sorted(v["titles"]),
                }
                for dt, v in sorted(types.items())
            },
        }


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="知识库管理工具")
    sub = parser.add_subparsers(dest="cmd", help="命令")

    # import
    p_import = sub.add_parser("import", help="导入知识数据")
    p_import.add_argument("path", nargs="+", help="文件或目录路径 (JSON/CSV/PDF/DOCX/TXT)")
    p_import.add_argument("--doc-type", help="知识类型标识")
    p_import.add_argument("--clear", action="store_true", help="导入前清除该类型旧数据")

    # clear
    p_clear = sub.add_parser("clear", help="清理指定分区")
    p_clear.add_argument("type", help="doc_type 名称 (如 job / resume_guide)")

    # stats
    sub.add_parser("stats", help="查看知识库分区统计")

    # rebuild — regenerate + reimport all
    p_rebuild = sub.add_parser("rebuild", help="重新生成并导入所有知识数据")
    p_rebuild.add_argument("--clear", action="store_true", help="导入前清除该类型旧数据")

    args = parser.parse_args()
    ingestion = KnowledgeIngestion()
    result = None

    if args.cmd == "import":
        SUPPORTED = {".json", ".csv", ".txt", ".pdf", ".doc", ".docx"}
        for p in args.path:
            path = Path(p)
            if path.is_dir():
                for f in sorted(path.glob("*")):
                    if f.suffix.lower() in SUPPORTED:
                        result = ingestion.import_file(str(f), doc_type=args.doc_type, clear_existing=args.clear)
                        print(result)
            else:
                result = ingestion.import_file(str(p), doc_type=args.doc_type, clear_existing=args.clear)
                print(result)

    elif args.cmd == "clear":
        result = ingestion.clear_type(args.type)
        print(result)

    elif args.cmd == "stats":
        result = ingestion.stats()
        print(f"Total documents: {result['total']}")
        for dt, info in result["types"].items():
            print(f"\n  [{dt}]  {info['total']} chunks (parent:{info['parent']} child:{info['child']})")
            for t in info["titles"]:
                print(f"    - {t}")

    elif args.cmd == "rebuild":
        import subprocess, sys
        knowledge_dir = Path(__file__).parent.parent.parent / "test_data" / "knowledge"
        gens = sorted(knowledge_dir.glob("gen_*.py"))
        for g in gens:
            print(f"[rebuild] Running {g.name}...")
            subprocess.run([sys.executable, str(g)], cwd=str(knowledge_dir.parent.parent), check=True)
        SUPPORTED = {".json", ".csv", ".txt", ".pdf", ".doc", ".docx"}
        for f in sorted(knowledge_dir.glob("*")):
            if f.name.startswith("gen_") or f.suffix.lower() not in SUPPORTED:
                continue
            result = ingestion.import_file(str(f), clear_existing=args.clear)
            print(result)

    else:
        parser.print_help()
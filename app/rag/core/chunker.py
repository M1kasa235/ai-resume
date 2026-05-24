"""知识库 Parent/Child 分层分块策略

- Parent chunk: 完整知识条目，上下文完整，用于最终生成
- Child chunk: 段落级小块，向量检索精准匹配
- 两阶段检索: search child → retrieve parent → 完整上下文
"""

import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class KnowledgeChunker:
    """知识库专用分块器，与简历的 smart_chunk 分离"""

    def __init__(
        self,
        child_size: int = 400,
        child_overlap: int = 80,
        min_parent_size: int = 200,
        max_parent_chars: int = 7000,
    ):
        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=child_size,
            chunk_overlap=child_overlap,
            separators=["\n\n", "\n", "。", "；", "、", " ", ""],
        )
        self.min_parent_size = min_parent_size
        self.max_parent_chars = max_parent_chars

    def chunk(self, content: str, parent_metadata: dict) -> tuple[list[Document], list[Document]]:
        """将一条知识拆分为 M 个 parent + N 个 child chunks

        长文档按段落边界切分为多个 section，每个 section 独立生成 parent+children，
        共享 doc_group_id。短文档（≤max_parent_chars）行为不变。

        Returns:
            ([parent_docs], [child_docs])
        """
        doc_group_id = str(uuid.uuid4())
        sections = self._split_into_sections(content, self.max_parent_chars)

        all_parents: list[Document] = []
        all_children: list[Document] = []

        for section_idx, section_text in enumerate(sections):
            if not section_text or not section_text.strip():
                continue

            parent_id = str(uuid.uuid4())
            section_meta = {
                **parent_metadata,
                "chunk_type": "parent",
                "parent_id": parent_id,
                "doc_group_id": doc_group_id,
                "section_index": section_idx,
                "total_sections": len(sections),
            }

            safe = section_text
            if len(section_text) > self.max_parent_chars:
                safe = section_text[:self.max_parent_chars]
                section_meta["truncated"] = True

            all_parents.append(Document(page_content=safe, metadata=section_meta))

            if len(section_text) >= self.min_parent_size:
                child_docs = self.child_splitter.split_documents(
                    [Document(page_content=section_text)]
                )
            else:
                # 短文本也生成一个 child，避免仅有 parent 导致默认检索漏召回。
                child_docs = [Document(page_content=section_text)]

            child_docs = [
                cd for cd in child_docs
                if cd.page_content and cd.page_content.strip()
            ]
            for ci, cd in enumerate(child_docs):
                cd.metadata = {
                    **section_meta,
                    "chunk_type": "child",
                    "chunk_id": str(uuid.uuid4()),
                    "parent_id": parent_id,
                    "doc_group_id": doc_group_id,
                    "child_index": ci,
                }
            all_children.extend(child_docs)

        return all_parents, all_children

    @staticmethod
    def _split_into_sections(content: str, max_chars: int) -> list[str]:
        """沿段落边界切分长文，每段 ≤ max_chars，避免截断句子"""
        paragraphs = content.split("\n\n")
        sections: list[str] = []
        current: list[str] = []
        current_len = 0

        for para in paragraphs:
            p = para.strip()
            if not p:
                continue
            # 加上 \n\n 分隔符开销：已有段之间 + 新段前
            sep_overhead = 2 * len(current)
            if current and current_len + sep_overhead + len(p) > max_chars:
                sections.append("\n\n".join(current))
                current = []
                current_len = 0
                sep_overhead = 0
            current.append(p)
            current_len += len(p)

        if current:
            sections.append("\n\n".join(current))

        return sections if sections else [content]
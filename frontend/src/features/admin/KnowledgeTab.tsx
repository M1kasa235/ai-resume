import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { adminApi } from '@services/api';
import type { KnowledgePartition, KnowledgeDocument } from '@/types/api';
import PartitionList from './PartitionList';
import DocumentList from './DocumentList';
import ChunkDetail from './ChunkDetail';

type ViewState =
  | { key: 'partitions' }
  | { key: 'documents'; docType: string }
  | { key: 'chunks'; docType: string; parentId: string; docTitle: string };

export default function KnowledgeTab() {
  const [viewState, setViewState] = useState<ViewState>({ key: 'partitions' });
  const [partitions, setPartitions] = useState<KnowledgePartition[]>([]);
  const [partLoading, setPartLoading] = useState(false);

  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [docTotal, setDocTotal] = useState(0);
  const [docPage, setDocPage] = useState(1);
  const [docPageSize, setDocPageSize] = useState(20);
  const [docLoading, setDocLoading] = useState(false);

  const fetchPartitions = useCallback(async () => {
    setPartLoading(true);
    try {
      const res = await adminApi.getPartitions();
      const d = (res as any).data || res;
      setPartitions(d.partitions || []);
    } catch {
      message.error('获取知识库分区失败');
    } finally {
      setPartLoading(false);
    }
  }, []);

  const fetchDocuments = useCallback(
    async (docType: string, page: number = 1, pageSize: number = 20) => {
      setDocLoading(true);
      try {
        const res = await adminApi.getDocuments({ doc_type: docType, page, page_size: pageSize });
        const d = (res as any).data || res;
        setDocuments(d.items || []);
        setDocTotal(d.total || 0);
        setDocPage(d.page || page);
        setDocPageSize(d.page_size || pageSize);
      } catch {
        message.error('获取文档列表失败');
      } finally {
        setDocLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    fetchPartitions();
  }, [fetchPartitions]);

  const goToDocuments = (docType: string) => {
    setViewState({ key: 'documents', docType });
    fetchDocuments(docType);
  };

  const goToChunks = (docType: string, parentId: string, docTitle: string) => {
    setViewState({ key: 'chunks', docType, parentId, docTitle });
  };

  const goToPartitions = () => {
    setViewState({ key: 'partitions' });
    fetchPartitions();
  };

  const handleImportFile = () => {
    fetchPartitions();
  };

  const goToDocList = () => {
    if (viewState.key === 'chunks') {
      const dt = (viewState as any).docType;
      setViewState({ key: 'documents', docType: dt });
      fetchDocuments(dt);
    }
  };

  if (viewState.key === 'documents') {
    return (
      <DocumentList
        docType={viewState.docType}
        documents={documents}
        total={docTotal}
        page={docPage}
        pageSize={docPageSize}
        loading={docLoading}
        onBack={goToPartitions}
        onSelectDocument={(parentId) => {
          const doc = documents.find((d) => d.parent_id === parentId);
          goToChunks(viewState.docType, parentId, doc?.title || '');
        }}
        onRefresh={() => fetchDocuments(viewState.docType, docPage, docPageSize)}
        onPageChange={(p, ps) => fetchDocuments(viewState.docType, p, ps)}
      />
    );
  }

  if (viewState.key === 'chunks') {
    return (
      <ChunkDetail
        parentId={viewState.parentId}
        docType={viewState.docType}
        docTitle={viewState.docTitle}
        onBack={goToDocList}
        onDeleted={goToDocList}
      />
    );
  }

  return (
    <PartitionList
      partitions={partitions}
      loading={partLoading}
      onSelect={goToDocuments}
      onImport={handleImportFile}
    />
  );
}

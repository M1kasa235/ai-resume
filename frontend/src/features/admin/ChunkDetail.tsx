import { useEffect, useState } from 'react';
import { Card, Table, Spin, Empty, Button, message, Tag, Descriptions, Popconfirm } from 'antd';
import { ArrowLeftOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { adminApi } from '@services/api';
import type { ChunkItem } from '@/types/api';
import DocumentFormModal from './DocumentFormModal';
import styles from './KnowledgeTab.module.scss';

interface Props {
  parentId: string;
  docType: string;
  docTitle: string;
  onBack: () => void;
  onDeleted: () => void;
}

export default function ChunkDetail({ parentId, docType, docTitle, onBack, onDeleted }: Props) {
  const [parent, setParent] = useState<ChunkItem | null>(null);
  const [children, setChildren] = useState<ChunkItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  const fetchChunks = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getDocumentChunks(parentId);
      const d = (res as any).data || res;
      setParent(d.parent);
      setChildren(d.children || []);
    } catch {
      message.error('获取文档详情失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChunks();
  }, [parentId]);

  const handleUpdate = async (values: {
    title: string;
    category: string;
    content: string;
    doc_type: string;
  }) => {
    try {
      await adminApi.updateDocument({
        parent_id: parentId,
        ...values,
      });
      message.success('更新成功');
      setModalOpen(false);
      fetchChunks();
    } catch {
      message.error('更新失败');
    }
  };

  const handleDelete = async () => {
    try {
      await adminApi.deleteDocument(parentId);
      message.success('删除成功');
      onDeleted();
    } catch {
      message.error('删除失败');
    }
  };

  if (loading) return <Spin style={{ display: 'block', margin: '40px auto' }} />;
  if (!parent) return <Empty description="文档不存在" style={{ margin: '40px 0' }} />;

  const meta = parent.metadata || {};

  const childColumns: ColumnsType<ChunkItem> = [
    { title: '#', dataIndex: 'child_index', key: 'idx', width: 50 },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (v: string) => (
        <span style={{ fontSize: 13, color: '#555' }}>{v}</span>
      ),
    },
    { title: 'ID', dataIndex: 'id', key: 'id', width: 120, ellipsis: true },
  ];

  return (
    <div>
      <div className={styles.toolbar}>
        <Button icon={<ArrowLeftOutlined />} onClick={onBack} type="text">
          返回文档列表
        </Button>
        <span className={styles.sectionTitle}>文档详情 — {docTitle}</span>
        <div>
          <Button icon={<EditOutlined />} onClick={() => setModalOpen(true)} style={{ marginRight: 8 }}>
            编辑
          </Button>
          <Popconfirm title="确定删除此文档及其所有子分块？" onConfirm={handleDelete}>
            <Button danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </div>
      </div>

      <Card title="Parent 文档（完整内容）" className={styles.parentCard}>
        <Descriptions column={2} size="small" style={{ marginBottom: 16 }}>
          <Descriptions.Item label="文档ID">{parentId}</Descriptions.Item>
          <Descriptions.Item label="标题">{String(meta.title || docTitle)}</Descriptions.Item>
          <Descriptions.Item label="分类">
            {meta.category ? <Tag>{String(meta.category)}</Tag> : '—'}
          </Descriptions.Item>
          <Descriptions.Item label="分区">
            <Tag color="blue">{String(meta.doc_type || docType)}</Tag>
          </Descriptions.Item>
        </Descriptions>
        <pre className={styles.contentBlock}>{parent.content}</pre>
      </Card>

      <Card title={`Child 分块（${children.length} 个）`} style={{ marginTop: 16 }}>
        {children.length === 0 ? (
          <Empty description="该文档没有子分块" />
        ) : (
          <Table
            rowKey="id"
            columns={childColumns}
            dataSource={children}
            size="small"
            pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 个分块` }}
          />
        )}
      </Card>

      <DocumentFormModal
        open={modalOpen}
        editing={{
          id: parentId,
          parent_id: parentId,
          title: String(meta.title || ''),
          category: String(meta.category || ''),
          content: parent.content || '',
          content_full: parent.content || '',
          doc_type: String(meta.doc_type || docType),
          source_file: String(meta.source_file || ''),
        }}
        defaultDocType={docType}
        onCancel={() => setModalOpen(false)}
        onSave={handleUpdate}
      />
    </div>
  );
}

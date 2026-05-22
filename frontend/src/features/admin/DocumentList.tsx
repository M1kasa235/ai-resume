import { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Popconfirm,
  Upload,
  message,
  Spin,
  Empty,
} from 'antd';
import {
  PlusOutlined,
  UploadOutlined,
  DeleteOutlined,
  EditOutlined,
  ArrowLeftOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { adminApi } from '@services/api';
import type { KnowledgeDocument } from '@/types/api';
import DocumentFormModal from './DocumentFormModal';
import styles from './KnowledgeTab.module.scss';

interface Props {
  docType: string;
  documents: KnowledgeDocument[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  onBack: () => void;
  onSelectDocument: (docId: string) => void;
  onRefresh: () => void;
  onPageChange: (page: number, pageSize: number) => void;
}

export default function DocumentList({
  docType,
  documents,
  total,
  page,
  pageSize,
  loading,
  onBack,
  onSelectDocument,
  onRefresh,
  onPageChange,
}: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<KnowledgeDocument | null>(null);

  const formatLabel = (dt: string) =>
    dt.replace(/_knowledge$/, '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  const handleCreate = () => {
    setEditing(null);
    setModalOpen(true);
  };

  const handleEdit = (doc: KnowledgeDocument) => {
    setEditing(doc);
    setModalOpen(true);
  };

  const handleSave = async (values: {
    title: string;
    category: string;
    content: string;
    doc_type: string;
  }) => {
    try {
      if (editing) {
        await adminApi.updateDocument({
          parent_id: editing.parent_id,
          ...values,
        });
        message.success('更新成功');
      } else {
        await adminApi.createDocument(values);
        message.success('创建成功');
      }
      setModalOpen(false);
      onRefresh();
    } catch {
      message.error('操作失败');
    }
  };

  const handleDelete = async (parentId: string) => {
    try {
      await adminApi.deleteDocument(parentId);
      message.success('删除成功');
      onRefresh();
    } catch {
      message.error('删除失败');
    }
  };

  const handleUpload = async (file: File) => {
    try {
      const res = await adminApi.importJobs(file, docType);
      const d = (res as any).data || res;
      message.success(`导入成功: ${d.records || 0} 条记录`);
      onRefresh();
    } catch {
      message.error('导入失败');
    }
    return false;
  };

  const columns: ColumnsType<KnowledgeDocument> = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      ellipsis: true,
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (v: string) => v ? <Tag>{v}</Tag> : null,
    },
    {
      title: '内容预览',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (v: string) => (
        <span style={{ color: '#666', fontSize: 13 }}>{v}</span>
      ),
    },
    {
      title: '分区',
      dataIndex: 'doc_type',
      key: 'doc_type',
      width: 130,
      render: (v: string) => <Tag color="blue">{formatLabel(v)}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: any, record: KnowledgeDocument) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="确定删除此文档及其所有分块？" onConfirm={() => handleDelete(record.parent_id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div className={styles.toolbar}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={onBack} type="text">
            返回分区
          </Button>
          <span className={styles.sectionTitle}>
            {formatLabel(docType)} — 文档列表
          </span>
        </Space>
        <Space>
          <Upload
            accept=".json,.csv,.pdf,.docx,.txt"
            showUploadList={false}
            beforeUpload={handleUpload}
          >
            <Button icon={<UploadOutlined />}>导入文件</Button>
          </Upload>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建文档
          </Button>
          <Button icon={<ReloadOutlined />} onClick={onRefresh}>刷新</Button>
        </Space>
      </div>

      {loading ? (
        <Spin style={{ display: 'block', margin: '40px auto' }} />
      ) : documents.length === 0 ? (
        <Empty description="该分区暂无文档" style={{ margin: '40px 0' }} />
      ) : (
        <Table
          rowKey="id"
          columns={columns}
          dataSource={documents}
          pagination={{
            current: page,
            total,
            pageSize,
            onChange: onPageChange,
            showTotal: (t) => `共 ${t} 条`,
          }}
          size="small"
          onRow={(record) => ({
            onClick: () => onSelectDocument(record.parent_id),
            style: { cursor: 'pointer' },
          })}
        />
      )}

      <DocumentFormModal
        open={modalOpen}
        editing={editing}
        defaultDocType={docType}
        onCancel={() => setModalOpen(false)}
        onSave={handleSave}
      />
    </div>
  );
}

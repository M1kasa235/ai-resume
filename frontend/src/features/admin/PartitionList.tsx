import { useState } from 'react';
import {
  Card, Row, Col, Statistic, Typography, Spin, Empty, Tag,
  Upload, Button, Space, message, Modal, Input, Popconfirm,
} from 'antd';
import {
  FileTextOutlined,
  BookOutlined,
  ExperimentOutlined,
  DatabaseOutlined,
  UploadOutlined,
  ReloadOutlined,
  PlusOutlined,
  DeleteOutlined,
  SnippetsOutlined,
} from '@ant-design/icons';
import { adminApi } from '@services/api';
import type { KnowledgePartition } from '@/types/api';
import styles from './KnowledgeTab.module.scss';

const { Text } = Typography;

const PARTITION_ICONS: Record<string, React.ReactNode> = {
  resume_guide: <FileTextOutlined />,
  interview: <ExperimentOutlined />,
  job: <BookOutlined />,
};

const PARTITION_COLORS: Record<string, string> = {
  resume_guide: '#1677ff',
  interview: '#52c41a',
  job: '#fa8c16',
};

function getIcon(docType: string) {
  for (const key of Object.keys(PARTITION_ICONS)) {
    if (docType.includes(key)) return PARTITION_ICONS[key];
  }
  return <DatabaseOutlined />;
}

function getColor(docType: string) {
  for (const key of Object.keys(PARTITION_COLORS)) {
    if (docType.includes(key)) return PARTITION_COLORS[key];
  }
  return '#8c8c8c';
}

function formatLabel(docType: string) {
  return docType
    .replace(/_knowledge$/, '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

interface Props {
  partitions: KnowledgePartition[];
  loading: boolean;
  onSelect: (docType: string) => void;
  onImport: () => void;
}

export default function PartitionList({ partitions, loading, onSelect, onImport }: Props) {
  const [uploading, setUploading] = useState(false);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [newKey, setNewKey] = useState('');
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const handleFileImport = async (file: File) => {
    setUploading(true);
    try {
      const res = await adminApi.importJobs(file);
      const d = (res as any).data || res;
      const records = d.records || d.parent_chunks || 0;
      message.success(`导入成功: ${records} 条记录`);
      onImport();
    } catch (e: any) {
      message.error(e?.message || '导入失败');
    } finally {
      setUploading(false);
    }
    return false;
  };

  const handleCreatePartition = async () => {
    if (!newKey.trim() || !newName.trim()) {
      message.warning('请填写分区标识和名称');
      return;
    }
    setCreating(true);
    try {
      await adminApi.createPartition({
        doc_key: newKey.trim(),
        name: newName.trim(),
        description: newDesc.trim(),
      });
      message.success('分区创建成功');
      setCreateModalOpen(false);
      setNewKey('');
      setNewName('');
      setNewDesc('');
      onImport();
    } catch (e: any) {
      message.error(e?.message || '创建失败');
    } finally {
      setCreating(false);
    }
  };

  const handleDeletePartition = async (id: number) => {
    try {
      await adminApi.deletePartition(id);
      message.success('分区已删除');
      onImport();
    } catch (e: any) {
      message.error(e?.message || '删除失败');
    }
  };

  const uploadButton = (
    <Upload
      accept=".json,.csv,.pdf,.docx,.txt"
      showUploadList={false}
      beforeUpload={handleFileImport}
    >
      <Button icon={<UploadOutlined />} loading={uploading}>
        导入文件
      </Button>
    </Upload>
  );

  if (loading) return <Spin style={{ display: 'block', margin: '40px auto' }} />;
  if (!partitions.length)
    return (
      <>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Empty description="暂无知识库分区" />
          <div style={{ marginTop: 16 }}>
            <Space>
              <Button icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
                新建分区
              </Button>
              {uploadButton}
            </Space>
          </div>
        </div>

        <Modal
          title="新建知识库分区"
          open={createModalOpen}
          onOk={handleCreatePartition}
          onCancel={() => {
            setCreateModalOpen(false);
            setNewKey('');
            setNewName('');
            setNewDesc('');
          }}
          confirmLoading={creating}
          okText="创建"
          cancelText="取消"
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 8 }}>
            <div>
              <Text strong style={{ display: 'block', marginBottom: 4 }}>分区标识（英文）</Text>
              <Input
                placeholder="如 my_kb"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value.replace(/\s/g, '_').toLowerCase())}
              />
            </div>
            <div>
              <Text strong style={{ display: 'block', marginBottom: 4 }}>分区名称</Text>
              <Input
                placeholder="如 我的知识库"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
            </div>
            <div>
              <Text strong style={{ display: 'block', marginBottom: 4 }}>描述（可选）</Text>
              <Input.TextArea
                placeholder="简要描述此分区的用途"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                rows={3}
              />
            </div>
          </div>
        </Modal>
      </>
    );

  return (
    <div>
      <div className={styles.toolbar}>
        <span className={styles.sectionTitle}>知识库分区</span>
        <Space>
          <Button icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
            新建分区
          </Button>
          {uploadButton}
          <Button icon={<ReloadOutlined />} onClick={onImport}>刷新</Button>
        </Space>
      </div>
      <Row gutter={[16, 16]}>
        {partitions.map((p) => (
          <Col key={p.doc_type} xs={24} sm={12} md={8} lg={6}>
            <Card
              hoverable
              className={styles.partitionCard}
              onClick={() => onSelect(p.doc_type)}
            >
              <div className={styles.cardHeader}>
                <span className={styles.cardIcon} style={{ color: getColor(p.doc_type) }}>
                  {getIcon(p.doc_type)}
                </span>
                <Text strong>{formatLabel(p.doc_type)}</Text>
                <Popconfirm
                  title="确认删除此分区？"
                  description="分区内所有文档和分块将被永久删除"
                  onConfirm={(e) => {
                    e?.stopPropagation();
                    handleDeletePartition(p.id!);
                  }}
                  onCancel={(e) => e?.stopPropagation()}
                  okText="删除"
                  cancelText="取消"
                  okButtonProps={{ danger: true }}
                >
                  <Button
                    type="text"
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={(e) => e.stopPropagation()}
                    style={{ marginLeft: 'auto' }}
                  />
                </Popconfirm>
              </div>
              <Row gutter={12} style={{ marginTop: 16 }}>
                <Col span={12}>
                  <Statistic title="文档" value={p.parent_count} suffix="篇" />
                </Col>
                <Col span={12}>
                  <Statistic title="分块" value={p.total} suffix="个" />
                </Col>
              </Row>
              {p.titles.length > 0 && (
                <div className={styles.titleTags}>
                  {p.titles.slice(0, 5).map((t) => (
                    <Tag key={t} color={getColor(p.doc_type)} style={{ marginBottom: 4 }}>
                      {t.length > 15 ? t.slice(0, 15) + '...' : t}
                    </Tag>
                  ))}
                  {p.titles.length > 5 && (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      +{p.titles.length - 5} 更多
                    </Text>
                  )}
                </div>
              )}
            </Card>
          </Col>
        ))}
      </Row>

      <Modal
        title="新建知识库分区"
        open={createModalOpen}
        onOk={handleCreatePartition}
        onCancel={() => {
          setCreateModalOpen(false);
          setNewKey('');
          setNewName('');
          setNewDesc('');
        }}
        confirmLoading={creating}
        okText="创建"
        cancelText="取消"
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 8 }}>
          <div>
            <Text strong style={{ display: 'block', marginBottom: 4 }}>分区标识（英文）</Text>
            <Input
              placeholder="如 my_kb"
              value={newKey}
              onChange={(e) => setNewKey(e.target.value.replace(/\s/g, '_').toLowerCase())}
            />
          </div>
          <div>
            <Text strong style={{ display: 'block', marginBottom: 4 }}>分区名称</Text>
            <Input
              placeholder="如 我的知识库"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
            />
          </div>
          <div>
            <Text strong style={{ display: 'block', marginBottom: 4 }}>描述（可选）</Text>
            <Input.TextArea
              placeholder="简要描述此分区的用途"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              rows={3}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}

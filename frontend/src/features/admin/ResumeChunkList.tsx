import { useEffect, useState } from 'react';
import { Card, Table, Spin, Empty, Button, message, Tag, Popconfirm, Descriptions } from 'antd';
import { ArrowLeftOutlined, DeleteOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { adminApi } from '@services/api';
import type { ResumeChunkItem } from '@/types/api';
import styles from './KnowledgeTab.module.scss';

interface Props {
  userId: number;
  section: string;
  label: string;
  onBack: () => void;
  onDeleted: () => void;
}

export default function ResumeChunkList({ userId, section, label, onBack, onDeleted }: Props) {
  const [chunks, setChunks] = useState<ResumeChunkItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const fetchChunks = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getResumeChunks(userId, section);
      const d = (res as any).data || res;
      setChunks(d.items || []);
    } catch {
      message.error('获取分块列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChunks();
  }, [userId, section]);

  const handleDeleteSelected = async () => {
    if (selectedRowKeys.length === 0) return;
    try {
      await adminApi.deleteResumeChunks(selectedRowKeys as string[]);
      message.success(`已删除 ${selectedRowKeys.length} 个分块`);
      setSelectedRowKeys([]);
      fetchChunks();
    } catch {
      message.error('删除失败');
    }
  };

  const handleDeleteSingle = async (id: string) => {
    try {
      await adminApi.deleteResumeChunks([id]);
      message.success('删除成功');
      fetchChunks();
    } catch {
      message.error('删除失败');
    }
  };

  if (loading) return <Spin style={{ display: 'block', margin: '40px auto' }} />;
  if (!chunks.length) return <Empty description="该分区暂无数据" style={{ margin: '40px 0' }} />;

  const firstMeta = chunks[0]?.metadata || {};

  const columns: ColumnsType<ResumeChunkItem> = [
    { title: '#', dataIndex: ['metadata', 'chunk_index'], key: 'idx', width: 50 },
    {
      title: '内容',
      dataIndex: 'content',
      key: 'content',
      ellipsis: true,
      render: (v: string) => (
        <span style={{ fontSize: 13, color: '#555' }}>{v}</span>
      ),
    },
    {
      title: '来源',
      dataIndex: ['metadata', 'source'],
      key: 'source',
      width: 180,
      ellipsis: true,
      render: (v: string) => (v ? <Tag>{v}</Tag> : '—'),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: ResumeChunkItem) => (
        <Popconfirm title="确定删除此分块？" onConfirm={() => handleDeleteSingle(record.id)}>
          <Button type="link" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div className={styles.toolbar}>
        <Button icon={<ArrowLeftOutlined />} onClick={onBack} type="text">
          返回分区列表
        </Button>
        <span className={styles.sectionTitle}>
          用户 #{userId} — {label}（共 {chunks.length} 个分块）
        </span>
        {selectedRowKeys.length > 0 && (
          <Popconfirm title={`确定删除选中的 ${selectedRowKeys.length} 个分块？`} onConfirm={handleDeleteSelected}>
            <Button danger icon={<DeleteOutlined />}>删除选中</Button>
          </Popconfirm>
        )}
      </div>

      <Card size="small" style={{ marginBottom: 16 }}>
        <Descriptions column={4} size="small">
          <Descriptions.Item label="用户ID">{userId}</Descriptions.Item>
          <Descriptions.Item label="分区">{label}</Descriptions.Item>
          <Descriptions.Item label="分块总数">{chunks.length}</Descriptions.Item>
          <Descriptions.Item label="来源文件">
            {String(firstMeta.source || '—')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Table
        rowKey="id"
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys,
        }}
        columns={columns}
        dataSource={chunks}
        size="small"
        pagination={{ pageSize: 10, showTotal: (t) => `共 ${t} 个分块` }}
      />
    </div>
  );
}
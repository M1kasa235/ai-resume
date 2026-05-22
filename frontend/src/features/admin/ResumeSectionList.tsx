import { Card, Row, Col, Statistic, Typography, Spin, Empty, Button, Popconfirm, message } from 'antd';
import { ArrowLeftOutlined, DeleteOutlined, FolderOutlined } from '@ant-design/icons';
import { adminApi } from '@services/api';
import type { ResumeSection } from '@/types/api';
import styles from './KnowledgeTab.module.scss';

const { Text } = Typography;

const SECTION_COLORS: Record<string, string> = {
  personal_info: '#1677ff',
  skills: '#52c41a',
  work_experience: '#fa8c16',
  projects: '#722ed1',
  education: '#13c2c2',
  self_evaluation: '#eb2f96',
  other: '#8c8c8c',
};

interface Props {
  userId: number;
  sections: ResumeSection[];
  totalChunks: number;
  loading: boolean;
  onBack: () => void;
  onSelect: (section: string, label: string) => void;
  onDeleted: () => void;
}

export default function ResumeSectionList({
  userId,
  sections,
  totalChunks,
  loading,
  onBack,
  onSelect,
  onDeleted,
}: Props) {
  const handleDeleteUser = async () => {
    try {
      await adminApi.deleteResumeUser(userId);
      message.success('删除成功');
      onDeleted();
    } catch {
      message.error('删除失败');
    }
  };

  if (loading) return <Spin style={{ display: 'block', margin: '40px auto' }} />;
  if (!sections.length) return <Empty description="该用户没有简历数据" style={{ margin: '40px 0' }} />;

  return (
    <div>
      <div className={styles.toolbar}>
        <Button icon={<ArrowLeftOutlined />} onClick={onBack} type="text">
          返回用户列表
        </Button>
        <span className={styles.sectionTitle}>用户 #{userId} — 简历分区（共 {totalChunks} 个分块）</span>
        <Popconfirm title="确定删除该用户的所有简历数据？" onConfirm={handleDeleteUser}>
          <Button danger icon={<DeleteOutlined />}>删除全部</Button>
        </Popconfirm>
      </div>
      <Row gutter={[16, 16]}>
        {sections.map((s) => (
          <Col key={s.section} xs={24} sm={12} md={8} lg={6}>
            <Card
              hoverable
              className={styles.partitionCard}
              onClick={() => onSelect(s.section, s.label)}
            >
              <div className={styles.cardHeader}>
                <span
                  className={styles.cardIcon}
                  style={{ color: SECTION_COLORS[s.section] || '#8c8c8c' }}
                >
                  <FolderOutlined />
                </span>
                <Text strong>{s.label}</Text>
              </div>
              <div style={{ marginTop: 16 }}>
                <Statistic
                  title="分块数"
                  value={s.chunk_count}
                  suffix="个"
                  valueStyle={{ fontSize: 20 }}
                />
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
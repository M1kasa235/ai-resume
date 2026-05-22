import { Card, Row, Col, Statistic, Typography, Spin, Empty, Tag } from 'antd';
import { UserOutlined, FileTextOutlined } from '@ant-design/icons';
import type { ResumeUser } from '@/types/api';
import styles from './KnowledgeTab.module.scss';

const { Text } = Typography;

interface Props {
  users: ResumeUser[];
  loading: boolean;
  onSelect: (userId: number) => void;
}

export default function ResumeUserList({ users, loading, onSelect }: Props) {
  if (loading) return <Spin style={{ display: 'block', margin: '40px auto' }} />;
  if (!users.length) return <Empty description="暂无用户上传简历" style={{ margin: '40px 0' }} />;

  return (
    <div>
      <div className={styles.sectionTitle}>简历管理 — 用户列表</div>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {users.map((u) => (
          <Col key={u.user_id} xs={24} sm={12} md={8} lg={6}>
            <Card
              hoverable
              className={styles.partitionCard}
              onClick={() => onSelect(u.user_id)}
            >
              <div className={styles.cardHeader}>
                <span className={styles.cardIcon} style={{ color: '#1677ff' }}>
                  <UserOutlined />
                </span>
                <Text strong>用户 #{u.user_id}</Text>
              </div>
              <Row gutter={12} style={{ marginTop: 16 }}>
                <Col span={12}>
                  <Statistic
                    title="分区数"
                    value={u.section_count}
                    suffix="个"
                    valueStyle={{ fontSize: 20 }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="分块数"
                    value={u.chunk_count}
                    suffix="个"
                    valueStyle={{ fontSize: 20 }}
                  />
                </Col>
              </Row>
              {u.sections.length > 0 && (
                <div className={styles.titleTags}>
                  {u.sections.map((s) => (
                    <Tag key={s} color="#1677ff" style={{ marginBottom: 4 }}>
                      {s}
                    </Tag>
                  ))}
                </div>
              )}
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
}
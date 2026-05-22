import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Empty, List, Pagination, Spin, Tag, Typography } from 'antd';
import { FileTextOutlined, RobotOutlined } from '@ant-design/icons';
import { aiInterviewApi } from '@services/api';
import type { AIInterviewReportListItem } from '@/types/api';
import styles from './History.module.scss';

const { Title, Text } = Typography;

const typeLabels: Record<string, string> = {
  technical: '技术面试',
  hr: 'HR 面试',
  comprehensive: '综合面试',
  behavioral: 'HR 面试',
};

export default function AIInterviewHistory() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const { data, isLoading } = useQuery({
    queryKey: ['ai-interview-reports', page],
    queryFn: async () => {
      const res = await aiInterviewApi.listReports(page, pageSize);
      return res as unknown as { total: number; items: AIInterviewReportListItem[] };
    },
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <div className={styles.history}>
      <div className={styles.header}>
        <Title level={4} style={{ margin: 0 }}>
          <RobotOutlined /> 面试记录
        </Title>
        <Button type="primary" onClick={() => navigate('/ai-interview')}>
          开始新面试
        </Button>
      </div>

      {isLoading ? (
        <div className={styles.loading}>
          <Spin size="large" />
        </div>
      ) : items.length === 0 ? (
        <Card>
          <Empty description="暂无面试记录">
            <Button type="primary" onClick={() => navigate('/ai-interview')}>
              去模拟面试
            </Button>
          </Empty>
        </Card>
      ) : (
        <>
          <List
            dataSource={items}
            renderItem={(item) => (
              <Card
                hoverable
                className={styles.card}
                onClick={() => navigate(`/ai-interview/report/${item.session_id}`)}
              >
                <div className={styles.cardContent}>
                  <div className={styles.cardLeft}>
                    <FileTextOutlined className={styles.icon} />
                    <div className={styles.cardInfo}>
                      <Text strong className={styles.cardTitle}>
                        {item.job_title || '模拟面试'}
                      </Text>
                      {item.company_name && (
                        <Text type="secondary" style={{ fontSize: 12 }}>{item.company_name}</Text>
                      )}
                      <div className={styles.cardMeta}>
                        <Tag color="blue">{typeLabels[item.interview_type ?? ''] || item.interview_type}</Tag>
                        <Text type="secondary">共 {item.total_questions} 题</Text>
                      </div>
                    </div>
                  </div>
                  <div className={styles.cardRight}>
                    {item.status === 'evaluating' ? (
                      <Tag color="processing">评估中</Tag>
                    ) : item.overall_score != null ? (
                      <div className={styles.score}>
                        <Text style={{ fontSize: 24, fontWeight: 700, color: item.overall_score >= 80 ? '#52c41a' : item.overall_score >= 60 ? '#faad14' : '#ff4d4f' }}>
                          {item.overall_score}
                        </Text>
                        <Text type="secondary">分</Text>
                      </div>
                    ) : null}
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.ended_at ? new Date(item.ended_at).toLocaleDateString() : '-'}
                    </Text>
                  </div>
                </div>
              </Card>
            )}
          />
          {total > pageSize && (
            <div className={styles.pagination}>
              <Pagination
                current={page}
                pageSize={pageSize}
                total={total}
                onChange={setPage}
                showTotal={(t) => `共 ${t} 条记录`}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}

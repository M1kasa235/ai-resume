import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Button, Card, Collapse, Descriptions, Empty, Progress, Segmented, Spin, Tag, Typography, Result } from 'antd';
import { ArrowLeftOutlined, LoadingOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { aiInterviewApi } from '@services/api';
import type { AIInterviewReport } from '@/types/api';
import styles from './Report.module.scss';

const { Title, Text, Paragraph } = Typography;

type ViewMode = 'structured' | 'markdown';

const typeLabels: Record<string, string> = {
  technical: '技术面试',
  hr: 'HR 面试',
  comprehensive: '综合面试',
  behavioral: 'HR 面试',
};

export default function AIInterviewReport() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<ViewMode>('structured');

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: ['ai-interview-report', id],
    queryFn: async () => {
      const res = await aiInterviewApi.getReport(id!);
      return res as unknown as AIInterviewReport;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const d = query.state.data as AIInterviewReport | undefined;
      if (d?.status === 'evaluating') return 3000;
      return false;
    },
  });

  if (isLoading) {
    return (
      <div className={styles.loading}>
        <Spin size="large" tip="加载报告中..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className={styles.error}>
        <Empty description="报告加载失败" />
        <Button onClick={() => navigate('/ai-interview')}>返回 AI 面试</Button>
      </div>
    );
  }

  if (data.status === 'evaluating') {
    return (
      <div className={styles.loading}>
        <Result
          icon={<LoadingOutlined spin style={{ fontSize: 48, color: '#1677ff' }} />}
          title="报告生成中"
          subTitle={
            <span>
              AI 正在评估你的面试表现，请稍候...
              {isFetching && <Spin size="small" style={{ marginLeft: 8 }} />}
            </span>
          }
          extra={
            <Button onClick={() => navigate('/ai-interview')}>
              返回 AI 面试
            </Button>
          }
        />
      </div>
    );
  }

  const scoreColor = (data.overall_score ?? 0) >= 80 ? '#52c41a' : (data.overall_score ?? 0) >= 60 ? '#faad14' : '#ff4d4f';

  return (
    <div className={styles.report}>
      <div className={styles.header}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/ai-interview')}>
          返回 AI 面试
        </Button>
        <Segmented
          options={[
            { label: '结构化', value: 'structured' as const },
            { label: 'Markdown 完整报告', value: 'markdown' as const },
          ]}
          value={viewMode}
          onChange={(v) => setViewMode(v as ViewMode)}
        />
      </div>

      {viewMode === 'markdown' && data.report_markdown ? (
        <Card className={styles.markdownCard}>
          <ReactMarkdown
            components={{
              h1: ({ children }) => <Title level={2} style={{ marginTop: 0 }}>{children}</Title>,
              h2: ({ children }) => <Title level={3} style={{ marginTop: 24 }}>{children}</Title>,
              h3: ({ children }) => <Title level={4} style={{ marginTop: 20 }}>{children}</Title>,
              p: ({ children }) => <Paragraph style={{ lineHeight: 1.8 }}>{children}</Paragraph>,
              strong: ({ children }) => <Text strong>{children}</Text>,
              ul: ({ children }) => <ul className={styles.mdList}>{children}</ul>,
              ol: ({ children }) => <ol className={styles.mdList}>{children}</ol>,
              li: ({ children }) => <li className={styles.mdListItem}>{children}</li>,
              hr: () => <hr className={styles.mdHr} />,
              code: ({ className, children }) => {
                const text = String(children).replace(/\n$/, '');
                if (className) {
                  return <code className={styles.mdCode}>{text}</code>;
                }
                return <code className={styles.mdInlineCode}>{text}</code>;
              },
              blockquote: ({ children }) => (
                <blockquote className={styles.mdBlockquote}>{children}</blockquote>
              ),
            }}
          >
            {data.report_markdown}
          </ReactMarkdown>
        </Card>
      ) : (
        <>
          <Card className={styles.summary}>
        <div className={styles.scoreArea}>
          <Progress
            type="circle"
            percent={data.overall_score ?? 0}
            format={(p) => `${p}分`}
            size={140}
            strokeColor={scoreColor}
          />
          <div className={styles.scoreInfo}>
            <Title level={3} style={{ margin: 0 }}>
              {data.job_title || '模拟面试'}
            </Title>
            {data.company_name && (
              <Text type="secondary" style={{ fontSize: 13 }}>{data.company_name}</Text>
            )}
            <div className={styles.meta}>
              <Tag color="blue">{typeLabels[data.interview_type ?? ''] || data.interview_type}</Tag>
              <Text type="secondary">共 {data.total_questions} 题</Text>
            </div>
          </div>
        </div>

        <Descriptions column={2} size="small" className={styles.descriptions}>
          <Descriptions.Item label="开始时间">{data.started_at ? new Date(data.started_at).toLocaleString() : '-'}</Descriptions.Item>
          <Descriptions.Item label="结束时间">{data.ended_at ? new Date(data.ended_at).toLocaleString() : '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      {data.strength_analysis && (
        <Card title="优势分析" className={styles.analysis}>
          <Paragraph>{data.strength_analysis}</Paragraph>
        </Card>
      )}

      {data.weakness_analysis && (
        <Card title="待改进点" className={styles.analysis}>
          <Paragraph>{data.weakness_analysis}</Paragraph>
        </Card>
      )}

      {data.improvement_suggestions && (
        <Card title="改进建议" className={styles.analysis}>
          <Paragraph>{data.improvement_suggestions}</Paragraph>
        </Card>
      )}

      {data.evaluations.length > 0 && (
        <Card title={`逐题评估（共 ${data.evaluations.length} 题）`} className={styles.evaluations}>
          <Collapse
            items={data.evaluations.map((ev) => ({
              key: String(ev.sequence),
              label: (
                <div className={styles.qaLabel}>
                  <span className={styles.qaSeq}>Q{ev.sequence}</span>
                  <span className={styles.qaTitle}>
                    {ev.question ? ev.question.slice(0, 60) + (ev.question.length > 60 ? '...' : '') : '查看详情'}
                  </span>
                  {ev.score != null && (
                    <Tag color={ev.score >= 7 ? 'green' : ev.score >= 5 ? 'orange' : 'red'}>
                      {ev.score}/10
                    </Tag>
                  )}
                </div>
              ),
              children: (
                <div className={styles.qaDetail}>
                  <div className={styles.qaQuestion}>
                    <Text strong>面试官提问：</Text>
                    <Paragraph>{ev.question || '-'}</Paragraph>
                  </div>
                  <div className={styles.qaAnswer}>
                    <Text strong>你的回答：</Text>
                    <Paragraph>{ev.answer || '（未回答）'}</Paragraph>
                  </div>
                  {ev.comment && (
                    <div className={styles.qaComment}>
                      <Text strong>点评：</Text>
                      <Paragraph>{ev.comment}</Paragraph>
                    </div>
                  )}
                  {ev.suggested_answer && (
                    <div className={styles.qaSuggested}>
                      <Text strong>参考回答：</Text>
                      <Paragraph>{ev.suggested_answer}</Paragraph>
                    </div>
                  )}
                </div>
              ),
            }))}
          />
        </Card>
      )}
      </>
      )}
    </div>
  );
}

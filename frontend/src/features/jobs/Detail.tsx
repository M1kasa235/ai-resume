import { useState } from 'react';

import {
  ArrowLeftOutlined,
  HeartOutlined,
  HeartFilled,
  EnvironmentOutlined,
  BankOutlined,
  TeamOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { jobApi, workbenchApi } from '@services/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Row,
  Col,
  Button,
  Tag,
  Space,
  Skeleton,
  Empty,
  Divider,
  Descriptions,
  message,
  Modal,
  Typography,
} from 'antd';
import { useParams, useNavigate } from 'react-router-dom';

import type { Job } from '@/types/api';

import styles from './JobDetail.module.scss';

const formatSalary = (min?: number, max?: number) => {
  if (min && max) return `${min}K-${max}K`;
  if (min) return `${min}K+`;
  return '面议';
};

const formatExperience = (min?: number, max?: number) => {
  if (min && max) return `${min}-${max}年`;
  if (min) return `${min}年+`;
  return '经验不限';
};

export default function JobDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [applyModalVisible, setApplyModalVisible] = useState(false);
  const [isFavorited, setIsFavorited] = useState(false);

  const { data: job, isLoading } = useQuery({
    queryKey: ['job', id],
    queryFn: () => jobApi.getJobDetail(Number(id)),
    enabled: !!id,
  });

  const jobData = job as Job | undefined;

  const applyMutation = useMutation({
    mutationFn: (data: { job_id: number; notes?: string }) =>
      workbenchApi.applyJob(data),
    onSuccess: () => {
      message.success('投递成功！');
      setApplyModalVisible(false);
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '投递失败，请重试';
      message.error(errorMsg);
    },
  });

  const handleApply = () => {
    if (!id) return;
    setApplyModalVisible(true);
  };

  const confirmApply = (notes?: string) => {
    if (!id) return;
    applyMutation.mutate({ job_id: Number(id), notes });
  };

  const toggleFavorite = async () => {
    if (!id) return;
    try {
      if (isFavorited) {
        await jobApi.removeFavorite(Number(id));
        setIsFavorited(false);
      } else {
        await jobApi.addFavorite(Number(id));
        setIsFavorited(true);
      }
    } catch {
      message.error('操作失败');
    }
  };

  if (isLoading) {
    return (
      <div className={styles.jobDetail}>
        <Skeleton active paragraph={{ rows: 1 }} />
        <Card style={{ marginTop: 16 }}>
          <Skeleton active paragraph={{ rows: 8 }} />
        </Card>
      </div>
    );
  }

  if (!jobData) {
    return (
      <div className={styles.jobDetail} style={{ textAlign: 'center', paddingTop: 80 }}>
        <Empty description="岗位不存在" />
        <Button type="primary" onClick={() => navigate('/jobs')} style={{ marginTop: 16 }}>
          返回岗位列表
        </Button>
      </div>
    );
  }

  return (
    <div className={styles.jobDetail}>
      <Button
        icon={<ArrowLeftOutlined />}
        type="text"
        onClick={() => navigate('/jobs')}
        className={styles.backBtn}
      >
        返回列表
      </Button>

      <Row gutter={[20, 20]}>
        <Col xs={24} lg={16}>
          {/* 主信息卡片 */}
          <Card className={styles.mainCard}>
            <div className={styles.jobHeader}>
              <div className={styles.jobTitleRow}>
                <h1 className={styles.jobTitle}>
                  {jobData.title}
                  {jobData.is_urgent && <Tag color="red" className={styles.urgentTag}>急聘</Tag>}
                </h1>
                <span className={styles.salaryBadge}>
                  {formatSalary(jobData.salary_min, jobData.salary_max)}
                </span>
              </div>

              <div className={styles.jobMeta}>
                <span><EnvironmentOutlined /> {jobData.city || '地点不限'}</span>
                <span className={styles.metaDot}>·</span>
                <span>{formatExperience(jobData.experience_min, jobData.experience_max)}</span>
                {jobData.education_requirement && (
                  <>
                    <span className={styles.metaDot}>·</span>
                    <span>{jobData.education_requirement}</span>
                  </>
                )}
              </div>

              <div className={styles.jobActions}>
                <Button type="primary" size="large" onClick={handleApply}>
                  立即投递
                </Button>
                <Button
                  size="large"
                  icon={isFavorited ? <HeartFilled /> : <HeartOutlined />}
                  onClick={toggleFavorite}
                >
                  {isFavorited ? '已收藏' : '收藏'}
                </Button>
              </div>
            </div>

            <Divider />

            {/* 职位描述 */}
            {jobData.description && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>职位描述</h3>
                <div
                  className={styles.content}
                  dangerouslySetInnerHTML={{ __html: jobData.description }}
                />
              </div>
            )}

            {/* 职位要求 */}
            {jobData.requirements && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>职位要求</h3>
                <div
                  className={styles.content}
                  dangerouslySetInnerHTML={{ __html: jobData.requirements }}
                />
              </div>
            )}

            {/* 技能标签 */}
            {jobData.tags && jobData.tags.length > 0 && (
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>技能标签</h3>
                <Space wrap>
                  {jobData.tags.map((tag, index) => (
                    <Tag key={index} color="blue">{tag}</Tag>
                  ))}
                </Space>
              </div>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {/* 公司信息 */}
          <Card className={styles.sideCard}>
            <div className={styles.companySection}>
              <div className={styles.companyIcon}>
                <BankOutlined />
              </div>
              <div>
                <h3 className={styles.companyName}>{jobData.company_name}</h3>
                <Descriptions column={1} size="small" className={styles.companyDesc}>
                  {jobData.company_stage && (
                    <Descriptions.Item label="公司阶段">{jobData.company_stage}</Descriptions.Item>
                  )}
                  {jobData.company_size && (
                    <Descriptions.Item label="公司规模">{jobData.company_size}</Descriptions.Item>
                  )}
                  {jobData.city && (
                    <Descriptions.Item label="所在城市">{jobData.city}</Descriptions.Item>
                  )}
                </Descriptions>
              </div>
            </div>
          </Card>

          {/* 岗位统计 */}
          <Card className={styles.sideCard} style={{ marginTop: 16 }}>
            <h4 style={{ marginBottom: 12 }}>岗位统计</h4>
            <div className={styles.jobStats}>
              <div className={styles.statItem}>
                <TeamOutlined /> 投递 {jobData.apply_count ?? 0}
              </div>
              <div className={styles.statItem}>
                <ClockCircleOutlined /> 发布 {jobData.published_at ? new Date(jobData.published_at).toLocaleDateString('zh-CN') : '-'}
              </div>
              <div className={styles.statItem}>
                <BankOutlined /> 来源 {jobData.source || '平台'}
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 投递确认对话框 */}
      <Modal
        title="确认投递"
        open={applyModalVisible}
        onOk={() => confirmApply()}
        onCancel={() => setApplyModalVisible(false)}
        okText="确认投递"
        cancelText="取消"
        confirmLoading={applyMutation.isPending}
      >
        <p>您即将投递以下岗位：</p>
        <p><strong>{jobData?.title}</strong></p>
        <p>{jobData?.company_name}</p>
        <Typography.Paragraph style={{ marginTop: 16, color: '#666' }}>
          投递后可以在工作台中查看投递记录
        </Typography.Paragraph>
      </Modal>
    </div>
  );
}

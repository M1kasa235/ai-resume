import { useState } from 'react';

import { ArrowLeftOutlined, HeartOutlined } from '@ant-design/icons';
import { jobApi, workbenchApi } from '@services/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Button, Tag, Space, Skeleton, Empty, message, Modal } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';

import type { Job } from '@/types';

import styles from './JobDetail.module.scss';

export default function JobDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [applyModalVisible, setApplyModalVisible] = useState(false);

  const { data: job, isLoading } = useQuery({
    queryKey: ['job', id],
    queryFn: () => jobApi.getJobDetail(Number(id)),
    enabled: !!id,
  });

  // http 拦截器已经提取了 data.data，所以 job 直接是 Job 对象
  const jobData = job as Job | undefined;

  // 投递 mutation
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

  if (isLoading) {
    return (
      <div className={styles.jobDetail}>
        <Skeleton active />
      </div>
    );
  }

  if (!jobData) {
    return (
      <div className={styles.jobDetail}>
        <Empty description="岗位不存在" />
        <Button type="primary" onClick={() => navigate('/jobs')}>
          返回岗位列表
        </Button>
      </div>
    );
  }

  return (
    <div className={styles.jobDetail}>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/jobs')}
        style={{ marginBottom: 16 }}
      >
        返回
      </Button>

      <Card
        title={
          <div className={styles.header}>
            <h1>{jobData.title}</h1>
            <Space>
              {jobData.is_urgent && <Tag color="red">急聘</Tag>}
              <Button icon={<HeartOutlined />}>收藏</Button>
              <Button type="primary" onClick={handleApply}>
                立即投递
              </Button>
            </Space>
          </div>
        }
      >
        <div className={styles.company}>
          <h2>{jobData.company_name}</h2>
          <div className={styles.info}>
            <span>{jobData.city}</span>
            <span>·</span>
            <span>
              {jobData.experience_min && jobData.experience_max
                ? `${jobData.experience_min}-${jobData.experience_max}年`
                : jobData.experience_min
                  ? `${jobData.experience_min}年+`
                  : '不限'}
            </span>
            <span>·</span>
            <span>
              {jobData.salary_min && jobData.salary_max
                ? `${jobData.salary_min}K-${jobData.salary_max}K`
                : jobData.salary_min
                  ? `${jobData.salary_min}K+`
                  : '面议'}
            </span>
          </div>
        </div>

        <div className={styles.content}>
          <h3>职位描述</h3>
          <div dangerouslySetInnerHTML={{ __html: jobData.description || '' }} />
        </div>

        <div className={styles.content}>
          <h3>职位要求</h3>
          <div dangerouslySetInnerHTML={{ __html: jobData.requirements || '' }} />
        </div>

        {jobData.tags && jobData.tags.length > 0 && (
          <div className={styles.tags}>
            <h3>标签</h3>
            <Space wrap>
              {jobData.tags.map((tag, index) => (
                <Tag key={index}>{tag}</Tag>
              ))}
            </Space>
          </div>
        )}
      </Card>

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
        <p style={{ marginTop: 16, color: '#666' }}>
          投递后可以在工作台中查看投递记录
        </p>
      </Modal>
    </div>
  );
}

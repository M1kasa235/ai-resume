import { useState } from 'react';

import {
  UploadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { workbenchApi } from '@services/api';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Row,
  Col,
  Upload,
  Button,
  Table,
  Tag,
  Progress,
  Space,
  Modal,
  message,
  Empty,
} from 'antd';


import type { Application, PaginatedResponse } from '@/types';

import styles from './Workbench.module.scss';

const { Dragger } = Upload;

export default function Workbench() {
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
  const [uploading, setUploading] = useState(false);

  // 获取简历信息
  const { data: resumeInfo, refetch: refetchResume } = useQuery({
    queryKey: ['resume-info'],
    queryFn: async () => {
      const result = await workbenchApi.getResumeInfo();
      return result as any;
    },
  });

  const { data: applicationsData, isLoading, error } = useQuery({
    queryKey: ['applications'],
    queryFn: async () => {
      const result = await workbenchApi.getApplications({ page: 1, size: 20 });
      return result as any as PaginatedResponse<Application>;
    },
  });

  // 显示错误信息
  if (error) {
    console.error('获取投递记录失败:', error);
  }

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf,.doc,.docx',
    customRequest: async ({ file, onSuccess, onError }: any) => {
      try {
        setUploading(true);
        await workbenchApi.uploadResume(file as File);
        message.success('简历上传成功！');
        setUploadModalVisible(false);
        onSuccess?.(null);
        // 刷新简历信息
        refetchResume();
      } catch (error) {
        message.error('简历上传失败，请重试');
        onError?.(error);
      } finally {
        setUploading(false);
      }
    },
    beforeUpload: (file: File) => {
      const isPDF = file.type === 'application/pdf';
      const isDOC = file.type === 'application/msword' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      
      if (!isPDF && !isDOC) {
        message.error('只能上传PDF或Word文档！');
        return false;
      }
      
      if (file.size / 1024 / 1024 > 5) {
        message.error('文件大小不能超过5MB！');
        return false;
      }
      
      return true;
    },
  };

  const applicationColumns = [
    {
      title: '岗位名称',
      dataIndex: 'job_title',
      key: 'job_title',
      render: (text: string, record: Application) => (
        <div>
          <div>{text}</div>
          <div style={{ color: '#666', fontSize: '12px' }}>{record.company_name}</div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          pending: { color: 'orange', text: '待处理' },
          reviewing: { color: 'blue', text: '筛选中' },
          interview: { color: 'green', text: '面试中' },
          rejected: { color: 'red', text: '已拒绝' },
          accepted: { color: 'success', text: '已录用' },
        };
        const config = statusMap[status as keyof typeof statusMap] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '投递时间',
      dataIndex: 'applied_at',
      key: 'applied_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: Application) => (
        <Space>
          <Button type="link" onClick={() => setSelectedApplication(record)}>
            查看
          </Button>
          <Button type="link" danger>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const getStatusStats = () => {
    const stats = {
      pending: 0,
      reviewing: 0,
      interview: 0,
      rejected: 0,
      accepted: 0,
    };

    applicationsData?.items?.forEach((app: Application) => {
      stats[app.status as keyof typeof stats]++;
    });

    return stats;
  };

  const statusStats = getStatusStats();

  return (
    <div className={styles.workbench}>
      <h1>工作台</h1>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={8}>
          <Card title="简历管理">
            <div className={styles.resumeCard}>
              <FileTextOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              <div className={styles.resumeInfo}>
                <h3>我的简历</h3>
                {resumeInfo?.resume_url ? (
                  <>
                    <p style={{ color: '#52c41a', marginBottom: 8 }}>✓ 已上传简历</p>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Button 
                        type="primary" 
                        icon={<DownloadOutlined />}
                        onClick={() => window.open(resumeInfo.resume_url, '_blank')}
                        block
                      >
                        查看完整简历
                      </Button>
                      <Button onClick={() => setUploadModalVisible(true)} block>
                        重新上传
                      </Button>
                    </Space>
                  </>
                ) : (
                  <>
                    <p>暂未上传简历</p>
                    <Button type="primary" onClick={() => setUploadModalVisible(true)} block>
                      上传简历
                    </Button>
                  </>
                )}
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          {resumeInfo?.resume_url ? (
            <Card title="简历预览" style={{ height: '100%' }}>
              <div style={{ 
                width: '100%', 
                height: '600px',
                border: '1px solid #d9d9d9',
                borderRadius: '4px'
              }}>
                <iframe
                  src={`${resumeInfo.resume_url}#toolbar=0`}
                  style={{
                    width: '100%',
                    height: '100%',
                    border: 'none'
                  }}
                  title="简历预览"
                />
              </div>
            </Card>
          ) : (
            <Card title="投递统计">
              <Row gutter={[16, 16]}>
                <Col xs={12}>
                  <div className={styles.statCard}>
                    <div className={styles.statIcon}>
                      <ClockCircleOutlined />
                    </div>
                    <div className={styles.statContent}>
                      <div className={styles.statNumber}>{statusStats.pending}</div>
                      <div className={styles.statLabel}>待处理</div>
                    </div>
                  </div>
                </Col>
                <Col xs={12}>
                  <div className={styles.statCard}>
                    <div className={styles.statIcon}>
                      <ExclamationCircleOutlined />
                    </div>
                    <div className={styles.statContent}>
                      <div className={styles.statNumber}>{statusStats.reviewing}</div>
                      <div className={styles.statLabel}>筛选中</div>
                    </div>
                  </div>
                </Col>
                <Col xs={12}>
                  <div className={styles.statCard}>
                    <div className={styles.statIcon}>
                      <CheckCircleOutlined />
                    </div>
                    <div className={styles.statContent}>
                      <div className={styles.statNumber}>{statusStats.interview}</div>
                      <div className={styles.statLabel}>面试中</div>
                    </div>
                  </div>
                </Col>
                <Col xs={12}>
                  <div className={styles.statCard}>
                    <div className={styles.statIcon}>
                      <CheckCircleOutlined />
                    </div>
                    <div className={styles.statContent}>
                      <div className={styles.statNumber}>{statusStats.accepted}</div>
                      <div className={styles.statLabel}>已录用</div>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card>
          )}
        </Col>
      </Row>

      <Card title="投递记录" style={{ marginTop: 24 }}>
        {isLoading ? (
          <div className={styles.loading}>
            <div>加载中...</div>
          </div>
        ) : applicationsData?.items?.length ? (
          <Table
            columns={applicationColumns}
            dataSource={applicationsData.items}
            rowKey="id"
            pagination={{
              total: applicationsData.total,
              pageSize: 20,
              showSizeChanger: true,
            }}
          />
        ) : (
          <Empty description="暂无投递记录" />
        )}
      </Card>

      <Modal
        title="上传简历"
        open={uploadModalVisible}
        onCancel={() => setUploadModalVisible(false)}
        footer={null}
        width={600}
      >
        <Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持PDF、Word文档，文件大小不超过5MB
          </p>
        </Dragger>
        {uploading && (
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <Progress percent={50} status="active" />
          </div>
        )}
      </Modal>

      <Modal
        title="投递详情"
        open={!!selectedApplication}
        onCancel={() => setSelectedApplication(null)}
        footer={null}
        width={800}
      >
        {selectedApplication && (
          <div className={styles.applicationDetail}>
            <h2>{selectedApplication.job_title}</h2>
            <p>{selectedApplication.company_name}</p>
            <div className={styles.detailInfo}>
              <div className={styles.detailItem}>
                <span>投递时间：</span>
                <span>{new Date(selectedApplication.applied_at).toLocaleString()}</span>
              </div>
              <div className={styles.detailItem}>
                <span>当前状态：</span>
                <Tag color={
                  selectedApplication.status === 'pending' ? 'orange' :
                  selectedApplication.status === 'reviewing' ? 'blue' :
                  selectedApplication.status === 'interview' ? 'green' :
                  selectedApplication.status === 'rejected' ? 'red' : 'success'
                }>
                  {selectedApplication.status === 'pending' ? '待处理' :
                   selectedApplication.status === 'reviewing' ? '筛选中' :
                   selectedApplication.status === 'interview' ? '面试中' :
                   selectedApplication.status === 'rejected' ? '已拒绝' : '已录用'}
                </Tag>
              </div>
              {selectedApplication.notes && (
                <div className={styles.detailItem}>
                  <span>备注：</span>
                  <span>{selectedApplication.notes}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

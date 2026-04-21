import { useState } from 'react';

import {
  FilterOutlined,
  HeartOutlined,
  HeartFilled,
} from '@ant-design/icons';
import { jobApi, workbenchApi } from '@services/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Row,
  Col,
  Input,
  Select,
  Button,
  Tag,
  Badge,
  Space,
  Empty,
  Modal,
  message,
} from 'antd';
import { useNavigate } from 'react-router-dom';

import type { Job, PaginatedResponse } from '@/types/api';

import styles from './Jobs.module.scss';

const { Search } = Input;
const { Option } = Select;

export default function Jobs() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useState({
    keyword: '',
    city: '',
    salary_min: '',
    salary_max: '',
    experience_min: '',
    experience_max: '',
    education: '',
    sort_by: 'published_at',
    sort_order: 'desc',
  });

  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const [applyModalVisible, setApplyModalVisible] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  // 投递 mutation
  const applyMutation = useMutation({
    mutationFn: (data: { job_id: number; notes?: string }) => 
      workbenchApi.applyJob(data),
    onSuccess: () => {
      message.success('投递成功！');
      setApplyModalVisible(false);
      setSelectedJob(null);
      queryClient.invalidateQueries({ queryKey: ['applications'] });
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || '投递失败，请重试';
      message.error(errorMsg);
    },
  });

  const handleApplyClick = (job: Job) => {
    setSelectedJob(job);
    setApplyModalVisible(true);
  };

  const confirmApply = () => {
    if (!selectedJob) return;
    applyMutation.mutate({ job_id: selectedJob.id });
  };

  const { data: jobsData, isLoading } = useQuery({
    queryKey: ['jobs', searchParams],
    queryFn: () => jobApi.getJobs(getApiParams()),
  });

  // http 拦截器已经提取了 response.data，所以 jobsData 直接是 PaginatedResponse
  const jobsList = jobsData as any as PaginatedResponse<Job> | undefined;

  const { data: hotJobs } = useQuery({
    queryKey: ['hot-jobs'],
    queryFn: () => jobApi.getHotJobs(8),
  });

  const hotJobsList: Job[] = Array.isArray(hotJobs)
    ? (hotJobs as Job[])
    : Array.isArray((hotJobs as any)?.data)
      ? ((hotJobs as any).data as Job[])
      : Array.isArray((hotJobs as any)?.data?.data)
        ? ((hotJobs as any).data.data as Job[])
        : [];

  const toggleFavorite = async (jobId: number) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(jobId)) {
      newFavorites.delete(jobId);
      await jobApi.removeFavorite(jobId);
    } else {
      newFavorites.add(jobId);
      await jobApi.addFavorite(jobId);
    }
    setFavorites(newFavorites);
  };

  const handleSearch = (values: Record<string, string>) => {
    setSearchParams(prev => ({ ...prev, ...values }));
  };

  // 将搜索参数转换为 API 需要的格式
  const getApiParams = () => {
    const params: Record<string, any> = {
      keyword: searchParams.keyword || undefined,
      city: searchParams.city || undefined,
      education: searchParams.education || undefined,
      sort_by: searchParams.sort_by,
      sort_order: searchParams.sort_order,
    };

    // 转换数字类型
    if (searchParams.salary_min) {
      params.salary_min = Number(searchParams.salary_min);
    }
    if (searchParams.salary_max) {
      params.salary_max = Number(searchParams.salary_max);
    }
    if (searchParams.experience_min) {
      params.experience_min = Number(searchParams.experience_min);
    }
    if (searchParams.experience_max) {
      params.experience_max = Number(searchParams.experience_max);
    }

    return params;
  };

  const renderSalary = (min?: number, max?: number) => {
    if (min && max) {
      return `${min}K-${max}K`;
    } else if (min) {
      return `${min}K+`;
    }
    return '面议';
  };

  const renderExperience = (min?: number, max?: number) => {
    if (min && max) {
      return `${min}-${max}年`;
    } else if (min) {
      return `${min}年+`;
    }
    return '不限';
  };

  return (
    <div className={styles.jobs}>
      <h1>岗位搜索</h1>

      <Card className={styles.searchCard}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Search
              placeholder="搜索职位、公司"
              allowClear
              onSearch={(value) => handleSearch({ keyword: value })}
            />
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Select
              placeholder="城市"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => handleSearch({ city: value || '' })}
            >
              <Option value="北京">北京</Option>
              <Option value="上海">上海</Option>
              <Option value="深圳">深圳</Option>
              <Option value="杭州">杭州</Option>
              <Option value="广州">广州</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Select
              placeholder="学历要求"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => handleSearch({ education: value || '' })}
            >
              <Option value="本科">本科</Option>
              <Option value="硕士">硕士</Option>
              <Option value="博士">博士</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={18}>
          <Card
            title={
              <Space>
                <span>搜索结果</span>
                <Badge count={jobsList?.total || 0} />
              </Space>
            }
            extra={
              <Space>
                <Button
                  icon={<FilterOutlined />}
                  onClick={() => handleSearch({})}
                >
                  重置筛选
                </Button>
              </Space>
            }
          >
            {isLoading ? (
              <div className={styles.loading}>
                <Empty description="加载中..." />
              </div>
            ) : jobsList?.items?.length ? (
              <Row gutter={[16, 16]}>
                {jobsList.items.map((job: Job) => (
                  <Col xs={24} sm={12} lg={8} key={job.id}>
                    <Card
                      hoverable
                      className={styles.jobCard}
                      onClick={() => navigate(`/jobs/${job.id}`)}
                      actions={[
                        <Button
                          key="favorite"
                          type="text"
                          icon={favorites.has(job.id) ? <HeartFilled /> : <HeartOutlined />}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFavorite(job.id);
                          }}
                          style={{ color: favorites.has(job.id) ? '#ff4d4f' : undefined }}
                        >
                          {favorites.has(job.id) ? '已收藏' : '收藏'}
                        </Button>,
                        <Button
                          key="apply"
                          type="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleApplyClick(job);
                          }}
                        >
                          立即投递
                        </Button>,
                      ]}
                    >
                      <div className={styles.jobHeader}>
                        <h3>{job.title}</h3>
                        <div className={styles.company}>
                          <span>{job.company_name}</span>
                          {job.is_urgent && <Tag color="red">急聘</Tag>}
                        </div>
                      </div>
                      
                      <div className={styles.jobInfo}>
                        <div className={styles.location}>
                          <span>{job.city}</span>
                          <span>·</span>
                          <span>{renderExperience(job.experience_min, job.experience_max)}</span>
                          <span>·</span>
                          <span>{renderSalary(job.salary_min, job.salary_max)}</span>
                        </div>
                        
                        <div className={styles.tags}>
                          {job.tags?.map((tag, index) => (
                            <Tag key={index}>
                              {tag}
                            </Tag>
                          ))}
                        </div>
                        
                        <div className={styles.jobStats}>
                          <span>浏览 {job.view_count}</span>
                          <span>投递 {job.apply_count}</span>
                        </div>
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            ) : (
              <Empty description="暂无符合条件的岗位" />
            )}
          </Card>
        </Col>

        <Col xs={24} lg={6}>
          <Card title="热门岗位">
            {hotJobsList.length > 0 ? (
              hotJobsList.map((job: Job) => (
                <div 
                  key={job.id} 
                  className={styles.hotJob}
                  onClick={() => navigate(`/jobs/${job.id}`)}
                  style={{ cursor: 'pointer' }}
                >
                  <h4>{job.title}</h4>
                  <p>{job.company_name}</p>
                  <div className={styles.hotJobInfo}>
                    <span>{job.city}</span>
                    <span>{job.salary_display || renderSalary(job.salary_min, job.salary_max)}</span>
                  </div>
                </div>
              ))
            ) : (
              <Empty description="暂无热门岗位" />
            )}
          </Card>
        </Col>
      </Row>

      {/* 投递确认对话框 */}
      <Modal
        title="确认投递"
        open={applyModalVisible}
        onOk={confirmApply}
        onCancel={() => {
          setApplyModalVisible(false);
          setSelectedJob(null);
        }}
        okText="确认投递"
        cancelText="取消"
        confirmLoading={applyMutation.isPending}
      >
        {selectedJob && (
          <>
            <p>您即将投递以下岗位：</p>
            <p><strong>{selectedJob.title}</strong></p>
            <p>{selectedJob.company_name}</p>
            <p style={{ marginTop: 16, color: '#666' }}>
              投递后可以在工作台中查看投递记录
            </p>
          </>
        )}
      </Modal>
    </div>
  );
}

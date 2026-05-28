import { useState, useMemo, useRef, useEffect, useCallback } from 'react';

import {
  SearchOutlined,
  ReloadOutlined,
  HeartOutlined,
  HeartFilled,
  EnvironmentOutlined,
  TeamOutlined,
  LoadingOutlined,
  EyeOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { jobApi, workbenchApi } from '@services/api';
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
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
  Checkbox,
  Segmented,
  Spin,
} from 'antd';
import { useNavigate } from 'react-router-dom';

import type { Job, PaginatedResponse, JobCategory } from '@/types/api';

import styles from './Jobs.module.scss';

const { Search } = Input;

const SALARY_RANGES = [
  { label: '不限', value: '' },
  { label: '10K以下', value: '0-10' },
  { label: '10K-20K', value: '10-20' },
  { label: '20K-35K', value: '20-35' },
  { label: '35K-50K', value: '35-50' },
  { label: '50K以上', value: '50-999' },
];

const EXPERIENCE_RANGES = [
  { label: '不限', value: '' },
  { label: '应届/实习', value: '0-1' },
  { label: '1-3年', value: '1-3' },
  { label: '3-5年', value: '3-5' },
  { label: '5-10年', value: '5-10' },
  { label: '10年以上', value: '10-50' },
];

const COMPANY_STAGES = [
  { label: '不限', value: '' },
  { label: '未融资', value: '未融资' },
  { label: '天使轮', value: '天使轮' },
  { label: 'A轮', value: 'A轮' },
  { label: 'B轮', value: 'B轮' },
  { label: 'C轮以上', value: 'C轮' },
  { label: '上市公司', value: '已上市' },
  { label: '不需要融资', value: '不需要融资' },
];

const SORT_OPTIONS = [
  { label: '最新发布', value: 'published_at' },
  { label: '最高薪资', value: 'salary_min' },
  { label: '最多投递', value: 'apply_count' },
  { label: '最多浏览', value: 'view_count' },
];

const PAGE_SIZE = 12;

const timeAgo = (dateStr?: string) => {
  if (!dateStr) return '';
  const now = Date.now();
  const past = new Date(dateStr).getTime();
  const diff = Math.floor((now - past) / 1000);
  if (diff < 60) return '刚刚';
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
  if (diff < 2592000) return `${Math.floor(diff / 86400)}天前`;
  return new Date(dateStr).toLocaleDateString('zh-CN');
};

const formatCount = (n?: number) => {
  if (!n) return '0';
  if (n >= 10000) return `${(n / 10000).toFixed(1)}w`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
};

export default function Jobs() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useState({
    keyword: '',
    city: '',
    category_id: undefined as number | undefined,
    salary_range: '',
    experience_range: '',
    education: '',
    company_stage: '',
    only_urgent: false,
    sort_by: 'published_at',
  });
  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [applyModalVisible, setApplyModalVisible] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [filterExpanded, setFilterExpanded] = useState(false);

  // 获取分类列表
  const { data: categoriesData } = useQuery({
    queryKey: ['job-categories'],
    queryFn: () => jobApi.getCategoryList(),
  });
  const categories: JobCategory[] = Array.isArray(categoriesData)
    ? (categoriesData as JobCategory[])
    : Array.isArray((categoriesData as any)?.data)
      ? ((categoriesData as any).data as JobCategory[])
      : [];

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

  // 构建 API 参数（不含页码）
  const baseParams = useMemo(() => {
    const params: Record<string, any> = {
      page_size: PAGE_SIZE,
      keyword: searchParams.keyword || undefined,
      city: searchParams.city || undefined,
      category_id: searchParams.category_id || undefined,
      education: searchParams.education || undefined,
      company_stage: searchParams.company_stage || undefined,
      only_urgent: searchParams.only_urgent || undefined,
      sort_by: searchParams.sort_by,
      sort_order: 'desc',
    };

    if (searchParams.salary_range) {
      const [min, max] = searchParams.salary_range.split('-');
      params.salary_min = Number(min);
      params.salary_max = Number(max);
    }
    if (searchParams.experience_range) {
      const [min, max] = searchParams.experience_range.split('-');
      params.experience_min = Number(min);
      params.experience_max = Number(max);
    }

    return params;
  }, [searchParams]);

  // 无限滚动查询
  const {
    data: jobsData,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['jobs', baseParams],
    queryFn: ({ pageParam }) =>
      jobApi.getJobs({ ...baseParams, page: pageParam }) as unknown as PaginatedResponse<Job>,
    getNextPageParam: (lastPage, allPages) => {
      if (!lastPage?.total) return undefined;
      const totalPages = Math.ceil(lastPage.total / PAGE_SIZE);
      return allPages.length < totalPages ? allPages.length + 1 : undefined;
    },
    initialPageParam: 1,
  });

  const allJobs = useMemo(() => {
    return jobsData?.pages.flatMap((p) => p.items) ?? [];
  }, [jobsData]);

  const total = jobsData?.pages?.[0]?.total ?? 0;

  // 收藏变化时持久化到 localStorage
  useEffect(() => {
    localStorage.setItem('job-favorites', JSON.stringify([...favorites]));
  }, [favorites]);

  // 从加载的岗位数据中同步收藏状态
  useEffect(() => {
    const favIds = allJobs.filter(j => j.is_favorited).map(j => j.id);
    if (favIds.length > 0) {
      setFavorites(prev => {
        const next = new Set(prev);
        favIds.forEach(id => next.add(id));
        return next;
      });
    }
  }, [allJobs]);


  // 热门岗位
  const { data: hotJobs } = useQuery({
    queryKey: ['hot-jobs'],
    queryFn: () => jobApi.getHotJobs(8),
  });

  const hotJobsList: Job[] = useMemo(() => {
    if (Array.isArray(hotJobs)) return hotJobs as Job[];
    if (Array.isArray((hotJobs as any)?.data)) return (hotJobs as any).data as Job[];
    if (Array.isArray((hotJobs as any)?.data?.data)) return (hotJobs as any).data.data as Job[];
    return [];
  }, [hotJobs]);

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

  const handleReset = useCallback(() => {
    setSearchParams({
      keyword: '',
      city: '',
      category_id: undefined,
      salary_range: '',
      experience_range: '',
      education: '',
      company_stage: '',
      only_urgent: false,
      sort_by: 'published_at',
    });
  }, []);

  const updateParam = useCallback((key: string, value: any) => {
    setSearchParams(prev => {
      if (prev[key as keyof typeof prev] === value) return prev;
      return { ...prev, [key]: value };
    });
  }, []);

  // 触底加载哨兵
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { rootMargin: '200px' },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const renderSalary = (min?: number, max?: number) => {
    if (min && max) return `${min}K-${max}K`;
    if (min) return `${min}K+`;
    return '面议';
  };

  const renderExperience = (min?: number, max?: number) => {
    if (min && max) return `${min}-${max}年`;
    if (min) return `${min}年+`;
    return '经验不限';
  };


  return (
    <div className={styles.jobsPage}>
      {/* 筛选栏 */}
      <Card className={styles.filterCard} size="small">
        <Row gutter={[12, 12]}>
          <Col xs={24} sm={12} md={8} lg={6}>
            <Search
              placeholder="搜索职位、公司"
              allowClear
              value={searchParams.keyword}
              onChange={(e) => updateParam('keyword', e.target.value)}
              onSearch={(value) => updateParam('keyword', value)}
              enterButton={<SearchOutlined />}
            />
          </Col>
          <Col xs={12} sm={6} md={4} lg={3}>
            <Select
              placeholder="城市"
              allowClear
              style={{ width: '100%' }}
              value={searchParams.city || undefined}
              onChange={(v) => updateParam('city', v || '')}
            >
              <Select.Option value="北京">北京</Select.Option>
              <Select.Option value="上海">上海</Select.Option>
              <Select.Option value="深圳">深圳</Select.Option>
              <Select.Option value="杭州">杭州</Select.Option>
              <Select.Option value="广州">广州</Select.Option>
              <Select.Option value="成都">成都</Select.Option>
              <Select.Option value="武汉">武汉</Select.Option>
              <Select.Option value="南京">南京</Select.Option>
            </Select>
          </Col>
          <Col xs={12} sm={6} md={4} lg={3}>
            <Select
              placeholder="分类"
              allowClear
              style={{ width: '100%' }}
              value={searchParams.category_id}
              onChange={(v) => updateParam('category_id', v)}
            >
              {categories.map((cat) => (
                <Select.Option key={cat.id} value={cat.id}>{cat.name}</Select.Option>
              ))}
            </Select>
          </Col>
          {filterExpanded && (
            <>
              <Col xs={12} sm={6} md={4} lg={3}>
                <Select
                  placeholder="薪资范围"
                  allowClear
                  style={{ width: '100%' }}
                  value={searchParams.salary_range || undefined}
                  onChange={(v) => updateParam('salary_range', v || '')}
                >
                  {SALARY_RANGES.map((r) => (
                    <Select.Option key={r.value} value={r.value}>{r.label}</Select.Option>
                  ))}
                </Select>
              </Col>
              <Col xs={12} sm={6} md={4} lg={3}>
                <Select
                  placeholder="工作经验"
                  allowClear
                  style={{ width: '100%' }}
                  value={searchParams.experience_range || undefined}
                  onChange={(v) => updateParam('experience_range', v || '')}
                >
                  {EXPERIENCE_RANGES.map((r) => (
                    <Select.Option key={r.value} value={r.value}>{r.label}</Select.Option>
                  ))}
                </Select>
              </Col>
              <Col xs={12} sm={6} md={4} lg={3}>
                <Select
                  placeholder="学历要求"
                  allowClear
                  style={{ width: '100%' }}
                  value={searchParams.education || undefined}
                  onChange={(v) => updateParam('education', v || '')}
                >
                  <Select.Option value="不限">不限</Select.Option>
                  <Select.Option value="大专">大专</Select.Option>
                  <Select.Option value="本科">本科</Select.Option>
                  <Select.Option value="硕士">硕士</Select.Option>
                  <Select.Option value="博士">博士</Select.Option>
                </Select>
              </Col>
              <Col xs={12} sm={6} md={4} lg={3}>
                <Select
                  placeholder="公司阶段"
                  allowClear
                  style={{ width: '100%' }}
                  value={searchParams.company_stage || undefined}
                  onChange={(v) => updateParam('company_stage', v || '')}
                >
                  {COMPANY_STAGES.map((r) => (
                    <Select.Option key={r.value} value={r.value}>{r.label}</Select.Option>
                  ))}
                </Select>
              </Col>
              <Col xs={12} sm={6} md={4} lg={3} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Checkbox
                  checked={searchParams.only_urgent}
                  onChange={(e) => updateParam('only_urgent', e.target.checked)}
                >
                  仅看急聘
                </Checkbox>
              </Col>
            </>
          )}
          <Col xs={12} sm={6} md={4} lg={3}>
            <Space>
              <Button type="primary" icon={<SearchOutlined />} onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
                搜索
              </Button>
              <Button icon={<ReloadOutlined />} onClick={handleReset}>
                重置
              </Button>
              <Button
                size="small"
                type="link"
                onClick={() => setFilterExpanded(!filterExpanded)}
              >
                {filterExpanded ? '收起筛选' : '展开筛选'}
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <div className={styles.resultsWrapper}>
        <Row gutter={[12, 12]}>
          <Col xs={24} lg={18}>
          <Card
            className={styles.resultCard}
            title={
              <Space>
                <span className={styles.resultTitle}>
                  {showFavoritesOnly ? '收藏夹' : '搜索结果'}
                </span>
                <Badge count={showFavoritesOnly ? allJobs.filter(j => favorites.has(j.id)).length : total} showZero overflowCount={9999} style={{ backgroundColor: '#1677ff' }} />
                <Button
                  size="small"
                  type={showFavoritesOnly ? 'primary' : 'text'}
                  icon={<HeartOutlined />}
                  onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
                >
                  收藏夹
                </Button>
              </Space>
            }
            extra={
              <Space>
                <span className={styles.sortLabel}>排序：</span>
                <Segmented
                  size="small"
                  options={SORT_OPTIONS}
                  value={searchParams.sort_by}
                  onChange={(v) => updateParam('sort_by', v as string)}
                />
              </Space>
            }
          >
            {isLoading ? (
              <div className={styles.loading}>
                <Spin />
              </div>
            ) : (showFavoritesOnly ? allJobs.filter(j => favorites.has(j.id)) : allJobs).length > 0 ? (
              <div className={styles.scrollArea}>
                <Row gutter={[16, 16]}>
                  {(showFavoritesOnly ? allJobs.filter(j => favorites.has(j.id)) : allJobs).map((job: Job) => (
                    <Col xs={24} sm={12} xl={8} key={job.id}>
                      <div className={styles.jobItem} onClick={() => navigate(`/jobs/${job.id}`)}>
                        <div className={styles.jobItemInner}>
                          <div className={styles.jobItemRow1}>
                          <span className={styles.jobItemTitle}>
                            {job.title}
                            {job.is_urgent && <Tag color="red" className={styles.urgentDot}>急</Tag>}
                          </span>
                          <span className={styles.jobItemSalary}>
                            {renderSalary(job.salary_min, job.salary_max)}
                          </span>
                          <span className={styles.jobItemActions}>
                            {favorites.has(job.id) ? (
                              <HeartFilled className={styles.jobItemFav}
                                onClick={(e) => { e.stopPropagation(); toggleFavorite(job.id); }}
                              />
                            ) : (
                              <HeartOutlined className={styles.jobItemFav}
                                onClick={(e) => { e.stopPropagation(); toggleFavorite(job.id); }}
                              />
                            )}
                            <Button type="primary" size="small" className={styles.jobItemApply}
                              onClick={(e) => { e.stopPropagation(); handleApplyClick(job); }}
                            >
                              投递
                            </Button>
                          </span>
                        </div>
                        <div className={styles.jobItemRow2}>
                          {job.company_name}
                          {job.company_stage && <><span className={styles.jobItemDot}>·</span>{job.company_stage}</>}
                          <span className={styles.jobItemDot}>·</span>
                          <EnvironmentOutlined /> {job.city || '地点不限'}
                          <span className={styles.jobItemDot}>·</span>
                          {renderExperience(job.experience_min, job.experience_max)}
                          {job.education_requirement && (
                            <><span className={styles.jobItemDot}>·</span>{job.education_requirement}</>
                          )}
                        </div>
                        {(job.tags?.length ?? 0) > 0 && (
                          <div className={styles.jobItemRow3}>
                            {job.tags!.slice(0, 5).map((tag, i) => (
                              <Tag key={i} className={styles.jobItemTag}>{tag}</Tag>
                            ))}
                            {job.tags!.length > 5 && <Tag className={styles.jobItemTag}>+{job.tags!.length - 5}</Tag>}
                          </div>
                        )}
                        {((job.view_count ?? 0) > 0 || (job.apply_count ?? 0) > 0 || job.published_at) && (
                          <div className={styles.jobItemRow4}>
                            {(job.view_count ?? 0) > 0 && (
                              <span className={styles.jobItemStat}><EyeOutlined /> {formatCount(job.view_count)}</span>
                            )}
                            {(job.apply_count ?? 0) > 0 && (
                              <span className={styles.jobItemStat}><TeamOutlined /> {formatCount(job.apply_count)}</span>
                            )}
                            {job.published_at && (
                              <span className={styles.jobItemStat}><ClockCircleOutlined /> {timeAgo(job.published_at)}</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    </Col>
                  ))}
                </Row>

                {/* 触底加载哨兵 */}
                <div ref={sentinelRef} className={styles.sentinel}>
                  {isFetchingNextPage && (
                    <Space>
                      <LoadingOutlined /> 加载更多...
                    </Space>
                  )}
                  {!hasNextPage && allJobs.length > 0 && (
                    <span className={styles.noMore}>
                      {showFavoritesOnly
                        ? `共收藏 ${favorites.size} 个岗位`
                        : `已展示全部 ${allJobs.length} 个岗位`}
                    </span>
                  )}
                </div>
              </div>
            ) : (
              <Empty description="暂无符合条件的岗位" />
            )}
          </Card>
        </Col>

        <Col xs={24} lg={6}>
          <Card
            title={<span className={styles.sidebarTitle}><TeamOutlined /> 热门岗位</span>}
            className={styles.sidebarCard}
          >
            {hotJobsList.length > 0 ? (
              hotJobsList.map((job: Job, index: number) => (
                <div
                  key={job.id}
                  className={styles.hotJobItem}
                  onClick={() => navigate(`/jobs/${job.id}`)}
                >
                  <div className={styles.hotJobRank} data-top={index < 3}>{index + 1}</div>
                  <div className={styles.hotJobContent}>
                    <h4 className={styles.hotJobTitle}>{job.title}</h4>
                    <p className={styles.hotJobCompany}>{job.company_name}</p>
                    <span className={styles.hotJobSalary}>
                      {renderSalary(job.salary_min, job.salary_max)}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <Empty description="暂无热门岗位" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>
        </Row>
        </div>

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

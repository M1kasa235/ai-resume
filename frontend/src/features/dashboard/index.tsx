import {
  SendOutlined,
  MessageOutlined,
  CheckCircleOutlined,
  StarOutlined,
  RiseOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { useMemo, useState } from 'react';

import { dashboardApi } from '@services/api';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Row,
  Col,
  Statistic,
  List,
  Tag,
  Progress,
  Skeleton,
  Empty,
  Segmented,
  Checkbox,
} from 'antd';
import { useNavigate } from 'react-router-dom';

import type { DashboardOverviewResponse, GrowthCurveResponse, ActivitiesResponse, ActivityRecord } from '@/types/api';

import styles from './Dashboard.module.scss';

export default function Dashboard() {
  const navigate = useNavigate();
  const [growthRange, setGrowthRange] = useState<7 | 30>(7);
  const [visibleSeries, setVisibleSeries] = useState<{
    applications: boolean;
    practices: boolean;
    interviews: boolean;
  }>({
    applications: true,
    practices: true,
    interviews: true,
  });

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: dashboardApi.getOverview,
  });

  const { data: activities, isLoading: activitiesLoading } = useQuery({
    queryKey: ['dashboard', 'activities'],
    queryFn: () => dashboardApi.getActivities(10),
  });

  const { data: growthCurve, isLoading: growthLoading } = useQuery({
    queryKey: ['dashboard', 'growth'],
    queryFn: () => dashboardApi.getGrowthCurve(30),
  });

  const growthData = growthCurve as GrowthCurveResponse | undefined;
  const growthDates = growthData?.dates || [];
  const applicationsSeries = growthData?.metrics?.applications || [];
  const practicesSeries = growthData?.metrics?.practices || [];
  const aiInterviewSeries = growthData?.metrics?.ai_interviews || [];
  const hasGrowthData = growthDates.length > 0;

  const maxValue = Math.max(
    ...applicationsSeries,
    ...practicesSeries,
    ...aiInterviewSeries,
    1
  );

  const trendRows = useMemo(() => {
    const sliceSize = growthRange;
    return growthDates.slice(-sliceSize).map((date, index, arr) => {
      const sourceIndex = growthDates.length - arr.length + index;
      return {
        date,
        applications: applicationsSeries[sourceIndex] || 0,
        practices: practicesSeries[sourceIndex] || 0,
        aiInterviews: aiInterviewSeries[sourceIndex] || 0,
      };
    });
  }, [growthRange, growthDates, applicationsSeries, practicesSeries, aiInterviewSeries]);

  const activeMaxValue = Math.max(
    ...trendRows.map((row) => (visibleSeries.applications ? row.applications : 0)),
    ...trendRows.map((row) => (visibleSeries.practices ? row.practices : 0)),
    ...trendRows.map((row) => (visibleSeries.interviews ? row.aiInterviews : 0)),
    1
  );

  // http 拦截器已经提取了 data.data，所以 overview 直接是 DashboardOverviewResponse
  const stats = [
    {
      title: '投递总数',
      value: (overview as DashboardOverviewResponse | undefined)?.statistics?.total_applications || 0,
      icon: <SendOutlined />,
      color: '#1890ff',
    },
    {
      title: 'AI面试',
      value: (overview as DashboardOverviewResponse | undefined)?.statistics?.total_ai_interviews || 0,
      icon: <MessageOutlined />,
      color: '#52c41a',
    },
    {
      title: '刷题数量',
      value: (overview as DashboardOverviewResponse | undefined)?.statistics?.total_practices || 0,
      icon: <CheckCircleOutlined />,
      color: '#722ed1',
    },
    {
      title: '收藏岗位',
      value: (overview as DashboardOverviewResponse | undefined)?.statistics?.favorite_jobs || 0,
      icon: <StarOutlined />,
      color: '#faad14',
    },
  ];

  return (
    <div className={styles.dashboard}>
      <h1>仪表盘</h1>

      <Row gutter={[24, 24]}>
        {stats.map((stat, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card>
              <Skeleton loading={overviewLoading} active>
                <Statistic
                  title={
                    <span className={styles.statTitle}>
                      {stat.icon}
                      <span>{stat.title}</span>
                    </span>
                  }
                  value={stat.value}
                  valueStyle={{ color: stat.color }}
                />
              </Skeleton>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={16}>
          <Card
            title="成长曲线"
            extra={
              <Segmented
                options={[
                  { label: '近7天', value: 7 },
                  { label: '近30天', value: 30 },
                ]}
                value={growthRange}
                onChange={(value) => setGrowthRange(value as 7 | 30)}
              />
            }
          >
            <Skeleton loading={growthLoading} active>
              {hasGrowthData ? (
                <div className={styles.growthPanel}>
                  <div className={styles.summaryRow}>
                    <Tag color="blue">总投递 {growthData?.summary?.total_applications || 0}</Tag>
                    <Tag color="purple">总刷题 {growthData?.summary?.total_practices || 0}</Tag>
                    <Tag color="green">
                      平均正确率 {(((growthData?.summary?.avg_accuracy || 0) * 100)).toFixed(1)}%
                    </Tag>
                  </div>
                  <div className={styles.legendRow}>
                    <Checkbox
                      checked={visibleSeries.applications}
                      onChange={(e) =>
                        setVisibleSeries((prev) => ({ ...prev, applications: e.target.checked }))
                      }
                    >
                      <span className={styles.legendItem}>
                        <span className={`${styles.legendDot} ${styles.dotApplications}`} />
                        投递
                      </span>
                    </Checkbox>
                    <Checkbox
                      checked={visibleSeries.practices}
                      onChange={(e) =>
                        setVisibleSeries((prev) => ({ ...prev, practices: e.target.checked }))
                      }
                    >
                      <span className={styles.legendItem}>
                        <span className={`${styles.legendDot} ${styles.dotPractices}`} />
                        刷题
                      </span>
                    </Checkbox>
                    <Checkbox
                      checked={visibleSeries.interviews}
                      onChange={(e) =>
                        setVisibleSeries((prev) => ({ ...prev, interviews: e.target.checked }))
                      }
                    >
                      <span className={styles.legendItem}>
                        <span className={`${styles.legendDot} ${styles.dotInterviews}`} />
                        AI面试
                      </span>
                    </Checkbox>
                  </div>

                  <div className={styles.chartArea}>
                    {trendRows.map((row) => (
                      <div key={row.date} className={styles.chartGroup}>
                        {visibleSeries.applications && (
                          <div
                            className={styles.barApplications}
                            style={{ height: `${Math.max((row.applications / activeMaxValue) * 120, 2)}px` }}
                            title={`投递: ${row.applications}`}
                          />
                        )}
                        {visibleSeries.practices && (
                          <div
                            className={styles.barPractices}
                            style={{ height: `${Math.max((row.practices / activeMaxValue) * 120, 2)}px` }}
                            title={`刷题: ${row.practices}`}
                          />
                        )}
                        {visibleSeries.interviews && (
                          <div
                            className={styles.barInterviews}
                            style={{ height: `${Math.max((row.aiInterviews / activeMaxValue) * 120, 2)}px` }}
                            title={`AI面试: ${row.aiInterviews}`}
                          />
                        )}
                        <span className={styles.chartLabel}>{row.date.slice(5)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <Empty description="暂无成长曲线数据" />
              )}
            </Skeleton>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            title="学习进度"
            extra={
              <span>
                <RiseOutlined /> 本周
              </span>
            }
          >
            <Skeleton loading={overviewLoading} active>
              <div className={styles.progress}>
                <div className={styles.progressItem}>
                  <span>简历完善度</span>
                  <Progress percent={75} status="active" />
                </div>
                <div className={styles.progressItem}>
                  <span>刷题目标</span>
                  <Progress percent={60} />
                </div>
                <div className={styles.progressItem}>
                  <span>投递目标</span>
                  <Progress percent={40} />
                </div>
              </div>
            </Skeleton>
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="最近动态" extra={<a href="#">查看全部</a>}>
            <Skeleton loading={activitiesLoading} active>
              <List
                dataSource={(activities as ActivitiesResponse | undefined)?.activities || []}
                renderItem={(item: ActivityRecord) => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<TrophyOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                      title={item.title}
                      description={item.description}
                    />
                  </List.Item>
                )}
              />
            </Skeleton>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="快速操作">
            <div className={styles.quickActions}>
              <Card.Grid className={styles.actionCard} onClick={() => navigate('/workbench')}>
                <SendOutlined style={{ fontSize: 32, color: '#1890ff' }} />
                <span>投递简历</span>
              </Card.Grid>
              <Card.Grid className={styles.actionCard} onClick={() => navigate('/ai-interview')}>
                <MessageOutlined style={{ fontSize: 32, color: '#52c41a' }} />
                <span>AI面试</span>
              </Card.Grid>
              <Card.Grid className={styles.actionCard} onClick={() => navigate('/questions')}>
                <CheckCircleOutlined style={{ fontSize: 32, color: '#722ed1' }} />
                <span>开始刷题</span>
              </Card.Grid>
              <Card.Grid className={styles.actionCard} onClick={() => navigate('/jobs')}>
                <StarOutlined style={{ fontSize: 32, color: '#faad14' }} />
                <span>我的收藏</span>
              </Card.Grid>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

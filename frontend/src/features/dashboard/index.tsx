import {
  SendOutlined,
  MessageOutlined,
  CheckCircleOutlined,
  StarOutlined,
  RiseOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
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
} from 'antd';

import type { DashboardOverviewResponse, GrowthCurveResponse, ActivitiesResponse, ActivityRecord } from '@/types/api';

import styles from './Dashboard.module.scss';

export default function Dashboard() {
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
          <Card title="成长曲线" extra={<Tag color="blue">近30天</Tag>}>
            <Skeleton loading={growthLoading} active>
              <div className={styles.chartPlaceholder}>
                <p>成长曲线图表区域</p>
                <p>投递: {(growthCurve as GrowthCurveResponse | undefined)?.summary?.total_applications || 0}</p>
                <p>刷题: {(growthCurve as GrowthCurveResponse | undefined)?.summary?.total_practices || 0}</p>
                <p>正确率: {(((growthCurve as GrowthCurveResponse | undefined)?.summary?.avg_accuracy || 0) * 100).toFixed(1)}%</p>
              </div>
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
              <Card.Grid className={styles.actionCard}>
                <SendOutlined style={{ fontSize: 32, color: '#1890ff' }} />
                <span>投递简历</span>
              </Card.Grid>
              <Card.Grid className={styles.actionCard}>
                <MessageOutlined style={{ fontSize: 32, color: '#52c41a' }} />
                <span>AI面试</span>
              </Card.Grid>
              <Card.Grid className={styles.actionCard}>
                <CheckCircleOutlined style={{ fontSize: 32, color: '#722ed1' }} />
                <span>开始刷题</span>
              </Card.Grid>
              <Card.Grid className={styles.actionCard}>
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

import {
  SendOutlined,
  MessageOutlined,
  CheckCircleOutlined,
  StarOutlined,
  RiseOutlined,
  TrophyOutlined,
  RightOutlined,
  AimOutlined,
  BookOutlined,
  RobotOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { useMemo, useState } from 'react';

import { dashboardApi } from '@services/api';
import { useUserStore } from '@stores/userStore';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Row,
  Col,
  Tag,
  Progress,
  Skeleton,
  Empty,
  Segmented,
  Checkbox,
} from 'antd';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';

import type { DashboardOverviewResponse, GrowthCurveResponse, ActivitiesResponse, ActivityRecord } from '@/types/api';

import styles from './Dashboard.module.scss';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useUserStore();
  const [growthRange, setGrowthRange] = useState<7 | 30>(7);
  const [visibleSeries, setVisibleSeries] = useState({
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
    queryFn: () => dashboardApi.getGrowthCurve(growthRange),
  });

  const overviewData = overview as DashboardOverviewResponse | undefined;
  const stats = overviewData?.statistics;
  const growthData = growthCurve as GrowthCurveResponse | undefined;
  const growthDates = growthData?.dates || [];
  const appSeries = growthData?.metrics?.applications || [];
  const pracSeries = growthData?.metrics?.practices || [];
  const aiSeries = growthData?.metrics?.ai_interviews || [];
  const hasGrowthData = growthDates.length > 0;

  const trendRows = useMemo(() => {
    const sliceSize = growthRange;
    return growthDates.slice(-sliceSize).map((date, i, arr) => {
      const si = growthDates.length - arr.length + i;
      return {
        date,
        applications: appSeries[si] || 0,
        practices: pracSeries[si] || 0,
        aiInterviews: aiSeries[si] || 0,
      };
    });
  }, [growthRange, growthDates, appSeries, pracSeries, aiSeries]);

  const today = dayjs().format('YYYY年M月D日');
  const hour = dayjs().hour();
  let greeting = '下午好';
  if (hour < 6) greeting = '夜深了';
  else if (hour < 9) greeting = '早上好';
  else if (hour < 12) greeting = '上午好';
  else if (hour < 14) greeting = '中午好';
  else if (hour < 18) greeting = '下午好';
  else greeting = '晚上好';

  const encouragements = [
    '坚持投递，总会有回响',
    '每一份努力都在为未来铺路',
    '机会总是留给有准备的人',
    '加油，Offer 已经在路上了',
    '日积跬步，以至千里',
    '今天的积累是明天的底气',
    '相信坚持的力量',
    '每次面试都是一次成长',
  ];
  const encouragement = encouragements[dayjs().date() % encouragements.length];

  const resumePct = stats?.resume_completeness ?? 0;
  const practicePct = Math.min(100, Math.round(((stats?.total_practices ?? 0) / (stats?.practice_goal ?? 500)) * 100));
  const applicationPct = Math.min(100, Math.round(((stats?.total_applications ?? 0) / (stats?.application_goal ?? 100)) * 100));

  const statCards = [
    {
      key: 'applications',
      label: '投递总数',
      value: stats?.total_applications ?? 0,
      icon: <SendOutlined />,
      bg: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
      tag: '投递',
    },
    {
      key: 'interviews',
      label: 'AI面试',
      value: stats?.total_ai_interviews ?? 0,
      icon: <RobotOutlined />,
      bg: 'linear-gradient(135deg, #52c41a 0%, #389e0d 100%)',
      tag: '面试',
    },
    {
      key: 'practices',
      label: '刷题数量',
      value: stats?.total_practices ?? 0,
      icon: <BookOutlined />,
      bg: 'linear-gradient(135deg, #722ed1 0%, #531dab 100%)',
      tag: '刷题',
    },
    {
      key: 'favorites',
      label: '收藏岗位',
      value: stats?.favorite_jobs ?? 0,
      icon: <StarOutlined />,
      bg: 'linear-gradient(135deg, #faad14 0%, #d48806 100%)',
      tag: '收藏',
    },
  ];

  return (
    <div className={styles.dashboard}>
      <div className={styles.rowSection}>
        {/* 欢迎横幅 */}
        <div className={styles.welcomeBanner}>
          <div className={styles.welcomeContent}>
            <div>
              <h2 className={styles.welcomeTitle}>
                {greeting}，{user?.username || '用户'}
              </h2>
              <p className={styles.welcomeDate}>{today}</p>
            </div>
            <div className={styles.welcomeCenter}>
              <span className={styles.welcomeEncourage}>{encouragement}</span>
            </div>
            <div className={styles.welcomeStats}>
              <div className={styles.welcomeStatItem}>
                <span className={styles.welcomeStatValue}>{stats?.total_applications ?? 0}</span>
                <span className={styles.welcomeStatLabel}>累计投递</span>
              </div>
              <div className={styles.welcomeStatDivider} />
              <div className={styles.welcomeStatItem}>
                <span className={styles.welcomeStatValue}>{stats?.total_practices ?? 0}</span>
                <span className={styles.welcomeStatLabel}>累计刷题</span>
              </div>
              <div className={styles.welcomeStatDivider} />
              <div className={styles.welcomeStatItem}>
                <span className={styles.welcomeStatValue}>
                  {((stats?.accuracy_rate ?? 0)).toFixed(0)}%
                </span>
                <span className={styles.welcomeStatLabel}>平均正确率</span>
              </div>
            </div>
          </div>
          <div className={styles.welcomeDecoration}>
            <AimOutlined />
          </div>
        </div>

        {/* 统计卡片 */}
        <Row gutter={[12, 12]} style={{ marginTop: 12 }}>
          {statCards.map((card) => (
            <Col xs={24} sm={12} lg={6} key={card.key}>
              <Card className={styles.statCard} styles={{ body: { background: card.bg, padding: '14px 20px', borderRadius: 12 } }}>
                <Skeleton loading={overviewLoading} active paragraph={{ rows: 0 }} title={false}>
                  <div className={styles.statCardInner}>
                    <div className={styles.statLeft}>
                      <div className={styles.statIcon}>{card.icon}</div>
                      <div>
                        <div className={styles.statLabel}>{card.label}</div>
                        <div className={styles.statValue}>{card.value}</div>
                      </div>
                    </div>
                    <Tag className={styles.statTag}>{card.tag}</Tag>
                  </div>
                </Skeleton>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      <div className={styles.flexSection}>
        {/* 成长曲线 + 学习进度 */}
        <Row gutter={[12, 12]} style={{ marginTop: 0 }}>
        <Col xs={24} lg={16}>
          <Card
            className={`${styles.sectionCard} ${styles.fillCard}`}
            title={
              <span className={styles.sectionTitle}>
                <RiseOutlined /> 成长曲线
              </span>
            }
            extra={
              <Segmented
                size="small"
                options={[
                  { label: '近7天', value: 7 },
                  { label: '近30天', value: 30 },
                ]}
                value={growthRange}
                onChange={(v) => setGrowthRange(v as 7 | 30)}
              />
            }
          >
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <Skeleton loading={growthLoading} active>
              {hasGrowthData ? (
                <div className={styles.growthPanel}>
                  <div className={styles.growthMeta}>
                    <Tag color="blue" className={styles.metaTag}>
                      总投递 {growthData?.summary?.total_applications || 0}
                    </Tag>
                    <Tag color="purple" className={styles.metaTag}>
                      总刷题 {growthData?.summary?.total_practices || 0}
                    </Tag>
                    <Tag color="green" className={styles.metaTag}>
                      平均正确率 {((growthData?.summary?.avg_accuracy || 0)).toFixed(1)}%
                    </Tag>
                  </div>
                  <div className={styles.legendRow}>
                    {[
                      { key: 'applications' as const, label: '投递', color: '#1677ff' },
                      { key: 'practices' as const, label: '刷题', color: '#722ed1' },
                      { key: 'interviews' as const, label: 'AI面试', color: '#52c41a' },
                    ].map((item) => (
                      <Checkbox
                        key={item.key}
                        checked={visibleSeries[item.key]}
                        onChange={(e) =>
                          setVisibleSeries((prev) => ({ ...prev, [item.key]: e.target.checked }))
                        }
                      >
                        <span className={styles.legendItem}>
                          <span className={styles.legendDot} style={{ background: item.color }} />
                          {item.label}
                        </span>
                      </Checkbox>
                    ))}
                  </div>
                  <div className={styles.chartArea}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={trendRows} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 11, fill: '#999' }}
                          tickFormatter={(v: string) => v.slice(5)}
                          axisLine={{ stroke: '#f0f0f0' }}
                          tickLine={false}
                        />
                        <YAxis
                          tick={{ fontSize: 11, fill: '#999' }}
                          axisLine={false}
                          tickLine={false}
                          allowDecimals={false}
                        />
                        <RechartsTooltip
                          contentStyle={{
                            borderRadius: 8,
                            border: '1px solid #f0f0f0',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                            fontSize: 13,
                          }}
                          formatter={(value, name) => {
                            const labels: Record<string, string> = {
                              applications: '投递',
                              practices: '刷题',
                              interviews: 'AI面试',
                            };
                            return [value, labels[name ?? ''] ?? name];
                          }}
                          labelFormatter={(label) => String(label)}
                        />
                        {visibleSeries.applications && (
                          <Line
                            type="monotone"
                            dataKey="applications"
                            stroke="#1677ff"
                            strokeWidth={2}
                            dot={{ r: 3, fill: '#1677ff' }}
                            activeDot={{ r: 5 }}
                          />
                        )}
                        {visibleSeries.practices && (
                          <Line
                            type="monotone"
                            dataKey="practices"
                            stroke="#722ed1"
                            strokeWidth={2}
                            dot={{ r: 3, fill: '#722ed1' }}
                            activeDot={{ r: 5 }}
                          />
                        )}
                        {visibleSeries.interviews && (
                          <Line
                            type="monotone"
                            dataKey="interviews"
                            stroke="#52c41a"
                            strokeWidth={2}
                            dot={{ r: 3, fill: '#52c41a' }}
                            activeDot={{ r: 5 }}
                          />
                        )}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              ) : (
                <Empty description="暂无成长曲线数据，快去投递刷题吧！" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </Skeleton>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            className={`${styles.sectionCard} ${styles.fillCard}`}
            title={
              <span className={styles.sectionTitle}>
                <AimOutlined /> 学习进度
              </span>
            }
          >
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <Skeleton loading={overviewLoading} active>
              <div className={styles.progressSection}>
                <div className={styles.progressCard}>
                  <div className={styles.progressHeader}>
                    <SendOutlined style={{ color: '#1890ff' }} />
                    <span>简历完善度</span>
                    <span className={styles.progressPercent}>{resumePct}%</span>
                  </div>
                  <Progress percent={resumePct} showInfo={false} strokeColor="#1890ff" size="small" />
                </div>
                <div className={styles.progressCard}>
                  <div className={styles.progressHeader}>
                    <BookOutlined style={{ color: '#722ed1' }} />
                    <span>刷题目标</span>
                    <span className={styles.progressPercent}>{practicePct}%</span>
                  </div>
                  <Progress percent={practicePct} showInfo={false} strokeColor="#722ed1" size="small" />
                </div>
                <div className={styles.progressCard}>
                  <div className={styles.progressHeader}>
                    <SendOutlined style={{ color: '#52c41a' }} />
                    <span>投递目标</span>
                    <span className={styles.progressPercent}>{applicationPct}%</span>
                  </div>
                  <Progress percent={applicationPct} showInfo={false} strokeColor="#52c41a" size="small" />
                </div>
              </div>
            </Skeleton>
            </div>
          </Card>
        </Col>
      </Row>
    </div>

      {/* 最近动态 + 快速操作 */}
    <div className={styles.flexSection}>
      <Row gutter={[12, 12]} style={{ marginTop: 0 }}>
        <Col xs={24} lg={12}>
          <Card
            className={`${styles.sectionCard} ${styles.fillCard}`}
            title={
              <span className={styles.sectionTitle}>
                <TrophyOutlined /> 最近动态
              </span>
            }
            extra={
              <a onClick={() => navigate('/workbench')} className={styles.viewAll}>
                查看全部 <RightOutlined />
              </a>
            }
          >
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <Skeleton loading={activitiesLoading} active>
              {activities && (activities as unknown as ActivitiesResponse).activities?.length > 0 ? (
                <div className={styles.activityList}>
                  {(activities as unknown as ActivitiesResponse).activities.map((item: ActivityRecord) => {
                    const colorMap: Record<string, string> = {
                      application_created: '#1890ff',
                      ai_interview_completed: '#52c41a',
                      practice_session: '#722ed1',
                      job_favorited: '#faad14',
                    };
                    const iconMap: Record<string, React.ReactNode> = {
                      application_created: <SendOutlined />,
                      ai_interview_completed: <RobotOutlined />,
                      practice_session: <BookOutlined />,
                      job_favorited: <StarOutlined />,
                    };
                    const bgMap: Record<string, string> = {
                      application_created: '#e6f7ff',
                      ai_interview_completed: '#f6ffed',
                      practice_session: '#f9f0ff',
                      job_favorited: '#fffbe6',
                    };
                    const c = colorMap[item.type] || '#1890ff';
                    const bg = bgMap[item.type] || '#f5f5f5';
                    const ic = iconMap[item.type] || <TrophyOutlined />;

                    return (
                      <div key={item.id} className={styles.activityItem}>
                        <div className={styles.activityIcon} style={{ background: bg, color: c }}>
                          {ic}
                        </div>
                        <div className={styles.activityContent}>
                          <div className={styles.activityTitle}>{item.title}</div>
                          <div className={styles.activityDesc}>{item.description}</div>
                        </div>
                        <div className={styles.activityTime}>
                          {dayjs(item.created_at).format('MM-DD')}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <Empty description="暂无动态" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </Skeleton>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            className={`${styles.sectionCard} ${styles.fillCard}`}
            title={
              <span className={styles.sectionTitle}>
                <AimOutlined /> 快速操作
              </span>
            }
          >
            <div className={styles.quickGrid}>
              <div className={styles.quickItem} onClick={() => navigate('/ai-advisor')}
                style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                <RobotOutlined className={styles.quickIcon} />
                <span className={styles.quickLabel}>求职咨询</span>
                <span className={styles.quickDesc}>AI 顾问帮你分析</span>
              </div>
              <div className={styles.quickItem} onClick={() => navigate('/jobs')}
                style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
                <SearchOutlined className={styles.quickIcon} />
                <span className={styles.quickLabel}>岗位速览</span>
                <span className={styles.quickDesc}>浏览最新岗位</span>
              </div>
              <div className={styles.quickItem} onClick={() => navigate('/ai-interview')}
                style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
                <MessageOutlined className={styles.quickIcon} />
                <span className={styles.quickLabel}>AI面试</span>
                <span className={styles.quickDesc}>模拟面试练习</span>
              </div>
              <div className={styles.quickItem} onClick={() => navigate('/questions')}
                style={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }}>
                <CheckCircleOutlined className={styles.quickIcon} />
                <span className={styles.quickLabel}>开始刷题</span>
                <span className={styles.quickDesc}>巩固基础知识</span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
    </div>
  );
}

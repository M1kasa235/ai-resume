import { useState } from 'react';

import {
  UploadOutlined,
  FileTextOutlined,
  DownloadOutlined,
  RobotOutlined,
  MessageOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { workbenchApi, ragApi, optimizeApi, versionApi } from '@services/api';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  Row,
  Col,
  Upload,
  Button,
  Table,
  Tag,
  Select,
  Progress,
  Space,
  Modal,
  message,
  Empty,
  Tabs,
  Input,
  Spin,
  Alert,
  Divider,
  List,
  Typography,
} from 'antd';
import type { Application, PaginatedResponse } from '@/types';
import type {
  ResumeDiagnoseResponse,
  OptimizeResponse,
  OptimizedSection,
  JobMatchResponse,
  VersionItem,
  CompareResponse,
} from '@/types/api';

import styles from './Workbench.module.scss';

const { TextArea } = Input;
const { Text, Paragraph, Title } = Typography;

function getResumeFormat(url: string): 'pdf' | 'txt' | 'doc' | 'docx' | 'other' {
  const ext = url.split('.').pop()?.toLowerCase() || '';
  if (ext === 'pdf') return 'pdf';
  if (ext === 'txt') return 'txt';
  if (ext === 'doc') return 'doc';
  if (ext === 'docx') return 'docx';
  return 'other';
}

// ==================== 简历管理子组件 ====================
function ResumeManager({
  resumeInfo,
  uploadModalVisible,
  setUploadModalVisible,
  refetchResume,
  applicationsData,
  isLoading,
  statusFilter,
  setStatusFilter,
  statusFilterOptions,
  filteredApplications,
  selectedApplication,
  setSelectedApplication,
  handleDelete,
}: {
  resumeInfo: any;
  uploadModalVisible: boolean;
  setUploadModalVisible: (v: boolean) => void;
  refetchResume: () => void;
  applicationsData: any;
  isLoading: boolean;
  statusFilter: string;
  setStatusFilter: (v: string) => void;
  statusFilterOptions: { label: string; value: string }[];
  filteredApplications: Application[];
  selectedApplication: Application | null;
  setSelectedApplication: (v: Application | null) => void;
  handleDelete: (record: Application) => void;
}) {
  const [uploading, setUploading] = useState(false);
  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.pdf,.doc,.docx,.txt',
    customRequest: async ({ file, onSuccess, onError }: any) => {
      try {
        setUploading(true);
        await workbenchApi.uploadResume(file as File);
        message.success('简历上传成功！');
        setUploadModalVisible(false);
        onSuccess?.(null);
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
      const isTXT = file.type === 'text/plain' || file.name.endsWith('.txt');
      if (!isPDF && !isDOC && !isTXT) {
        message.error('只能上传PDF、Word或TXT文档！');
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
        const statusMap: Record<string, { color: string; text: string }> = {
          pending: { color: 'orange', text: '待处理' },
          reviewing: { color: 'blue', text: '筛选中' },
          interview: { color: 'green', text: '面试中' },
          rejected: { color: 'red', text: '已拒绝' },
          accepted: { color: 'success', text: '已录用' },
        };
        const config = statusMap[status] || { color: 'default', text: status };
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
          <Button type="link" onClick={() => setSelectedApplication(record)}>查看</Button>
          <Button type="link" danger onClick={() => handleDelete(record)}>删除</Button>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Row gutter={[24, 24]} className={styles.mainRow}>
        <Col xs={24} lg={16} className={styles.leftCol}>
          {resumeInfo?.resume_url ? (
            (() => {
              const fmt = getResumeFormat(resumeInfo.resume_url);
              if (fmt === 'pdf' || fmt === 'txt') {
                return (
                  <div className={styles.resumePreview}>
                    <iframe
                      src={`${resumeInfo.resume_url}${fmt === 'pdf' ? '#toolbar=0' : ''}`}
                      title="简历预览"
                      className={styles.resumeIframe}
                    />
                  </div>
                );
              }
              return (
                <div className={styles.emptyResume}>
                  <FileTextOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />
                  <p className={styles.emptyText}>该格式暂不支持在线预览</p>
                  <Button type="primary" icon={<DownloadOutlined />} onClick={() => window.open(resumeInfo.resume_url, '_blank')}>
                    下载查看
                  </Button>
                </div>
              );
            })()
          ) : (
            <div className={styles.emptyResume}>
              <FileTextOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />
              <p className={styles.emptyText}>暂未上传简历</p>
              <Button type="primary" onClick={() => setUploadModalVisible(true)}>上传简历</Button>
            </div>
          )}
        </Col>
        <Col xs={24} lg={8} className={styles.rightCol}>
          <Card title="简历管理" className={styles.resumeCardWrapper}>
            <div className={styles.resumeInfo}>
              <div className={styles.resumeHeader}>
                <FileTextOutlined style={{ fontSize: 36, color: '#1890ff' }} />
                <div>
                  <h3>我的简历</h3>
                  {resumeInfo?.resume_url ? (
                    <p style={{ color: '#52c41a', margin: 0 }}>✓ 已上传简历</p>
                  ) : (
                    <p style={{ color: '#999', margin: 0 }}>暂未上传简历</p>
                  )}
                </div>
              </div>
              <Space style={{ marginTop: 12 }}>
                {resumeInfo?.resume_url ? (
                  <>
                    <Button type="primary" icon={<DownloadOutlined />} onClick={() => window.open(resumeInfo.resume_url, '_blank')}>下载简历</Button>
                    <Button onClick={() => setUploadModalVisible(true)}>重新上传</Button>
                  </>
                ) : (
                  <Button type="primary" onClick={() => setUploadModalVisible(true)}>上传简历</Button>
                )}
              </Space>
            </div>
          </Card>
          <Card title="投递记录" className={styles.tableCard} extra={
            <Select size="small" value={statusFilter} onChange={setStatusFilter} style={{ width: 140 }} options={statusFilterOptions} />
          }>
            {isLoading ? (
              <div className={styles.loading}><div>加载中...</div></div>
            ) : filteredApplications.length > 0 ? (
              <Table columns={applicationColumns} dataSource={filteredApplications} rowKey="id"
                pagination={{ total: applicationsData?.total ?? 0, pageSize: 20, showSizeChanger: true }} />
            ) : (
              <Empty description="暂无投递记录" />
            )}
          </Card>
        </Col>
      </Row>

      {/* Upload Modal */}
      <Modal title="上传简历" open={uploadModalVisible} onCancel={() => setUploadModalVisible(false)} footer={null} width={600}>
        <Upload.Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon"><UploadOutlined /></p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">支持 PDF、Word、TXT 文档，文件大小不超过 5MB</p>
        </Upload.Dragger>
        {uploading && <div style={{ marginTop: 16, textAlign: 'center' }}><Progress percent={50} status="active" /></div>}
      </Modal>

      {/* Application Detail Modal */}
      <Modal title="投递详情" open={!!selectedApplication} onCancel={() => setSelectedApplication(null)} footer={null} width={800}>
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
    </>
  );
}

// ==================== 简历优化子组件 ====================
function ResumeOptimizer() {
  const [diagnosing, setDiagnosing] = useState(false);
  const [diagnoseResult, setDiagnoseResult] = useState<ResumeDiagnoseResponse | null>(null);
  const [optimizing, setOptimizing] = useState(false);
  const [optimizeResult, setOptimizeResult] = useState<OptimizeResponse | null>(null);
  const [jobId, setJobId] = useState<string>('');
  const [polishing, setPolishing] = useState(false);
  const [polishSection, setPolishSection] = useState('项目经验');
  const [polishContent, setPolishContent] = useState('');
  const [polishResult, setPolishResult] = useState<{ original: string; optimized: string; change_reason: string } | null>(null);
  const [fullResumeVisible, setFullResumeVisible] = useState(false);

  // 岗位匹配度分析
  const [matchJobId, setMatchJobId] = useState('');
  const [matching, setMatching] = useState(false);
  const [matchResult, setMatchResult] = useState<JobMatchResponse | null>(null);

  // 版本管理
  const [versions, setVersions] = useState<VersionItem[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [savingVersion, setSavingVersion] = useState(false);
  const [versionContent, setVersionContent] = useState('');
  const [versionSummary, setVersionSummary] = useState('');
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [compareVisible, setCompareVisible] = useState(false);

  const handleDiagnose = async () => {
    setDiagnosing(true);
    setDiagnoseResult(null);
    try {
      const res = await optimizeApi.diagnoseResume();
      setDiagnoseResult(res);
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '诊断失败');
    } finally {
      setDiagnosing(false);
    }
  };

  const handleOptimize = async () => {
    if (!jobId || isNaN(Number(jobId))) {
      message.warning('请输入有效的岗位ID');
      return;
    }
    setOptimizing(true);
    setOptimizeResult(null);
    try {
      const res = await optimizeApi.optimizeResume({ job_id: Number(jobId) });
      setOptimizeResult(res);
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '优化失败');
    } finally {
      setOptimizing(false);
    }
  };

  const handlePolish = async () => {
    if (!polishContent.trim()) {
      message.warning('请输入需要润色的内容');
      return;
    }
    setPolishing(true);
    setPolishResult(null);
    try {
      const res = await optimizeApi.polishSection({ section: polishSection, content: polishContent });
      setPolishResult(res);
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '润色失败');
    } finally {
      setPolishing(false);
    }
  };

  const handleMatchJob = async () => {
    if (!matchJobId || isNaN(Number(matchJobId))) {
      message.warning('请输入有效的岗位ID');
      return;
    }
    setMatching(true);
    setMatchResult(null);
    try {
      const res = await ragApi.matchJob({ job_id: Number(matchJobId) });
      setMatchResult(res);
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '匹配分析失败');
    } finally {
      setMatching(false);
    }
  };

  const handleLoadVersions = async () => {
    setLoadingVersions(true);
    try {
      const res = await versionApi.listVersions();
      setVersions(res.versions || []);
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '加载版本列表失败');
    } finally {
      setLoadingVersions(false);
    }
  };

  const handleSaveVersion = async () => {
    if (!versionContent.trim()) {
      message.warning('请输入要保存的简历内容');
      return;
    }
    setSavingVersion(true);
    try {
      await versionApi.saveVersion({
        content: versionContent,
        source: 'manual',
        summary: versionSummary || undefined,
      });
      message.success('版本保存成功');
      setVersionContent('');
      setVersionSummary('');
      handleLoadVersions();
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '保存失败');
    } finally {
      setSavingVersion(false);
    }
  };

  const handleCompare = async (v1Id: number, v2Id: number) => {
    try {
      const res = await versionApi.compareVersions(v1Id, v2Id);
      setCompareResult(res);
      setCompareVisible(true);
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '对比失败');
    }
  };

  return (
    <div className={styles.optimizeContainer}>
      {/* 简历诊断 */}
      <Card title={<><RobotOutlined /> 简历诊断</>} className={styles.optimizeCard}>
        <Text>AI将分析您的简历，给出综合评分、优势、不足和改进建议。</Text>
        <div style={{ marginTop: 12 }}>
          <Button type="primary" loading={diagnosing} onClick={handleDiagnose} icon={<ThunderboltOutlined />}>
            开始诊断
          </Button>
        </div>
        {diagnoseResult && (
          <div className={styles.resultSection}>
            <Alert type="success" showIcon message={`综合评分：${diagnoseResult.overall_score}`} style={{ marginBottom: 12 }} />
            {diagnoseResult.strengths.length > 0 && (
              <>
                <Text strong>优势：</Text>
                <List size="small" dataSource={diagnoseResult.strengths} renderItem={(item) => <List.Item>✅ {item}</List.Item>} />
              </>
            )}
            {diagnoseResult.weaknesses.length > 0 && (
              <>
                <Text strong>不足：</Text>
                <List size="small" dataSource={diagnoseResult.weaknesses} renderItem={(item) => <List.Item>⚠️ {item}</List.Item>} />
              </>
            )}
            {diagnoseResult.suggestions.length > 0 && (
              <>
                <Divider />
                <Text strong>改进建议：</Text>
                {diagnoseResult.suggestions.map((s, i) => (
                  <div key={i} className={styles.suggestionItem}>
                    <Text strong style={{ color: '#1890ff' }}>[{s.section}]</Text>
                    <div>问题：{s.issue}</div>
                    <div>建议：{s.advice}</div>
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </Card>

      {/* 针对岗位优化 */}
      <Card title={<><RobotOutlined /> 针对岗位优化</>} className={styles.optimizeCard}>
        <Text>输入岗位ID，AI将针对该岗位要求优化您的简历。</Text>
        <div style={{ marginTop: 12, display: 'flex', gap: 12, alignItems: 'center' }}>
          <Input placeholder="请输入岗位ID" value={jobId} onChange={(e) => setJobId(e.target.value)} style={{ width: 200 }} />
          <Button type="primary" loading={optimizing} onClick={handleOptimize}>开始优化</Button>
        </div>
        {optimizeResult && (
          <div className={styles.resultSection}>
            {optimizeResult.summary?.match_score_before !== undefined && (
              <Alert type="info" showIcon message={`匹配度：${optimizeResult.summary.match_score_before}/10 → ${optimizeResult.summary.match_score_after}/10`} style={{ marginBottom: 12 }} />
            )}
            {optimizeResult.optimized_sections.map((section: OptimizedSection, i: number) => (
              <div key={i} className={styles.optimizeSection}>
                <Title level={5}>{section.section}</Title>
                <div className={styles.diffBlock}>
                  <div className={styles.diffOriginal}>
                    <Text type="danger" strong>优化前：</Text>
                    <Paragraph ellipsis={{ rows: 3, expandable: true }}>{section.original}</Paragraph>
                  </div>
                  <div className={styles.diffOptimized}>
                    <Text type="success" strong>优化后：</Text>
                    <Paragraph ellipsis={{ rows: 3, expandable: true }}>{section.optimized}</Paragraph>
                  </div>
                </div>
                <Text type="secondary" style={{ fontSize: 12 }}>原因：{section.change_reason}</Text>
                <Divider />
              </div>
            ))}
            <Button type="link" onClick={() => setFullResumeVisible(true)}>查看完整简历</Button>
            <Modal title="优化后的完整简历" open={fullResumeVisible} onCancel={() => setFullResumeVisible(false)} footer={null}>
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>{optimizeResult.full_resume}</pre>
            </Modal>
          </div>
        )}
      </Card>

      {/* 岗位匹配度分析 */}
      <Card title={<><ThunderboltOutlined /> 岗位匹配度分析</>} className={styles.optimizeCard}>
        <Text>输入岗位ID，AI将分析您的简历与该岗位的匹配程度，从多个维度给出评分和建议。</Text>
        <div style={{ marginTop: 12, display: 'flex', gap: 12, alignItems: 'center' }}>
          <Input placeholder="请输入岗位ID" value={matchJobId} onChange={(e) => setMatchJobId(e.target.value)} style={{ width: 200 }} />
          <Button type="primary" loading={matching} onClick={handleMatchJob}>开始分析</Button>
        </div>
        {matchResult && (
          <div className={styles.resultSection}>
            <Alert type="success" showIcon message={`综合匹配度：${(matchResult.overall_score * 100).toFixed(1)}%`} style={{ marginBottom: 12 }} />
            <Text strong>各维度评分：</Text>
            <div style={{ margin: '8px 0' }}>
              {matchResult.scores.map((s, i) => (
                <div key={i} style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Text>{s.dimension}</Text>
                    <Text strong>{(s.score * 100).toFixed(0)}%</Text>
                  </div>
                  <Progress percent={Math.round(s.score * 100)} size="small" />
                  <Text type="secondary" style={{ fontSize: 12 }}>{s.reason}</Text>
                </div>
              ))}
            </div>
            {matchResult.analysis && (
              <>
                <Divider />
                <Text strong>详细分析：</Text>
                <Paragraph style={{ marginTop: 8 }}>{matchResult.analysis}</Paragraph>
              </>
            )}
            {matchResult.suggestions.length > 0 && (
              <>
                <Divider />
                <Text strong>改进建议：</Text>
                <List size="small" dataSource={matchResult.suggestions} renderItem={(item) => <List.Item>💡 {item}</List.Item>} />
              </>
            )}
          </div>
        )}
      </Card>

      {/* 单段润色 */}
      <Card title={<><MessageOutlined /> 单段润色</>} className={styles.optimizeCard}>
        <div style={{ marginBottom: 12 }}>
          <Text>选择段落类型，输入内容进行AI润色。</Text>
        </div>
        <Select value={polishSection} onChange={setPolishSection} style={{ width: 200, marginBottom: 12 }}
          options={[
            { label: '项目经验', value: '项目经验' },
            { label: '工作经历', value: '工作经历' },
            { label: '个人技能', value: '个人技能' },
            { label: '教育背景', value: '教育背景' },
            { label: '自我评价', value: '自我评价' },
          ]} />
        <TextArea rows={4} value={polishContent} onChange={(e) => setPolishContent(e.target.value)} placeholder="请输入需要润色的内容..." />
        <div style={{ marginTop: 12 }}>
          <Button type="primary" loading={polishing} onClick={handlePolish}>开始润色</Button>
        </div>
        {polishResult && (
          <div className={styles.resultSection}>
            <div className={styles.diffBlock}>
              <div className={styles.diffOriginal}>
                <Text type="danger" strong>原始：</Text>
                <Paragraph>{polishResult.original}</Paragraph>
              </div>
              <div className={styles.diffOptimized}>
                <Text type="success" strong>润色后：</Text>
                <Paragraph>{polishResult.optimized}</Paragraph>
              </div>
            </div>
            {polishResult.change_reason && (
              <Text type="secondary">{polishResult.change_reason}</Text>
            )}
          </div>
        )}
      </Card>

      {/* 版本管理 */}
      <Card title={<><FileTextOutlined /> 版本管理</>} className={styles.optimizeCard}>
        <Tabs items={[
          {
            key: 'save',
            label: '保存版本',
            children: (
              <div>
                <Text>将当前简历内容保存为一个新版本，方便回溯和对比。</Text>
                <div style={{ margin: '12px 0' }}>
                  <TextArea rows={6} value={versionContent} onChange={(e) => setVersionContent(e.target.value)} placeholder="请输入简历内容..." />
                </div>
                <div style={{ marginBottom: 12 }}>
                  <Input placeholder="版本备注（可选）" value={versionSummary} onChange={(e) => setVersionSummary(e.target.value)} />
                </div>
                <Button type="primary" loading={savingVersion} onClick={handleSaveVersion}>保存版本</Button>
              </div>
            ),
          },
          {
            key: 'history',
            label: '版本历史',
            children: (
              <div>
                <Button onClick={handleLoadVersions} loading={loadingVersions} style={{ marginBottom: 12 }}>刷新列表</Button>
                {versions.length === 0 && !loadingVersions ? (
                  <Empty description="暂无版本记录" />
                ) : (
                  <List size="small" dataSource={versions} renderItem={(item, idx) => (
                    <List.Item actions={idx > 0 ? [
                      <Button type="link" onClick={() => handleCompare(versions[idx - 1].id, item.id)}>对比上一版</Button>,
                    ] : undefined}>
                      <List.Item.Meta
                        title={`v${item.version} (${item.source})`}
                        description={
                          <>
                            <Text type="secondary">{new Date(item.created_at).toLocaleString()}</Text>
                            {item.summary && <div><Text type="secondary">备注：{item.summary}</Text></div>}
                          </>
                        }
                      />
                    </List.Item>
                  )} />
                )}
              </div>
            ),
          },
        ]} />
      </Card>

      {/* 版本对比弹窗 */}
      <Modal title="版本对比" open={compareVisible} onCancel={() => setCompareVisible(false)} footer={null} width={800}>
        {compareResult && (
          <div>
            <Alert type="info" showIcon message={`v${compareResult.v1_version} vs v${compareResult.v2_version}`} style={{ marginBottom: 12 }} />
            {compareResult.changes.length === 0 ? (
              <Text>两个版本内容一致，无差异。</Text>
            ) : (
              compareResult.changes.map((c, i) => (
                <div key={i} style={{ marginBottom: 8 }}>
                  {c.before && <div className={styles.diffOriginal}><Text type="danger">- {c.before}</Text></div>}
                  {c.after && <div className={styles.diffOptimized}><Text type="success">+ {c.after}</Text></div>}
                </div>
              ))
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}

// ==================== 简历问答(RAG)子组件 ====================
function ResumeQA() {
  const [question, setQuestion] = useState('');
  const [qaHistory, setQaHistory] = useState<Array<{ question: string; answer: string; references: Array<{ content: string; section: string }> }>>([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await ragApi.queryResume({ question: question.trim() });
      setQaHistory((prev) => [...prev, { question: question.trim(), answer: res.answer, references: res.references || [] }]);
      setQuestion('');
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '查询失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.qaContainer}>
      <Card title={<><RobotOutlined /> 简历问答</>} className={styles.qaCard}>
        <Text>基于您的简历内容进行智能问答，例如"我的项目经验有哪些"、"我掌握哪些技能"等。</Text>
        <Divider />
        <div className={styles.qaMessages}>
          {qaHistory.length === 0 ? (
            <Empty description="还没有提问，试试问一些关于简历的问题吧" />
          ) : (
            qaHistory.map((item, i) => (
              <div key={i} className={styles.qaMessage}>
                <div className={styles.qaQuestion}>
                  <Tag color="blue">问</Tag>
                  <Text>{item.question}</Text>
                </div>
                <div className={styles.qaAnswer}>
                  <Tag color="green">答</Tag>
                  <Paragraph>{item.answer}</Paragraph>
                </div>
                {item.references.length > 0 && (
                  <div className={styles.qaReferences}>
                    <Text type="secondary" style={{ fontSize: 12 }}>参考来源：</Text>
                    {item.references.map((ref, j) => (
                      <Tag key={j} color="processing" style={{ marginBottom: 4 }}>[{ref.section}] {ref.content.slice(0, 60)}...</Tag>
                    ))}
                  </div>
                )}
                <Divider style={{ margin: '12px 0' }} />
              </div>
            ))
          )}
          {loading && <Spin style={{ display: 'block', margin: '12px auto' }} />}
        </div>
        <div className={styles.qaInput}>
          <TextArea
            rows={2}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="请输入关于您简历的问题..."
            onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); handleAsk(); } }}
            disabled={loading}
          />
          <Button type="primary" onClick={handleAsk} loading={loading} style={{ marginTop: 8 }}>发送</Button>
        </div>
      </Card>
    </div>
  );
}

// ==================== 主组件 ====================
export default function Workbench() {
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState<Application | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: resumeInfo, refetch: refetchResume } = useQuery({
    queryKey: ['resume-info'],
    queryFn: async () => {
      const result = await workbenchApi.getResumeInfo();
      return result as any;
    },
  });

  const { data: applicationsData, isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: async () => {
      const result = await workbenchApi.getApplications({ page: 1, size: 20 });
      return result as any as PaginatedResponse<Application>;
    },
  });

  const getStatusStats = () => {
    const stats = { pending: 0, reviewing: 0, interview: 0, rejected: 0, accepted: 0 };
    applicationsData?.items?.forEach((app: Application) => {
      const s = app.status as keyof typeof stats;
      if (s in stats) stats[s]++;
    });
    return stats;
  };

  const statusStats = getStatusStats();
  const filteredApplications = statusFilter
    ? (applicationsData?.items ?? []).filter((app) => app.status === statusFilter)
    : (applicationsData?.items ?? []);

  const statusFilterOptions = [
    { label: '全部', value: '' },
    { label: `待处理 (${statusStats.pending})`, value: 'pending' },
    { label: `筛选中 (${statusStats.reviewing})`, value: 'reviewing' },
    { label: `面试中 (${statusStats.interview})`, value: 'interview' },
    { label: `已拒绝 (${statusStats.rejected})`, value: 'rejected' },
    { label: `已录用 (${statusStats.accepted})`, value: 'accepted' },
  ];

  const handleDelete = (record: Application) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除投递「${record.job_title}」的记录吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => message.success('已删除投递记录'),
    });
  };

  const tabItems = [
    {
      key: 'resume',
      label: <span><FileTextOutlined /> 简历管理</span>,
      children: (
        <ResumeManager
          resumeInfo={resumeInfo}
          uploadModalVisible={uploadModalVisible}
          setUploadModalVisible={setUploadModalVisible}
          refetchResume={refetchResume}
          applicationsData={applicationsData}
          isLoading={isLoading}
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          statusFilterOptions={statusFilterOptions}
          filteredApplications={filteredApplications}
          selectedApplication={selectedApplication}
          setSelectedApplication={setSelectedApplication}
          handleDelete={handleDelete}
        />
      ),
    },
    {
      key: 'optimize',
      label: <span><RobotOutlined /> 简历优化</span>,
      children: <ResumeOptimizer />,
    },
    {
      key: 'rag',
      label: <span><MessageOutlined /> 简历问答</span>,
      children: <ResumeQA />,
    },
  ];

  return (
    <div className={styles.workbench}>
      <h1>工作台</h1>
      <Tabs items={tabItems} />
    </div>
  );
}

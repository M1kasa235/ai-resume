import { useMemo, useRef, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import { aiInterviewApi } from '@services/api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card, Col, Input, List, Modal, Progress, Radio, Row, Space, Tag, Typography, message, Empty, Alert } from 'antd';
import { FileTextOutlined, RobotOutlined, CheckCircleOutlined } from '@ant-design/icons';

import type {
  AIInterviewMessage,
  AIInterviewSession,
  AIInterviewStartRequest,
  AIInterviewReportListItem,
} from '@/types/api';

import styles from './AIInterview.module.scss';

const { TextArea } = Input;
const { Text } = Typography;

const typeLabels: Record<string, string> = {
  technical: '技术面试',
  hr: 'HR 面试',
  comprehensive: '综合面试',
  behavioral: 'HR 面试',
};

type InterviewType = 'hr' | 'technical' | 'comprehensive';

const END_HINT_KEYWORDS = ['差不多了', '感谢你的参与', '面试到这里', '再见', '祝你好运', '期待你的'];

export default function AIInterview() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [interviewType, setInterviewType] = useState<InterviewType>('technical');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AIInterviewMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [showEndHint, setShowEndHint] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const startSessionMutation = useMutation({
    mutationFn: (payload: AIInterviewStartRequest) => aiInterviewApi.startSession(payload),
    onSuccess: (data) => {
      const session = data as unknown as AIInterviewSession;
      setSessionId(session.session_id);
      setMessages([]);
      setModalOpen(true);
    },
    onError: () => {
      message.error('创建面试会话失败，请稍后重试');
    },
  });

  const streamFromServer = useCallback((sid: string, msg: string) => {
    setIsStreaming(true);
    setStreamingContent('');
    setShowEndHint(false);
    const controller = new AbortController();
    abortRef.current = controller;

    aiInterviewApi.streamMessage(
      sid,
      msg,
      (token) => setStreamingContent((prev) => prev + token),
      (_seq) => {
        setStreamingContent((current) => {
          const finalContent = current || '好的，我们继续。';
          setMessages((prev) => [...prev, { role: 'assistant', content: finalContent }]);
          // 检测结束语
          if (END_HINT_KEYWORDS.some((kw) => finalContent.includes(kw))) {
            setShowEndHint(true);
          }
          return '';
        });
        setIsStreaming(false);
        abortRef.current = null;
      },
      (err) => {
        message.error(err.message || '流式请求失败');
        setIsStreaming(false);
        abortRef.current = null;
      },
      controller.signal,
    );
  }, []);

  // 会话创建成功后自动拉取第一个问题
  useEffect(() => {
    if (sessionId && modalOpen && messages.length === 0 && !isStreaming) {
      streamFromServer(sessionId, '');
    }
  }, [sessionId, modalOpen, messages.length, isStreaming, streamFromServer]);

  // 清理 abort
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const endSessionMutation = useMutation({
    mutationFn: (id: string) => aiInterviewApi.endSession(id),
    onSuccess: (_data, sid) => {
      setModalOpen(false);
      setMessages([]);
      setInputValue('');
      setSessionId(null);
      setShowEndHint(false);
      message.success('报告生成中，请稍候...');
      queryClient.invalidateQueries({ queryKey: ['ai-interview-history'] });
      navigate(`/ai-interview/report/${sid}`);
    },
    onError: () => {
      message.error('结束会话失败，请稍后重试');
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming, streamingContent]);

  const canStart = useMemo(() => jobTitle.trim().length > 0, [jobTitle]);

  const handleStart = () => {
    if (!canStart) {
      message.warning('请至少填写目标岗位');
      return;
    }
    startSessionMutation.mutate({
      job_title: jobTitle.trim(),
      company_name: companyName.trim() || undefined,
      interview_type: interviewType,
      job_description: jobDescription.trim() || undefined,
    });
  };

  const handleSend = () => {
    if (!sessionId || isStreaming) return;
    const userText = inputValue.trim();
    if (!userText) return;
    setMessages((prev) => [...prev, { role: 'user', content: userText }]);
    setInputValue('');
    streamFromServer(sessionId, userText);
  };

  const handleEnd = () => {
    if (!sessionId) return;
    Modal.confirm({
      title: '确认结束面试？',
      content: '结束后将生成评估报告，面试对话不可恢复。',
      okText: '确认结束',
      cancelText: '继续面试',
      onOk: () => endSessionMutation.mutate(sessionId),
    });
  };

  const handleModalClose = () => {
    if (sessionId) {
      abortRef.current?.abort();
      Modal.confirm({
        title: '退出面试？',
        content: '退出后面试将结束，可稍后回来查看报告。',
        okText: '退出',
        cancelText: '取消',
        onOk: () => {
          endSessionMutation.mutate(sessionId);
        },
      });
    }
  };

  const { data: historyData } = useQuery({
    queryKey: ['ai-interview-history'],
    queryFn: async () => {
      const res = await aiInterviewApi.listReports(1, 20);
      return res as unknown as { total: number; items: AIInterviewReportListItem[] };
    },
  });

  return (
    <div className={styles.page}>
      <Row gutter={20}>
        {/* 左侧：面试配置 */}
        <Col xs={24} lg={14}>
          <Card title={<><RobotOutlined /> 新建面试</>} className={styles.configCard}>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Input
                size="large"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="目标岗位（必填），例如：前端开发工程师"
              />
              <Input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="目标公司（可选）"
              />
              <TextArea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="岗位 JD（可选，如粘贴 JD，AI 将基于实际岗位要求出题）"
                rows={4}
              />
              <Radio.Group
                value={interviewType}
                onChange={(e) => setInterviewType(e.target.value)}
                optionType="button"
                buttonStyle="solid"
              >
                <Radio.Button value="technical">技术面</Radio.Button>
                <Radio.Button value="hr">HR 面</Radio.Button>
                <Radio.Button value="comprehensive">综合面</Radio.Button>
              </Radio.Group>
              <Button
                type="primary"
                size="large"
                block
                onClick={handleStart}
                loading={startSessionMutation.isPending}
              >
                开始面试
              </Button>
              <Text type="secondary">
                预计约 20 道题，AI 面试官将查阅你的简历和知识库，进行个性化提问。
              </Text>
            </Space>
          </Card>
        </Col>

        {/* 右侧：历史记录 */}
        <Col xs={24} lg={10}>
          <Card title="面试记录" className={styles.historyCard}>
            {!historyData?.items?.length ? (
              <Empty description="暂无面试记录" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ padding: 32 }} />
            ) : (
              <List
                dataSource={historyData.items}
                className={styles.historyList}
                renderItem={(item) => (
                  <List.Item
                    className={styles.historyItem}
                    onClick={() => navigate(`/ai-interview/report/${item.session_id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <List.Item.Meta
                      avatar={<FileTextOutlined style={{ fontSize: 18, color: '#1677ff' }} />}
                      title={
                        <Space size={8}>
                          <Text strong style={{ fontSize: 14 }}>{item.job_title || '模拟面试'}</Text>
                          <Tag color="blue" style={{ fontSize: 11, lineHeight: '18px' }}>{typeLabels[item.interview_type ?? ''] || item.interview_type}</Tag>
                        </Space>
                      }
                      description={
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {item.total_questions} 题 · {item.ended_at ? new Date(item.ended_at).toLocaleDateString() : '-'}
                        </Text>
                      }
                    />
                    {item.status === 'evaluating' ? (
                      <Tag color="processing" style={{ fontSize: 11 }}>评估中</Tag>
                    ) : item.overall_score != null ? (
                      <Progress
                        type="circle"
                        percent={item.overall_score}
                        size={48}
                        format={(p) => `${p}`}
                        strokeColor={item.overall_score >= 80 ? '#52c41a' : item.overall_score >= 60 ? '#faad14' : '#ff4d4f'}
                      />
                    ) : null}
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* 面试对话 - 全屏弹窗 */}
      <Modal
        open={modalOpen}
        onCancel={handleModalClose}
        width="100vw"
        style={{ maxWidth: '100vw', top: 0, paddingBottom: 0 }}
        styles={{ body: { height: 'calc(100vh - 110px)', padding: 0 } }}
        title={
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Space>
              <Tag color="blue">{typeLabels[interviewType]}</Tag>
              <span>{jobTitle || '模拟面试'}</span>
            </Space>
            <Space>
              <Text type="secondary" style={{ fontSize: 12 }}>第 {messages.filter(m => m.role === 'assistant').length}/20 题</Text>
              <Progress
                percent={Math.round((messages.filter(m => m.role === 'assistant').length / 20) * 100)}
                showInfo={false}
                size="small"
                style={{ width: 80, margin: 0 }}
                strokeColor="#1677ff"
              />
            </Space>
          </Space>
        }
        footer={
          <div className={styles.modalFooter}>
            <Button danger onClick={handleEnd} loading={endSessionMutation.isPending}>
              结束面试
            </Button>
          </div>
        }
        closable
        maskClosable={false}
        destroyOnClose
      >
        <div className={styles.chatContainer}>
          <div className={styles.chatMessages}>
            <List
              split={false}
              dataSource={messages}
              renderItem={(item) => (
                <div className={item.role === 'user' ? styles.userMsg : styles.aiMsg}>
                  <div className={item.role === 'user' ? styles.userBubble : styles.aiBubble}>
                    <div className={styles.bubbleRole}>{item.role === 'user' ? '我' : 'AI 面试官'}</div>
                    <div className={styles.bubbleContent}>{item.content}</div>
                  </div>
                </div>
              )}
            />
            {isStreaming && (
              <div className={styles.aiMsg}>
                <div className={styles.aiBubble}>
                  <div className={styles.bubbleRole}>AI 面试官</div>
                  <div className={styles.bubbleContent}>
                    {streamingContent || '...'}
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          {showEndHint && (
            <Alert
              message="面试已接近尾声，你可以点击下方「结束面试」生成评估报告"
              type="success"
              icon={<CheckCircleOutlined />}
              showIcon
              closable
              onClose={() => setShowEndHint(false)}
              className={styles.endHint}
            />
          )}
          <div className={styles.chatInput}>
            <TextArea
              rows={3}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="输入你的回答..."
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <Button
              type="primary"
              onClick={handleSend}
              loading={isStreaming}
              disabled={isStreaming}
              style={{ marginLeft: 12, alignSelf: 'flex-end' }}
            >
              发送
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

import { useMemo, useState } from 'react';

import { aiInterviewApi } from '@services/api';
import { useMutation } from '@tanstack/react-query';
import { Button, Card, Input, List, Radio, Space, Tag, Typography, message } from 'antd';

import type {
  AIInterviewMessage,
  AIInterviewReplyResponse,
  AIInterviewSession,
  AIInterviewStartRequest,
} from '@/types/api';

import styles from './AIInterview.module.scss';

const { TextArea } = Input;
const { Text } = Typography;

type InterviewType = 'hr' | 'technical' | 'comprehensive';

export default function AIInterview() {
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [interviewType, setInterviewType] = useState<InterviewType>('technical');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AIInterviewMessage[]>([]);
  const [inputValue, setInputValue] = useState('');

  const startSessionMutation = useMutation({
    mutationFn: (payload: AIInterviewStartRequest) => aiInterviewApi.startSession(payload),
    onSuccess: (data) => {
      const session = data as unknown as AIInterviewSession;
      setSessionId(session.session_id);
      if (session.messages?.length) {
        setMessages(session.messages);
      } else {
        setMessages([
          {
            role: 'assistant',
            content: '你好，我是你的AI面试官。请先做一个30秒的自我介绍，我们开始吧。',
          },
        ]);
      }
      message.success('AI面试会话已开始');
    },
    onError: () => {
      message.error('创建面试会话失败，请稍后重试');
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: (payload: { session_id: string; message: string }) => aiInterviewApi.sendMessage(payload),
    onSuccess: (data) => {
      const result = data as unknown as AIInterviewReplyResponse;
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.reply || '已收到你的回答，请继续下一题。',
        },
      ]);
      setInputValue('');
    },
    onError: () => {
      message.error('发送失败，请稍后重试');
    },
  });

  const endSessionMutation = useMutation({
    mutationFn: (id: string) => aiInterviewApi.endSession(id),
    onSuccess: () => {
      message.success('本次面试已结束');
      setSessionId(null);
      setMessages([]);
      setInputValue('');
    },
    onError: () => {
      message.error('结束会话失败，请稍后重试');
    },
  });

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
    });
  };

  const handleSend = () => {
    if (!sessionId) {
      message.warning('请先开始面试');
      return;
    }
    const userText = inputValue.trim();
    if (!userText) return;

    setMessages((prev) => [...prev, { role: 'user', content: userText }]);
    sendMessageMutation.mutate({ session_id: sessionId, message: userText });
  };

  const handleEnd = () => {
    if (!sessionId) return;
    endSessionMutation.mutate(sessionId);
  };

  return (
    <div className={styles.aiInterview}>
      <h1>AI面试</h1>
      <Card className={styles.setupCard} title="面试配置">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Input
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            placeholder="目标岗位（必填），例如：前端开发工程师"
            disabled={!!sessionId}
          />
          <Input
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="目标公司（可选）"
            disabled={!!sessionId}
          />
          <Radio.Group
            value={interviewType}
            onChange={(e) => setInterviewType(e.target.value)}
            disabled={!!sessionId}
          >
            <Radio.Button value="technical">技术面</Radio.Button>
            <Radio.Button value="hr">HR面</Radio.Button>
            <Radio.Button value="comprehensive">综合面</Radio.Button>
          </Radio.Group>
          <Space>
            <Button type="primary" onClick={handleStart} loading={startSessionMutation.isPending} disabled={!!sessionId}>
              开始面试
            </Button>
            <Button danger onClick={handleEnd} disabled={!sessionId} loading={endSessionMutation.isPending}>
              结束面试
            </Button>
            {sessionId && <Tag color="blue">会话ID: {sessionId}</Tag>}
          </Space>
          <Text type="secondary">
            当前为前端模块化接入版本，后续你只需要把 `aiInterviewApi` 对接到大模型后端接口即可。
          </Text>
        </Space>
      </Card>

      <Card className={styles.chatCard} title="面试对话">
        <List
          locale={{ emptyText: '点击“开始面试”后，这里将显示面试问答。' }}
          dataSource={messages}
          renderItem={(item) => (
            <List.Item className={item.role === 'user' ? styles.userItem : styles.assistantItem}>
              <div className={styles.bubble}>
                <div className={styles.role}>{item.role === 'user' ? '我' : 'AI面试官'}</div>
                <div>{item.content}</div>
              </div>
            </List.Item>
          )}
        />
        <Space direction="vertical" style={{ width: '100%', marginTop: 16 }}>
          <TextArea
            rows={4}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={sessionId ? '输入你的回答...' : '请先开始面试'}
            disabled={!sessionId}
          />
          <div className={styles.actions}>
            <Button type="primary" onClick={handleSend} disabled={!sessionId} loading={sendMessageMutation.isPending}>
              发送回答
            </Button>
          </div>
        </Space>
      </Card>
    </div>
  );
}

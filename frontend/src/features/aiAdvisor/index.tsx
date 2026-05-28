import { useCallback, useEffect, useRef, useState } from 'react';
import { message as antMessage } from 'antd';

import { advisorApi } from '@services/api';
import type { ChatMessage } from '@/types/api';

import SessionList from './components/SessionList';
import ChatArea from './components/ChatArea';
import MessageInput from './components/MessageInput';
import type { StreamStep } from './components/StreamProcess';
import styles from './Advisor.module.scss';

interface Session {
  id: string;
  title: string;
  created_at: string;
}

function getStorageKey(): string {
  try {
    const stored = JSON.parse(localStorage.getItem('user-storage') || '{}');
    const userId = stored?.state?.user?.id || 'anonymous';
    return `advisor-sessions-${userId}`;
  } catch {
    return 'advisor-sessions-anonymous';
  }
}

const WEB_SEARCH_STORAGE_KEY = 'advisor-web-search-enabled';

function loadWebSearchEnabled(): boolean {
  try {
    return localStorage.getItem(WEB_SEARCH_STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function loadSessions(): Session[] {
  try {
    const newKey = getStorageKey();
    const data = localStorage.getItem(newKey);
    if (data) return JSON.parse(data);

    // 迁移旧 key 下的会话数据（单 key → 按用户隔离 key）
    const oldData = localStorage.getItem('advisor-sessions');
    if (oldData) {
      const oldSessions = JSON.parse(oldData);
      localStorage.setItem(newKey, JSON.stringify(oldSessions));
      localStorage.removeItem('advisor-sessions');
      return oldSessions;
    }
    return [];
  } catch {
    return [];
  }
}

function saveSessions(sessions: Session[]) {
  localStorage.setItem(getStorageKey(), JSON.stringify(sessions));
}

export default function AIAdvisor() {
  const [sessions, setSessions] = useState<Session[]>(loadSessions);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(() => {
    return sessions[0]?.id || generateId();
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [streamSteps, setStreamSteps] = useState<StreamStep[]>([]);
  const [webSearchEnabled, setWebSearchEnabled] = useState(loadWebSearchEnabled);
  const streamingRef = useRef('');
  const stepCounterRef = useRef(0);

  // 初始化：如果没有会话，自动创建一个
  useEffect(() => {
    if (sessions.length === 0) {
      const id = generateId();
      const newSession: Session = { id, title: '新对话', created_at: new Date().toISOString() };
      setSessions([newSession]);
      saveSessions([newSession]);
      setActiveThreadId(id);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 切换会话时加载历史消息
  useEffect(() => {
    if (!activeThreadId) return;
    advisorApi
      .getMessages(activeThreadId)
      .then((data) => setMessages(data.messages || []))
      .catch(() => setMessages([]));
  }, [activeThreadId]);

  const handleNewSession = useCallback(() => {
    const id = generateId();
    const newSession: Session = { id, title: '新对话', created_at: new Date().toISOString() };
    const updated = [newSession, ...sessions];
    setSessions(updated);
    saveSessions(updated);
    setActiveThreadId(id);
    setMessages([]);
  }, [sessions]);

  const handleDeleteSession = useCallback(
    async (id: string) => {
      try {
        await advisorApi.clearMessages(id);
      } catch {
        antMessage.warning('服务端会话清理失败，本地已移除');
      }

      const updated = sessions.filter((s) => s.id !== id);
      setSessions(updated);
      saveSessions(updated);
      if (activeThreadId === id) {
        const nextId = updated[0]?.id || null;
        setActiveThreadId(nextId);
        setMessages([]);
      }
    },
    [sessions, activeThreadId],
  );

  const updateSessionTitle = useCallback(
    (threadId: string, title: string) => {
      const updated = sessions.map((s) =>
        s.id === threadId ? { ...s, title: title.slice(0, 30) + (title.length > 30 ? '...' : '') } : s,
      );
      setSessions(updated);
      saveSessions(updated);
    },
    [sessions],
  );

  const handleSend = useCallback(
    async (content: string) => {
      if (!activeThreadId) return;

      // 第一条消息自动作为会话标题
      const session = sessions.find((s) => s.id === activeThreadId);
      if (session && session.title === '新对话') {
        updateSessionTitle(activeThreadId, content);
      }

      const userMsg: ChatMessage = { role: 'user', content };
      setMessages((prev) => [...prev, userMsg]);
      setStreaming(true);
      setStreamingContent('');
      setStreamSteps([]);
      streamingRef.current = '';
      stepCounterRef.current = 0;

      await advisorApi.chatStream(
        {
          message: content,
          image_url: '',
          thread_id: activeThreadId,
          web_search_enabled: webSearchEnabled,
        },
        (statusMessage, step) => {
          setStreamSteps((prev) => {
            const completed = prev.map((item) => ({ ...item, done: true }));
            return [
              ...completed,
              {
                id: `${step || 'step'}-${stepCounterRef.current++}`,
                message: statusMessage,
                done: false,
              },
            ];
          });
        },
        (token) => {
          setStreamSteps((prev) => prev.map((item) => ({ ...item, done: true })));
          streamingRef.current += token;
          setStreamingContent(streamingRef.current);
        },
        () => {
          setStreaming(false);
          setStreamingContent('');
          setStreamSteps([]);
          const finalContent = streamingRef.current;
          streamingRef.current = '';
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: finalContent },
          ]);
        },
        () => {
          setStreaming(false);
          setStreamSteps([]);
          antMessage.error('发送失败，请重试');
        },
      );
    },
    [activeThreadId, sessions, updateSessionTitle, webSearchEnabled],
  );

  const handleWebSearchChange = useCallback((enabled: boolean) => {
    setWebSearchEnabled(enabled);
    localStorage.setItem(WEB_SEARCH_STORAGE_KEY, String(enabled));
  }, []);

  return (
    <div className={styles.advisor}>
      <SessionList
        sessions={sessions}
        activeId={activeThreadId}
        onSelect={setActiveThreadId}
        onNew={handleNewSession}
        onDelete={handleDeleteSession}
      />
      <div className={styles.main}>
        <ChatArea
          messages={messages}
          streaming={streaming}
          streamingContent={streamingContent}
          streamSteps={streamSteps}
        />
        <MessageInput
          onSend={handleSend}
          disabled={!activeThreadId || streaming}
          webSearchEnabled={webSearchEnabled}
          onWebSearchChange={handleWebSearchChange}
        />
      </div>
    </div>
  );
}

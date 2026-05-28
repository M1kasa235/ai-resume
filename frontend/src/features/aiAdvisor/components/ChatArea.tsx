import { useEffect, useRef } from 'react';
import { Empty } from 'antd';

import type { ChatMessage } from '@/types/api';
import MessageBubble from './MessageBubble';
import StreamProcess, { type StreamStep } from './StreamProcess';
import styles from '../Advisor.module.scss';

interface ChatAreaProps {
  messages: ChatMessage[];
  streaming?: boolean;
  streamingContent?: string;
  streamSteps?: StreamStep[];
}

export default function ChatArea({
  messages,
  streaming,
  streamingContent,
  streamSteps = [],
}: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent, streamSteps]);

  const hasContent =
    messages.length > 0 || !!streaming || !!streamingContent || streamSteps.length > 0;

  return (
    <div className={styles.chatArea}>
      {!hasContent ? (
        <div className={styles.emptyState}>
          <Empty
            description="开始新的求职咨询吧"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
          <div className={styles.emptyHints}>
            <p>你可以这样问：</p>
            <ul>
              <li>帮我搜索 Python 开发的工作</li>
              <li>Java 后端的薪资怎么样？</li>
              <li>推荐一些适合我的岗位</li>
            </ul>
          </div>
        </div>
      ) : (
        <>
          {messages.map((msg, i) => (
            <MessageBubble key={i} role={msg.role} content={msg.content} />
          ))}
          {streaming && streamSteps.length > 0 && (
            <StreamProcess steps={streamSteps} streaming={!!streaming} />
          )}
          {streaming && streamingContent && (
            <MessageBubble role="assistant" content={streamingContent} />
          )}
        </>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

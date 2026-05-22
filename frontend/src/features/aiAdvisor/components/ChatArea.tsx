import { useEffect, useRef } from 'react';
import { Spin, Empty } from 'antd';

import type { ChatMessage } from '@/types/api';
import MessageBubble from './MessageBubble';
import styles from '../Advisor.module.scss';

interface ChatAreaProps {
  messages: ChatMessage[];
  streaming?: boolean;
  streamingContent?: string;
}

export default function ChatArea({
  messages,
  streaming,
  streamingContent,
}: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const hasContent = messages.length > 0 || (streaming && streamingContent);

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
          {streaming && streamingContent && (
            <MessageBubble role="assistant" content={streamingContent} />
          )}
          {streaming && (
            <div className={styles.streamingIndicator}>
              <Spin size="small" />
              <span>AI 正在思考...</span>
            </div>
          )}
        </>
      )}
      <div ref={bottomRef} />
    </div>
  );
}

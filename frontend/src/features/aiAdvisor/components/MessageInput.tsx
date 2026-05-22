import { useCallback, useState } from 'react';
import { Button, Input } from 'antd';
import { SendOutlined } from '@ant-design/icons';

import styles from '../Advisor.module.scss';

const { TextArea } = Input;

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

export default function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [value, setValue] = useState('');

  const handleSend = useCallback(() => {
    const text = value.trim();
    if (!text) return;
    onSend(text);
    setValue('');
  }, [value, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  return (
    <div className={styles.inputArea}>
      <TextArea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? '请先新建或选择一个会话' : '输入你的问题，按 Enter 发送，Shift+Enter 换行'}
        disabled={disabled}
        rows={3}
        className={styles.textarea}
      />
      <div className={styles.inputActions}>
        <span className={styles.inputHint}>Enter 发送 · Shift+Enter 换行</span>
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          disabled={disabled || !value.trim()}
        >
          发送
        </Button>
      </div>
    </div>
  );
}

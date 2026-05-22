import { Button, List, Popconfirm } from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  MessageOutlined,
} from '@ant-design/icons';

import styles from '../Advisor.module.scss';

interface Session {
  id: string;
  title: string;
  created_at: string;
}

interface SessionListProps {
  sessions: Session[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export default function SessionList({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: SessionListProps) {
  return (
    <div className={styles.sidebar}>
      <div className={styles.sidebarHeader}>
        <span>历史会话</span>
        <Button
          type="primary"
          size="small"
          icon={<PlusOutlined />}
          onClick={onNew}
        >
          新建
        </Button>
      </div>
      <div className={styles.sidebarList}>
        <List
          dataSource={sessions}
          locale={{ emptyText: '暂无会话' }}
          renderItem={(item) => (
            <List.Item
              className={`${styles.sessionItem} ${item.id === activeId ? styles.sessionActive : ''}`}
              onClick={() => onSelect(item.id)}
            >
              <div className={styles.sessionContent}>
                <MessageOutlined className={styles.sessionIcon} />
                <div className={styles.sessionTitle}>{item.title}</div>
                <Popconfirm
                  title="确定删除该会话？"
                  onConfirm={(e) => {
                    e?.stopPropagation();
                    onDelete(item.id);
                  }}
                  onCancel={(e) => e?.stopPropagation()}
                >
                  <Button
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => e.stopPropagation()}
                    className={styles.deleteBtn}
                  />
                </Popconfirm>
              </div>
            </List.Item>
          )}
        />
      </div>
    </div>
  );
}

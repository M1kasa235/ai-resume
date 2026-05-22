import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { adminApi } from '@services/api';
import type { ResumeUser, ResumeSection } from '@/types/api';
import ResumeUserList from './ResumeUserList';
import ResumeSectionList from './ResumeSectionList';
import ResumeChunkList from './ResumeChunkList';

type ViewState =
  | { key: 'users' }
  | { key: 'sections'; userId: number }
  | { key: 'chunks'; userId: number; section: string; label: string };

export default function ResumeTab() {
  const [viewState, setViewState] = useState<ViewState>({ key: 'users' });
  const [users, setUsers] = useState<ResumeUser[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);

  const [sections, setSections] = useState<ResumeSection[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [sectionsLoading, setSectionsLoading] = useState(false);

  const fetchUsers = useCallback(async () => {
    setUsersLoading(true);
    try {
      const res = await adminApi.getResumeUsers();
      const d = (res as any).data || res;
      setUsers(d.items || []);
    } catch {
      message.error('获取简历用户列表失败');
    } finally {
      setUsersLoading(false);
    }
  }, []);

  const fetchSections = useCallback(async (userId: number) => {
    setSectionsLoading(true);
    try {
      const res = await adminApi.getResumeSections(userId);
      const d = (res as any).data || res;
      setSections(d.items || []);
      setTotalChunks(d.total_chunks || 0);
    } catch {
      message.error('获取简历分区失败');
    } finally {
      setSectionsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const goToSections = (userId: number) => {
    setViewState({ key: 'sections', userId });
    fetchSections(userId);
  };

  const goToChunks = (userId: number, section: string, label: string) => {
    setViewState({ key: 'chunks', userId, section, label });
  };

  const goToUsers = () => {
    setViewState({ key: 'users' });
    fetchUsers();
  };

  const goBackToSections = () => {
    if (viewState.key === 'chunks') {
      const vs = viewState as { key: 'chunks'; userId: number };
      setViewState({ key: 'sections', userId: vs.userId });
      fetchSections(vs.userId);
    }
  };

  if (viewState.key === 'sections') {
    return (
      <ResumeSectionList
        userId={viewState.userId}
        sections={sections}
        totalChunks={totalChunks}
        loading={sectionsLoading}
        onBack={goToUsers}
        onSelect={(sec, lbl) => goToChunks(viewState.userId, sec, lbl)}
        onDeleted={goToUsers}
      />
    );
  }

  if (viewState.key === 'chunks') {
    return (
      <ResumeChunkList
        userId={viewState.userId}
        section={viewState.section}
        label={viewState.label}
        onBack={goBackToSections}
        onDeleted={goBackToSections}
      />
    );
  }

  return (
    <ResumeUserList
      users={users}
      loading={usersLoading}
      onSelect={goToSections}
    />
  );
}
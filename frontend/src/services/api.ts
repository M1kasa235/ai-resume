import type {
  ApiResponse,
  PaginatedResponse,
  Token,
  User,
  ChatMessage,
  DashboardOverviewResponse,
  GrowthCurveResponse,
  ActivitiesResponse,
  Job,
  Question,
  WrongQuestionItem,
  FavoriteQuestionItem,
  AIInterviewSession,
  AIInterviewStartRequest,
  AIInterviewReplyRequest,
  AIInterviewReplyResponse,
  AIInterviewEndResponse,
  AIInterviewReport,
  AIInterviewReportListItem,
  ResumeQueryResponse,
  JobMatchResponse,
  ResumeDiagnoseResponse,
  OptimizeResponse,
  PolishResponse,
  VersionListResponse,
  VersionDetail,
  CompareResponse,
  KnowledgeStats,
  KnowledgePartition,
  KnowledgeDocument,
  DocumentChunksResponse,
  ResumeUser,
  ResumeSection,
  ResumeChunkItem,
} from '@/types/api';

import http from './http';

// ==================== 认证相关接口 ====================
export const authApi = {
  // 用户注册
  register: async (data: {
    username: string;
    email: string;
    phone?: string;
    password: string;
  }) => {
    return http.post<ApiResponse>('/api/v1/auth/register', data);
  },

  // 用户登录
  login: async (data: {
    username: string;
    password: string;
  }) => {
    return http.post<ApiResponse<Token>>('/api/v1/auth/login', data);
  },

  // 刷新Token
  refreshToken: async (refreshToken: string) => {
    return http.post<ApiResponse<Token>>('/api/v1/auth/refresh', { refresh_token: refreshToken });
  },

  // 获取当前用户信息
  getCurrentUser: async () => {
    return http.get<ApiResponse<User>>('/api/v1/auth/me');
  },

  // 用户登出
  logout: async () => {
    return http.post<ApiResponse>('/api/v1/auth/logout');
  },
};

// ==================== 用户管理接口 ====================
export const userApi = {
  // 获取个人资料
  getProfile: async () => {
    return http.get<ApiResponse<User>>('/api/v1/users/profile');
  },

  // 更新个人资料
  updateProfile: async (data: {
    real_name?: string;
    gender?: string;
    current_city?: string;
    target_city?: string;
    work_years?: number;
    education?: string;
    avatar_url?: string;
  }) => {
    return http.put<ApiResponse<User>>('/api/v1/users/profile', data);
  },

  // 修改密码
  changePassword: async (data: {
    old_password: string;
    new_password: string;
  }) => {
    return http.put<ApiResponse>('/api/v1/users/password', data);
  },
};

// ==================== 岗位管理接口 ====================
export const jobApi = {
  // 获取岗位列表（支持多维度筛选）
  getJobs: async (params: {
    keyword?: string;
    city?: string;
    category_id?: number;
    salary_min?: number;
    salary_max?: number;
    experience_min?: number;
    experience_max?: number;
    education?: string;
    company_stage?: string;
    skills?: string[];
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
    page?: number;
    page_size?: number;
    only_urgent?: boolean;
  }) => {
    return http.get<PaginatedResponse<Job>>('/api/v1/jobs/list', { params });
  },

  // 获取热门岗位
  getHotJobs: async (limit: number = 10) => {
    return http.get<ApiResponse>('/api/v1/jobs/hot', { params: { limit } });
  },

  // 获取最新岗位
  getLatestJobs: async (limit: number = 10) => {
    return http.get<ApiResponse>('/api/v1/jobs/latest', { params: { limit } });
  },

  // 获取岗位统计数据
  getJobStatistics: async () => {
    return http.get<ApiResponse>('/api/v1/jobs/statistics');
  },

  // 获取岗位详情
  getJobDetail: async (id: number) => {
    return http.get<ApiResponse<Job>>(`/api/v1/jobs/${id}`);
  },

  // 创建岗位
  createJob: async (data: {
    title: string;
    category_id?: number;
    company_name: string;
    company_logo?: string;
    company_stage?: string;
    company_size?: string;
    description?: string;
    requirements?: string;
    salary_min?: number;
    salary_max?: number;
    salary_months?: number;
    city?: string;
    district?: string;
    address?: string;
    experience_min?: number;
    experience_max?: number;
    education_requirement?: string;
    skills_required?: string[];
    tags?: string[];
    is_urgent?: boolean;
    expired_at?: string;
  }) => {
    return http.post<ApiResponse>('/api/v1/jobs', data);
  },

  // 更新岗位
  updateJob: async (id: number, data: Partial<{
    title: string;
    category_id?: number;
    company_name: string;
    company_logo?: string;
    company_stage?: string;
    company_size?: string;
    description?: string;
    requirements?: string;
    salary_min?: number;
    salary_max?: number;
    salary_months?: number;
    city?: string;
    district?: string;
    address?: string;
    experience_min?: number;
    experience_max?: number;
    education_requirement?: string;
    skills_required?: string[];
    tags?: string[];
    is_urgent?: boolean;
    is_active?: boolean;
    expired_at?: string;
  }>) => {
    return http.put<ApiResponse>(`/api/v1/jobs/${id}`, data);
  },

  // 删除岗位
  deleteJob: async (id: number) => {
    return http.delete<ApiResponse>(`/api/v1/jobs/${id}`);
  },

  // 岗位分类相关
  getCategoryTree: async () => {
    return http.get<ApiResponse>('/api/v1/jobs/categories/tree');
  },

  getCategoryList: async () => {
    return http.get<ApiResponse>('/api/v1/jobs/categories/list');
  },

  createCategory: async (data: {
    name: string;
    code: string;
    parent_id?: number;
    sort_order?: number;
  }) => {
    return http.post<ApiResponse>('/api/v1/jobs/categories', data);
  },

  updateCategory: async (id: number, data: Partial<{
    name: string;
    code: string;
    parent_id?: number;
    sort_order?: number;
    is_active?: boolean;
  }>) => {
    return http.put<ApiResponse>(`/api/v1/jobs/categories/${id}`, data);
  },

  deleteCategory: async (id: number) => {
    return http.delete<ApiResponse>(`/api/v1/jobs/categories/${id}`);
  },

  // 收藏相关
  addFavorite: async (jobId: number) => {
    return http.post<ApiResponse>(`/api/v1/jobs/${jobId}/favorite`);
  },

  removeFavorite: async (jobId: number) => {
    return http.delete<ApiResponse>(`/api/v1/jobs/${jobId}/favorite`);
  },

  getMyFavorites: async (params: {
    page?: number;
    page_size?: number;
  }) => {
    return http.get<PaginatedResponse<Job>>('/api/v1/jobs/user/favorites', { params });
  },

  checkFavoriteStatus: async (jobId: number) => {
    return http.get<ApiResponse<{ is_favorited: boolean }>>(`/api/v1/jobs/${jobId}/favorite/status`);
  },
};

// ==================== 题库接口 ====================
export const questionApi = {
  // 获取题目列表（支持多维度筛选）
  getQuestions: async (params: {
    category_id?: number;
    difficulty?: 'easy' | 'medium' | 'hard';
    question_type?: string;
    keyword?: string;
    only_hot?: boolean;
    page?: number;
    page_size?: number;
  }) => {
    return http.get<PaginatedResponse<Question>>('/api/v1/questions', { params });
  },

  // 获取题目详情
  getQuestionDetail: async (id: number) => {
    return http.get<ApiResponse>(`/api/v1/questions/${id}`);
  },

  // 提交答案
  submitAnswer: async (questionId: number, data: {
    answer: string;
    time_spent?: number;
  }) => {
    return http.post<ApiResponse>(`/api/v1/questions/${questionId}/answer`, data);
  },

  // 获取我的刷题统计
  getPracticeStats: async () => {
    return http.get<ApiResponse>('/api/v1/questions/my/stats');
  },

  // 获取我的错题列表
  getWrongQuestions: async (params: {
    page?: number;
    page_size?: number;
  }) => {
    return http.get<PaginatedResponse<WrongQuestionItem>>('/api/v1/questions/my/wrong', { params });
  },

  // 标记错题为已掌握
  markWrongAsMastered: async (wrongId: number) => {
    return http.put<ApiResponse>(`/api/v1/questions/my/wrong/${wrongId}/mastered`);
  },

  // 获取我的收藏列表
  getFavorites: async (params: {
    page?: number;
    page_size?: number;
  }) => {
    return http.get<PaginatedResponse<FavoriteQuestionItem>>('/api/v1/questions/my/favorites', { params });
  },

  // 收藏/取消收藏题目
  toggleFavorite: async (questionId: number) => {
    return http.post<ApiResponse>(`/api/v1/questions/${questionId}/favorite`);
  },
};

// ==================== 工作台接口 ====================
export const workbenchApi = {
  // 上传个人简历 PDF
  uploadResume: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return http.post<ApiResponse>('/api/v1/workbench/resume/upload', formData);
  },

  // 获取当前用户的简历信息及基础画像
  getResumeInfo: async () => {
    return http.get<ApiResponse>('/api/v1/workbench/resume');
  },

  // 分页获取个人的投递记录
  getApplications: async (params: {
    page?: number;
    size?: number;
  }) => {
    return http.get<PaginatedResponse<any>>('/api/v1/workbench/applications', { params });
  },

  // 投递简历到指定岗位
  applyJob: async (data: {
    job_id: number;
    notes?: string;
  }) => {
    return http.post<ApiResponse>('/api/v1/workbench/applications', data);
  },
};

// ==================== AI求职顾问接口 ====================
export const advisorApi = {
  // 流式对话（SSE：status / token / done）
  chatStream: async (
    data: {
      message: string;
      image_url?: string;
      thread_id: string;
      web_search_enabled?: boolean;
    },
    onStatus: (message: string, step?: string) => void,
    onToken: (text: string) => void,
    onDone: () => void,
    onError: (err: Error) => void,
    signal?: AbortSignal,
  ) => {
    const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
    let token: string | null = null;
    try {
      const stored = JSON.parse(localStorage.getItem('user-storage') || '{}');
      token = stored?.state?.token || null;
    } catch { /* ignore */ }
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const response = await fetch(`${BASE_URL}/api/v1/agent/chat/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data),
        signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const payload = JSON.parse(line.slice(6)) as {
              type: string;
              content?: string;
              message?: string;
              step?: string;
            };
            if (payload.type === 'status' && payload.message) {
              onStatus(payload.message, payload.step);
            } else if (payload.type === 'token' && payload.content) {
              onToken(payload.content);
            } else if (payload.type === 'done') {
              onDone();
              return;
            } else if (payload.type === 'error') {
              onError(new Error((payload as { message?: string }).message || 'stream error'));
              return;
            }
          } catch {
            // ignore malformed SSE lines
          }
        }
      }
      onDone();
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') onError(err);
    }
  },

  // 获取历史消息
  getMessages: async (threadId: string) => {
    const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
    let token: string | null = null;
    try {
      const stored = JSON.parse(localStorage.getItem('user-storage') || '{}');
      token = stored?.state?.token || null;
    } catch {}
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${BASE_URL}/api/v1/agent/chat/history?thread_id=${threadId}`, { headers });
    return res.json() as Promise<{ messages: ChatMessage[] }>;
  },

  // 清空会话
  clearMessages: async (threadId: string) => {
    const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
    let token: string | null = null;
    try {
      const stored = JSON.parse(localStorage.getItem('user-storage') || '{}');
      token = stored?.state?.token || null;
    } catch {}
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    await fetch(`${BASE_URL}/api/v1/agent/chat/history?thread_id=${threadId}`, { method: 'DELETE', headers });
  },
};

// ==================== 首页接口 ====================
export const dashboardApi = {
  // 获取首页概览数据
  getOverview: async () => {
    return http.get<ApiResponse<DashboardOverviewResponse>>('/api/v1/dashboard/overview');
  },

  // 获取个人成长曲线数据
  getGrowthCurve: async (days: number = 30) => {
    return http.get<ApiResponse<GrowthCurveResponse>>('/api/v1/dashboard/growth-curve', { params: { days } });
  },

  // 获取个人最新动态
  getActivities: async (limit: number = 10) => {
    return http.get<ApiResponse<ActivitiesResponse>>('/api/v1/dashboard/activities', { params: { limit } });
  },
};

// ==================== RAG 简历问答接口 ====================
export const ragApi = {
  queryResume: async (data: { question: string }) => {
    const res = await http.post<ResumeQueryResponse>('/api/v1/rag/resume/query', data);
    return (res as any) as ResumeQueryResponse;
  },

  matchJob: async (data: { job_id: number }) => {
    const res = await http.post<JobMatchResponse>('/api/v1/rag/job/match', data);
    return (res as any) as JobMatchResponse;
  },
};

// ==================== 简历优化接口 ====================
export const optimizeApi = {
  diagnoseResume: async () => {
    const res = await http.post<ResumeDiagnoseResponse>('/api/v1/resume/diagnose');
    return (res as any) as ResumeDiagnoseResponse;
  },

  optimizeResume: async (data: { job_id: number }) => {
    const res = await http.post<OptimizeResponse>('/api/v1/resume/optimize', data);
    return (res as any) as OptimizeResponse;
  },

  polishSection: async (data: { section: string; content: string }) => {
    const res = await http.post<PolishResponse>('/api/v1/resume/polish', data);
    return (res as any) as PolishResponse;
  },
};

// ==================== 简历版本管理接口 ====================
export const versionApi = {
  listVersions: async () => {
    const res = await http.get<VersionListResponse>('/api/v1/resume/versions');
    return (res as any) as VersionListResponse;
  },

  saveVersion: async (data: { content: string; source: string; summary?: string }) => {
    const res = await http.post<any>('/api/v1/resume/versions', data);
    return (res as any) as any;
  },

  getVersion: async (id: number) => {
    const res = await http.get<VersionDetail>(`/api/v1/resume/versions/${id}`);
    return (res as any) as VersionDetail;
  },

  compareVersions: async (v1: number, v2: number) => {
    const res = await http.get<CompareResponse>(`/api/v1/resume/versions/${v1}/compare/${v2}`);
    return (res as any) as CompareResponse;
  },
};

// ==================== 管理后台接口 ====================
export const adminApi = {
  // 知识库统计
  getKnowledgeStats: async () => {
    return http.get<ApiResponse<KnowledgeStats>>('/api/v1/admin/knowledge/stats');
  },

  // 知识库文档块列表
  listChunks: async (params: {
    collection?: string;
    user_id?: number;
    page?: number;
    page_size?: number;
  }) => {
    return http.get<ApiResponse>('/api/v1/admin/knowledge/chunks', { params });
  },

  // 删除文档块
  deleteChunks: async (ids: string[], collection?: string) => {
    const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
    const { token } = JSON.parse(localStorage.getItem('user-storage') || '{}')?.state || {};
    const params = new URLSearchParams();
    ids.forEach((id) => params.append('ids', id));
    if (collection) params.append('collection', collection);
    const res = await fetch(`${BASE_URL}/api/v1/admin/knowledge/chunks?${params}`, {
      method: 'DELETE',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return res.json();
  },

  // 删除用户的所有文档块
  deleteUserChunks: async (userId: number) => {
    return http.delete<ApiResponse>(`/api/v1/admin/knowledge/user/${userId}`);
  },

  // 导入岗位数据（CSV/JSON/PDF/DOCX/TXT）
  importJobs: async (file: File, docType?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    const url = docType
      ? `/api/v1/admin/knowledge/import?doc_type=${encodeURIComponent(docType)}`
      : '/api/v1/admin/knowledge/import';
    return http.post<ApiResponse>(url, formData);
  },

  // 创建题目
  createQuestion: async (data: {
    category_id: number;
    type: string;
    difficulty?: string;
    title: string;
    content?: string;
    options?: any[];
    correct_answer?: string;
    explanation?: string;
    code_template?: string;
    test_cases?: any[];
    tags?: string[];
    company_tags?: string[];
    is_hot?: boolean;
  }) => {
    return http.post<ApiResponse>('/api/v1/admin/questions', data);
  },

  // 更新题目
  updateQuestion: async (id: number, data: any) => {
    return http.put<ApiResponse>(`/api/v1/admin/questions/${id}`, data);
  },

  // 删除题目
  deleteQuestion: async (id: number) => {
    return http.delete<ApiResponse>(`/api/v1/admin/questions/${id}`);
  },

  // ==================== 知识库文档管理 ====================

  // 获取所有知识库分区
  getPartitions: async () => {
    return http.get<ApiResponse<{ total: number; partitions: KnowledgePartition[] }>>('/api/v1/admin/knowledge/partitions');
  },

  // 创建分区
  createPartition: async (data: { doc_key: string; name: string; description?: string }) => {
    return http.post<ApiResponse>('/api/v1/admin/knowledge/partitions', data);
  },

  // 更新分区
  updatePartition: async (id: number, data: { name?: string; description?: string }) => {
    return http.put<ApiResponse>(`/api/v1/admin/knowledge/partitions/${id}`, data);
  },

  // 删除分区
  deletePartition: async (id: number) => {
    return http.delete<ApiResponse>(`/api/v1/admin/knowledge/partitions/${id}`);
  },

  // 种子默认分区
  seedPartitions: async () => {
    return http.post<ApiResponse>('/api/v1/admin/knowledge/partitions/seed');
  },

  // 获取某分区下的文档列表
  getDocuments: async (params: {
    doc_type: string;
    page?: number;
    page_size?: number;
  }) => {
    return http.get<ApiResponse<{ total: number; page: number; page_size: number; items: KnowledgeDocument[] }>>('/api/v1/admin/knowledge/documents', { params });
  },

  // 获取文档的分块详情
  getDocumentChunks: async (parentId: string) => {
    return http.get<ApiResponse<DocumentChunksResponse>>(`/api/v1/admin/knowledge/documents/${parentId}/chunks`);
  },

  // 创建知识文档
  createDocument: async (data: {
    title: string;
    category?: string;
    content: string;
    doc_type: string;
  }) => {
    return http.post<ApiResponse>('/api/v1/admin/knowledge/documents', data);
  },

  // 更新知识文档
  updateDocument: async (data: {
    parent_id: string;
    title: string;
    category?: string;
    content: string;
    doc_type: string;
  }) => {
    return http.post<ApiResponse>('/api/v1/admin/knowledge/documents', data);
  },

  // 删除知识文档
  deleteDocument: async (parentId: string) => {
    return http.delete<ApiResponse>(`/api/v1/admin/knowledge/documents/${parentId}`);
  },

  // 上传 JSON 文件导入知识库
  uploadKnowledgeFile: async (file: File, docType: string) => {
    const formData = new FormData();
    formData.append('file', file);
    return http.post<ApiResponse>(`/api/v1/admin/knowledge/upload?doc_type=${encodeURIComponent(docType)}`, formData);
  },

  // ==================== 简历知识库管理 ====================

  // 获取所有已上传简历的用户列表
  getResumeUsers: async () => {
    return http.get<ApiResponse<{ total: number; items: ResumeUser[] }>>('/api/v1/admin/resume/users');
  },

  // 获取某用户的简历分区（section）
  getResumeSections: async (userId: number) => {
    return http.get<ApiResponse<{ user_id: number; total_sections: number; total_chunks: number; items: ResumeSection[] }>>(`/api/v1/admin/resume/users/${userId}/sections`);
  },

  // 获取某用户某分区的所有分块
  getResumeChunks: async (userId: number, section: string) => {
    return http.get<ApiResponse<{ user_id: number; section: string; label: string; total: number; items: ResumeChunkItem[] }>>(`/api/v1/admin/resume/users/${userId}/sections/${section}`);
  },

  // 删除用户的所有简历文档块
  deleteResumeUser: async (userId: number) => {
    return http.delete<ApiResponse>(`/api/v1/admin/resume/users/${userId}`);
  },

  // 删除指定的简历文档块
  deleteResumeChunks: async (ids: string[]) => {
    const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
    const { token } = JSON.parse(localStorage.getItem('user-storage') || '{}')?.state || {};
    const params = new URLSearchParams();
    ids.forEach((id) => params.append('ids', id));
    const res = await fetch(`${BASE_URL}/api/v1/admin/resume/chunks?${params}`, {
      method: 'DELETE',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return res.json();
  },
};

// ==================== AI面试接口 ====================
export const aiInterviewApi = {
  // 创建一次新的AI面试会话
  startSession: async (data: AIInterviewStartRequest) => {
    return http.post<ApiResponse<AIInterviewSession>>('/api/v1/ai-interview/sessions', data);
  },

  // 发送消息并获取AI回复
  sendMessage: async (data: AIInterviewReplyRequest) => {
    return http.post<ApiResponse<AIInterviewReplyResponse>>('/api/v1/ai-interview/messages', data);
  },

  // 获取会话详情（用于恢复历史）
  getSession: async (sessionId: string) => {
    return http.get<ApiResponse<AIInterviewSession>>(`/api/v1/ai-interview/sessions/${sessionId}`);
  },

  // 结束会话
  endSession: async (sessionId: string) => {
    return http.post<ApiResponse<AIInterviewEndResponse>>(`/api/v1/ai-interview/sessions/${sessionId}/end`);
  },

  // 获取面试报告
  getReport: async (sessionId: string) => {
    return http.get<ApiResponse<AIInterviewReport>>(`/api/v1/ai-interview/reports/${sessionId}`);
  },

  // 获取历史报告列表
  listReports: async (page = 1, size = 10) => {
    return http.get<ApiResponse<{ total: number; items: AIInterviewReportListItem[] }>>(`/api/v1/ai-interview/reports?page=${page}&size=${size}`);
  },

  // 流式发送消息（SSE），实时接收 AI 追问
  streamMessage: async (
    sessionId: string,
    message: string,
    onToken: (token: string) => void,
    onDone: (sequence: number) => void,
    onError: (err: Error) => void,
    signal?: AbortSignal,
  ) => {
    const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
    let token: string | null = null;
    try {
      const stored = JSON.parse(localStorage.getItem('user-storage') || '{}');
      token = stored?.state?.token || null;
    } catch { /* ignore */ }

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
      const response = await fetch(`${BASE_URL}/api/v1/ai-interview/sessions/${sessionId}/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ session_id: sessionId, message }),
        signal,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error((err as any).detail || `HTTP ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'token') {
                onToken(data.content as string);
              } else if (data.type === 'done') {
                onDone(data.sequence as number);
              } else if (data.type === 'error') {
                onError(new Error(data.message as string));
              }
            } catch { /* skip malformed JSON */ }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') onError(err);
    }
  },
};
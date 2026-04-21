import type {
  ApiResponse,
  PaginatedResponse,
  Token,
  User,
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
    return http.post<ApiResponse>('/api/v1/workbench/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
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
    return http.post<ApiResponse>(`/api/v1/ai-interview/sessions/${sessionId}/end`);
  },
};
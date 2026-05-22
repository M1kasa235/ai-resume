// ==================== 通用响应类型 ====================
export interface ApiResponse<T = unknown> {
  error_code?: string;
  detail?: string;
  data?: T;
}

export interface PaginatedResponse<T> {
  total: number;
  items: T[];
  page: number;
  page_size: number;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// ==================== 认证相关类型 ====================
export interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  avatar_url?: string;
  real_name?: string;
  gender?: string;
  current_city?: string;
  target_city?: string;
  work_years?: number;
  education?: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  last_login_at?: string;
}

export interface UserCreate {
  username: string;
  email: string;
  phone?: string;
  password: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface UserUpdate {
  real_name?: string;
  gender?: string;
  current_city?: string;
  target_city?: string;
  work_years?: number;
  education?: string;
  avatar_url?: string;
}

export interface PasswordUpdate {
  old_password: string;
  new_password: string;
}

// ==================== 岗位相关类型 ====================
export interface JobCategory {
  id: number;
  name: string;
  code: string;
  parent_id?: number;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  children?: JobCategory[];
}

export interface Job {
  id: number;
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
  salary_months: number;
  city?: string;
  district?: string;
  address?: string;
  experience_min?: number;
  experience_max?: number;
  education_requirement: string;
  skills_required?: string[];
  tags?: string[];
  source: string;
  source_url?: string;
  is_urgent: boolean;
  expired_at?: string;
  view_count: number;
  apply_count: number;
  is_active: boolean;
  published_at: string;
  created_at: string;
  updated_at: string;
  salary_display: string;
  experience_display: string;
  category?: JobCategory;
  is_favorited: boolean;
}

export interface JobSearchParams {
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
}

// ==================== 题库相关类型 ====================
export interface QuestionCategory {
  id: number;
  name: string;
  type: string;
  parent_id?: number;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  children?: QuestionCategory[];
}

export interface Question {
  id: number;
  category_id: number;
  title: string;
  content?: string;
  type: string;
  difficulty?: string;
  options?: string[];
  correct_answer?: string;
  explanation?: string;
  code_template?: string;
  test_cases?: string[];
  tags?: string[];
  company_tags?: string[];
  frequency: number;
  is_hot: boolean;
  created_at: string;
}

export interface QuestionDetail extends Question {
  category: QuestionCategory;
}

export interface AnswerSubmitRequest {
  answer: string;
  time_spent?: number;
}

export interface AnswerSubmitResponse {
  is_correct: boolean;
  correct_answer?: string;
  explanation?: string;
}

export interface PracticeStats {
  total_practiced: number;
  correct_count: number;
  wrong_count: number;
  accuracy_rate: number;
}

export interface WrongQuestionItem {
  id: number;
  question_id: number;
  question_title: string;
  difficulty?: string;
  wrong_count: number;
  last_wrong_at: string;
  is_mastered: boolean;
  notes?: string;
}

export interface FavoriteQuestionItem {
  id: number;
  question_id: number;
  question_title: string;
  difficulty?: string;
  type: string;
  practiced_at?: string;
}

// ==================== 工作台相关类型 ====================
export interface ResumeInfo {
  resume_url?: string;
  real_name?: string;
  phone?: string;
  email?: string;
  education?: string;
}

export interface ApplicationItem {
  id: number;
  company_name: string;
  job_title: string;
  status?: string;
  applied_at?: string;
  created_at: string;
}

export interface UploadResumeResponse {
  url: string;
  message: string;
}

// ==================== RAG 相关类型 ====================
export interface ReferenceItem {
  content: string;
  section: string;
}

export interface ResumeQueryResponse {
  answer: string;
  references: ReferenceItem[];
}

export interface MatchScore {
  dimension: string;
  score: number;
  reason: string;
}

export interface JobMatchResponse {
  overall_score: number;
  scores: MatchScore[];
  analysis: string;
  suggestions: string[];
}

// ==================== 简历优化相关类型 ====================
export interface ResumeDiagnoseResponse {
  overall_score: string;
  strengths: string[];
  weaknesses: string[];
  suggestions: Array<{
    section: string;
    issue: string;
    advice: string;
  }>;
}

export interface OptimizedSection {
  section: string;
  original: string;
  optimized: string;
  change_reason: string;
}

export interface OptimizeResponse {
  optimized_sections: OptimizedSection[];
  full_resume: string;
  summary: Record<string, unknown>;
}

export interface PolishResponse {
  original: string;
  optimized: string;
  change_reason: string;
}

// ==================== 简历版本管理相关类型 ====================
export interface VersionItem {
  id: number;
  version: number;
  source: string;
  summary?: string;
  job_id?: number;
  created_at: string;
}

export interface VersionDetail {
  id: number;
  version: number;
  source: string;
  content: string;
  summary?: string;
  job_id?: number;
  created_at: string;
}

export interface VersionListResponse {
  versions: VersionItem[];
}

export interface CompareItem {
  section: string;
  before: string;
  after: string;
}

export interface CompareResponse {
  v1_id: number;
  v2_id: number;
  v1_version: number;
  v2_version: number;
  changes: CompareItem[];
}

// ==================== AI面试相关类型 ====================
export interface AIInterviewMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
}

export interface AIInterviewSession {
  session_id: string;
  job_title?: string;
  company_name?: string;
  job_description?: string;
  interview_type?: 'hr' | 'technical' | 'comprehensive';
  messages: AIInterviewMessage[];
}

export interface AIInterviewStartRequest {
  job_title?: string;
  company_name?: string;
  interview_type?: 'hr' | 'technical' | 'comprehensive';
  job_description?: string;
}

export interface AIInterviewReplyRequest {
  session_id: string;
  message: string;
}

export interface AIInterviewReplyResponse {
  session_id: string;
  reply: string;
  limit_reached?: boolean;
}

// 逐题评估
export interface QAEvaluation {
  sequence: number;
  question?: string;
  answer?: string;
  score?: number;
  comment?: string;
  suggested_answer?: string;
}

// 结束面试响应
export interface AIInterviewEndResponse {
  session_id: string;
  status: string;
  total_questions: number;
  overall_score?: number;
  strength_analysis?: string;
  weakness_analysis?: string;
  improvement_suggestions?: string;
  report_markdown?: string;
  evaluations: QAEvaluation[];
}

// 报告详情
export interface AIInterviewReport {
  session_id: string;
  job_title?: string;
  company_name?: string;
  interview_type?: string;
  status: string;
  total_questions: number;
  overall_score?: number;
  strength_analysis?: string;
  weakness_analysis?: string;
  improvement_suggestions?: string;
  report_markdown?: string;
  evaluations: QAEvaluation[];
  started_at?: string;
  ended_at?: string;
}

// 报告列表项
export interface AIInterviewReportListItem {
  session_id: string;
  job_title?: string;
  company_name?: string;
  interview_type?: string;
  status: string;
  total_questions: number;
  overall_score?: number;
  started_at?: string;
  ended_at?: string;
}

// ==================== 首页相关类型 ====================
export interface QuickAction {
  name: string;
  path: string;
  icon: string;
  description?: string;
}

export interface StatisticsSummary {
  total_applications: number;
  total_ai_interviews: number;
  total_practices: number;
  favorite_jobs: number;
  accuracy_rate: number;
  completed_interviews: number;
  resume_completeness: number;
  practice_goal: number;
  application_goal: number;
}

export interface DashboardOverviewResponse {
  quick_actions: QuickAction[];
  statistics: StatisticsSummary;
}

export interface GrowthCurveDataPoint {
  date: string;
  applications: number;
  ai_interviews: number;
  practices: number;
  accuracy?: number;
}

export interface GrowthCurveResponse {
  dates: string[];
  metrics: {
    applications: number[];
    ai_interviews: number[];
    practices: number[];
    accuracy?: number[];
  };
  summary: {
    total_applications: number;
    total_practices: number;
    avg_accuracy: number;
  };
}

export interface ActivityRecord {
  id: number;
  type: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  created_at: string;
}

export interface ActivitiesResponse {
  activities: ActivityRecord[];
  total: number;
}

// ==================== AI求职顾问相关类型 ====================
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// ==================== 管理后台类型 ====================
export interface KnowledgeChunk {
  id: string;
  content: string;
  metadata: Record<string, any>;
}

export interface KnowledgeStats {
  collections: Array<{
    name: string;
    document_count: number;
    type: string;
    partitions?: Record<string, {
      parent: number;
      child: number;
      total: number;
      titles: string[];
    }>;
  }>;
}

export interface KnowledgePartition {
  id: number | null;
  doc_type: string;
  name: string;
  description: string;
  parent_count: number;
  child_count: number;
  total: number;
  titles: string[];
  is_custom: boolean;
}

export interface KnowledgeDocument {
  id: string;
  parent_id: string;
  title: string;
  category: string;
  content: string;
  content_full: string;
  doc_type: string;
  source_file: string;
}

export interface ChunkItem {
  id: string;
  content: string;
  metadata: Record<string, any>;
  child_index?: number;
}

export interface DocumentChunksResponse {
  parent: ChunkItem;
  children: ChunkItem[];
  child_count: number;
}

// ==================== 简历知识库管理相关类型 ====================
export interface ResumeUser {
  user_id: number;
  chunk_count: number;
  section_count: number;
  sections: string[];
}

export interface ResumeSection {
  section: string;
  label: string;
  chunk_count: number;
}

export interface ResumeChunkItem {
  id: string;
  content: string;
  metadata: {
    chunk_index: number;
    total_chunks: number;
    source: string;
    created_at: string;
    section: string;
  };
}

// ==================== 收藏相关类型 ====================
export interface UserFavoriteJob {
  id: number;
  job_id: number;
  job: Job;
  created_at: string;
}

export interface UserFavoriteQuestion {
  id: number;
  question_id: number;
  question: Question;
  created_at: string;
}
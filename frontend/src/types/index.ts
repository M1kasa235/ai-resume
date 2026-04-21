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
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  phone?: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiResponse<T = unknown> {
  error_code?: string;
  detail?: string;
  data?: T;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface Job {
  id: number;
  title: string;
  company_name: string;
  city: string;
  salary_min: number;
  salary_max: number;
  experience_min?: number;
  experience_max?: number;
  education?: string;
  description?: string;
  requirements?: string;
  benefits?: string;
  tags?: string[];
  source?: string;
  source_url?: string;
  is_urgent: boolean;
  is_active: boolean;
  view_count: number;
  apply_count: number;
  published_at: string;
  expired_at?: string;
  created_at: string;
  updated_at: string;
  is_favorited?: boolean;
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
  tags?: string[];
  frequency: number;
  is_hot: boolean;
  created_at: string;
}

export interface Application {
  id: number;
  user_id: number;
  job_id?: number;
  job_title: string;
  company_name: string;
  status: string;
  resume_url?: string;
  cover_letter?: string;
  notes?: string;
  applied_at: string;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  total_applications: number;
  total_ai_interviews: number;
  total_practices: number;
  favorite_jobs: number;
  accuracy_rate: number;
  completed_interviews: number;
}

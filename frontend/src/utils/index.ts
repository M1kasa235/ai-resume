import dayjs from 'dayjs';

import { DATE_FORMATS } from '@/constants';

/**
 * 格式化日期
 * @param date 日期字符串或Date对象
 * @param formatStr 格式字符串
 * @returns 格式化后的日期字符串
 */
export function formatDate(date: string | Date, formatStr = DATE_FORMATS.full): string {
  return dayjs(date instanceof Date ? date : date).format(formatStr);
}

/**
 * 格式化相对时间
 * @param date 日期字符串或Date对象
 * @returns 相对时间字符串
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const targetDate = date instanceof Date ? date : new Date(date);
  const diffMs = now.getTime() - targetDate.getTime();
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMinutes < 1) return '刚刚';
  if (diffMinutes < 60) return `${diffMinutes}分钟前`;
  if (diffHours < 24) return `${diffHours}小时前`;
  if (diffDays < 7) return `${diffDays}天前`;
  
  return formatDate(date);
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 格式化金额
 * @param amount 金额
 * @param currency 货币符号
 * @returns 格式化后的金额字符串
 */
export function formatCurrency(amount: number, currency = '¥'): string {
  return `${currency}${amount.toLocaleString()}`;
}

/**
 * 格式化手机号
 * @param phone 手机号
 * @returns 格式化后的手机号
 */
export function formatPhone(phone: string): string {
  if (!phone || phone.length !== 11) return phone;
  return phone.replace(/(\d{3})(\d{4})(\d{4})/, '$1****$3');
}

/**
 * 格式化邮箱
 * @param email 邮箱
 * @returns 格式化后的邮箱
 */
export function formatEmail(email: string): string {
  if (!email) return email;
  const [name, domain] = email.split('@');
  if (name.length <= 2) return email;
  return `${name[0]}***@${domain}`;
}

/**
 * 防抖函数
 * @param func 要防抖的函数
 * @param delay 延迟时间（毫秒）
 * @returns 防抖后的函数
 */
export function debounce<T extends (..._args: any[]) => any>(
  func: T,
  delay: number
): (..._args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  };
}

/**
 * 节流函数
 * @param func 要节流的函数
 * @param delay 延迟时间（毫秒）
 * @returns 节流后的函数
 */
export function throttle<T extends (..._args: any[]) => any>(
  func: T,
  delay: number
): (..._args: Parameters<T>) => void {
  let lastCall = 0;
  
  return (..._args: Parameters<T>) => {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      func.apply(null, _args);
    }
  };
}

/**
 * 深拷贝
 * @param obj 要拷贝的对象
 * @returns 拷贝后的对象
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as T;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as T;
  
  const clonedObj = {} as T;
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      clonedObj[key] = deepClone(obj[key]);
    }
  }
  return clonedObj;
}

/**
 * 生成唯一ID
 * @param prefix 前缀
 * @returns 唯一ID
 */
export function generateId(prefix = ''): string {
  return `${prefix}${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 检查是否为空值
 * @param value 要检查的值
 * @returns 是否为空值
 */
export function isEmpty(value: any): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}

/**
 * 数组分组
 * @param array 要分组的数组
 * @param key 分组键
 * @returns 分组后的对象
 */
export function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce((groups, item) => {
    const group = String(item[key]);
    if (!groups[group]) {
      groups[group] = [];
    }
    groups[group].push(item);
    return groups;
  }, {} as Record<string, T[]>);
}

/**
 * 数组去重
 * @param array 要去重的数组
 * @param key 去重键（可选）
 * @returns 去重后的数组
 */
export function uniqueBy<T>(array: T[], key?: keyof T): T[] {
  if (!key) {
    return [...new Set(array)];
  }
  
  const seen = new Set();
  return array.filter(item => {
    const value = item[key];
    if (seen.has(value)) {
      return false;
    }
    seen.add(value);
    return true;
  });
}

/**
 * 数组排序
 * @param array 要排序的数组
 * @param key 排序键
 * @param order 排序顺序
 * @returns 排序后的数组
 */
export function sortBy<T>(
  array: T[],
  key: keyof T,
  order: 'asc' | 'desc' = 'asc'
): T[] {
  return [...array].sort((a, b) => {
    const aValue = a[key];
    const bValue = b[key];
    
    if (aValue < bValue) return order === 'asc' ? -1 : 1;
    if (aValue > bValue) return order === 'asc' ? 1 : -1;
    return 0;
  });
}

/**
 * URL参数解析
 * @param url URL字符串
 * @returns 参数对象
 */
export function parseUrlParams(url: string): Record<string, string> {
  const params: Record<string, string> = {};
  const urlSearchParams = new URLSearchParams(url.split('?')[1]);
  
  for (const [key, value] of urlSearchParams.entries()) {
    params[key] = value;
  }
  
  return params;
}

/**
 * URL参数构建
 * @param params 参数对象
 * @returns URL参数字符串
 */
export function buildUrlParams(params: Record<string, any>): string {
  const searchParams = new URLSearchParams();
  
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, String(value));
    }
  }
  
  return searchParams.toString();
}

/**
 * 本地存储工具
 */
export const storage = {
  get<T>(key: string, defaultValue?: T): T | null {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue || null;
    } catch {
      return defaultValue || null;
    }
  },
  
  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  },
  
  remove(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Failed to remove from localStorage:', error);
    }
  },
  
  clear(): void {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
    }
  },
};

/**
 * 会话存储工具
 */
export const sessionStore = {
  get<T>(key: string, defaultValue?: T): T | null {
    try {
      const item = window.sessionStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue || null;
    } catch {
      return defaultValue || null;
    }
  },
  
  set<T>(key: string, value: T): void {
    try {
      window.sessionStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Failed to save to sessionStorage:', error);
    }
  },
  
  remove(key: string): void {
    try {
      window.sessionStorage.removeItem(key);
    } catch (error) {
      console.error('Failed to remove from sessionStorage:', error);
    }
  },
  
  clear(): void {
    try {
      window.sessionStorage.clear();
    } catch (error) {
      console.error('Failed to clear sessionStorage:', error);
    }
  },
};
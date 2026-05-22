import { lazy } from 'react';

import { AuthGuard } from '@components/AuthGuard';
import { GuestGuard } from '@components/GuestGuard';
import AuthLayout from '@components/layouts/AuthLayout';
import MainLayout from '@components/layouts/MainLayout';
import type { RouteObject } from 'react-router-dom';
import { Navigate } from 'react-router-dom';

const Dashboard = lazy(() => import('@features/dashboard'));
const Jobs = lazy(() => import('@features/jobs'));
const JobDetail = lazy(() => import('@features/jobs/Detail'));
const Questions = lazy(() => import('@features/questions'));
const Workbench = lazy(() => import('@features/workbench'));
const AIInterview = lazy(() => import('@features/aiInterview'));
const AIInterviewReport = lazy(() => import('@features/aiInterview/Report'));
const AIInterviewHistory = lazy(() => import('@features/aiInterview/History'));
const AIAdvisor = lazy(() => import('@features/aiAdvisor'));
const Admin = lazy(() => import('@features/admin'));
const Profile = lazy(() => import('@features/profile'));
const Settings = lazy(() => import('@features/settings'));

const Login = lazy(() => import('@features/auth/Login'));
const Register = lazy(() => import('@features/auth/Register'));
const ForgotPassword = lazy(() => import('@features/auth/ForgotPassword'));

const NotFound = lazy(() => import('@features/error/NotFound'));
const Forbidden = lazy(() => import('@features/error/Forbidden'));

export interface AppRoute extends Omit<RouteObject, 'children'> {
  path: string;
  element: React.ReactElement;
  children?: AppRoute[];
  meta?: {
    title?: string;
    icon?: string;
    auth?: boolean;
    guest?: boolean;
    admin?: boolean;
    breadcrumb?: string;
  };
}

export const routes: AppRoute[] = [
  {
    path: '/',
    element: (
      <AuthGuard>
        <MainLayout />
      </AuthGuard>
    ),
    children: [
      {
        path: '',
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Dashboard />,
        meta: { title: '仪表盘', icon: 'DashboardOutlined', breadcrumb: '仪表盘' },
      },
      {
        path: 'jobs',
        element: <Jobs />,
        meta: { title: '岗位列表', icon: 'SearchOutlined', breadcrumb: '岗位列表' },
      },
      {
        path: 'jobs/:id',
        element: <JobDetail />,
        meta: { title: '岗位详情', breadcrumb: '岗位详情' },
      },
      {
        path: 'questions',
        element: <Questions />,
        meta: { title: '题库', icon: 'QuestionCircleOutlined', breadcrumb: '题库' },
      },
      {
        path: 'workbench',
        element: <Workbench />,
        meta: { title: '工作台', icon: 'ToolOutlined', breadcrumb: '工作台' },
      },
      {
        path: 'ai-interview',
        element: <AIInterview />,
        meta: { title: 'AI面试', icon: 'RobotOutlined', breadcrumb: 'AI面试' },
      },
      {
        path: 'ai-interview/report/:id',
        element: <AIInterviewReport />,
        meta: { title: '面试报告', icon: 'RobotOutlined', breadcrumb: '面试报告' },
      },
      {
        path: 'ai-interview/history',
        element: <AIInterviewHistory />,
        meta: { title: '面试记录', icon: 'RobotOutlined', breadcrumb: '面试记录' },
      },
      {
        path: 'ai-advisor',
        element: <AIAdvisor />,
        meta: { title: 'AI求职顾问', icon: 'MessageOutlined', breadcrumb: 'AI求职顾问' },
      },
      {
        path: 'admin',
        element: <Admin />,
        meta: { title: '管理后台', icon: 'SettingOutlined', breadcrumb: '管理后台', admin: true },
      },
      {
        path: 'profile',
        element: <Profile />,
        meta: { title: '个人中心', icon: 'UserOutlined', breadcrumb: '个人中心' },
      },
      {
        path: 'settings',
        element: <Settings />,
        meta: { title: '设置', icon: 'SettingOutlined', breadcrumb: '设置' },
      },
    ],
  },
  {
    path: '/auth',
    element: (
      <GuestGuard>
        <AuthLayout />
      </GuestGuard>
    ),
    children: [
      {
        path: '',
        element: <Navigate to="/auth/login" replace />,
      },
      {
        path: 'login',
        element: <Login />,
        meta: { title: '登录', guest: true },
      },
      {
        path: 'register',
        element: <Register />,
        meta: { title: '注册', guest: true },
      },
      {
        path: 'forgot-password',
        element: <ForgotPassword />,
        meta: { title: '忘记密码', guest: true },
      },
    ],
  },
  {
    path: '/403',
    element: <Forbidden />,
    meta: { title: '无权限' },
  },
  {
    path: '*',
    element: <NotFound />,
    meta: { title: '页面不存在' },
  },
];

export const flattenRoutes = (routes: AppRoute[], parentPath = ''): AppRoute[] => {
  return routes.reduce<AppRoute[]>((acc, route) => {
    const fullPath = parentPath + route.path;
    acc.push({ ...route, path: fullPath });
    if (route.children) {
      acc.push(...flattenRoutes(route.children, fullPath));
    }
    return acc;
  }, []);
};

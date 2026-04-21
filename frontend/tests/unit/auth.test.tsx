import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import Login from '@/features/auth/Login/index';

// Mock the useAuth hook
const mockLogin = vi.fn();
const mockRegister = vi.fn();
const mockLogout = vi.fn();
const mockRefreshUser = vi.fn();

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: null,
    isAuthenticated: false,
    isLoading: false,
    login: mockLogin,
    register: mockRegister,
    logout: mockLogout,
    refreshUser: mockRefreshUser,
  }),
}));

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form', () => {
    render(<Login />);
    
    expect(screen.getByText('登录')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('用户名')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('密码')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();
  });

  it('allows user to type in form fields', () => {
    render(<Login />);
    
    const usernameInput = screen.getByPlaceholderText('用户名');
    const passwordInput = screen.getByPlaceholderText('密码');
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    
    expect(usernameInput).toHaveValue('testuser');
    expect(passwordInput).toHaveValue('password123');
  });

  it('calls login function when form is submitted', async () => {
    render(<Login />);
    
    const usernameInput = screen.getByPlaceholderText('用户名');
    const passwordInput = screen.getByPlaceholderText('密码');
    const submitButton = screen.getByRole('button', { name: '登录' });
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);
    
    expect(mockLogin).toHaveBeenCalledWith({
      username: 'testuser',
      password: 'password123',
    });
  });

  it('shows validation errors for empty fields', async () => {
    render(<Login />);
    
    const submitButton = screen.getByRole('button', { name: '登录' });
    fireEvent.click(submitButton);
    
    expect(await screen.findByText('请输入用户名')).toBeInTheDocument();
    expect(await screen.findByText('请输入密码')).toBeInTheDocument();
  });
});

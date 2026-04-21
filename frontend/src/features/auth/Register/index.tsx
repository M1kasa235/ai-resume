import { useState } from 'react';

import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  PhoneOutlined,
} from '@ant-design/icons';
import { useAuth } from '@hooks/useAuth';
import { Form, Input, Button, message } from 'antd';
import { Link, useNavigate } from 'react-router-dom';

import type { RegisterRequest } from '@/types';

import styles from './Register.module.scss';

export default function Register() {
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const handleSubmit = async (values: RegisterRequest) => {
    setLoading(true);
    try {
      await register(values);
      message.success('注册成功');
      navigate('/auth/login');
    } catch {
      message.error('注册失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.register}>
      <h2>注册</h2>
      <Form form={form} onFinish={handleSubmit} layout="vertical">
        <Form.Item
          name="username"
          rules={[
            { required: true, message: '请输入用户名' },
            { min: 3, max: 50, message: '用户名长度为3-50个字符' },
          ]}
        >
          <Input prefix={<UserOutlined />} placeholder="用户名" size="large" />
        </Form.Item>

        <Form.Item
          name="email"
          rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' },
          ]}
        >
          <Input prefix={<MailOutlined />} placeholder="邮箱" size="large" />
        </Form.Item>

        <Form.Item name="phone" rules={[{ pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' }]}>
          <Input prefix={<PhoneOutlined />} placeholder="手机号（可选）" size="large" />
        </Form.Item>

        <Form.Item
          name="password"
          rules={[
            { required: true, message: '请输入密码' },
            { min: 6, max: 20, message: '密码长度为6-20个字符' },
          ]}
        >
          <Input.Password prefix={<LockOutlined />} placeholder="密码" size="large" />
        </Form.Item>

        <Form.Item
          name="confirmPassword"
          dependencies={['password']}
          rules={[
            { required: true, message: '请确认密码' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('两次输入的密码不一致'));
              },
            }),
          ]}
        >
          <Input.Password prefix={<LockOutlined />} placeholder="确认密码" size="large" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block size="large">
            注册
          </Button>
        </Form.Item>

        <div className={styles.footer}>
          已有账号？ <Link to="/auth/login">立即登录</Link>
        </div>
      </Form>
    </div>
  );
}

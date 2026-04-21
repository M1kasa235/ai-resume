import { useState } from 'react';

import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '@hooks/useAuth';
import { Form, Input, Button, Checkbox, message } from 'antd';
import { Link } from 'react-router-dom';

import type { LoginRequest } from '@/types';

import styles from './Login.module.scss';

export default function Login() {
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const [form] = Form.useForm();

  const handleSubmit = async (values: LoginRequest) => {
    setLoading(true);
    try {
      await login(values);
    } catch {
      message.error('登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.login}>
      <h2>登录</h2>
      <Form
        form={form}
        onFinish={handleSubmit}
        layout="vertical"
        initialValues={{ remember: true }}
      >
        <Form.Item
          name="username"
          rules={[
            { required: true, message: '请输入用户名' },
            { min: 3, message: '用户名至少3个字符' },
          ]}
        >
          <Input
            prefix={<UserOutlined />}
            placeholder="用户名"
            size="large"
          />
        </Form.Item>

        <Form.Item
          name="password"
          rules={[
            { required: true, message: '请输入密码' },
            { min: 6, message: '密码至少6个字符' },
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="密码"
            size="large"
          />
        </Form.Item>

        <Form.Item>
          <div className={styles.options}>
            <Form.Item name="remember" valuePropName="checked" noStyle>
              <Checkbox>记住我</Checkbox>
            </Form.Item>
            <Link to="/auth/forgot-password">忘记密码？</Link>
          </div>
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block size="large">
            登录
          </Button>
        </Form.Item>

        <div className={styles.footer}>
          还没有账号？ <Link to="/auth/register">立即注册</Link>
        </div>
      </Form>
    </div>
  );
}

import { useState } from 'react';

import { MailOutlined } from '@ant-design/icons';
import { Form, Input, Button, message } from 'antd';
import { Link } from 'react-router-dom';

import styles from './ForgotPassword.module.scss';

export default function ForgotPassword() {
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [form] = Form.useForm();

  const handleSubmit = async () => {
    setLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setSubmitted(true);
      message.success('重置密码邮件已发送');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className={styles.forgot}>
        <h2>邮件已发送</h2>
        <p>请检查您的邮箱，按照邮件中的说明重置密码。</p>
        <Link to="/auth/login">返回登录</Link>
      </div>
    );
  }

  return (
    <div className={styles.forgot}>
      <h2>忘记密码</h2>
      <Form form={form} onFinish={handleSubmit} layout="vertical">
        <Form.Item
          name="email"
          rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' },
          ]}
        >
          <Input prefix={<MailOutlined />} placeholder="注册时使用的邮箱" size="large" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block size="large">
            发送重置邮件
          </Button>
        </Form.Item>

        <div className={styles.footer}>
          想起密码了？ <Link to="/auth/login">返回登录</Link>
        </div>
      </Form>
    </div>
  );
}

import { useState } from 'react';

import {
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  LockOutlined,
  CameraOutlined,
} from '@ant-design/icons';
import { userApi } from '@services/api';
import { useUserStore } from '@stores/userStore';
import {
  Card,
  Row,
  Col,
  Form,
  Input,
  Button,
  Upload,
  Tabs,
  Avatar,
  Space,
  message,
} from 'antd';

import styles from './Profile.module.scss';

const { TabPane } = Tabs;

export default function Profile() {
  const { user } = useUserStore();
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const handleUpdateProfile = async (values: Record<string, string>) => {
    setLoading(true);
    try {
      await userApi.updateProfile(values);
      message.success('个人资料更新成功');
    } catch (error) {
      message.error('更新失败');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (values: Record<string, string>) => {
    setLoading(true);
    try {
      await userApi.changePassword({
        old_password: values.oldPassword,
        new_password: values.newPassword,
      });
      message.success('密码修改成功');
      form.resetFields(['oldPassword', 'newPassword', 'confirmPassword']);
    } catch (error) {
      message.error('密码修改失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarChange = (info: any) => {
    if (info.file.status === 'done') {
      message.success('头像上传成功');
    }
  };

  return (
    <div className={styles.profile}>
      <h1>个人中心</h1>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={8}>
          <Card title="个人信息">
            <div className={styles.profileCard}>
              <div className={styles.avatarSection}>
                <Avatar
                  src={user?.avatar_url}
                  icon={<UserOutlined />}
                  size={80}
                />
                <Upload
                  name="avatar"
                  showUploadList={false}
                  onChange={handleAvatarChange}
                  accept="image/*"
                >
                  <Button
                    type="text"
                    icon={<CameraOutlined />}
                    className={styles.avatarButton}
                  >
                    更换头像
                  </Button>
                </Upload>
              </div>
              
              <div className={styles.profileInfo}>
                <h3>{user?.username || '用户'}</h3>
                <p>{user?.email}</p>
                {user?.phone && <p>{user.phone}</p>}
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card>
            <Tabs defaultActiveKey="basic">
              <TabPane tab="基本信息" key="basic">
                <Form
                  form={form}
                  layout="vertical"
                  onFinish={handleUpdateProfile}
                  initialValues={{
                    username: user?.username,
                    email: user?.email,
                    phone: user?.phone,
                    real_name: user?.real_name,
                    current_city: user?.current_city,
                    target_city: user?.target_city,
                    work_years: user?.work_years,
                    education: user?.education,
                  }}
                >
                  <Row gutter={[16, 0]}>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="username"
                        label="用户名"
                        rules={[{ required: true, message: '请输入用户名' }]}
                      >
                        <Input prefix={<UserOutlined />} />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="real_name"
                        label="真实姓名"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="email"
                        label="邮箱"
                        rules={[{ required: true, type: 'email' }]}
                      >
                        <Input prefix={<MailOutlined />} />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="phone"
                        label="手机号"
                        rules={[{ pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号' }]}
                      >
                        <Input prefix={<PhoneOutlined />} />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="current_city"
                        label="当前城市"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="target_city"
                        label="目标城市"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="work_years"
                        label="工作年限"
                      >
                        <Input type="number" />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="education"
                        label="学历"
                      >
                        <Input />
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}>
                      保存修改
                    </Button>
                  </Form.Item>
                </Form>
              </TabPane>

              <TabPane tab="修改密码" key="password">
                <Form
                  layout="vertical"
                  onFinish={handlePasswordChange}
                >
                  <Form.Item
                    name="oldPassword"
                    label="当前密码"
                    rules={[{ required: true, message: '请输入当前密码' }]}
                  >
                    <Input.Password prefix={<LockOutlined />} />
                  </Form.Item>
                  
                  <Form.Item
                    name="newPassword"
                    label="新密码"
                    rules={[
                      { required: true, message: '请输入新密码' },
                      { min: 6, message: '密码至少6个字符' }
                    ]}
                  >
                    <Input.Password prefix={<LockOutlined />} />
                  </Form.Item>
                  
                  <Form.Item
                    name="confirmPassword"
                    label="确认新密码"
                    dependencies={['newPassword']}
                    rules={[
                      { required: true, message: '请确认新密码' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('newPassword') === value) {
                            return Promise.resolve();
                          }
                          return Promise.reject(new Error('两次输入的密码不一致'));
                        },
                      }),
                    ]}
                  >
                    <Input.Password prefix={<LockOutlined />} />
                  </Form.Item>
                  
                  <Form.Item>
                    <Button type="primary" htmlType="submit" loading={loading}>
                      修改密码
                    </Button>
                  </Form.Item>
                </Form>
              </TabPane>

              <TabPane tab="求职信息" key="career">
                <div className={styles.careerInfo}>
                  <h3>求职意向</h3>
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <div>
                      <label>期望职位：</label>
                      <span>前端开发工程师</span>
                    </div>
                    <div>
                      <label>期望薪资：</label>
                      <span>15-25K</span>
                    </div>
                    <div>
                      <label>期望城市：</label>
                      <span>{user?.target_city || '北京'}</span>
                    </div>
                    <div>
                      <label>工作性质：</label>
                      <span>全职</span>
                    </div>
                  </Space>
                </div>
              </TabPane>
            </Tabs>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

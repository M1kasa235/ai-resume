import { useEffect, useState } from 'react';

import {
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  LockOutlined,
  CameraOutlined,
} from '@ant-design/icons';
import { userApi } from '@services/api';
import { useQuery } from '@tanstack/react-query';
import { useUserStore } from '@stores/userStore';
import { AxiosError } from 'axios';
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
  Select,
  InputNumber,
} from 'antd';
import type { User } from '@/types';

import styles from './Profile.module.scss';

const { TabPane } = Tabs;

interface ProfileFormValues {
  real_name?: string;
  gender?: 'male' | 'female' | 'other';
  current_city?: string;
  target_city?: string;
  work_years?: number;
  education?: 'high_school' | 'college' | 'bachelor' | 'master' | 'phd';
}

export default function Profile() {
  const { user, setUser } = useUserStore();
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const { data: profileData, isLoading: profileLoading, refetch } = useQuery({
    queryKey: ['user-profile'],
    queryFn: userApi.getProfile,
  });

  useEffect(() => {
    const profile = profileData as {
      username?: string;
      email?: string;
      phone?: string;
      real_name?: string;
      gender?: 'male' | 'female' | 'other';
      current_city?: string;
      target_city?: string;
      work_years?: number;
      education?: string;
    } | undefined;
    if (!profile) return;
    form.setFieldsValue({
      username: profile.username,
      email: profile.email,
      phone: profile.phone,
      real_name: profile.real_name,
      gender: profile.gender,
      current_city: profile.current_city,
      target_city: profile.target_city,
      work_years: profile.work_years,
      education: profile.education,
    });
    setUser(profile as User);
  }, [profileData, form, setUser]);

  const handleUpdateProfile = async (values: ProfileFormValues) => {
    setLoading(true);
    try {
      const normalizedWorkYears =
        typeof values.work_years === 'number' && Number.isFinite(values.work_years)
          ? values.work_years
          : undefined;
      const payload = {
        real_name: values.real_name?.trim() || undefined,
        gender: values.gender || undefined,
        current_city: values.current_city?.trim() || undefined,
        target_city: values.target_city?.trim() || undefined,
        work_years: normalizedWorkYears,
        education: values.education?.trim() || undefined,
      };
      const updated = await userApi.updateProfile(payload);
      setUser(updated as User);
      await refetch();
      message.success('个人资料更新成功');
    } catch (error: unknown) {
      const axiosError = error as AxiosError<{ detail?: string }>;
      message.error(axiosError.response?.data?.detail || '更新失败');
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
                  disabled={profileLoading}
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
                      >
                        <Input prefix={<UserOutlined />} disabled />
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
                      >
                        <Input prefix={<MailOutlined />} disabled />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="phone"
                        label="手机号"
                      >
                        <Input prefix={<PhoneOutlined />} disabled />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item name="gender" label="性别">
                        <Select
                          allowClear
                          options={[
                            { label: '男', value: 'male' },
                            { label: '女', value: 'female' },
                            { label: '其他', value: 'other' },
                          ]}
                        />
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
                        <InputNumber min={0} max={50} style={{ width: '100%' }} />
                      </Form.Item>
                    </Col>
                    <Col xs={24} sm={12}>
                      <Form.Item
                        name="education"
                        label="学历"
                      >
                        <Select
                          allowClear
                          placeholder="请选择学历"
                          options={[
                            { label: '高中', value: 'high_school' },
                            { label: '大专', value: 'college' },
                            { label: '本科', value: 'bachelor' },
                            { label: '硕士', value: 'master' },
                            { label: '博士', value: 'phd' },
                          ]}
                        />
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

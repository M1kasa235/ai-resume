import {
  BellOutlined,
  SafetyOutlined,
  GlobalOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useUserStore } from '@stores/userStore';
import {
  Card,
  Row,
  Col,
  Switch,
  Button,
  Select,
  Space,
  message,
} from 'antd';

import styles from './Settings.module.scss';

export default function Settings() {
  const { user } = useUserStore();

  const handleSave = () => {
    message.success('设置已保存');
  };

  return (
    <div className={styles.settings}>
      <h1>设置</h1>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card title="通知设置">
            <Row gutter={[16, 16]}>
              <Col xs={24}>
                <div className={styles.settingsItem}>
                  <div className={styles.settingsItemLeft}>
                    <BellOutlined style={{ fontSize: 20, marginRight: 12 }} />
                    <div>
                      <h4>邮件通知</h4>
                      <p>接收新岗位推荐和面试通知</p>
                    </div>
                  </div>
                  <Switch defaultChecked />
                </div>
              </Col>
              <Col xs={24}>
                <div className={styles.settingsItem}>
                  <div className={styles.settingsItemLeft}>
                    <BellOutlined style={{ fontSize: 20, marginRight: 12 }} />
                    <div>
                      <h4>短信通知</h4>
                      <p>接收重要面试提醒</p>
                    </div>
                  </div>
                  <Switch />
                </div>
              </Col>
              <Col xs={24}>
                <div className={styles.settingsItem}>
                  <div className={styles.settingsItemLeft}>
                    <BellOutlined style={{ fontSize: 20, marginRight: 12 }} />
                    <div>
                      <h4>推送通知</h4>
                      <p>浏览器推送提醒</p>
                    </div>
                  </div>
                  <Switch defaultChecked />
                </div>
              </Col>
            </Row>
          </Card>

          <Card title="隐私设置" style={{ marginTop: 24 }}>
            <Row gutter={[16, 16]}>
              <Col xs={24}>
                <div className={styles.settingsItem}>
                  <div className={styles.settingsItemLeft}>
                    <UserOutlined style={{ fontSize: 20, marginRight: 12 }} />
                    <div>
                      <h4>公开个人资料</h4>
                      <p>其他用户可以看到你的基本信息</p>
                    </div>
                  </div>
                  <Switch defaultChecked />
                </div>
              </Col>
              <Col xs={24}>
                <div className={styles.settingsItem}>
                  <div className={styles.settingsItemLeft}>
                    <UserOutlined style={{ fontSize: 20, marginRight: 12 }} />
                    <div>
                      <h4>显示求职状态</h4>
                      <p>在个人资料中显示当前求职状态</p>
                    </div>
                  </div>
                  <Switch />
                </div>
              </Col>
            </Row>
          </Card>

          <Card title="安全设置" style={{ marginTop: 24 }}>
            <Row gutter={[16, 16]}>
              <Col xs={24}>
                <div className={styles.settingsItem}>
                  <div className={styles.settingsItemLeft}>
                    <SafetyOutlined style={{ fontSize: 20, marginRight: 12 }} />
                    <div>
                      <h4>双重验证</h4>
                      <p>启用短信验证码登录</p>
                    </div>
                  </div>
                  <Switch />
                </div>
              </Col>
              <Col xs={24}>
                <div className={styles.settingsItem}>
                  <div className={styles.settingsItemLeft}>
                    <SafetyOutlined style={{ fontSize: 20, marginRight: 12 }} />
                    <div>
                      <h4>自动登出</h4>
                      <p>30分钟无操作自动登出</p>
                    </div>
                  </div>
                  <Switch defaultChecked />
                </div>
              </Col>
            </Row>
          </Card>

          <Card title="语言设置" style={{ marginTop: 24 }}>
            <Row gutter={[16, 16]}>
              <Col xs={24}>
                <div className={styles.settingsItem}>
                  <div className={styles.settingsItemLeft}>
                    <GlobalOutlined style={{ fontSize: 20, marginRight: 12 }} />
                    <div>
                      <h4>界面语言</h4>
                      <p>选择界面显示语言</p>
                    </div>
                  </div>
                  <div className={styles.settingsItemRight}>
                    <Select
                      defaultValue="zh-CN"
                      style={{ width: 140 }}
                      options={[
                        { label: '简体中文', value: 'zh-CN' },
                        { label: '繁體中文', value: 'zh-TW' },
                        { label: 'English', value: 'en' },
                      ]}
                    />
                  </div>
                </div>
              </Col>
            </Row>
          </Card>

          <div className={styles.settingsActions}>
            <Space>
              <Button type="primary" onClick={handleSave}>
                保存设置
              </Button>
              <Button onClick={() => window.location.reload()}>
                重置
              </Button>
            </Space>
          </div>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="账户信息">
            <div className={styles.accountInfo}>
              <div className={styles.infoItem}>
                <span>用户名：</span>
                <span>{user?.username || '-'}</span>
              </div>
              <div className={styles.infoItem}>
                <span>邮箱：</span>
                <span>{user?.email || '-'}</span>
              </div>
              <div className={styles.infoItem}>
                <span>注册时间：</span>
                <span>{user?.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '-'}</span>
              </div>
              <div className={styles.infoItem}>
                <span>最后登录：</span>
                <span>{user?.last_login_at ? new Date(user.last_login_at).toLocaleString('zh-CN') : '-'}</span>
              </div>
            </div>
          </Card>

          <Card title="危险操作" style={{ marginTop: 24, borderColor: '#ff4d4f' }}>
            <div className={styles.dangerActions}>
              <Button danger block style={{ marginBottom: 12 }}>
                删除账户
              </Button>
              <Button danger block>
                导出数据
              </Button>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

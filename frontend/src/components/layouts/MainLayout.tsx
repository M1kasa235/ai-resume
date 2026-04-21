import { useState } from 'react';

import {
  DashboardOutlined,
  SearchOutlined,
  QuestionCircleOutlined,
  ToolOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useUserStore } from '@stores/userStore';
import { Layout, Menu, Avatar, Dropdown, Button, Badge, theme } from 'antd';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';

import styles from './MainLayout.module.scss';

const { Header, Sider, Content } = Layout;

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '仪表盘',
  },
  {
    key: '/jobs',
    icon: <SearchOutlined />,
    label: '岗位搜索',
  },
  {
    key: '/questions',
    icon: <QuestionCircleOutlined />,
    label: '题库练习',
  },
  {
    key: '/workbench',
    icon: <ToolOutlined />,
    label: '工作台',
  },
];

export default function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useUserStore();
  const [collapsed, setCollapsed] = useState(false);
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleLogout = () => {
    logout();
    navigate('/auth/login');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const getSelectedKey = () => {
    const path = location.pathname;
    const firstSegment = '/' + path.split('/')[1];
    return firstSegment || '/dashboard';
  };

  return (
    <Layout className={styles.layout}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className={styles.sider}
        width={240}
      >
        <div className={styles.logo}>
          <img src="/logo.svg" alt="Logo" />
          {!collapsed && <span>AI Job Assistant</span>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[getSelectedKey()]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header className={styles.header} style={{ background: colorBgContainer }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            className={styles.trigger}
          />
          <div className={styles.right}>
            <Badge count={5} size="small">
              <Button type="text" icon={<BellOutlined />} />
            </Badge>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div className={styles.user}>
                <Avatar
                  src={user?.avatar_url}
                  icon={!user?.avatar_url && <UserOutlined />}
                  size="small"
                />
                <span className={styles.username}>{user?.username || '用户'}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content
          className={styles.content}
          style={{
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

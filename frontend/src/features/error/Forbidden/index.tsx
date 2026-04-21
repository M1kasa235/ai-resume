import { Button } from 'antd';
import { Link } from 'react-router-dom';

import styles from './Forbidden.module.scss';

export default function Forbidden() {
  return (
    <div className={styles.forbidden}>
      <div className={styles.content}>
        <h1>403</h1>
        <h2>访问被拒绝</h2>
        <p>抱歉，您没有权限访问此页面。</p>
        <div className={styles.actions}>
          <Button type="primary" size="large">
            <Link to="/dashboard">返回仪表盘</Link>
          </Button>
          <Button size="large">
            <Link to="/">返回首页</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

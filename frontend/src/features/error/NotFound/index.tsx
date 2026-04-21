import { Button } from 'antd';
import { Link } from 'react-router-dom';

import styles from './NotFound.module.scss';

export default function NotFound() {
  return (
    <div className={styles.notFound}>
      <div className={styles.content}>
        <h1>404</h1>
        <h2>页面不存在</h2>
        <p>抱歉，您访问的页面不存在或已被删除。</p>
        <div className={styles.actions}>
          <Button type="primary" size="large">
            <Link to="/">返回首页</Link>
          </Button>
          <Button size="large">
            <Link to="/dashboard">仪表盘</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

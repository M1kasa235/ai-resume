import { Outlet } from 'react-router-dom';

import styles from './AuthLayout.module.scss';

export default function AuthLayout() {
  return (
    <div className={styles.container}>
      <div className={styles.left}>
        <div className={styles.content}>
          <h1>Offer Pilot</h1>
          <p>智能求职助手，助你找到理想工作</p>
        </div>
      </div>
      <div className={styles.right}>
        <div className={styles.formContainer}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}

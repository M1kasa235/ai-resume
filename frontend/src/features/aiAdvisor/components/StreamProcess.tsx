import { CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';

import styles from '../Advisor.module.scss';

export interface StreamStep {
  id: string;
  message: string;
  done: boolean;
}

interface StreamProcessProps {
  steps: StreamStep[];
  streaming: boolean;
}

export default function StreamProcess({ steps, streaming }: StreamProcessProps) {
  if (steps.length === 0) return null;

  return (
    <div className={styles.processPanel}>
      <div className={styles.processTitle}>运行过程</div>
      <ul className={styles.processList}>
        {steps.map((step, index) => {
          const isActive = streaming && index === steps.length - 1 && !step.done;
          return (
            <li key={step.id} className={styles.processItem}>
              {isActive ? (
                <LoadingOutlined className={styles.processIconActive} spin />
              ) : (
                <CheckCircleOutlined className={styles.processIconDone} />
              )}
              <span className={isActive ? styles.processTextActive : styles.processTextDone}>
                {step.message}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

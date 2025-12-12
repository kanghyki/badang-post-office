'use client';

import { useEffect, useState } from 'react';
import styles from './template.module.scss';

export default function Template({ children }: { children: React.ReactNode }) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <div className={`${styles.template} ${isVisible ? styles.visible : ''}`}>
      {children}
    </div>
  );
}

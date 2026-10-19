import type { ComponentPropsWithoutRef } from 'react';

import styles from './ModuleList.module.css';

export type ModuleListProps = ComponentPropsWithoutRef<'div'>;

export function ModuleList({ className, ...props }: ModuleListProps) {
  const rootClassName = [styles.root, className].filter(Boolean).join(' ');
  return <div className={rootClassName} {...props} />;
}

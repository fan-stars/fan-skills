import type { ComponentPropsWithoutRef } from 'react';

import styles from './ModuleGrid.module.css';

export type ModuleGridProps = ComponentPropsWithoutRef<'div'>;

export function ModuleGrid({ className, ...props }: ModuleGridProps) {
  const rootClassName = [styles.root, className].filter(Boolean).join(' ');
  return <div className={rootClassName} {...props} />;
}

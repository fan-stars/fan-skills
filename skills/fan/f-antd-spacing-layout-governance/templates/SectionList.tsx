import type { ComponentPropsWithoutRef } from 'react';

import styles from './SectionList.module.css';

export type SectionListProps = ComponentPropsWithoutRef<'div'>;

export function SectionList({ className, ...props }: SectionListProps) {
  const rootClassName = [styles.root, className].filter(Boolean).join(' ');
  return <div className={rootClassName} {...props} />;
}

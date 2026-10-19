import type { ComponentPropsWithoutRef } from 'react';

import styles from './ContentContainer.module.css';

export type ContentContainerProps = ComponentPropsWithoutRef<'div'>;

export function ContentContainer({
  className,
  ...props
}: ContentContainerProps) {
  const rootClassName = [styles.root, className].filter(Boolean).join(' ');
  return <div className={rootClassName} {...props} />;
}

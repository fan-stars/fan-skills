import type { ComponentPropsWithoutRef } from 'react';

import styles from './MobilePageContainer.module.css';

export type MobilePageContainerProps = ComponentPropsWithoutRef<'main'>;

export function MobilePageContainer({
  className,
  ...props
}: MobilePageContainerProps) {
  const rootClassName = [styles.root, className].filter(Boolean).join(' ');
  return <main className={rootClassName} {...props} />;
}

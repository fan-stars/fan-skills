import type { ComponentPropsWithoutRef } from 'react';

import styles from './MobilePageContainerWithBottomNav.module.css';

export type MobilePageContainerWithBottomNavProps =
  ComponentPropsWithoutRef<'main'>;

export function MobilePageContainerWithBottomNav({
  className,
  ...props
}: MobilePageContainerWithBottomNavProps) {
  const rootClassName = [styles.root, className].filter(Boolean).join(' ');
  return <main className={rootClassName} {...props} />;
}

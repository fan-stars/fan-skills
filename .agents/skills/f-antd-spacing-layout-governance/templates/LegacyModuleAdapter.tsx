import type { ComponentPropsWithoutRef } from 'react';

import styles from './LegacyModuleAdapter.module.css';

export type LegacyModuleAdapterProps = ComponentPropsWithoutRef<'div'>;

export function LegacyModuleAdapter({
  className,
  ...props
}: LegacyModuleAdapterProps) {
  const rootClassName = [styles.root, className].filter(Boolean).join(' ');
  return <div className={rootClassName} {...props} />;
}

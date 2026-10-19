import type { ComponentPropsWithoutRef } from 'react';

import styles from './PCPageContainer.module.css';

export type PCPageContainerProps = ComponentPropsWithoutRef<'main'> & {
  constrained?: boolean;
};

export function PCPageContainer({
  className,
  constrained = false,
  ...props
}: PCPageContainerProps) {
  const rootClassName = [
    styles.root,
    constrained ? styles.constrained : undefined,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return <main className={rootClassName} {...props} />;
}

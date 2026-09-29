import { HTMLAttributes, forwardRef } from 'react';
import { classNames } from '@/utils/formatters';

interface SeparatorProps extends HTMLAttributes<HTMLDivElement> {
  orientation?: 'horizontal' | 'vertical';
}

export const Separator = forwardRef<HTMLDivElement, SeparatorProps>(
  ({ className, orientation = 'horizontal', ...props }, ref) => (
    <div
      ref={ref}
      className={classNames(
        'bg-slate-200 dark:bg-slate-700',
        orientation === 'horizontal' ? 'w-full h-px' : 'h-full w-px',
        className
      )}
      role="separator"
      {...props}
    />
  )
);

Separator.displayName = 'Separator';
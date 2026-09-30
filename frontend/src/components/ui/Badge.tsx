import { HTMLAttributes, forwardRef } from 'react';
import { classNames } from '@/utils/formatters';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?:
    | 'primary'
    | 'secondary'
    | 'default'
    | 'outline'
    | 'success'
    | 'warning'
    | 'destructive'
    | 'muted';
}

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'primary', children, ...props }, ref) => {
    const variantClasses = {
      primary: 'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200',
      secondary: 'bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100',
      default: 'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200',
      outline: 'border border-slate-300 text-slate-700 dark:border-slate-600 dark:text-slate-200',
      success: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      destructive: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      muted: 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200',
    };

    return (
      <span
        ref={ref}
        className={classNames(
          'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
          variantClasses[variant],
          className
        )}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
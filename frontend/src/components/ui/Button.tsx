import { forwardRef, ButtonHTMLAttributes, Children, cloneElement, isValidElement } from 'react';
import { classNames } from '@/utils/formatters';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  loading?: boolean;
  /**
   * Render the single child element instead of a `<button>`, applying the
   * button styling to it. Lets navigation targets (`<a>`, react-router `<Link>`)
   * look like buttons without a duplicate styled element. Event props, `type`,
   * and `disabled` are dropped because a link cannot carry them.
   */
  asChild?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { className, variant = 'primary', size = 'md', loading, disabled, children, asChild, ...props },
    ref
  ) => {
    const baseClasses = 'inline-flex items-center justify-center gap-2 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';
    
    const variantClasses = {
      primary: 'bg-primary-600 text-white hover:bg-primary-700',
      secondary: 'bg-slate-100 text-slate-900 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700',
      outline:
        'border border-slate-300 bg-transparent text-slate-900 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-100 dark:hover:bg-slate-800',
      ghost: 'bg-transparent hover:bg-slate-100 dark:hover:bg-slate-800',
      destructive: 'bg-red-600 text-white hover:bg-red-700',
    };

    const sizeClasses = {
      sm: 'px-3 py-1.5 text-sm rounded-md',
      md: 'px-4 py-2 text-sm rounded-lg',
      lg: 'px-6 py-3 text-base rounded-lg',
      icon: 'h-9 w-9 p-0',
    };

    const buttonClassName = classNames(
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      className
    );

    if (asChild) {
      const child = Children.only(children);

      if (!isValidElement(child)) {
        throw new Error('Button: `asChild` expects a single React element child.');
      }

      const childProps = child.props as { className?: string };
      const { onClick: _onClick, type: _type, ...restProps } = props;

      return cloneElement(child, {
        ...restProps,
        className: classNames(buttonClassName, childProps.className),
      });
    }

    return (
      <button
        ref={ref}
        className={buttonClassName}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
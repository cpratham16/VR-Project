import React from 'react';

export interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg' | 'full';
}

const sizeMap = {
  sm: 'max-w-3xl',
  md: 'max-w-5xl',
  lg: 'max-w-7xl',
  full: 'max-w-none',
};

export const Container: React.FC<ContainerProps> = ({
  className = '',
  size = 'lg',
  children,
  ...props
}) => (
  <div className={`mx-auto w-full px-4 sm:px-6 lg:px-8 ${sizeMap[size]} ${className}`} {...props}>
    {children}
  </div>
);

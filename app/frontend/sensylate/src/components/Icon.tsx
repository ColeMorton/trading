import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { IconDefinition } from '@fortawesome/fontawesome-svg-core';

interface IconProps {
  icon: IconDefinition;
  className?: string;
  size?: 'xs' | 'sm' | 'lg' | 'xl' | '2xl' | '1x' | '2x' | '3x' | '4x' | '5x' | '6x' | '7x' | '8x' | '9x' | '10x';
  spin?: boolean;
  pulse?: boolean;
  fixedWidth?: boolean;
  title?: string;
  'aria-label'?: string;
}

const Icon: React.FC<IconProps> = ({
  icon,
  className = '',
  size,
  spin = false,
  pulse = false,
  fixedWidth = false,
  title,
  'aria-label': ariaLabel,
  ...props
}) => {
  return (
    <FontAwesomeIcon
      icon={icon}
      className={className}
      size={size}
      spin={spin}
      pulse={pulse}
      fixedWidth={fixedWidth}
      title={title}
      aria-label={ariaLabel}
      {...props}
    />
  );
};

export default Icon;
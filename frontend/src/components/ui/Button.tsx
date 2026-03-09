import { ReactNode, MouseEvent, TouchEvent, useState } from 'react';

interface TouchButtonProps {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

export function TouchButton({
  children,
  onClick,
  disabled = false,
  className = '',
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  type = 'button',
}: TouchButtonProps) {
  const [isPressed, setIsPressed] = useState(false);

  const handleMouseDown = () => {
    if (!disabled) setIsPressed(true);
  };

  const handleMouseUp = () => {
    setIsPressed(false);
  };

  const handleMouseLeave = () => {
    setIsPressed(false);
  };

  const handleTouchStart = (e: TouchEvent) => {
    if (!disabled) {
      e.preventDefault(); // Prevent mouse emulation
      setIsPressed(true);
    }
  };

  const handleTouchEnd = () => {
    setIsPressed(false);
  };

  const handleClick = (e: MouseEvent) => {
    if (!disabled && !isPressed) {
      onClick?.();
    }
  };

  const baseClasses = 'inline-flex items-center justify-center font-medium transition-all duration-200 select-none touch-manipulation';

  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800',
    secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200 active:bg-gray-300',
    ghost: 'bg-transparent text-gray-600 hover:bg-gray-100 active:bg-gray-200',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3',
  };

  const pressedClasses = isPressed
    ? {
        primary: 'bg-blue-700',
        secondary: 'bg-gray-200',
        ghost: 'bg-gray-100',
      }[variant]
    : '';

  const widthClass = fullWidth ? 'w-full' : '';

  const disabledClasses = disabled
    ? 'opacity-50 cursor-not-allowed'
    : 'cursor-pointer';

  return (
    <button
      type={type}
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${pressedClasses}
        ${widthClass}
        ${disabledClasses}
        rounded-lg
        ${className}
      `}
      disabled={disabled}
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {children}
    </button>
  );
}

// Ripple Effect Button
export function RippleButton({ children, className = '', ...props }: any) {
  const [ripples, setRipples] = useState<Array<{ id: number; x: number; y: number }>>([]);

  const addRipple = (e: MouseEvent | TouchEvent) => {
    const button = e.currentTarget as HTMLElement;
    const rect = button.getBoundingClientRect();

    let x: number, y: number;
    if ('touches' in e) {
      x = (e as TouchEvent).touches[0].clientX - rect.left;
      y = (e as TouchEvent).touches[0].clientY - rect.top;
    } else {
      x = (e as MouseEvent).clientX - rect.left;
      y = (e as MouseEvent).clientY - rect.top;
    }

    const newRipple = {
      id: Date.now(),
      x,
      y,
    };

    setRipples(prev => [...prev, newRipple]);

    // Remove ripple after animation
    setTimeout(() => {
      setRipples(prev => prev.filter(r => r.id !== newRipple.id));
    }, 600);
  };

  return (
    <button
      className={`relative overflow-hidden ${className}`}
      onMouseDown={addRipple}
      onTouchStart={addRipple}
      {...props}
    >
      {children}
      {ripples.map(ripple => (
        <span
          key={ripple.id}
          className="absolute rounded-full bg-white opacity-30 animate-ping pointer-events-none"
          style={{
            left: ripple.x - 10,
            top: ripple.y - 10,
            width: 20,
            height: 20,
          }}
        />
      ))}
    </button>
  );
}

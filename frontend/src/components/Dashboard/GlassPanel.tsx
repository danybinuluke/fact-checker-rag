import { ReactNode } from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  noPadding?: boolean;
  onClick?: () => void;
}

export function GlassPanel({ children, className, noPadding = false, onClick }: GlassPanelProps) {
  return (
    <div 
      className={cn(
        "glass-panel rounded-2xl overflow-hidden",
        !noPadding && "p-6",
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}

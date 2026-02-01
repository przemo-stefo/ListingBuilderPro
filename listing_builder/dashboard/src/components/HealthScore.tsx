// src/components/HealthScore.tsx
// Purpose: Health score display with circular progress
// NOT for: API calls or data fetching

'use client';

import { cn } from '@/lib/utils';

interface HealthScoreProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export function HealthScore({ score, size = 'md', showLabel = true }: HealthScoreProps) {
  // Determine color based on score
  const getColor = () => {
    if (score >= 80) return { stroke: '#22c55e', text: 'text-green-500', label: 'Excellent' };
    if (score >= 60) return { stroke: '#84cc16', text: 'text-lime-500', label: 'Good' };
    if (score >= 40) return { stroke: '#f59e0b', text: 'text-yellow-500', label: 'Warning' };
    return { stroke: '#ef4444', text: 'text-red-500', label: 'Critical' };
  };

  const { stroke, text, label } = getColor();

  // Size configurations
  const sizes = {
    sm: { width: 80, strokeWidth: 6, fontSize: 'text-lg' },
    md: { width: 120, strokeWidth: 8, fontSize: 'text-3xl' },
    lg: { width: 160, strokeWidth: 10, fontSize: 'text-4xl' },
  };

  const { width, strokeWidth, fontSize } = sizes[size];
  const radius = (width - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width, height: width }}>
        {/* Background circle */}
        <svg
          className="transform -rotate-90"
          width={width}
          height={width}
        >
          <circle
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="none"
            stroke="#333333"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="none"
            stroke={stroke}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className="transition-all duration-500 ease-out"
          />
        </svg>

        {/* Score text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn('font-bold', fontSize, text)}>
            {score}
          </span>
        </div>
      </div>

      {showLabel && (
        <div className="mt-2 text-center">
          <p className={cn('font-medium', text)}>{label}</p>
          <p className="text-xs text-muted-foreground">Health Score</p>
        </div>
      )}
    </div>
  );
}

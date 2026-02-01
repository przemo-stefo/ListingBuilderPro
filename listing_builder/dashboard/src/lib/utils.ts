// src/lib/utils.ts
// Purpose: Utility functions for the dashboard
// NOT for: API calls or business logic

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

// Combine Tailwind classes safely
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format currency
export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(value);
}

// Format number with commas
export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

// Format percentage
export function formatPercent(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

// Format relative time
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return then.toLocaleDateString();
}

// Get health score color
export function getHealthColor(score: number): string {
  if (score >= 80) return 'text-green-500';
  if (score >= 60) return 'text-lime-500';
  if (score >= 40) return 'text-yellow-500';
  return 'text-red-500';
}

// Get health score background
export function getHealthBg(score: number): string {
  if (score >= 80) return 'bg-green-500/10';
  if (score >= 60) return 'bg-lime-500/10';
  if (score >= 40) return 'bg-yellow-500/10';
  return 'bg-red-500/10';
}

// Get severity color
export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical': return 'text-red-500 bg-red-500/10';
    case 'high': return 'text-orange-500 bg-orange-500/10';
    case 'medium': return 'text-yellow-500 bg-yellow-500/10';
    case 'low': return 'text-blue-500 bg-blue-500/10';
    default: return 'text-gray-500 bg-gray-500/10';
  }
}

// Get status color
export function getStatusColor(status: string): string {
  switch (status) {
    case 'active': return 'text-red-400 bg-red-500/10';
    case 'acknowledged': return 'text-yellow-400 bg-yellow-500/10';
    case 'resolved': return 'text-green-400 bg-green-500/10';
    case 'dismissed': return 'text-gray-400 bg-gray-500/10';
    default: return 'text-gray-400 bg-gray-500/10';
  }
}

// Get marketplace color
export function getMarketplaceColor(marketplace: string): string {
  switch (marketplace) {
    case 'amazon': return 'text-orange-400';
    case 'ebay': return 'text-blue-400';
    case 'allegro': return 'text-orange-300';
    case 'kaufland': return 'text-red-400';
    case 'temu': return 'text-purple-400';
    default: return 'text-gray-400';
  }
}

// Get marketplace icon/badge
export function getMarketplaceBadge(marketplace: string): string {
  switch (marketplace) {
    case 'amazon': return 'AMZ';
    case 'ebay': return 'EBAY';
    case 'allegro': return 'ALG';
    case 'kaufland': return 'KFL';
    case 'temu': return 'TEMU';
    default: return marketplace.substring(0, 3).toUpperCase();
  }
}

// Truncate text
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

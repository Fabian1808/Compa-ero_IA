import { format, formatDistanceToNow, parseISO, isToday, isTomorrow, isYesterday } from 'date-fns';
import { es } from 'date-fns/locale';

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return '';
  try {
    const date = parseISO(dateString);
    if (isToday(date)) return `Hoy, ${format(date, 'HH:mm')}`;
    if (isTomorrow(date)) return `Mañana, ${format(date, 'HH:mm')}`;
    if (isYesterday(date)) return `Ayer, ${format(date, 'HH:mm')}`;
    return format(date, 'dd MMM yyyy, HH:mm', { locale: es });
  } catch {
    return '';
  }
}

export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return '';
  try {
    const date = parseISO(dateString);
    return formatDistanceToNow(date, { addSuffix: true, locale: es });
  } catch {
    return '';
  }
}

export function formatDuration(minutes: number | null | undefined): string {
  if (!minutes) return '';
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}min` : `${hours}h`;
}

export function getPriorityColor(priority: string): string {
  switch (priority) {
    case 'critical':
      return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-200';
    case 'high':
      return 'text-orange-600 bg-orange-100 dark:bg-orange-900 dark:text-orange-200';
    case 'medium':
      return 'text-amber-600 bg-amber-100 dark:bg-amber-900 dark:text-amber-200';
    case 'low':
      return 'text-slate-600 bg-slate-100 dark:bg-slate-700 dark:text-slate-200';
    default:
      return 'text-slate-600 bg-slate-100 dark:bg-slate-700 dark:text-slate-200';
  }
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-200';
    case 'in_progress':
      return 'text-blue-600 bg-blue-100 dark:bg-blue-900 dark:text-blue-200';
    case 'blocked':
      return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-200';
    case 'waiting_response':
      return 'text-purple-600 bg-purple-100 dark:bg-purple-900 dark:text-purple-200';
    case 'requires_decision':
      return 'text-amber-600 bg-amber-100 dark:bg-amber-900 dark:text-amber-200';
    case 'cancelled':
      return 'text-slate-600 bg-slate-100 dark:bg-slate-700 dark:text-slate-200';
    case 'pending':
    default:
      return 'text-slate-600 bg-slate-100 dark:bg-slate-700 dark:text-slate-200';
  }
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'critical':
      return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-200 border-red-200 dark:border-red-800';
    case 'important':
      return 'text-orange-600 bg-orange-100 dark:bg-orange-900 dark:text-orange-200 border-orange-200 dark:border-orange-800';
    case 'reminder':
      return 'text-amber-600 bg-amber-100 dark:bg-amber-900 dark:text-amber-200 border-amber-200 dark:border-amber-800';
    case 'info':
    default:
      return 'text-slate-600 bg-slate-100 dark:bg-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700';
  }
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
}

export function classNames(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}
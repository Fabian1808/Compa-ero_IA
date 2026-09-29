import { Card, CardContent, Badge } from '@/components/ui';
import { AlertCircle, Clock, Mail, Link } from 'lucide-react';
import { formatRelativeTime } from '@/utils/formatters';

interface AttentionItem {
  type: 'followup' | 'blocked_task' | 'deadline' | 'commitment';
  title: string;
  description?: string;
  time?: string;
  count?: number;
}

interface AttentionCardProps {
  items: AttentionItem[];
}

const icons = {
  followup: Mail,
  blocked_task: Link,
  deadline: Clock,
  commitment: AlertCircle,
};

const colors = {
  followup: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400',
  blocked_task: 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400',
  deadline: 'text-amber-600 bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400',
  commitment: 'text-purple-600 bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400',
};

export function AttentionCard({ items }: AttentionCardProps) {
  if (items.length === 0) {
    return (
      <Card className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
        <CardContent className="py-6 text-center">
          <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30 inline-flex mb-2">
            <AlertCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
          </div>
          <h3 className="font-medium text-green-800 dark:text-green-300">Todo bajo control</h3>
          <p className="text-sm text-green-600 dark:text-green-400 mt-1">No hay elementos que requieran atención inmediata.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-l-4 border-amber-500">
      <CardContent className="py-2">
        <div className="flex items-center gap-2 mb-3">
          <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          <h3 className="font-semibold text-slate-900 dark:text-slate-100">ATENCIÓN</h3>
          <Badge variant="warning">{items.length}</Badge>
        </div>
        <div className="space-y-2">
          {items.map((item, index) => (
            <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50">
              <div className={`p-1.5 rounded ${colors[item.type]}`}>
                <icons[item.type] className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-slate-900 dark:text-slate-100">{item.title}</p>
                {item.description && (
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">{item.description}</p>
                )}
                {item.time && (
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{formatRelativeTime(item.time)}</p>
                )}
              </div>
              {item.count && item.count > 1 && (
                <Badge variant="muted">{item.count} elementos</Badge>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
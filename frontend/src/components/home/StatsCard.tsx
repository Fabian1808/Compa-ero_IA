import { Card, CardContent } from '@/components/ui';
import { CheckCircle, Clock, AlertCircle, FolderKanban } from 'lucide-react';

interface StatsCardProps {
  completedToday: number;
  pending: number;
  inProgress: number;
  blocked: number;
}

export function StatsCard({ completedToday, pending, inProgress, blocked }: StatsCardProps) {
  const stats = [
    { label: 'Completadas hoy', value: completedToday, icon: CheckCircle, color: 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400' },
    { label: 'Pendientes', value: pending, icon: FolderKanban, color: 'text-slate-600 bg-slate-100 dark:bg-slate-700 dark:text-slate-300' },
    { label: 'En marcha', value: inProgress, icon: Clock, color: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400' },
    { label: 'Bloqueadas', value: blocked, icon: AlertCircle, color: 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <Card key={index} className="text-center">
          <CardContent className="py-4">
            <div className={`p-2 rounded-lg inline-flex ${stat.color} mb-3`}>
              <stat.icon className="h-5 w-5" />
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{stat.value}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">{stat.label}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
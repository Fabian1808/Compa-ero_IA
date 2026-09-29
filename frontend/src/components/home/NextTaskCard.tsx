import { Task } from '@/types/task';
import { Card, CardContent, Button, Badge } from '@/components/ui';
import { Clock, AlertCircle, CheckCircle, ChevronRight } from 'lucide-react';
import { formatDate, formatDuration, getPriorityColor } from '@/utils/formatters';

interface NextTaskCardProps {
  task: Task | null;
  onStart: () => void;
  loading?: boolean;
}

export function NextTaskCard({ task, onStart, loading }: NextTaskCardProps) {
  if (!task) {
    return (
      <Card className="bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700">
        <CardContent className="py-8 text-center">
          <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100">¡Todo al día!</h3>
          <p className="text-slate-500 dark:text-slate-400 mt-1">No hay tareas pendientes urgentes por ahora.</p>
        </CardContent>
      </Card>
    );
  }

  const isOverdue = task.deadline_at && new Date(task.deadline_at) < new Date();
  const isDueToday = task.deadline_at && new Date(task.deadline_at).toDateString() === new Date().toDateString();

  return (
    <Card className="border-l-4 border-primary-500">
      <CardContent className="py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-primary-700 dark:text-primary-300 bg-primary-100 dark:bg-primary-900 px-2 py-0.5 rounded">
                AHORA
              </span>
              {isOverdue && (
                <Badge variant="destructive" className="text-xs">
                  Vencida
                </Badge>
              )}
              {isDueToday && !isOverdue && (
                <Badge variant="warning" className="text-xs">
                  Vence hoy
                </Badge>
              )}
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-1">{task.title}</h3>
            {task.description && (
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-3 line-clamp-2">{task.description}</p>
            )}
            <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
              {task.estimated_minutes && (
                <span className="flex items-center gap-1">
                  <Clock className="h-4 w-4" />
                  {formatDuration(task.estimated_minutes)}
                </span>
              )}
              {task.deadline_at && (
                <span className="flex items-center gap-1">
                  <AlertCircle className="h-4 w-4" />
                  {formatDate(task.deadline_at)}
                </span>
              )}
              {task.priority && (
                <Badge className={getPriorityColor(task.priority)}>
                  {task.priority}
                </Badge>
              )}
            </div>
          </div>
          <Button
            onClick={onStart}
            disabled={loading}
            loading={loading}
            className="flex-shrink-0"
          >
            Empezar
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
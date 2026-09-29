import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, Badge, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';
import { Clock, AlertTriangle, Calendar, CheckCircle, Flag } from 'lucide-react';
import { formatRelativeTime, formatDate, formatDuration } from '@/utils/formatters';

interface Deadline {
  id: string;
  type: 'task' | 'commitment';
  title: string;
  description?: string;
  deadline: string | null;
  priority: string;
  status?: string;
  project_id?: string;
  project_name?: string;
  hours_until?: number;
}

export function DeadlinesPage() {
  const [allDeadlines, setAllDeadlines] = useState<Deadline[]>([]);
  const [upcomingDeadlines, setUpcomingDeadlines] = useState<Deadline[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'upcoming' | 'overdue' | 'this-week'>('upcoming');

  useEffect(() => {
    fetchDeadlines();
  }, []);

  const fetchDeadlines = async () => {
    setLoading(true);
    try {
      const [allRes, upcomingRes] = await Promise.all([
        api.get('/deadlines?days=30'),
        api.get('/deadlines/upcoming?hours=168'),
      ]);
      setAllDeadlines(allRes.data.deadlines || []);
      setUpcomingDeadlines(upcomingRes.data.deadlines || []);
    } catch (err) {
      console.error('Failed to fetch deadlines:', err);
    } finally {
      setLoading(false);
    }
  };

  const getFilteredDeadlines = () => {
    const now = new Date();
    const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

    switch (activeTab) {
      case 'overdue':
        return allDeadlines.filter(d => d.deadline && new Date(d.deadline) < now);
      case 'this-week':
        return allDeadlines.filter(d => d.deadline && new Date(d.deadline) <= weekFromNow);
      case 'upcoming':
        return upcomingDeadlines;
      default:
        return allDeadlines;
    }
  };

  const filtered = getFilteredDeadlines();

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
      case 'medium': return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400';
      default: return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300';
    }
  };

  const getTypeIcon = (type: string) => {
    return type === 'task' ? <Clock className="h-4 w-4" /> : <Flag className="h-4 w-4" />;
  };

  const getTypeLabel = (type: string) => type === 'task' ? 'Tarea' : 'Compromiso';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Deadlines</h1>
        <p className="text-slate-500 dark:text-slate-400">Fechas límite de tareas y compromisos</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="upcoming">Próximas 24h</TabsTrigger>
          <TabsTrigger value="this-week">Esta semana</TabsTrigger>
          <TabsTrigger value="overdue">Vencidas</TabsTrigger>
          <TabsTrigger value="all">Todas (30 días)</TabsTrigger>
        </TabsList>

        <TabsContent value="upcoming" className="mt-4">
          <DeadlinesList deadlines={upcomingDeadlines} loading={loading} />
        </TabsContent>
        <TabsContent value="this-week" className="mt-4">
          <DeadlinesList deadlines={filtered} loading={loading} />
        </TabsContent>
        <TabsContent value="overdue" className="mt-4">
          <DeadlinesList deadlines={filtered} loading={loading} />
        </TabsContent>
        <TabsContent value="all" className="mt-4">
          <DeadlinesList deadlines={filtered} loading={loading} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function DeadlinesList({ deadlines, loading }: { deadlines: Deadline[]; loading: boolean }) {
  if (loading) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent mx-auto" />
        </CardContent>
      </Card>
    );
  }

  if (deadlines.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Calendar className="h-16 w-16 mx-auto text-slate-300 dark:text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">No hay deadlines</h3>
          <p className="text-slate-500 dark:text-slate-400">¡Todo bajo control por ahora!</p>
        </CardContent>
      </Card>
    );
  }

  // Group by date
  const grouped = deadlines.reduce((acc, d) => {
    if (!d.deadline) return acc;
    const date = new Date(d.deadline).toISOString().split('T')[0];
    if (!acc[date]) acc[date] = [];
    acc[date].push(d);
    return acc;
  }, {} as Record<string, Deadline[]>);

  const sortedDates = Object.keys(grouped).sort();

  return (
    <div className="space-y-6">
      {sortedDates.map((date) => (
        <Card key={date}>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-3">
              <Calendar className="h-5 w-5 text-primary-600 dark:text-primary-400" />
              {formatDate(new Date(date + 'T00:00:00').toISOString())}
              <Badge variant="primary">{grouped[date].length} items</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {grouped[date].map((deadline) => (
                <DeadlineItem key={deadline.id} deadline={deadline} />
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function DeadlineItem({ deadline }: { deadline: Deadline }) {
  const isOverdue = deadline.deadline && new Date(deadline.deadline) < new Date();
  const hoursUntil = deadline.hours_until;

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400';
      case 'medium': return 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400';
      default: return 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300';
    }
  };

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${isOverdue ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20' : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50'}`}>
      <div className={`flex-shrink-0 p-2 rounded-lg ${isOverdue ? 'bg-red-100 dark:bg-red-900/30' : 'bg-primary-100 dark:bg-primary-900/30'}`}>
        {deadline.type === 'task' ? <Clock className="h-5 w-5 text-primary-600 dark:text-primary-400" /> : <Flag className="h-5 w-5 text-primary-600 dark:text-primary-400" />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="font-medium text-slate-900 dark:text-slate-100 truncate">{deadline.title}</h4>
          <Badge variant={isOverdue ? 'destructive' : 'muted'}>{deadline.type === 'task' ? 'Tarea' : 'Compromiso'}</Badge>
          <Badge className={getPriorityColor(deadline.priority)}>{deadline.priority}</Badge>
        </div>
        {deadline.description && (
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-2 line-clamp-1">{deadline.description}</p>
        )}
        <div className="flex items-center gap-3 text-sm">
          <span className={`flex items-center gap-1 ${isOverdue ? 'text-red-600 dark:text-red-400 font-medium' : 'text-slate-500 dark:text-slate-400'}`}>
            <Clock className="h-3.5 w-3.5" />
            {deadline.deadline ? formatDate(deadline.deadline) : 'Sin fecha'}
          </span>
          {hoursUntil !== undefined && hoursUntil > 0 && (
            <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="h-3.5 w-3.5" />
              {hoursUntil < 1 ? `${Math.round(hoursUntil * 60)} min` : `${Math.round(hoursUntil)}h`}
            </span>
          )}
          {deadline.project_name && (
            <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
              <Flag className="h-3.5 w-3.5" />
              {deadline.project_name}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
import { useEffect, useState } from 'react';
import { useTasks } from '@/hooks/useTasks';
import { useAI } from '@/hooks/useAI';
import { useNotifications } from '@/hooks/useNotifications';
import { useSync } from '@/hooks/useSync';
import { NextTaskCard } from '@/components/home/NextTaskCard';
import { UpcomingMeetingCard } from '@/components/home/UpcomingMeetingCard';
import { AttentionCard } from '@/components/home/AttentionCard';
import { StatsCard } from '@/components/home/StatsCard';
import { Card, CardContent, Button, Input } from '@/components/ui';
import { Search, Sparkles, RefreshCw, Plus } from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

export function HomePage() {
  const { tasks, stats, isLoading, fetchTasks, recommendNext, startFocus } = useTasks();
  const { askAI } = useAI();
  const { unreadCount } = useNotifications();
  const { lastSync, triggerSync, isSyncing } = useSync();
  const [question, setQuestion] = useState('');
  const [recommendation, setRecommendation] = useState<{
    recommended_task_id: string | null;
    title: string;
    reasoning: string;
    confidence: number;
  } | null>(null);
  const [showRecommendation, setShowRecommendation] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const handleAskAI = async () => {
    if (!question.trim()) return;
    setAiLoading(true);
    try {
      const result = await askAI({ question, context: { current_page: 'home' } });
      console.log('AI Response:', result);
      // Handle response - could show in a modal or toast
    } catch (err) {
      console.error('AI error:', err);
    } finally {
      setAiLoading(false);
      setQuestion('');
    }
  };

  const handleRecommendNext = async () => {
    setAiLoading(true);
    try {
      const rec = await recommendNext();
      setRecommendation(rec);
      setShowRecommendation(true);
    } catch (err) {
      console.error('Recommendation error:', err);
    } finally {
      setAiLoading(false);
    }
  };

  // Find next meeting (mock for now)
  const nextMeeting = null; // Would come from calendar data

  // Build attention items
  const attentionItems = [
    ...(unreadCount > 0 ? [{
      type: 'followup' as const,
      title: 'Notificaciones sin leer',
      description: `${unreadCount} notificación${unreadCount !== 1 ? 'es' : ''} pendiente${unreadCount !== 1 ? 's' : ''}`,
    }] : []),
    ...(stats.blocked > 0 ? [{
      type: 'blocked_task' as const,
      title: 'Tareas bloqueadas',
      description: `${stats.blocked} tarea${stats.blocked !== 1 ? 's' : ''} no pueden avanzar`,
      count: stats.blocked,
    }] : []),
  ];

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Buenos días';
    if (hour < 18) return 'Buenas tardes';
    return 'Buenas noches';
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {greeting()}
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            {format(new Date(), "EEEE, d 'de' MMMM", { locale: es })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={triggerSync} disabled={isSyncing} loading={isSyncing}>
            <RefreshCw className="h-4 w-4" />
            {lastSync ? `Última sync: ${new Date(lastSync).toLocaleTimeString()}` : 'Sincronizar'}
          </Button>
        </div>
      </div>

      {/* AI Assistant - Main Question */}
      <Card className="bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/30 dark:to-primary-800/30 border-primary-200 dark:border-primary-800">
        <CardContent className="py-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
              <Sparkles className="h-5 w-5 text-primary-700 dark:text-primary-300" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-100">¿Qué necesitas hacer?</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">Pregúntame cualquier cosa sobre tu trabajo</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAskAI()}
              placeholder="Ej: ¿Qué debería hacer ahora? ¿Qué tengo bloqueado? ¿Qué vence mañana?"
              className="flex-1"
            />
            <Button onClick={handleAskAI} loading={aiLoading}>
              Preguntar
            </Button>
            <Button variant="secondary" onClick={handleRecommendNext} loading={aiLoading}>
              <Sparkles className="h-4 w-4" />
              Qué hacer ahora
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* AI Recommendation */}
      {showRecommendation && recommendation && (
        <Card className="border-primary-200 dark:border-primary-800 bg-primary-50 dark:bg-primary-900/20">
          <CardContent className="py-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
                <Sparkles className="h-5 w-5 text-primary-700 dark:text-primary-300" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-primary-700 dark:text-primary-300 bg-primary-100 dark:bg-primary-900 px-2 py-0.5 rounded">
                    RECOMENDACIÓN IA
                  </span>
                  <Badge variant="primary">{recommendation.confidence}% confianza</Badge>
                </div>
                <h3 className="font-semibold text-slate-900 dark:text-slate-100">{recommendation.title}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{recommendation.reasoning}</p>
                <div className="flex items-center gap-3 mt-3">
                  {recommendation.recommended_task_id && (
                    <Button onClick={() => startFocus(tasks.find(t => t.id === recommendation.recommended_task_id)!)} size="sm">
                      Empezar esta tarea
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" onClick={() => setShowRecommendation(false)}>
                    Descartar
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      <StatsCard
        completedToday={stats.completed_today}
        pending={stats.pending}
        inProgress={stats.in_progress}
        blocked={stats.blocked}
      />

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column - Main task */}
        <div className="lg:col-span-2 space-y-6">
          {/* Next Task */}
          <NextTaskCard
            task={recommendation?.recommended_task_id ? tasks.find(t => t.id === recommendation.recommended_task_id) || null : tasks.find(t => t.status === 'pending' || t.status === 'in_progress') || null}
            onStart={() => {
              const nextTask = tasks.find(t => t.status === 'pending' || t.status === 'in_progress');
              if (nextTask) startFocus(nextTask);
            }}
            loading={aiLoading}
          />

          {/* Upcoming Meeting */}
          <UpcomingMeetingCard meeting={nextMeeting} />
        </div>

        {/* Right column - Attention & Quick Actions */}
        <div className="space-y-6">
          <AttentionCard items={attentionItems} />

          {/* Quick Actions */}
          <Card>
            <CardContent className="py-4">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-4">Acciones rápidas</h3>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="secondary" className="h-20 flex flex-col gap-1">
                  <Plus className="h-5 w-5" />
                  <span className="text-xs">Nueva tarea</span>
                </Button>
                <Button variant="secondary" className="h-20 flex flex-col gap-1">
                  <Plus className="h-5 w-5" />
                  <span className="text-xs">Nuevo proyecto</span>
                </Button>
                <Button variant="secondary" className="h-20 flex flex-col gap-1">
                  <Sparkles className="h-5 w-5" />
                  <span className="text-xs">Preguntar a IA</span>
                </Button>
                <Button variant="secondary" className="h-20 flex flex-col gap-1">
                  <RefreshCw className="h-5 w-5" />
                  <span className="text-xs">Sincronizar</span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
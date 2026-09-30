import { useEffect, useState } from 'react';
import { useTasks } from '@/hooks/useTasks';
import { Task } from '@/types/task';
import { Card, CardContent, Button } from '@/components/ui';
import { useI18n } from '@/i18n/I18nProvider';
import { PauseCircle, CheckCircle, XCircle, Clock, RotateCcw, Flag, AlertTriangle } from 'lucide-react';
import { formatDuration, formatRelativeTime } from '@/utils/formatters';

export function FocusPage() {
  const { t } = useI18n();
  const { currentTask, endFocus, completeTask, updateTask, tasks } = useTasks();
  const [elapsed, setElapsed] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [actualMinutes, setActualMinutes] = useState('');

  useEffect(() => {
    if (!currentTask) return;
    
    const interval = setInterval(() => {
      if (!isPaused) {
        setElapsed(prev => prev + 1);
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [currentTask, isPaused]);

  useEffect(() => {
    if (currentTask && currentTask.started_at) {
      const started = new Date(currentTask.started_at).getTime();
      const now = Date.now();
      setElapsed(Math.floor((now - started) / 1000));
    } else {
      setElapsed(0);
    }
  }, [currentTask]);

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hrs > 0) return `${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    return `${mins}:${String(secs).padStart(2, '0')}`;
  };

  const handlePause = () => setIsPaused(!isPaused);
  const handleStop = () => endFocus();
  const handleComplete = () => {
    if (actualMinutes) {
      completeTask(currentTask!.id, parseInt(actualMinutes));
    } else {
      completeTask(currentTask!.id);
    }
    setShowCompleteModal(false);
    setActualMinutes('');
  };

  if (!currentTask) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <Card className="bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700">
          <CardContent className="py-12">
            <div className="p-3 rounded-full bg-slate-100 dark:bg-slate-700 inline-flex mb-4">
              <Flag className="h-10 w-10 text-slate-400" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">{t('pages.focus.empty')}</h2>
            <p className="text-slate-500 dark:text-slate-400 mb-6">{t('pages.focus.emptyHint')}</p>
            <Button variant="secondary" onClick={() => window.history.back()}>
              {t('pages.focus.back')}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isOverdue = currentTask.deadline_at && new Date(currentTask.deadline_at) < new Date();

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="ghost" onClick={handleStop}>
          <RotateCcw className="h-5 w-5" />
        </Button>
        <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{t('pages.focus.title')}</h1>
        <div className="w-10" />
      </div>

      {/* Timer */}
      <Card className="bg-gradient-to-br from-primary-50 to-primary-100 dark:from-primary-900/30 dark:to-primary-800/30 border-primary-200 dark:border-primary-800">
        <CardContent className="py-8 text-center">
          <div className="mb-4">
            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${
              isOverdue ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
            }`}>
              <Flag className="h-3.5 w-3.5" />
              {isPaused ? 'PAUSADO' : 'EN FOCO'}
            </span>
          </div>
          <div className="text-6xl font-mono font-bold text-slate-900 dark:text-slate-100 mb-2" style={{ fontFamily: 'ui-monospace, SFMono-Regular, monospace' }}>
            {formatTime(elapsed)}
          </div>
          {currentTask.estimated_minutes && (
            <div className="text-sm text-slate-600 dark:text-slate-400">
              Estimado: {formatDuration(currentTask.estimated_minutes)} • 
              {elapsed > currentTask.estimated_minutes * 60 
                ? <span className="text-red-600 dark:text-red-400">{t('pages.focus.overtime')}</span>
                : <span>Faltan {formatDuration(Math.max(0, currentTask.estimated_minutes * 60 - elapsed))}</span>
              }
            </div>
          )}
        </CardContent>
      </Card>

      {/* Task Details */}
      <Card>
        <CardContent className="py-4">
          <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">{currentTask.title}</h3>
          {currentTask.description && (
            <p className="text-slate-600 dark:text-slate-400 mb-4">{currentTask.description}</p>
          )}
          
          <div className="flex flex-wrap items-center gap-3">
            {currentTask.priority && (
              <span className={`px-2 py-1 rounded text-xs font-medium ${['critical', 'high'].includes(currentTask.priority) ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : currentTask.priority === 'medium' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300'}`}>
                {currentTask.priority}
              </span>
            )}
            {currentTask.deadline_at && (
              <span className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${isOverdue ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'}`}>
                <Clock className="h-3 w-3" />
                {formatRelativeTime(currentTask.deadline_at)}
              </span>
            )}
            {currentTask.project && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
                {currentTask.project.name}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Controls */}
      <div className="flex gap-3">
        <Button
          variant={isPaused ? 'primary' : 'secondary'}
          size="lg"
          className="flex-1"
          onClick={handlePause}
        >
          {isPaused ? (
            <>
              <RotateCcw className="h-5 w-5" />
              {t('pages.focus.resume')}
            </>
          ) : (
            <>
              <PauseCircle className="h-5 w-5" />
              {t('pages.focus.pause')}
            </>
          )}
        </Button>
        <Button variant="destructive" size="lg" onClick={handleStop}>
          <XCircle className="h-5 w-5" />
          {t('pages.focus.stop')}
        </Button>
      </div>

      <Button 
        variant="primary" 
        size="lg" 
        className="w-full"
        onClick={() => setShowCompleteModal(true)}
      >
        <CheckCircle className="h-5 w-5" />
        {t('pages.focus.markCompleted')}
      </Button>

      {/* Quick Notes */}
      <Card>
        <CardContent className="py-4">
          <h4 className="font-medium text-slate-900 dark:text-slate-100 mb-3">{t('pages.focus.notes')}</h4>
          <textarea
            className="input resize-none min-h-[100px]"
            placeholder="Anota avances, bloqueos, ideas... (se guardan al completar)"
            defaultValue={currentTask.metadata_json ? JSON.parse(currentTask.metadata_json).focusNotes || '' : ''}
            onChange={(e) => updateTask(currentTask.id, { 
              metadata_json: JSON.stringify({ 
                ...JSON.parse(currentTask.metadata_json || '{}'), 
                focusNotes: e.target.value 
              }) 
            })}
          />
        </CardContent>
      </Card>
    </div>
  );
}
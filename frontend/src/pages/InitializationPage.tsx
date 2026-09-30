import { useState, useEffect, useCallback } from 'react';
import { 
  Brain, Loader2, CheckCircle, XCircle, AlertCircle, 
  Download, Check, Clock, Zap, Server, Database,
  ArrowRight, Sparkles, Shield
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Progress, Button, Badge } from '@/components/ui';
import { api } from '@/services/api';

interface StepProgress {
  step: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  progress: number;
  message: string;
  error?: string;
}

interface InitStatus {
  overall_progress: number;
  overall_status: string;
  current_step: string | null;
  steps: Record<string, StepProgress>;
  error: string | null;
}

interface StepProgress {
  status: string;
  progress: number;
  message: string;
  error?: string;
}

const STEPS_CONFIG = [
  { key: 'check_ollama', label: 'Verificar Ollama', icon: Brain, description: 'Motor de IA local' },
  { key: 'install_ollama', label: 'Instalar Ollama', icon: Download, description: 'Si no está presente' },
  { key: 'start_ollama', label: 'Iniciar Ollama', icon: Zap, description: 'Servicio de IA' },
  { key: 'check_models', label: 'Verificar modelos', icon: Brain, description: 'phi3:3.8b + nomic-embed-text' },
  { key: 'download_chat_model', label: 'Descargar phi3:3.8b', icon: Download, description: 'Modelo de chat (2.3GB)' },
  { key: 'download_embed_model', label: 'Descargar embeddings', icon: Download, description: 'nomic-embed-text (274MB)' },
  { key: 'verify_backend', label: 'Verificar backend', icon: Server, description: 'API local puerto 8000' },
  { key: 'init_database', label: 'Inicializar BD', icon: Database, description: 'SQLite + migraciones' },
];

const STATUS_ICONS = {
  not_started: <Clock className="h-5 w-5 text-slate-400" />,
  in_progress: <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />,
  completed: <CheckCircle className="h-5 w-5 text-green-500" />,
  failed: <XCircle className="h-5 w-5 text-red-500" />,
  skipped: <Badge variant="outline" className="text-xs">Omitido</Badge>,
};

const STATUS_COLORS = {
  not_started: 'text-slate-400',
  in_progress: 'text-blue-500',
  completed: 'text-green-500',
  failed: 'text-red-500',
  skipped: 'text-slate-400',
};

export function InitializationPage() {
  const [status, setStatus] = useState<{
    overall_progress: number;
    overall_status: string;
    current_step: string | null;
    steps: Record<string, { status: string; progress: number; message: string; error?: string }>;
    error: string | null;
  } | null>(null);
  
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await api.get('/init/status');
      setStatus(data);
    } catch (err) {
      console.error('Error fetching init status:', err);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Poll for updates while running
  useEffect(() => {
    if (!isRunning) return;
    
    const interval = setInterval(() => {
      fetchStatus();
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isRunning, fetchStatus]);

  const handleStart = async () => {
    try {
      setIsRunning(true);
      setStartTime(Date.now());
      const { data } = await api.post('/init/start', {});
      setStatus(data.status);
    } catch (err: any) {
      console.error('Error starting init:', err);
      alert(err.response?.data?.detail || 'Error al iniciar');
    }
  };

  const handleCancel = async () => {
    try {
      await api.post('/init/cancel');
      setIsRunning(false);
      fetchStatus();
    } catch (err) {
      console.error('Error cancelling:', err);
    }
  };

  const getElapsedTime = () => {
    if (!startTime) return '0:00';
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  if (!status) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-primary-500 mx-auto mb-4" />
          <p className="text-slate-500 dark:text-slate-400">Cargando estado...</p>
        </div>
      </div>
    );
  }

  const { overall_progress, overall_status, current_step, steps, error } = status;
  const isCompleted = overall_status === 'completed';
  const isFailed = overall_status === 'failed';
  const isRunningStatus = overall_status === 'in_progress';

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">AI Workmate</h1>
                <p className="text-sm text-slate-500 dark:text-slate-400">Configuración inicial</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-slate-500 dark:text-slate-400">Tiempo transcurrido</p>
                <p className="font-mono font-medium text-lg">{getElapsedTime()}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-8">
        {/* Overall Progress */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Progreso general</h2>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {isCompleted ? '¡Todo listo! Tu AI Workmate está listo para usar.' :
                   isFailed ? 'Ocurrió un error durante la configuración.' :
                   isRunningStatus ? 'Configurando tu entorno local...' : 'Listo para comenzar'}
                </p>
              </div>
              <div className="text-right">
                <span className={`text-2xl font-bold ${isCompleted ? 'text-green-600' : isFailed ? 'text-red-600' : 'text-primary-600'}`}>
                  {Math.round(status.overall_progress * 100)}%
                </span>
              </div>
            </div>
            <Progress value={status.overall_progress * 100} className="h-3" />
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
              {isRunningStatus && status.current_step && (
                <>
                  Paso actual: <span className="font-medium capitalize">{status.current_step.replace(/_/g, ' ')}</span>
                </>
              )}
              {status.error && (
                <span className="text-red-500">Error: {status.error}</span>
              )}
            </p>
          </CardContent>
        </Card>

        {/* Steps */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary-500" />
              Pasos de configuración
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {STEPS_CONFIG.map((stepConfig, index) => {
                const stepData = status.steps[stepConfig.key] || { status: 'not_started', progress: 0, message: '' };
                const Icon = stepConfig.icon;
                const isCurrent = status.current_step === stepConfig.key;
                const isDone = stepData.status === 'completed';
                const hasError = stepData.status === 'failed';

                return (
                  <div 
                    key={stepConfig.key}
                    className={`relative group transition-all duration-300 ${
                      isCurrent ? 'ring-2 ring-primary-500/50' : ''
                    } ${hasError ? 'border-l-4 border-red-500' : ''}`}
                  >
                    <div className="flex items-start gap-4 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
                      {/* Step Number / Status Icon */}
                      <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                        {STATUS_ICONS[stepData.status as keyof typeof STATUS_ICONS]}
                      </div>

                      {/* Step Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3">
                          <Icon className={`h-5 w-5 ${STATUS_COLORS[stepData.status as keyof typeof STATUS_COLORS]}`} />
                          <div>
                            <h3 className="font-medium text-slate-900 dark:text-slate-100">{stepConfig.label}</h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400">{stepConfig.description}</p>
                          </div>
                          {isCurrent && (
                            <Badge variant="secondary" className="text-xs animate-pulse">
                              En progreso
                            </Badge>
                          )}
                          {hasError && (
                            <Badge variant="destructive" className="text-xs">
                              Error
                            </Badge>
                          )}
                        </div>
                        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 ml-10">
                          {stepData.message || (isCurrent ? 'Procesando...' : 'Pendiente')}
                        </p>
                        {stepData.error && (
                          <p className="mt-2 text-sm text-red-500 ml-10 flex items-center gap-1">
                            <AlertCircle className="h-3.5 w-3.5" />
                            {stepData.error}
                          </p>
                        )}
                        {stepData.progress > 0 && stepData.progress < 1 && stepData.status === 'in_progress' && (
                          <div className="mt-2 ml-10">
                            <Progress value={stepData.progress * 100} className="h-1.5 w-3/4" />
                          </div>
                        )}
                      </div>

                      {/* Step Number */}
                      <div className="flex-shrink-0 w-8 text-center text-slate-400 dark:text-slate-500 font-mono text-lg font-bold">
                        {index + 1}
                      </div>
                    </div>

                    {/* Connector line */}
                    {index < STEPS_CONFIG.length - 1 && (
                      <div className="absolute left-5 top-14 bottom-0 w-0.5 bg-slate-200 dark:bg-slate-700" />
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Error Display */}
        {status.error && (
          <Card className="border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 text-red-700 dark:text-red-300">
                <AlertCircle className="h-6 w-6 flex-shrink-0" />
                <div>
                  <h3 className="font-medium">Error durante la inicialización</h3>
                  <p className="text-sm">{status.error}</p>
                </div>
              </div>
              <div className="mt-4">
                <Button variant="destructive" onClick={handleStart}>
                  Reintentar
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mt-6">
          {!isRunningStatus && !isCompleted && !isFailed && (
            <Button 
              onClick={handleStart} 
              size="lg" 
              className="flex-1 sm:flex-none flex items-center justify-center gap-2"
            >
              <Sparkles className="h-5 w-5" />
              Iniciar configuración
            </Button>
          )}
          
          {isRunningStatus && (
            <Button 
              onClick={handleCancel} 
              variant="secondary" 
              size="lg" 
              className="flex-1 sm:flex-none flex items-center justify-center gap-2"
            >
              <XCircle className="h-5 w-5" />
              Cancelar
            </Button>
          )}

          {isCompleted && (
            <Button 
              onClick={() => window.location.href = '/'} 
              size="lg" 
              className="flex-1 sm:flex-none flex items-center justify-center gap-2"
            >
              <ArrowRight className="h-5 w-5" />
              Entrar a AI Workmate
            </Button>
          )}

          {isFailed && (
            <Button 
              onClick={handleStart} 
              variant="destructive" 
              size="lg" 
              className="flex-1 sm:flex-none flex items-center justify-center gap-2"
            >
              <Loader2 className="h-5 w-5" />
              Reintentar
            </Button>
          )}
        </div>

        {/* Info Box */}
        <Card className="mt-6 border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Shield className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800 dark:text-amber-200">
                <h4 className="font-medium mb-1">Todo corre en tu computadora</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>✅ IA 100% local (Ollama) - ningún dato sale de tu PC</li>
                  <li>✅ Base de datos SQLite local encriptada</li>
                  <li>✅ Tokens Microsoft guardados en Windows Credential Manager</li>
                  <li>✅ Sin servidores en la nube - gratis para siempre</li>
                  <li>✅ Solo conexión externa: Microsoft Graph (tu cuenta 365)</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 py-4">
        <div className="max-w-4xl mx-auto px-6 text-center text-sm text-slate-500 dark:text-slate-400">
          AI Workmate v0.1.0 - Tu compañero de organización local
        </div>
      </footer>
    </div>
  );
}
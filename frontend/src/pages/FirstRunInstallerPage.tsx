import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@/services/api';
import { Card, CardContent, Button } from '@/components/ui';
import {
  AlertCircle,
  Loader2,
  Download,
  Cpu,
  Database,
  HardDrive,
  Search,
  CheckCircle2,
  RefreshCw,
  Mail
} from 'lucide-react';
import { useI18n, formatPercent } from '@/i18n';

interface Dependency {
  name: string;
  installed: boolean;
  version?: string;
  required_version?: string;
  description: string;
  install_url?: string;
  auto_installable: boolean;
}

interface InstallProgress {
  step: string;
  progress: number;
  message: string;
  details?: string;
  completed: boolean;
  error?: string;
}

type InstallStep = 'checking' | 'review' | 'installing' | 'complete' | 'error';

/**
 * Installation order and the catalog key / icon for each component.
 * The display label and description always come from the message catalog so the
 * installer never exposes model names or other technical internals.
 */
const DEPENDENCY_ORDER = ['data_dir', 'database', 'ollama', 'phi3', 'nomic-embed'] as const;

type DependencyKey = (typeof DEPENDENCY_ORDER)[number];

const COMPONENT_META: Record<DependencyKey, { labelKey: string; descriptionKey: string }> = {
  data_dir: { labelKey: 'installer.components.dataDir.label', descriptionKey: 'installer.components.dataDir.description' },
  database: { labelKey: 'installer.components.database.label', descriptionKey: 'installer.components.database.description' },
  ollama: { labelKey: 'installer.components.ollama.label', descriptionKey: 'installer.components.ollama.description' },
  phi3: { labelKey: 'installer.components.chatModel.label', descriptionKey: 'installer.components.chatModel.description' },
  'nomic-embed': { labelKey: 'installer.components.embeddingModel.label', descriptionKey: 'installer.components.embeddingModel.description' },
};

function componentIcon(key: DependencyKey) {
  switch (key) {
    case 'data_dir':
      return <HardDrive className="h-5 w-5" />;
    case 'database':
      return <Database className="h-5 w-5" />;
    case 'phi3':
    case 'nomic-embed':
      return <Search className="h-5 w-5" />;
    default:
      return <Cpu className="h-5 w-5" />;
  }
}

const POLL_INTERVAL_MS = 1000;
const POLL_RETRY_MS = 2000;

export function FirstRunInstallerPage() {
  const { t } = useI18n();
  const [step, setStep] = useState<InstallStep>('checking');
  const [dependencies, setDependencies] = useState<Partial<Record<DependencyKey, Dependency>>>({});
  const [progress, setProgress] = useState<InstallProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Kept in a ref so the polling loop never captures a stale `step`, which
  // previously restarted itself from an outdated closure.
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelled = useRef(false);

  const checkDependencies = useCallback(async () => {
    setStep('checking');
    setError(null);
    try {
      const status = await api.getInstallerStatus();
      setDependencies(status ?? {});
      setStep('review');
    } catch (err) {
      console.error('Error checking dependencies:', err);
      setError('installer.checkFailed');
      setStep('error');
    }
  }, []);

  const pollProgress = useCallback(async () => {
    try {
      const current = await api.getInstallProgress();
      setProgress(current);

      if (current?.completed || current?.step === 'complete') {
        const status = await api.getInstallerStatus();
        setDependencies(status ?? {});
        setStep('complete');
        return;
      }

      if (current?.error) {
        setError('installer.unexpectedError');
        setStep('error');
        return;
      }

      pollTimer.current = setTimeout(() => {
        void pollProgress();
      }, POLL_INTERVAL_MS);
    } catch (err) {
      console.error('Error polling progress:', err);
      pollTimer.current = setTimeout(() => {
        void pollProgress();
      }, POLL_RETRY_MS);
    }
  }, []);

  const startInstallation = useCallback(async () => {
    setError(null);
    setProgress(null);
    setStep('installing');
    try {
      await api.installDependencies();
      await pollProgress();
    } catch (err) {
      console.error('Error starting installation:', err);
      setError('installer.installFailed');
      setStep('error');
    }
  }, [pollProgress]);

  const retry = useCallback(() => {
    void checkDependencies();
  }, [checkDependencies]);

  const goToAuth = useCallback(async () => {
    try {
      await api.markInitialized();
    } catch (err) {
      console.error('Error marking first run as complete:', err);
    }
    window.location.href = '/auth';
  }, []);

  useEffect(() => {
    void checkDependencies();
    return () => {
      cancelled.current = true;
      if (pollTimer.current) {
        clearTimeout(pollTimer.current);
      }
    };
  }, [checkDependencies]);

  useEffect(() => {
    if (step === 'installing' && !cancelled.current) {
      void pollProgress();
    }
  }, [step, pollProgress]);

  const knownComponents = DEPENDENCY_ORDER.filter((key) => dependencies[key]);
  const missingCount = DEPENDENCY_ORDER.filter((key) => dependencies[key] && !dependencies[key]?.installed).length;
  const readyCount = DEPENDENCY_ORDER.length - missingCount;

  if (step === 'checking') {
    return (
      <Shell>
        <div className="text-center mb-8">
          <div className="p-4 rounded-full bg-primary-100 dark:bg-primary-900/30 inline-flex mb-4">
            <Loader2 className="h-10 w-10 text-primary-600 dark:text-primary-400 animate-spin" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            {t('installer.title')}
          </h1>
          <p className="text-slate-500 dark:text-slate-400">{t('installer.checking')}</p>
        </div>
      </Shell>
    );
  }

  if (step === 'error') {
    return (
      <Shell narrow>
        <div className="text-center">
          <div className="p-3 rounded-full bg-red-100 dark:bg-red-900/30 inline-flex mb-4">
            <AlertCircle className="h-8 w-8 text-red-600 dark:text-red-400" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            {t('installer.errorTitle')}
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mb-6">
            {error ? t(error) : t('installer.unexpectedError')}
          </p>
          <div className="flex gap-3 justify-center">
            <Button variant="secondary" onClick={retry}>
              <RefreshCw className="h-4 w-4" />
              {t('installer.retry')}
            </Button>
          </div>
        </div>
      </Shell>
    );
  }

  if (step === 'installing') {
    const percent = progress?.progress ?? 0;
    return (
      <Shell>
        <div className="text-center mb-8">
          <div className="p-4 rounded-full bg-primary-100 dark:bg-primary-900/30 inline-flex mb-4">
            <Download className="h-10 w-10 text-primary-600 dark:text-primary-400 animate-spin" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            {t('installer.installing')}
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            {progress?.message ? t(progress.message) : t('installer.starting')}
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-600 dark:text-slate-400">
                {t('installer.progress')}
              </span>
              <span className="font-mono font-bold text-primary-600 dark:text-primary-400">
                {formatPercent(percent / 100)}
              </span>
            </div>
            <div
              className="h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden"
              role="progressbar"
              aria-valuenow={percent}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className="h-full bg-primary-600 transition-all duration-300 ease-out"
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {knownComponents.map((key) => {
              const meta = COMPONENT_META[key];
              const isReady = Boolean(dependencies[key]?.installed);
              return (
                <div
                  key={key}
                  className={`p-3 rounded-lg text-center ${
                    isReady
                      ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                      : 'bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-center gap-2 mb-1">
                    {componentIcon(key)}
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      {t(meta.labelKey)}
                    </span>
                  </div>
                  <div className="flex items-center justify-center gap-1">
                    {isReady ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <Loader2 className="h-4 w-4 text-primary-500 animate-spin" />
                    )}
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {isReady ? t('installer.ready') : t('installer.installingShort')}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Shell>
    );
  }

  if (step === 'complete') {
    return (
      <Shell>
        <div className="text-center mb-8">
          <div className="p-4 rounded-full bg-green-100 dark:bg-green-900/30 inline-flex mb-4">
            <CheckCircle2 className="h-10 w-10 text-green-600 dark:text-green-400" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
            {t('installer.completeTitle')}
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            {t('installer.completeSubtitle')}
          </p>
        </div>

        <div className="space-y-3 mb-8">
          {knownComponents.map((key) => {
            const meta = COMPONENT_META[key];
            return (
              <div
                key={key}
                className="flex items-center gap-4 p-4 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800"
              >
                <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900/30">
                  {componentIcon(key)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-green-800 dark:text-green-300">
                    {t(meta.labelKey)}
                  </p>
                  <p className="text-sm text-green-600 dark:text-green-400">
                    {t(meta.descriptionKey)}
                  </p>
                </div>
                <CheckCircle2 className="h-5 w-5 text-green-500" />
              </div>
            );
          })}
        </div>

        <Button className="w-full" size="lg" onClick={goToAuth}>
          {t('installer.continueToOutlook')}
          <Mail className="h-4 w-4 ml-2" />
        </Button>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">
          {t('installer.reviewTitle')}
        </h1>
        <p className="text-slate-500 dark:text-slate-400">{t('installer.reviewSubtitle')}</p>
      </div>

      <div className="space-y-3 mb-6">
        {knownComponents.map((key) => {
          const meta = COMPONENT_META[key];
          const isReady = Boolean(dependencies[key]?.installed);
          return (
            <div
              key={key}
              className="flex items-center gap-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700"
            >
              <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-700">
                {componentIcon(key)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-slate-900 dark:text-slate-100">
                  {t(meta.labelKey)}
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {t(meta.descriptionKey)}
                </p>
              </div>
              {isReady ? (
                <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
              ) : (
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 shrink-0">
                  {t('installer.notReady')}
                </span>
              )}
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-center text-sm text-slate-500 dark:text-slate-400 mb-6">
        {t('work.counts.componentsReady', { count: readyCount })}
      </div>

      <div className="flex gap-3">
        <Button variant="secondary" className="flex-1" onClick={retry}>
          {t('installer.retry')}
        </Button>
        <Button
          className="flex-1"
          onClick={startInstallation}
          disabled={missingCount === 0}
        >
          <Download className="h-4 w-4 mr-2" />
          {missingCount === 0 ? t('installer.completeTitle') : t('installer.start')}
        </Button>
      </div>
    </Shell>
  );
}

function Shell({ children, narrow = false }: { children: React.ReactNode; narrow?: boolean }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
      <Card className={narrow ? 'w-full max-w-md' : 'w-full max-w-2xl'}>
        <CardContent className="py-10">{children}</CardContent>
      </Card>
    </div>
  );
}
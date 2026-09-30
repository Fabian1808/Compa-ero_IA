import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { I18nProvider, useI18n } from './i18n'
import './styles/globals.css'

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {error: Error | null}> {
  constructor(props: any) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    if (!this.state.error) {
      return this.props.children;
    }
    return <ErrorFallback error={this.state.error} />;
  }
}

/**
 * Reads user-facing copy from the catalog, so even the crash screen stays
 * inside the terminology rules. The raw stack is shown collapsed under a
 * technical heading because it is diagnostic output, not product language.
 */
function ErrorFallback({ error }: { error: Error }) {
  const { t } = useI18n();

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-50 dark:bg-slate-950">
      <div className="w-full max-w-2xl rounded-lg p-6 bg-white dark:bg-slate-900 border border-red-200 dark:border-red-800">
        <h2 className="text-xl font-semibold text-red-700 dark:text-red-400">
          {t('app.error.title')}
        </h2>
        <p className="mt-2 text-slate-600 dark:text-slate-300">{t('app.error.description')}</p>
        <details className="mt-4">
          <summary className="cursor-pointer text-sm text-slate-500 dark:text-slate-400">
            {t('app.error.details')}
          </summary>
          <pre className="mt-2 p-3 rounded bg-slate-100 dark:bg-slate-800 text-xs overflow-auto" style={{whiteSpace: 'pre-wrap', wordBreak: 'break-word'}}>
            {error.toString()}
            {'\n'}
            {error.stack}
          </pre>
        </details>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <I18nProvider>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </I18nProvider>
  </React.StrictMode>,
)
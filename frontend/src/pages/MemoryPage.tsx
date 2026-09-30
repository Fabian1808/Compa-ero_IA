import { useState } from 'react';
import { Card, CardContent, Input, Button, Badge, ScrollArea } from '@/components/ui';
import { Brain, Search, Database, Trash2, Download, RefreshCw, Loader2, X, MessageSquare, FileText, Calendar, Flag, CheckSquare, Users } from 'lucide-react';

interface SearchResult {
  id: string;
  score: number;
  content: string;
  source_type: string;
  source_id: string;
  metadata: Record<string, any>;
  search_type: string;
}

interface MemoryStats {
  total_vectors: number;
  by_source_type: Record<string, number>;
  collection: string;
}

const SOURCE_ICONS: Record<string, any> = {
  email: MessageSquare,
  task: CheckSquare,
  commitment: Flag,
  followup: MessageSquare,
  meeting: Calendar,
  project: FileText,
  document: FileText,
  chat: Users,
};

const SOURCE_LABELS: Record<string, string> = {
  email: 'Correo',
  task: 'Tarea',
  commitment: 'Compromiso',
  followup: 'Seguimiento',
  meeting: 'Reunión',
  project: 'Proyecto',
  document: 'Documento',
  chat: 'Chat',
};

export function MemoryPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = async () => {
    if (!query.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const { api } = await import('@/services/api');
      const data = await api.search(query, 20);
      setResults(data.results || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al buscar');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const { api } = await import('@/services/api');
      const data = await api.getMemoryStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats', err);
    }
  };

  const handleReindex = async () => {
    setIsReindexing(true);
    try {
      const { api } = await import('@/services/api');
      await api.reindexMemory();
      await loadStats();
      if (query.trim()) await search();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al reindexar');
    } finally {
      setIsReindexing(false);
    }
  };

  const handleClear = async () => {
    if (!confirm('¿Estás seguro? Esto borrará toda la memoria semántica.')) return;
    
    try {
      const { api } = await import('@/services/api');
      await api.clearMemory();
      setResults([]);
      await loadStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al limpiar');
    }
  };

  const getSourceIcon = (sourceType: string) => {
    const Icon = SOURCE_ICONS[sourceType] || FileText;
    return <Icon className="h-4 w-4" />;
  };

  const getSourceLabel = (sourceType: string) => SOURCE_LABELS[sourceType] || sourceType;

  // Load stats on mount
  const [mounted, setMounted] = useState(false);
  if (!mounted) {
    setMounted(true);
    loadStats();
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Memoria Semántica</h1>
          <p className="text-slate-500 dark:text-slate-400">Búsqueda híbrida (semántica + keywords) en tu trabajo</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleReindex} disabled={isReindexing}>
            <RefreshCw className={`h-4 w-4 ${isReindexing ? 'animate-spin' : ''}`} />
            Reindexar
          </Button>
          <Button variant="destructive" onClick={handleClear} disabled={isReindexing}>
            <Trash2 className="h-4 w-4" />
            Limpiar
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-700 dark:text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={() => setError(null)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      <Card>
        <CardContent className="py-4">
          <div className="flex gap-3 mb-6">
            <Input
              placeholder="Busca en tu memoria... (ej: qué prometí a Juan, deadline contratos, proyecto HES)"
              className="flex-1"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && search()}
              leftIcon={<Search className="h-4 w-4" />}
              disabled={isLoading}
            />
            <Button onClick={search} disabled={isLoading || !query.trim()}>
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Buscar'}
            </Button>
          </div>

          {stats && (
            <div className="mb-4 flex flex-wrap gap-2">
              <Badge variant="secondary">
                <Brain className="h-3 w-3 mr-1" />
                {stats.total_vectors} vectores indexados
              </Badge>
              {Object.entries(stats.by_source_type).map(([type, count]) => (
                count > 0 && (
                  <Badge key={type} variant="outline">
                    {getSourceIcon(type)}
                    {getSourceLabel(type)}: {count}
                  </Badge>
                )
              ))}
            </div>
          )}

          {results.length > 0 && (
            <ScrollArea className="max-h-96">
              <div className="space-y-3">
                {results.map((result, index) => (
                  <Card key={`${result.id}-${index}`} className="border-slate-200 dark:border-slate-700">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                          {getSourceIcon(result.source_type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline" className="text-xs">
                              {getSourceLabel(result.source_type)}
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {result.search_type === 'keyword' ? '🔍 Keyword' : '🧠 Semántico'}
                            </Badge>
                            <span className="text-xs text-slate-500 dark:text-slate-400">
                              Score: {(result.score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="text-slate-900 dark:text-slate-100 text-sm leading-relaxed">
                            {result.content}
                          </p>
                          {result.metadata && Object.keys(result.metadata).length > 0 && (
                            <details className="mt-2">
                              <summary className="text-xs text-slate-500 dark:text-slate-400 cursor-pointer">
                                Ver metadatos
                              </summary>
                              <pre className="mt-1 text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 p-2 rounded overflow-auto max-h-32">
                                {JSON.stringify(result.metadata, null, 2)}
                              </pre>
                            </details>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          )}

          {results.length === 0 && !isLoading && query.trim() && (
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              <Brain className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
              <p>No se encontraron resultados para "<span className="font-medium">{query}</span>"</p>
              <p className="text-sm mt-1">Intenta con otras palabras clave o reindexa la memoria</p>
            </div>
          )}

          {results.length === 0 && !isLoading && !query.trim() && (
            <div className="space-y-2 text-sm text-slate-500 dark:text-slate-400">
              <p>La búsqueda semántica te permite encontrar información usando lenguaje natural.</p>
              <p className="font-medium">Ejemplos de consultas:</p>
              <ul className="list-disc list-inside space-y-1 mt-1">
                <li>"¿Qué prometí hacer esta semana?"</li>
                <li>"¿Qué correos hablan del proyecto HES?"</li>
                <li>"¿Qué tareas tengo bloqueadas?"</li>
                <li>"¿Qué deadlines vienen esta semana?"</li>
                <li>"¿Qué me dijo Juan sobre el presupuesto?"</li>
                <li>"Reuniones con el equipo de ventas"</li>
              </ul>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="py-6 text-center">
            <Database className="h-10 w-10 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
            <h3 className="font-medium text-slate-900 dark:text-slate-100 mb-1">Estadísticas</h3>
            <p className="text-slate-500 dark:text-slate-400 text-sm">
              {stats?.total_vectors || 0} vectores en {stats?.collection || 'ai_workmate_memory'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="py-6 text-center">
            <Download className="h-10 w-10 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
            <h3 className="font-medium text-slate-900 dark:text-slate-100 mb-1">Exportar</h3>
            <Button variant="secondary" size="sm" className="mt-2" disabled>
              Exportar memoria (próximamente)
            </Button>
          </CardContent>
        </Card>

        <Card className="border-red-200 dark:border-red-800">
          <CardContent className="py-6 text-center">
            <Trash2 className="h-10 w-10 mx-auto text-red-400 mb-3" />
            <h3 className="font-medium text-red-600 dark:text-red-400 mb-1">Limpiar</h3>
            <Button variant="destructive" size="sm" className="mt-2" onClick={handleClear} disabled={isReindexing}>
              Borrar toda la memoria
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
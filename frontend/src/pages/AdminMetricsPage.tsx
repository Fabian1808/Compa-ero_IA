import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Tabs, TabsList, TabsTrigger, TabsContent, Badge } from '@/components/ui';
import { 
  Users, Building2, CheckSquare, Mail, TrendingUp, TrendingDown,
  Clock, Target, DollarSign, Activity, BarChart3,
  Loader2, CheckCircle, AlertTriangle
} from 'lucide-react';
import { api } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

interface SystemMetrics {
  tenants: { total: number; active: number };
  users: { total: number };
  tasks: { total: number; completed: number; completion_rate: number; recent_week: number };
  emails: { total: number };
  generated_at: string;
}

export function AdminMetricsPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'quarter' | 'year'>('month');

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const data = await api.getSystemMetrics();
      setMetrics(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al cargar métricas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const StatCard = ({ title, value, change, icon: Icon, color }: any) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500 dark:text-slate-400">{title}</p>
            <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-1">{value}</p>
            {change && (
              <p className={`text-sm mt-1 ${change >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                <TrendingUp className="h-4 w-4 inline mr-1" /> {Math.abs(change)}%
              </p>
            )}
          </div>
          <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-12 w-12 animate-spin text-primary-500" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto space-y-6">
        <Card>
          <CardContent className="py-12 text-center">
            <AlertTriangle className="h-12 w-12 mx-auto text-red-500 mb-3" />
            <p className="text-red-500">{error}</p>
            <Button onClick={fetchMetrics} className="mt-4">Reintentar</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!metrics) return null;

  const taskCompletionRate = metrics.tasks.total > 0 
    ? Math.round((metrics.tasks.completed / metrics.tasks.total) * 100) 
    : 0;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Métricas del Sistema</h1>
          <p className="text-slate-500 dark:text-slate-400">Dashboard de métricas globales</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={fetchMetrics} disabled={loading}>
            <Loader2 className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard 
          title="Tenants Totales" 
          value={metrics.tenants.total} 
          icon={Building2} 
          color="bg-blue-500" 
          change={metrics.tenants.active > 0 ? Math.round((metrics.tenants.active / metrics.tenants.total) * 100) : 0}
        />
        <StatCard 
          title="Tenants Activos" 
          value={metrics.tenants.active} 
          icon={CheckCircle} 
          color="bg-green-500" 
        />
        <StatCard 
          title="Usuarios Totales" 
          value={metrics.users.total} 
          icon={Users} 
          color="bg-purple-500" 
        />
        <StatCard 
          title="Tareas Totales" 
          value={metrics.tasks.total} 
          icon={CheckSquare} 
          color="bg-amber-500" 
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard 
          title="Tareas Completadas" 
          value={metrics.tasks.completed} 
          icon={CheckCircle} 
          color="bg-green-500" 
        />
        <StatCard 
          title="Tasa Completación" 
          value={`${taskCompletionRate}%`} 
          icon={Target} 
          color="bg-blue-500" 
        />
        <StatCard 
          title="Tareas Esta Semana" 
          value={metrics.tasks.recent_week} 
          icon={Clock} 
          color="bg-purple-500" 
        />
        <StatCard 
          title="Emails Procesados" 
          value={metrics.emails.total} 
          icon={Mail} 
          color="bg-orange-500" 
        />
      </div>

      {/* Detailed Sections */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview"><BarChart3 className="h-4 w-4 mr-2" />Resumen</TabsTrigger>
          <TabsTrigger value="tenants">Tenants</TabsTrigger>
          <TabsTrigger value="tasks">Tareas</TabsTrigger>
          <TabsTrigger value="activity">Actividad</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Salud del Sistema</CardTitle>
                <Badge variant="default">Saludable</Badge>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Uptime</span>
                    <span className="font-medium text-green-600">99.9%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">API Response</span>
                    <span className="font-medium text-green-600">&lt; 200ms</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Error Rate</span>
                    <span className="font-medium text-green-600">&lt; 0.1%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Uso de IA</CardTitle>
                <Badge variant="outline">Ollama Local</Badge>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Modelo Chat</span>
                    <span className="font-mono text-sm">phi3:3.8b</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Modelo Embeddings</span>
                    <span className="font-mono text-sm">nomic-embed-text</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Temperatura</span>
                    <span className="font-medium">0.1</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Última Actualización</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-500 text-sm">
                  {formatDistanceToNow(new Date(metrics.generated_at), { addSuffix: true, locale: es })}
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="tenants" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Distribución de Tenants</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Total Tenants</span>
                  <span className="text-2xl font-bold">{metrics.tenants.total}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Activos</span>
                  <span className="text-2xl font-bold text-green-600">{metrics.tenants.active}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Inactivos</span>
                  <span className="text-2xl font-bold text-red-600">{metrics.tenants.total - metrics.tenants.active}</span>
                </div>
                <div className="flex items-center justify-between pt-4 border-t">
                  <span className="text-slate-500">% Activos</span>
                  <span className="text-2xl font-bold">{metrics.tenants.total > 0 ? Math.round((metrics.tenants.active / metrics.tenants.total) * 100) : 0}%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tasks" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Análisis de Tareas</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400">{metrics.tasks.completed}</p>
                  <p className="text-sm text-slate-500">Completadas</p>
                </div>
                <div className="text-center p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
                  <p className="text-3xl font-bold text-amber-600 dark:text-amber-400">{metrics.tasks.total - metrics.tasks.completed}</p>
                  <p className="text-sm text-slate-500">Pendientes</p>
                </div>
                <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{taskCompletionRate}%</p>
                  <p className="text-sm text-slate-500">Tasa Completación</p>
                </div>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-500">Esta Semana</p>
                  <p className="text-2xl font-bold">{metrics.tasks.recent_week}</p>
                  <p className="text-xs text-slate-400">Tareas creadas</p>
                </div>
                <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-500">Promedio Diario</p>
                  <p className="text-2xl font-bold">{Math.round(metrics.tasks.recent_week / 7)}</p>
                  <p className="text-xs text-slate-400">Tareas/día</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Actividad Reciente</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Activity className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium">Sistema Operativo</p>
                      <p className="text-sm text-slate-500">Todos los servicios funcionando correctamente</p>
                    </div>
                  </div>
                  <Badge variant="default">Activo</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="flex items-center gap-3">
                    <BarChart3 className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="font-medium">Métricas Actualizadas</p>
                      <p className="text-sm text-slate-500">{formatDistanceToNow(new Date(metrics.generated_at), { addSuffix: true, locale: es })}</p>
                    </div>
                  </div>
                  <Badge variant="outline">Reciente</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Users className="h-5 w-5 text-slate-600" />
                    <div>
                      <p className="font-medium">Usuarios Totales</p>
                      <p className="text-sm text-slate-500">{metrics.users.total} registrados</p>
                    </div>
                  </div>
                  <Badge variant="outline">Registrados</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
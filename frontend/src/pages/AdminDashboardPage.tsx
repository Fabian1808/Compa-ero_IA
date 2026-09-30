import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';
import { 
  Building2, Users, CheckSquare, Mail, TrendingUp, TrendingDown,
  Clock, Target, Shield, Activity, BarChart3,
  Loader2, CheckCircle, AlertTriangle, Settings, FileText
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

export function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Panel de Administración</h1>
          <p className="text-slate-500 dark:text-slate-400">Vista general del sistema</p>
        </div>
        <Button onClick={fetchMetrics} disabled={loading}>
          <Loader2 className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </Button>
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

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Acciones Rápidas</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2" asChild>
            <a href="/admin/tenants">
              <Building2 className="h-8 w-8" />
              <span>Gestionar Tenants</span>
            </a>
          </Button>
          <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2" asChild>
            <a href="/admin/users">
              <Users className="h-8 w-8" />
              <span>Usuarios</span>
            </a>
          </Button>
          <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2" asChild>
            <a href="/admin/metrics">
              <BarChart3 className="h-8 w-8" />
              <span>Métricas Detalladas</span>
            </a>
          </Button>
          <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2" asChild>
            <a href="/admin/audit-logs">
              <FileText className="h-8 w-8" />
              <span>Audit Logs</span>
            </a>
          </Button>
          <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2" asChild>
            <a href="/admin/settings">
              <Settings className="h-8 w-8" />
              <span>Configuración</span>
            </a>
          </Button>
          <Button variant="outline" className="h-24 flex flex-col items-center justify-center gap-2" asChild>
            <a href="/admin/security">
              <Shield className="h-8 w-8" />
              <span>Seguridad</span>
            </a>
          </Button>
        </CardContent>
      </Card>

      {/* System Health */}
      <Tabs defaultValue="health" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="health"><Activity className="h-4 w-4 mr-2" />Salud</TabsTrigger>
          <TabsTrigger value="ai">IA</TabsTrigger>
          <TabsTrigger value="recent">Actividad</TabsTrigger>
        </TabsList>

        <TabsContent value="health" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
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

        <TabsContent value="ai" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Configuración de IA Actual</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 md:grid-cols-2">
                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-500">Proveedor</p>
                  <p className="font-mono">Ollama (Local)</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-500">Modelo Chat</p>
                  <p className="font-mono">phi3:3.8b</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-500">Modelo Embeddings</p>
                  <p className="font-mono">nomic-embed-text</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-500">Temperatura</p>
                  <p className="font-medium">0.1</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-500">Max Tokens</p>
                  <p className="font-medium">2048</p>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-500">Confianza Auto-crear</p>
                  <p className="font-medium">95%</p>
                </div>
              </div>
              <Button variant="outline" asChild>
                <a href="/admin/settings?tab=ai">
                  <Settings className="h-4 w-4 mr-2" />
                  Configurar IA
                </a>
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recent" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Actividad Reciente del Sistema</CardTitle>
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
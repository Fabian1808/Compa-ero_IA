import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Input, Button, Badge, Select, SelectTrigger, SelectValue, SelectContent, SelectItem, Table, TableHeader, TableRow, TableHead, TableBody, TableCell, Pagination, Dialog, DialogContent, DialogHeader, DialogTitle, Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui';
import { 
  FileText, Search, Filter, MoreHorizontal, 
  Loader2, Eye, Download, Clock, User, Globe,
  AlertTriangle, CheckCircle
} from 'lucide-react';
import { api } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

interface AuditLog {
  id: string;
  tenant_id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details_json: string;
  ip_address: string;
  user_agent: string;
  created_at: string;
}

export function AdminAuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 20;
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [showDetail, setShowDetail] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'today' | 'week' | 'month'>('all');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let startDate: string | undefined;
      let endDate: string | undefined;
      const now = new Date();
      
      if (activeTab === 'today') {
        startDate = now.toISOString().split('T')[0];
        endDate = startDate;
      } else if (activeTab === 'week') {
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        startDate = weekAgo.toISOString().split('T')[0];
      } else if (activeTab === 'month') {
        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        startDate = monthAgo.toISOString().split('T')[0];
      }

      const data = await api.getAuditLogs({
        page,
        per_page: perPage,
        action: actionFilter,
        start_date: startDate,
        end_date: endDate,
      });
      setLogs(data.logs);
      setTotal(data.total);
    } catch (err: any) {
      console.error('Error loading audit logs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, actionFilter, activeTab]);

  const getActionBadge = (action: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
      create: 'default',
      update: 'secondary',
      delete: 'destructive',
      login: 'outline',
      logout: 'outline',
      invite: 'secondary',
      accept: 'default',
      revoke: 'destructive',
    };
    return <Badge variant={variants[action] || 'outline'}>{action}</Badge>;
  };

  const formatDetails = (json: string) => {
    try {
      return JSON.parse(json);
    } catch {
      return json;
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Audit Logs</h1>
          <p className="text-slate-500 dark:text-slate-400">Historial de acciones del sistema</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="all">Todos</TabsTrigger>
          <TabsTrigger value="today">Hoy</TabsTrigger>
          <TabsTrigger value="week">Esta semana</TabsTrigger>
          <TabsTrigger value="month">Este mes</TabsTrigger>
        </TabsList>
      </Tabs>

      <Card>
        <CardHeader className="pb-2">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Buscar por acción, recurso, IP..."
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
                className="pl-10"
              />
            </div>
            <Select value={actionFilter} onValueChange={v => { setActionFilter(v); setPage(1); }} className="w-40">
              <SelectTrigger><SelectValue placeholder="Acción" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="">Todas</SelectItem>
                <SelectItem value="create">Crear</SelectItem>
                <SelectItem value="update">Actualizar</SelectItem>
                <SelectItem value="delete">Eliminar</SelectItem>
                <SelectItem value="login">Login</SelectItem>
                <SelectItem value="invite">Invitar</SelectItem>
              </SelectContent>
            </Select>
            <Select value={resourceFilter} onValueChange={v => { setResourceFilter(v); setPage(1); }} className="w-40">
              <SelectTrigger><SelectValue placeholder="Recurso" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="">Todos</SelectItem>
                <SelectItem value="tenant">Tenant</SelectItem>
                <SelectItem value="user">Usuario</SelectItem>
                <SelectItem value="task">Tarea</SelectItem>
                <SelectItem value="email">Email</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8"><Loader2 className="h-8 w-8 animate-spin text-primary-500" /></div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 mx-auto text-slate-300 dark:text-slate-600 mb-3" />
              <p className="text-slate-500 dark:text-slate-400">No se encontraron logs</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fecha</TableHead>
                      <TableHead>Acción</TableHead>
                      <TableHead>Recurso</TableHead>
                      <TableHead>Usuario</TableHead>
                      <TableHead>IP</TableHead>
                      <TableHead className="w-40">Detalles</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.map(log => (
                      <TableRow key={log.id} className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800" onClick={() => { setSelectedLog(log); setShowDetail(true); }}>
                        <TableCell className="text-sm text-slate-500 dark:text-slate-400">
                          {formatDistanceToNow(new Date(log.created_at), { addSuffix: true, locale: es })}
                        </TableCell>
                        <TableCell>{getActionBadge(log.action)}</TableCell>
                        <TableCell className="font-mono text-sm">{log.resource_type}:{log.resource_id?.slice(0, 8)}</TableCell>
                        <TableCell className="text-sm text-slate-500 dark:text-slate-400">{log.user_id?.slice(0, 8)}</TableCell>
                        <TableCell className="font-mono text-sm">{log.ip_address || '—'}</TableCell>
                        <TableCell className="max-w-xs truncate">
                          {Object.keys(formatDetails(log.details_json)).length > 0 ? (
                            Object.entries(formatDetails(log.details_json)).map(([k, v]) => (
                              <span key={k} className="inline-block bg-slate-100 dark:bg-slate-800 text-xs px-1.5 py-0.5 rounded mr-1">{k}: {String(v).slice(0, 20)}</span>
                            ))
                          ) : '—'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <Pagination
                page={page}
                total={total}
                perPage={perPage}
                onPageChange={setPage}
              />
            </>
          )}
        </CardContent>
      </Card>

      {showDetail && selectedLog && (
        <Dialog open={showDetail} onOpenChange={setShowDetail}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Detalle del Log</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs text-slate-500">ID</label>
                  <code className="text-sm font-mono bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">{selectedLog.id}</code>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-500">Fecha</label>
                  <span className="text-sm">{new Date(selectedLog.created_at).toLocaleString()}</span>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-500">Acción</label>
                  {getActionBadge(selectedLog.action)}
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-500">Recurso</label>
                  <code className="text-sm font-mono">{selectedLog.resource_type}</code>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-500">Recurso ID</label>
                  <code className="text-sm font-mono">{selectedLog.resource_id}</code>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-500">Usuario ID</label>
                  <code className="text-sm font-mono">{selectedLog.user_id}</code>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-500">IP</label>
                  <code className="text-sm font-mono">{selectedLog.ip_address || '—'}</code>
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-500">Tenant</label>
                  <code className="text-sm font-mono">{selectedLog.tenant_id?.slice(0, 8)}</code>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-xs text-slate-500">Detalles (JSON)</label>
                <pre className="bg-slate-900 text-slate-100 p-4 rounded text-xs overflow-auto max-h-64">
                  {JSON.stringify(formatDetails(selectedLog.details_json), null, 2)}
                </pre>
              </div>
              <div className="space-y-2">
                <label className="text-xs text-slate-500">User Agent</label>
                <pre className="bg-slate-100 dark:bg-slate-800 p-2 rounded text-xs overflow-auto max-h-20">
                  {selectedLog.user_agent || '—'}
                </pre>
              </div>
            </div>
            <div className="flex justify-end pt-4 border-t">
              <Button variant="secondary" onClick={() => setShowDetail(false)}>Cerrar</Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

function getActionBadge(action: string) {
  const variants: Record<string, 'default' | 'secondary' | 'outline' | 'destructive'> = {
    create: 'default',
    update: 'secondary',
    delete: 'destructive',
    login: 'outline',
    logout: 'outline',
    invite: 'secondary',
    accept: 'default',
    revoke: 'destructive',
  };
  return <Badge variant={variants[action] || 'outline'}>{action}</Badge>;
}